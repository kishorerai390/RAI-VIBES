import re
import time
import logging
from collections import defaultdict, deque
from datetime import timedelta
from typing import Dict, Optional
import discord
from discord.ext import commands

import database

logger = logging.getLogger("AntiSpam")

EMOJI_REGEX = re.compile(r"<a?:[a-zA-Z0-9_]+:[0-9]+>|[\U00010000-\U0010ffff]", flags=re.UNICODE)
REPEATED_CHAR_REGEX = re.compile(r"(.)\1{18,}")

class AntiSpam(commands.Cog):
    """Anti-Spam Engine detecting message flooding, character spam, emoji floods, and repeated messages."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # User message history: user_id -> deque of timestamps
        self.msg_timestamps: Dict[int, deque] = defaultdict(lambda: deque(maxlen=20))
        # User last messages: user_id -> deque of (content, timestamp)
        self.msg_history: Dict[int, deque] = defaultdict(lambda: deque(maxlen=5))
        # User violation strike tracker: guild_id -> user_id -> count
        self.violations: Dict[int, Dict[int, int]] = defaultdict(lambda: defaultdict(int))
        # Channel burst velocity tracker
        self.channel_rates: Dict[int, deque] = defaultdict(lambda: deque(maxlen=30))
        self.active_slowmodes = set()

    async def get_log_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        chan = guild.get_channel(1546593526073135107) or guild.get_channel(1546540192343523399)
        if chan and isinstance(chan, discord.TextChannel):
            return chan
        settings = await database.get_guild_settings(guild.id)
        log_id = settings.get("log_channel_id")
        if log_id:
            channel = guild.get_channel(log_id)
            if channel and isinstance(channel, discord.TextChannel):
                return channel
        for ch in guild.text_channels:
            if "security" in ch.name.lower() or "audit" in ch.name.lower():
                return ch
        return None

    async def handle_violation(self, message: discord.Message, reason: str):
        guild = message.guild
        member = message.author
        if not isinstance(member, discord.Member):
            return

        # Delete the violating message immediately
        try:
            await message.delete()
        except Exception:
            pass

        self.violations[guild.id][member.id] += 1
        strikes = self.violations[guild.id][member.id]

        log_channel = await self.get_log_channel(guild)

        if strikes == 1:
            # 1st violation: Warning
            try:
                warn_msg = await message.channel.send(
                    f"⚠️ {member.mention}, please stop spamming ({reason}). *[Warning 1/3]*",
                    delete_after=6
                )
            except Exception:
                pass
            punishment = "Warning"
        elif strikes == 2:
            # 2nd violation: 5-minute timeout
            duration = timedelta(minutes=5)
            try:
                await member.timeout(duration, reason=f"[Anti-Spam] {reason} (Strike 2)")
                await message.channel.send(
                    f"🔇 {member.mention} has been timed out for 5 minutes for continued spam.",
                    delete_after=8
                )
            except Exception as e:
                logger.debug(f"Timeout strike 2 error: {e}")
            punishment = "5-Minute Timeout"
        elif strikes == 3:
            # 3rd violation: 1-hour timeout
            duration = timedelta(hours=1)
            try:
                await member.timeout(duration, reason=f"[Anti-Spam] Repeated chat flooding (Strike 3)")
                await message.channel.send(
                    f"🔇 {member.mention} has been timed out for 1 hour for persistent chat abuse.",
                    delete_after=10
                )
            except Exception as e:
                logger.debug(f"Timeout strike 3 error: {e}")
            punishment = "1-Hour Timeout"
        else:
            # Severe repeated spam: 24-hour timeout or kick
            duration = timedelta(days=1)
            try:
                await member.timeout(duration, reason="[Anti-Spam] Excessive relentless spam")
            except Exception:
                try:
                    await member.kick(reason="[Anti-Spam] Relentless spamming after multiple timeouts")
                except Exception:
                    pass
            punishment = "24-Hour Timeout / Kick"

        # Record infraction in SQLite
        await database.record_infraction(
            guild.id,
            member.id,
            f"SPAM_{punishment.upper()}",
            reason,
            moderator_id=self.bot.user.id
        )

        # Log embed
        if log_channel:
            embed = discord.Embed(
                title="🛡️ Anti-Spam Enforcement",
                description=f"**User:** {member.mention} (`{member.name}` • ID: `{member.id}`)\n**Reason:** {reason}\n**Action Taken:** `{punishment}` (Strike {strikes})",
                color=0xFFAA00
            )
            embed.set_footer(text=f"Channel: #{message.channel.name}")
            embed.timestamp = discord.utils.utcnow()
            try:
                await log_channel.send(embed=embed)
            except Exception:
                pass

    async def handle_automod_spam_kick(self, message: discord.Message, count: int = 4):
        """Thor Apex AutoMod Rapid Spam Kick: Auto-kicks users flooding > 3 messages."""
        guild = message.guild
        member = message.author
        if not isinstance(member, discord.Member):
            return

        # 1. Delete triggering message and purge recent messages from this spammer in this channel
        try:
            await message.delete()
        except Exception:
            pass

        try:
            def is_spammer(m: discord.Message):
                return m.author.id == member.id
            await message.channel.purge(limit=10, check=is_spammer)
        except Exception:
            pass

        # 2. Kick member with AutoMod reason
        kick_reason = "AutoMod (Spamming (> 3 msgs))"
        kicked = False
        try:
            await member.kick(reason=kick_reason)
            kicked = True
        except discord.Forbidden:
            # Fallback to timeout if hierarchy prevents kicking
            try:
                await member.timeout(timedelta(hours=1), reason=kick_reason)
            except Exception:
                pass
        except Exception as e:
            logger.error(f"AutoMod kick error on {member}: {e}")

        # 3. Post public AutoMod notification in the channel (Exact Thor Apex format)
        try:
            if kicked:
                await message.channel.send(f"🚫 **{member.name}** was KICKED by AutoMod (Spamming (> 3 msgs)).")
            else:
                await message.channel.send(f"🚫 **{member.name}** was TIMED OUT by AutoMod (Spamming (> 3 msgs)).")
        except Exception:
            pass

        # 4. Record infraction in database
        try:
            await database.record_infraction(
                guild.id,
                member.id,
                "AUTOMOD_KICK" if kicked else "AUTOMOD_TIMEOUT",
                kick_reason,
                moderator_id=self.bot.user.id
            )
        except Exception:
            pass

        # 5. Security Sentinel Log Embed
        log_channel = await self.get_log_channel(guild)
        if log_channel:
            embed = discord.Embed(
                title="🚨 AutoMod Spam Enforcement",
                description=(
                    f"**User:** {member.mention} (`{member.name}` • ID: `{member.id}`)\n"
                    f"**Action:** `{'KICKED' if kicked else 'TIMED OUT'}`\n"
                    f"**Reason:** `Spamming (> 3 msgs in rapid succession)`\n"
                    f"**Channel:** {message.channel.mention}"
                ),
                color=0xFF0033
            )
            embed.set_footer(text="Thor Apex AutoMod Defense Protocol")
            embed.timestamp = discord.utils.utcnow()
            try:
                await log_channel.send(embed=embed)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Dynamic Chat Slowmode Scaler: Temporary burst defense
        ch = message.channel
        if isinstance(ch, discord.TextChannel):
            now_ts = time.time()
            self.channel_rates[ch.id].append(now_ts)
            burst_msgs = [t for t in self.channel_rates[ch.id] if now_ts - t <= 3.0]
            if len(burst_msgs) >= 7 and ch.id not in self.active_slowmodes and not ch.slowmode_delay:
                self.active_slowmodes.add(ch.id)
                try:
                    await ch.edit(slowmode_delay=3, reason="[Sentinel Dynamic Automod] Rapid chat burst detected")
                    notice = await ch.send("🌊 **Dynamic Slowmode Activated (3s):** High message velocity detected. Speed will restore automatically once calm.")
                    
                    async def _restore():
                        import asyncio
                        await asyncio.sleep(20)
                        try:
                            await ch.edit(slowmode_delay=0, reason="[Sentinel Dynamic Automod] Chat velocity stabilized")
                            await notice.delete()
                        except Exception:
                            pass
                        finally:
                            self.active_slowmodes.discard(ch.id)
                            
                    import asyncio
                    asyncio.create_task(_restore())
                except Exception:
                    self.active_slowmodes.discard(ch.id)

        member = message.author
        if not isinstance(member, discord.Member):
            return

        # Bypass for Server Owner, Admins & Whitelisted Users/Roles
        if member.id == message.guild.owner_id or member.guild_permissions.administrator:
            return
        if await database.is_whitelisted(message.guild, member):
            return

        settings = await database.get_guild_settings(message.guild.id)
        if not settings.get("antispam_enabled", 1):
            return

        now = time.time()
        content = message.content

        # 1. Thor Apex AutoMod Rapid Spam Rule: Kick on > 3 msgs in rapid burst (3.5s)
        timestamps = self.msg_timestamps[member.id]
        timestamps.append(now)
        rapid_burst = [t for t in timestamps if now - t <= 3.5]
        if len(rapid_burst) > 3:
            self.msg_timestamps[member.id].clear()
            await self.handle_automod_spam_kick(message, count=len(rapid_burst))
            return

        # 2. General Message Flooding Check: >6 messages in 6 seconds
        recent_msgs = [t for t in timestamps if now - t <= 6]
        if len(recent_msgs) >= 6:
            await self.handle_violation(message, "Message Flooding (>6 msgs / 6s)")
            return

        # 3. Repeated Character Spam: e.g. "aaaaaaaaaaaaaaaaaaaaa"
        if REPEATED_CHAR_REGEX.search(content):
            await self.handle_violation(message, "Excessive Repeated Characters")
            return

        # 4. Excessive Emoji Spam: >10 emojis
        emojis = EMOJI_REGEX.findall(content)
        if len(emojis) > 10:
            await self.handle_violation(message, f"Emoji Spam ({len(emojis)} emojis)")
            return

        # 5. Duplicate Message Spam
        history = self.msg_history[member.id]
        history.append((content.strip().lower(), now))
        if len(content.strip()) > 3:
            recent_identical = [
                text for text, t in history
                if text == content.strip().lower() and now - t <= 12
            ]
            if len(recent_identical) > 3:
                self.msg_history[member.id].clear()
                await self.handle_automod_spam_kick(message, count=len(recent_identical))
                return

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Detects and alerts on ghost-pings (deleted messages containing user or role mentions)."""
        if not message.guild or message.author.bot:
            return

        # Check if the deleted message contained member or role mentions
        if not message.mentions and not message.role_mentions:
            return

        # Ignore if author is whitelisted administrator or server owner
        if await database.is_whitelisted(message.guild, message.author):
            return

        # Don't alert if the message was posted more than 3 minutes ago
        if message.created_at and (discord.utils.utcnow() - message.created_at).total_seconds() > 180:
            return

        # Build list of pinged targets (exclude self-ping)
        pinged_users = [m for m in message.mentions if m.id != message.author.id]
        pinged_roles = message.role_mentions

        if not pinged_users and not pinged_roles:
            return

        targets_str = ", ".join([u.mention for u in pinged_users] + [r.mention for r in pinged_roles])

        embed = discord.Embed(
            title="👻 GHOST-PING DETECTED",
            description=(
                f"**Perpetrator:** {message.author.mention} (`{message.author.id}`)\n"
                f"**Channel:** {message.channel.mention}\n"
                f"**Targets Pinged:** {targets_str}\n\n"
                f"**Original Message Content:**\n```\n{message.content[:800] if message.content else '[No text content]'}\n```"
            ),
            color=0xFFA502
        )
        embed.timestamp = discord.utils.utcnow()
        embed.set_footer(text="RAI SENTINEL • Anti-Ghost-Ping Sentinel")

        # Notify channel (auto-deleted after 12s)
        try:
            await message.channel.send(
                f"👻 **Ghost-Ping Detected!** {message.author.mention} pinged {targets_str} and deleted their message.",
                delete_after=12
            )
        except Exception:
            pass

        # Send detailed incident report to security log channel
        log_chan = await self.get_log_channel(message.guild)
        if log_chan:
            try:
                await log_chan.send(embed=embed)
            except Exception:
                pass

async def setup(bot: commands.Bot):
    await bot.add_cog(AntiSpam(bot))
