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

    async def get_log_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        settings = await database.get_guild_settings(guild.id)
        log_id = settings.get("log_channel_id")
        if log_id:
            channel = guild.get_channel(log_id)
            if channel and isinstance(channel, discord.TextChannel):
                return channel
        for name in ["security-logs", "mod-logs"]:
            channel = discord.utils.get(guild.text_channels, name=name)
            if channel:
                return channel
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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

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

        # 1. Message Flooding Check: >6 messages in 5 seconds
        timestamps = self.msg_timestamps[member.id]
        timestamps.append(now)
        recent_msgs = [t for t in timestamps if now - t <= 5]
        if len(recent_msgs) >= 6:
            await self.handle_violation(message, "Message Flooding (>6 msgs / 5s)")
            return

        # 2. Repeated Character Spam: e.g. "aaaaaaaaaaaaaaaaaaaaa"
        if REPEATED_CHAR_REGEX.search(content):
            await self.handle_violation(message, "Excessive Repeated Characters")
            return

        # 3. Excessive Emoji Spam: >10 emojis
        emojis = EMOJI_REGEX.findall(content)
        if len(emojis) > 10:
            await self.handle_violation(message, f"Emoji Spam ({len(emojis)} emojis)")
            return

        # 4. Duplicate Message Spam
        history = self.msg_history[member.id]
        history.append((content.strip().lower(), now))
        if len(content.strip()) > 6:
            recent_identical = [
                text for text, t in history
                if text == content.strip().lower() and now - t <= 15
            ]
            if len(recent_identical) >= 3:
                await self.handle_violation(message, "Repeated Duplicate Messages")
                return

async def setup(bot: commands.Bot):
    await bot.add_cog(AntiSpam(bot))
