import re
import time
import datetime
import asyncio
import json
from pathlib import Path
from typing import Optional, Dict, List

import discord
from discord.ext import commands
from discord import app_commands

import config

INVITE_REGEX = re.compile(r"(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li|com/invite)/[a-zA-Z0-9]+)")

SCAM_DOMAINS = [
    "discorcl", "dlscord", "discrod", "discord-nitro", "free-nitro", "nitro-gift",
    "steamcommuniity", "steamcomminuty", "gift-discord", "discordapp.biz", "discord-app.me",
    "airdrop-nitro", "claim-nitro", "steam-gift", "discordgift", "t.me/airdrop"
]

# Inappropriate, toxic, NSFW & slur keywords regex pattern
INAPPROPRIATE_KEYWORDS = [
    r"\bn+[i1l]+g+g+[e3a4r]+\b", # slurs
    r"\bf+[a4]+g+[o0e3]*t*\b",
    r"\br+[e3]+t+[a4]+r+d+\b",
    r"\bk+[y1]+s+\b",
    r"\bhitler\b",
    r"\bnazi\b",
    r"\bporn\b",
    r"\bhentai\b",
    r"\brape\b",
    r"\bcp\b",
    r"\bchildporn\b"
]
INAPPROPRIATE_REGEX = re.compile("|".join(INAPPROPRIATE_KEYWORDS), re.IGNORECASE)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INFRACTIONS_FILE = DATA_DIR / "infractions.json"
FROZEN_FILE = DATA_DIR / "frozen_members.json"


def load_infractions() -> Dict[str, Dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if INFRACTIONS_FILE.exists():
        try:
            with open(INFRACTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_infractions(data: Dict[str, Dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(INFRACTIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_frozen_members() -> Dict[str, Dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if FROZEN_FILE.exists():
        try:
            with open(FROZEN_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_frozen_members(data: Dict[str, Dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(FROZEN_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class FreezeActionView(discord.ui.View):
    """Interactive Staff Quick-Action button to unfreeze an isolated member."""
    def __init__(self, target_id: int, target_name: str, bot: commands.Bot):
        super().__init__(timeout=86400)
        self.target_id = target_id
        self.target_name = target_name
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.moderate_members and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only staff moderators can unfreeze members.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Unfreeze Member", style=discord.ButtonStyle.success, emoji="🔓")
    async def unfreeze_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.target_id)
        mod_cog = self.bot.get_cog("Moderation")

        if member and mod_cog:
            try:
                await mod_cog.execute_unfreeze(guild, member, interaction.user)
                button.disabled = True
                button.label = "Unfrozen ✅"
                await interaction.response.edit_message(view=self)
                await interaction.followup.send(f"🔓 **{member.mention}** has been released from Freeze Isolation by {interaction.user.mention}.")
            except Exception as e:
                await interaction.response.send_message(f"❌ Failed to unfreeze member: {e}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Member or Moderation system unavailable.", ephemeral=True)


class QuickModActionView(discord.ui.View):
    """Interactive Staff Quick-Action buttons on auto-mod log embeds."""
    def __init__(self, target_id: int, target_name: str, bot: commands.Bot):
        super().__init__(timeout=86400) # 24 hours
        self.target_id = target_id
        self.target_name = target_name
        self.bot = bot

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not interaction.user.guild_permissions.moderate_members and not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message("❌ Only staff moderators can use these quick action buttons.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Server Mute (10m)", style=discord.ButtonStyle.secondary, emoji="🔇")
    async def mute_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        member = guild.get_member(self.target_id)
        if not member:
            return await interaction.response.send_message(f"❌ User `{self.target_name}` is no longer in the server.", ephemeral=True)
        
        try:
            # Voice Server Mute if in voice
            if member.voice:
                await member.edit(mute=True, deafen=True, reason=f"Quick Mute by {interaction.user.name}")
            # Text timeout 10 mins
            await member.timeout(datetime.timedelta(minutes=10), reason=f"Quick Mute by {interaction.user.name}")
            button.disabled = True
            button.label = "Muted (10m) ✅"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"🔇 **{member.mention}** has been server muted and timed out for 10 minutes by {interaction.user.mention}.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to server mute: {e}", ephemeral=True)

    @discord.ui.button(label="Kick User", style=discord.ButtonStyle.danger, emoji="👢")
    async def kick_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.kick_members and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You require 'Kick Members' permission.", ephemeral=True)
        
        guild = interaction.guild
        member = guild.get_member(self.target_id)
        if not member:
            return await interaction.response.send_message(f"❌ User `{self.target_name}` is not in the server.", ephemeral=True)
        
        try:
            await member.kick(reason=f"Quick Kick by {interaction.user.name}")
            button.disabled = True
            button.label = "Kicked ✅"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"👢 **{self.target_name}** has been kicked from the server by {interaction.user.mention}.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to kick user: {e}", ephemeral=True)

    @discord.ui.button(label="Ban User", style=discord.ButtonStyle.danger, emoji="🔨")
    async def ban_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.ban_members and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You require 'Ban Members' permission.", ephemeral=True)
        
        guild = interaction.guild
        try:
            await guild.ban(discord.Object(id=self.target_id), reason=f"Quick Ban by {interaction.user.name}", delete_message_days=1)
            button.disabled = True
            button.label = "Banned ✅"
            await interaction.response.edit_message(view=self)
            await interaction.followup.send(f"🔨 **{self.target_name}** (`{self.target_id}`) has been **banned** by {interaction.user.mention}.")
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to ban user: {e}", ephemeral=True)


class Moderation(commands.Cog):
    """
    🛡️ Auto-Moderation Sentinel & Safety Enforcement.
    Automatically detects inappropriate content, toxicity, spam, slurs, phishing links,
    and applies Server Mute, Timeout, Auto-Kick, or Auto-Ban based on strikes!
    """

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.message_logs = {} # user_id: [timestamps]
        self.infractions = load_infractions()
        self.frozen_members = load_frozen_members()
        self.voice_spam_tracker = {} # user_id: [timestamps]

    async def log_mod_action(self, guild: discord.Guild, embed: discord.Embed, view: Optional[discord.ui.View] = None):
        log_channel = (
            discord.utils.get(guild.text_channels, name="📋・mod-logs") or
            discord.utils.get(guild.text_channels, name="mod-logs") or
            discord.utils.get(guild.text_channels, name="📋・audit-moderation-logs")
        )
        if log_channel:
            try:
                await log_channel.send(embed=embed, view=view)
            except Exception:
                pass

    def add_strike(self, guild_id: int, user_id: int, reason: str, moderator: str = "AutoMod") -> int:
        g_key = str(guild_id)
        u_key = str(user_id)
        if g_key not in self.infractions:
            self.infractions[g_key] = {}
        if u_key not in self.infractions[g_key]:
            self.infractions[g_key][u_key] = {"strikes": 0, "history": []}

        self.infractions[g_key][u_key]["strikes"] += 1
        self.infractions[g_key][u_key]["history"].append({
            "timestamp": datetime.datetime.now().isoformat(),
            "reason": reason,
            "moderator": moderator
        })
        save_infractions(self.infractions)
        return self.infractions[g_key][u_key]["strikes"]

    async def execute_escalated_punishment(self, member: discord.Member, strikes: int, reason: str, channel: Optional[discord.TextChannel] = None):
        """
        Escalation Rules:
        - Strike 1: Warning + 5 Min Server Mute & Timeout
        - Strike 2: 1 Hour Server Mute & Timeout
        - Strike 3: KICK from Server
        - Strike 4+: BAN from Server
        """
        guild = member.guild
        action_taken = ""

        # Voice Server Mute if currently in a voice channel
        if member.voice:
            try:
                await member.edit(mute=True, deafen=True, reason=f"AutoMod Enforcement (Strike {strikes}): {reason}")
            except Exception:
                pass

        if strikes == 1:
            # 5 min Server Mute / Timeout
            try:
                await member.timeout(datetime.timedelta(minutes=5), reason=f"AutoMod Strike 1: {reason}")
                action_taken = "🔇 Server Mute & 5m Timeout"
            except Exception:
                action_taken = "⚠️ Warning Issued"
            
            try:
                await member.send(
                    f"⚠️ **[RAI FAM AutoMod Warning]**\n"
                    f"You have received **Strike 1** in **{guild.name}**.\n"
                    f"**Reason:** `{reason}`\n"
                    f"**Action:** 5-minute timeout & server mute applied. Further inappropriate behavior will lead to an automatic Kick or Ban."
                )
            except Exception:
                pass

        elif strikes == 2:
            # 1 Hour Server Mute / Timeout
            try:
                await member.timeout(datetime.timedelta(hours=1), reason=f"AutoMod Strike 2: {reason}")
                action_taken = "🔇 Server Mute & 1h Timeout"
            except Exception:
                action_taken = "⚠️ Second Warning"

            try:
                await member.send(
                    f"🚨 **[RAI FAM AutoMod Warning - Strike 2]**\n"
                    f"You have received **Strike 2** in **{guild.name}**.\n"
                    f"**Reason:** `{reason}`\n"
                    f"**Action:** 1-hour timeout & server mute applied. **Next violation will result in an immediate KICK.**"
                )
            except Exception:
                pass

        elif strikes == 3:
            # Automatic KICK
            action_taken = "👢 Automatic KICK"
            try:
                await member.send(
                    f"👢 **[RAI FAM AutoMod - Kicked]**\n"
                    f"You have been **kicked** from **{guild.name}** due to reaching **Strike 3**.\n"
                    f"**Reason:** `{reason}`\n"
                    f"You may rejoin with an invite if you adhere strictly to community rules."
                )
            except Exception:
                pass
            
            try:
                await member.kick(reason=f"AutoMod Strike 3 Threshold Reached: {reason}")
            except Exception as e:
                action_taken = f"❌ Kick Failed: {e}"

        else: # strikes >= 4
            # Automatic BAN
            action_taken = "🔨 Automatic BAN"
            try:
                await member.send(
                    f"🔨 **[RAI FAM AutoMod - BANNED]**\n"
                    f"You have been **permanently banned** from **{guild.name}** for repeated inappropriate behavior (Strike {strikes}).\n"
                    f"**Reason:** `{reason}`"
                )
            except Exception:
                pass

            try:
                await guild.ban(member, reason=f"AutoMod Strike {strikes} (Severe/Repeated Infractions): {reason}", delete_message_days=1)
            except Exception as e:
                action_taken = f"❌ Ban Failed: {e}"

        # Public notification in channel if provided
        if channel:
            try:
                await channel.send(
                    f"🛡️ **AutoMod Action:** {member.mention} has received **Strike {strikes}** (`{reason}`).\n"
                    f"⚡ **Penalty:** **{action_taken}**",
                    delete_after=10
                )
            except Exception:
                pass

        # Detailed Mod Log entry with Quick Actions
        embed = discord.Embed(
            title=f"🛡️ [AUTOMOD PUNISHMENT] Strike {strikes}",
            description=(
                f"**Offender:** {member.mention} (`{member.name}` / `{member.id}`)\n"
                f"**Total Strikes:** `{strikes}`\n"
                f"**Reason:** `{reason}`\n"
                f"**Enforcement:** `{action_taken}`\n"
                f"**Voice Muted:** `{'Yes' if member.voice else 'Not in VC'}`"
            ),
            color=config.COLOR_ERROR if strikes >= 3 else config.COLOR_WARNING,
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="RAI VIBES 💗 Auto-Security Sentinel", icon_url=config.RAI_ICON_URL)
        view = QuickModActionView(target_id=member.id, target_name=member.name, bot=self.bot)
        await self.log_mod_action(guild, embed, view=view)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        member = message.author
        now = datetime.datetime.now().timestamp()

        # Bypass for Server Owner & Admins
        if member.id == message.guild.owner_id or member.guild_permissions.administrator:
            return

        lower_content = message.content.lower()

        # 1. Anti-Scam & Phishing Domain Filter (Instant Severe Strike / Ban)
        if any(scam in lower_content for scam in SCAM_DOMAINS):
            try:
                await message.delete()
            except Exception:
                pass
            strikes = self.add_strike(message.guild.id, member.id, "Phishing/Scam Domain Link", moderator="AutoMod Anti-Phish")
            # Severe: escalate by adding extra strike if first time
            if strikes < 2:
                strikes = self.add_strike(message.guild.id, member.id, "Severe Phishing Attempt", moderator="AutoMod Anti-Phish")
            await self.execute_escalated_punishment(member, strikes, "Phishing / Scam Link Detected", channel=message.channel)
            return

        # 2. Inappropriate / Toxic / Slur / NSFW Filter
        if INAPPROPRIATE_REGEX.search(lower_content):
            try:
                await message.delete()
            except Exception:
                pass
            strikes = self.add_strike(message.guild.id, member.id, "Inappropriate Language / Toxic Slur", moderator="AutoMod Content Sentinel")
            await self.execute_escalated_punishment(member, strikes, "Inappropriate / Profane Language", channel=message.channel)
            return

        # 3. Anti-Invite Filter
        if INVITE_REGEX.search(message.content):
            try:
                await message.delete()
            except Exception:
                pass
            strikes = self.add_strike(message.guild.id, member.id, "Unauthorized Discord Invite Link", moderator="AutoMod Anti-Invite")
            await self.execute_escalated_punishment(member, strikes, "Unauthorized Invite Link", channel=message.channel)
            return

        # 4. Anti-Mass Mentions (> 3 mentions)
        if len(message.mentions) > 3:
            try:
                await message.delete()
            except Exception:
                pass
            strikes = self.add_strike(message.guild.id, member.id, f"Mass Mention Spam ({len(message.mentions)} users)", moderator="AutoMod Anti-Mention")
            await self.execute_escalated_punishment(member, strikes, "Mass Mention Spam", channel=message.channel)
            return

        # 5. Anti-Spam Rapid Burst Detection (5 msgs in 3.5s)
        u_id = member.id
        if u_id not in self.message_logs:
            self.message_logs[u_id] = []
        
        self.message_logs[u_id] = [t for t in self.message_logs[u_id] if now - t < 3.5]
        self.message_logs[u_id].append(now)

        if len(self.message_logs[u_id]) >= 5:
            self.message_logs[u_id] = []
            try:
                await message.channel.purge(limit=5, check=lambda m: m.author.id == member.id)
            except Exception:
                pass
            strikes = self.add_strike(message.guild.id, member.id, "Message Flooding / Rapid Spam", moderator="AutoMod Anti-Spam")
            await self.execute_escalated_punishment(member, strikes, "Rapid Message Spam Flood", channel=message.channel)

    # ==========================================
    # MODERATOR SLASH & HYBRID COMMANDS
    # ==========================================

    @commands.hybrid_command(name="servermute", aliases=["vmute", "smute"], description="Server mute a member (Voice Mute + Text Timeout).")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to server mute", minutes="Duration in minutes (default: 15)", reason="Reason for mute")
    async def servermute(self, ctx: commands.Context, member: discord.Member, minutes: int = 15, *, reason: str = "Inappropriate behavior"):
        """Puts an improper user to voice server mute and text timeout."""
        await ctx.defer()
        duration = datetime.timedelta(minutes=minutes)
        vc_muted = False
        
        if member.voice:
            try:
                await member.edit(mute=True, deafen=True, reason=f"{ctx.author.name}: {reason}")
                vc_muted = True
            except Exception as e:
                pass

        try:
            await member.timeout(duration, reason=f"{ctx.author.name}: {reason}")
            strikes = self.add_strike(ctx.guild.id, member.id, f"Manual Server Mute ({minutes}m): {reason}", moderator=ctx.author.name)
            
            embed = discord.Embed(
                title="🔇 Member Server Muted",
                description=(
                    f"**Offender:** {member.mention} (`{member.id}`)\n"
                    f"**Duration:** `{minutes} minute(s)`\n"
                    f"**Voice Server Mute:** `{'Active' if vc_muted else 'Not in VC (Text timeout applied)'}`\n"
                    f"**Moderator:** {ctx.author.mention}\n"
                    f"**Reason:** `{reason}`\n"
                    f"**Total Strikes:** `{strikes}`"
                ),
                color=config.COLOR_WARNING
            )
            embed.set_footer(text="RAI VIBES 💗 Safety Sentinel", icon_url=config.RAI_ICON_URL)
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, embed)

            try:
                await member.send(f"🔇 You were **server muted and timed out** in **{ctx.guild.name}** for {minutes}m.\n**Reason:** `{reason}`")
            except Exception:
                pass
        except Exception as e:
            await ctx.send(f"❌ Failed to timeout member: {e}", ephemeral=True)

    @commands.hybrid_command(name="serverunmute", aliases=["vunmute", "sunmute"], description="Remove Server Mute and text timeout from a member.")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to unmute")
    async def serverunmute(self, ctx: commands.Context, member: discord.Member):
        await ctx.defer()
        if member.voice:
            try:
                await member.edit(mute=False, deafen=False, reason=f"Unmuted by {ctx.author.name}")
            except Exception:
                pass

        try:
            await member.timeout(None, reason=f"Unmuted by {ctx.author.name}")
            embed = discord.Embed(
                title="🔊 Member Unmuted",
                description=f"**User:** {member.mention}\n**Moderator:** {ctx.author.mention}\nServer mute and timeouts have been lifted.",
                color=config.COLOR_SUCCESS
            )
            embed.set_footer(text="RAI VIBES 💗 Safety Sentinel", icon_url=config.RAI_ICON_URL)
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, embed)
        except Exception as e:
            await ctx.send(f"❌ Failed to unmute user: {e}", ephemeral=True)

    @commands.hybrid_command(name="kick", description="Kick an inappropriate member from the server.")
    @commands.has_permissions(kick_members=True)
    @app_commands.describe(member="Member to kick", reason="Reason for kick")
    async def kick(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Violating server community rules"):
        await ctx.defer()
        if member.id == ctx.guild.owner_id:
            return await ctx.send("❌ You cannot kick the server owner.", ephemeral=True)

        try:
            await member.send(f"👢 You have been **kicked** from **{ctx.guild.name}** by {ctx.author.name}.\n**Reason:** `{reason}`")
        except Exception:
            pass

        try:
            await member.kick(reason=f"{ctx.author.name}: {reason}")
            strikes = self.add_strike(ctx.guild.id, member.id, f"Kicked: {reason}", moderator=ctx.author.name)
            
            embed = discord.Embed(
                title="👢 Member Kicked",
                description=(
                    f"**User:** `{member.name}` (`{member.id}`)\n"
                    f"**Moderator:** {ctx.author.mention}\n"
                    f"**Reason:** `{reason}`\n"
                    f"**Total Strikes:** `{strikes}`"
                ),
                color=config.COLOR_ERROR
            )
            embed.set_footer(text="RAI VIBES 💗 Safety Sentinel", icon_url=config.RAI_ICON_URL)
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, embed)
        except Exception as e:
            await ctx.send(f"❌ Could not kick member: {e}", ephemeral=True)

    @commands.hybrid_command(name="ban", description="Ban an inappropriate member from the server.")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(member="Member to ban", delete_days="Number of days of messages to delete (0-7)", reason="Reason for ban")
    async def ban(self, ctx: commands.Context, member: discord.Member, delete_days: int = 1, *, reason: str = "Severe inappropriate behavior / rules violation"):
        await ctx.defer()
        if member.id == ctx.guild.owner_id:
            return await ctx.send("❌ You cannot ban the server owner.", ephemeral=True)

        try:
            await member.send(f"🔨 You have been **permanently banned** from **{ctx.guild.name}**.\n**Reason:** `{reason}`")
        except Exception:
            pass

        try:
            await ctx.guild.ban(member, reason=f"{ctx.author.name}: {reason}", delete_message_days=min(7, max(0, delete_days)))
            strikes = self.add_strike(ctx.guild.id, member.id, f"Banned: {reason}", moderator=ctx.author.name)
            
            embed = discord.Embed(
                title="🔨 Member Banned",
                description=(
                    f"**User:** `{member.name}` (`{member.id}`)\n"
                    f"**Moderator:** {ctx.author.mention}\n"
                    f"**Reason:** `{reason}`\n"
                    f"**Purged Days:** `{delete_days}`\n"
                    f"**Total Strikes:** `{strikes}`"
                ),
                color=config.COLOR_ERROR
            )
            embed.set_footer(text="RAI VIBES 💗 Safety Sentinel", icon_url=config.RAI_ICON_URL)
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, embed)
        except Exception as e:
            await ctx.send(f"❌ Could not ban member: {e}", ephemeral=True)

    @commands.hybrid_command(name="unban", description="Unban a user by ID.")
    @commands.has_permissions(ban_members=True)
    @app_commands.describe(user_id="Discord User ID to unban", reason="Reason for unban")
    async def unban(self, ctx: commands.Context, user_id: str, *, reason: str = "Pardoned by staff"):
        await ctx.defer()
        try:
            uid = int(user_id)
            user = await self.bot.fetch_user(uid)
            await ctx.guild.unban(user, reason=f"{ctx.author.name}: {reason}")
            
            embed = discord.Embed(
                title="🔓 Member Unbanned",
                description=f"**User:** `{user.name}` (`{user.id}`)\n**Moderator:** {ctx.author.mention}\n**Reason:** `{reason}`",
                color=config.COLOR_SUCCESS
            )
            embed.set_footer(text="RAI VIBES 💗 Safety Sentinel", icon_url=config.RAI_ICON_URL)
            await ctx.send(embed=embed)
            await self.log_mod_action(ctx.guild, embed)
        except Exception as e:
            await ctx.send(f"❌ Could not unban user ID `{user_id}`: {e}", ephemeral=True)

    @commands.hybrid_command(name="warn", description="Issue an official strike/warning to a member.")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(member="Member to warn", reason="Reason for warning")
    async def warn(self, ctx: commands.Context, member: discord.Member, *, reason: str = "Violating server rules"):
        await ctx.defer()
        strikes = self.add_strike(ctx.guild.id, member.id, reason, moderator=ctx.author.name)
        
        embed = discord.Embed(
            title=f"⚠️ Official Warning (Strike {strikes})",
            description=(
                f"**Warned Member:** {member.mention}\n"
                f"**Moderator:** {ctx.author.mention}\n"
                f"**Reason:** `{reason}`\n"
                f"**Total Strikes:** `{strikes}`\n\n"
                f"ℹ️ *Note: Strikes automatically escalate to Server Mute, Kick, and Ban.*"
            ),
            color=config.COLOR_WARNING
        )
        embed.set_footer(text="RAI VIBES 💗 Safety Sentinel", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)
        await self.log_mod_action(ctx.guild, embed)

        try:
            await member.send(f"⚠️ You received a warning (**Strike {strikes}**) in **{ctx.guild.name}**.\n**Reason:** `{reason}`")
        except Exception:
            pass

    @commands.hybrid_command(name="strikes", aliases=["infractions", "modlogs"], description="View moderation strike history for a member.")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to view infractions for")
    async def strikes(self, ctx: commands.Context, member: discord.Member):
        g_key = str(ctx.guild.id)
        u_key = str(member.id)
        user_data = self.infractions.get(g_key, {}).get(u_key, {"strikes": 0, "history": []})
        
        count = user_data.get("strikes", 0)
        history = user_data.get("history", [])[-5:] # last 5

        desc = f"**User:** {member.mention} (`{member.id}`)\n**Total Active Strikes:** `{count}`\n\n"
        if not history:
            desc += "✅ *No prior infractions recorded. Clean record!*"
        else:
            desc += "### 📋 Recent Infractions:\n"
            for idx, item in enumerate(history, 1):
                t = item.get('timestamp', '')[:10]
                desc += f"**{idx}.** `[{t}]` **{item.get('reason')}** *(By: {item.get('moderator')})*\n"

        embed = discord.Embed(
            title=f"🛡️ Infraction Record: {member.display_name}",
            description=desc,
            color=config.COLOR_PRIMARY if count == 0 else config.COLOR_WARNING
        )
        embed.set_footer(text="RAI VIBES 💗 Auto-Mod History", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clearstrikes", description="Reset all strikes and infractions for a member.")
    @commands.has_permissions(administrator=True)
    @app_commands.describe(member="Member to reset strikes for")
    async def clearstrikes(self, ctx: commands.Context, member: discord.Member):
        g_key = str(ctx.guild.id)
        u_key = str(member.id)
        if g_key in self.infractions and u_key in self.infractions[g_key]:
            self.infractions[g_key][u_key] = {"strikes": 0, "history": []}
            save_infractions(self.infractions)
        
        embed = discord.Embed(
            title="✨ Strikes Cleared",
            description=f"All strikes and infraction history for {member.mention} have been reset by {ctx.author.mention}.",
            color=config.COLOR_SUCCESS
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="clear", aliases=["purge"], description="Bulk delete recent messages from channel.")
    @commands.has_permissions(manage_messages=True)
    @app_commands.describe(amount="Number of messages to delete (1-100)")
    async def clear(self, ctx: commands.Context, amount: int = 10):
        if not 1 <= amount <= 100:
            return await ctx.send("❌ Amount must be between 1 and 100.", ephemeral=True)

        await ctx.defer(ephemeral=True)
        deleted = await ctx.channel.purge(limit=amount)
        await ctx.send(f"🧹 **Deleted {len(deleted)} message(s).**", ephemeral=True)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        """Anti-Ghost Ping Detector."""
        if message.author.bot or not message.guild:
            return

        if message.mentions:
            pings = ", ".join([m.mention for m in message.mentions if not m.bot and m.id != message.author.id])
            if pings:
                embed = discord.Embed(
                    title="👻 [ANTI-GHOST PING] Message Deleted With Mentions",
                    description=(
                        f"**Author:** {message.author.mention} (`{message.author.id}`)\n"
                        f"**Channel:** {message.channel.mention}\n"
                        f"**Pinged Users:** {pings}\n"
                        f"**Content:** `{message.content[:300]}`"
                    ),
                    color=config.COLOR_WARNING,
                    timestamp=datetime.datetime.now()
                )
                await self.log_mod_action(message.guild, embed)

    @commands.hybrid_command(name="lockdown", description="Emergency Lockdown: Lock down all public channels in a raid.")
    @commands.has_permissions(administrator=True)
    async def lockdown(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        guild = ctx.guild
        count = 0
        for channel in guild.text_channels:
            if "staff" in channel.name.lower() or "mod" in channel.name.lower() or "ticket" in channel.name.lower():
                continue
            try:
                await channel.set_permissions(guild.default_role, send_messages=False)
                count += 1
            except Exception:
                pass

        embed = discord.Embed(
            title="🚨 EMERGENCY SERVER LOCKDOWN ACTIVATED 🚨",
            description=f"Server has been locked down by {ctx.author.mention}.\nLocked **{count}** channels.",
            color=config.COLOR_ERROR
        )
        await ctx.send(embed=embed)
        await self.log_mod_action(guild, embed)

    @commands.hybrid_command(name="unlock", description="Remove server lockdown and restore public chatting.")
    @commands.has_permissions(administrator=True)
    async def unlock(self, ctx: commands.Context):
        await ctx.defer(ephemeral=True)
        guild = ctx.guild
        count = 0
        for channel in guild.text_channels:
            if "staff" in channel.name.lower() or "mod" in channel.name.lower() or "ticket" in channel.name.lower():
                continue
            try:
                await channel.set_permissions(guild.default_role, send_messages=None)
                count += 1
            except Exception:
                pass

        embed = discord.Embed(
            title="🔓 SERVER UNLOCKED",
            description=f"Server lockdown lifted by {ctx.author.mention}. Normal chatting restored.",
            color=config.COLOR_SUCCESS
        )
        await ctx.send(embed=embed)
        await self.log_mod_action(guild, embed)

    @commands.hybrid_command(name="automod", description="View the AutoMod Sentinel status and active protections.")
    @commands.has_permissions(moderate_members=True)
    async def automod(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🛡️ RAI VIBES 💗 • AutoMod & Safety Sentinel",
            description=(
                "**Active 24/7 Server Shield Protections:**\n\n"
                "• 🤬 **Toxicity & Profanity Filter:** Active (Auto-Deletes & Strikes)\n"
                "• 🔗 **Anti-Scam & Phishing Guard:** Active (Auto-Mutes & Strikes)\n"
                "• 📨 **Anti-Invite Link Filter:** Active (Deletes Discord invites)\n"
                "• 📢 **Anti-Mass Mentions:** Active (>3 Mentions = Auto-Timeout)\n"
                "• 🌊 **Anti-Spam Flooding:** Active (5 msgs/3.5s = Auto-Timeout)\n"
                "• 🔇 **Voice Server Mute:** Enabled (`/servermute`, `/serverunmute`)\n"
                "• 👢 **Auto-Kick:** Strike 3 Threshold\n"
                "• 🔨 **Auto-Ban:** Strike 4+ / Severe Phishing\n\n"
                "**Quick Commands for Staff:**\n"
                "`/servermute @user [mins] [reason]` - Voice & text server mute\n"
                "`/serverunmute @user` - Lift server mute\n"
                "`/kick @user [reason]` - Kick user\n"
                "`/ban @user [days] [reason]` - Ban user\n"
                "`/strikes @user` - Check user strike history\n"
                "`/clearstrikes @user` - Reset strikes"
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="RAI VIBES 💗 Auto-Security Sentinel", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)


    # =========================================================================
    # VOICE ISOLATION & NOISE FREEZE CHAMBER SYSTEM
    # =========================================================================

    async def get_or_create_freeze_chamber(self, guild: discord.Guild) -> discord.VoiceChannel:
        """Finds or creates a secure, isolated Freeze Chamber voice channel."""
        for ch in guild.voice_channels:
            if "freeze chamber" in ch.name.lower() or "isolation" in ch.name.lower() or "🧊" in ch.name:
                return ch

        # Find target category (Sentinel Defense or Private Zone or first category)
        category = (
            discord.utils.get(guild.categories, name="🛡️ | 𝑺𝑬𝑵𝑻𝑰𝑵𝑬𝑳 𝑫𝑬𝑭𝑬𝑵𝑺𝑬") or
            discord.utils.get(guild.categories, name="🔒 | 𝑷𝑹𝑰𝑽𝑨𝑻𝑬-𝒁𝑶𝑵𝑬") or
            (guild.categories[0] if guild.categories else None)
        )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                view_channel=False,
                connect=False,
                speak=False
            )
        }

        # Ensure administrators / moderators can always access
        for role in guild.roles:
            if role.permissions.administrator or role.permissions.moderate_members:
                overwrites[role] = discord.PermissionOverwrite(
                    view_channel=True,
                    connect=True,
                    speak=True,
                    move_members=True,
                    mute_members=True
                )

        channel = await guild.create_voice_channel(
            name="🧊 | FREEZE CHAMBER",
            category=category,
            user_limit=10,
            overwrites=overwrites,
            reason="Created secure Voice Freeze & Noise Isolation Chamber"
        )
        return channel

    async def execute_freeze(self, guild: discord.Guild, member: discord.Member, moderator: discord.Member, minutes: int = 10, reason: str = "Extreme noise / mic spamming"):
        """Isolates member in Freeze Chamber, applies server mute/deafen, and locks permissions."""
        chamber = await self.get_or_create_freeze_chamber(guild)
        
        # 1. Set trap permissions for the member on Freeze Chamber
        await chamber.set_permissions(
            member,
            view_channel=True,
            connect=True,
            speak=False,
            stream=False,
            use_soundboard=False,
            use_voice_activity=False
        )

        # 2. Server Mute & Deafen member + move to chamber if connected
        try:
            if member.voice:
                await member.edit(
                    mute=True,
                    deafen=True,
                    voice_channel=chamber,
                    reason=f"Voice Freeze by {moderator.name}: {reason}"
                )
            else:
                # Member not currently in voice, but will be trapped when they connect
                pass
        except Exception as e:
            logger = logging.getLogger("RaiSentinel")
            logger.warning(f"Could not move/mute frozen member: {e}")

        # 3. Apply Discord Text & Voice Timeout
        try:
            if minutes > 0:
                await member.timeout(
                    datetime.timedelta(minutes=minutes),
                    reason=f"Voice Freeze & Noise Isolation by {moderator.name}: {reason}"
                )
            else:
                await member.timeout(
                    datetime.timedelta(days=28),
                    reason=f"Permanent Voice Freeze: {reason}"
                )
        except Exception as e:
            logger = logging.getLogger("RaiSentinel")
            logger.warning(f"Could not apply timeout: {e}")

        # 4. Save freeze record
        g_key = str(guild.id)
        u_key = str(member.id)
        if g_key not in self.frozen_members:
            self.frozen_members[g_key] = {}

        expire_time = (datetime.datetime.now() + datetime.timedelta(minutes=minutes)).isoformat() if minutes > 0 else "PERMANENT"
        self.frozen_members[g_key][u_key] = {
            "expires_at": expire_time,
            "reason": reason,
            "moderator": moderator.name,
            "moderator_id": moderator.id,
            "chamber_id": chamber.id,
            "frozen_at": datetime.datetime.now().isoformat()
        }
        save_frozen_members(self.frozen_members)

        # 5. Log action with interactive unfreeze button
        embed = discord.Embed(
            title="🧊 [VOICE FREEZE & TIMEOUT] Member Isolated in Freeze Chamber",
            description=(
                f"**Target Member:** {member.mention} (`{member.id}`)\n"
                f"**Enforcer:** {moderator.mention}\n"
                f"**Duration:** `{minutes} minute(s)`" + (" *(Permanent until /unfreeze)*" if minutes == 0 else "") + "\n"
                f"**Reason:** `{reason}`\n"
                f"**Isolation Chamber:** {chamber.mention}\n\n"
                f"🔒 **Enforcements Active:**\n"
                f"• Server Muted & Server Deafened\n"
                f"• Discord Timeout Applied (Text & Voice Restricted)\n"
                f"• Voice/Video Transmission & Soundboards Blocked\n"
                f"• Channel Hopping Locked (Auto-Yank Back)"
            ),
            color=0x3498DB,
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="RAI SENTINEL 🛡️ Voice Isolation & AutoMod", icon_url=config.RAI_ICON_URL)
        view = FreezeActionView(member.id, member.display_name, self.bot)
        await self.log_mod_action(guild, embed, view=view)

        # 6. DM Member
        try:
            await member.send(
                f"🧊 **You have been timed out and moved to the Voice Freeze Chamber in {guild.name}.**\n"
                f"**Duration:** `{minutes} minute(s)`\n"
                f"**Reason:** `{reason}`\n"
                f"*Please refrain from loud noises, earrape, mic spam, or soundboard trolling.*"
            )
        except Exception:
            pass

    async def execute_unfreeze(self, guild: discord.Guild, member: discord.Member, moderator: discord.Member):
        """Releases member from Freeze Chamber and restores standard voice & text permissions."""
        g_key = str(guild.id)
        u_key = str(member.id)

        # 1. Clear permissions on Freeze Chamber
        chamber = await self.get_or_create_freeze_chamber(guild)
        try:
            await chamber.set_permissions(member, overwrite=None)
        except Exception:
            pass

        # 2. Lift server mute and deafen
        try:
            if member.voice:
                await member.edit(mute=False, deafen=False, reason=f"Unfrozen by {moderator.name}")
        except Exception:
            pass

        # 3. Remove Discord Timeout
        try:
            await member.timeout(None, reason=f"Unfrozen by {moderator.name}")
        except Exception:
            pass

        # 4. Remove from frozen registry
        if g_key in self.frozen_members and u_key in self.frozen_members[g_key]:
            del self.frozen_members[g_key][u_key]
            save_frozen_members(self.frozen_members)

        # 5. Log mod action
        embed = discord.Embed(
            title="🔓 [VOICE UNFREEZE] Member Released from Freeze Chamber",
            description=(
                f"**Member:** {member.mention} (`{member.id}`)\n"
                f"**Moderator:** {moderator.mention}\n"
                f"**Status:** All voice restrictions, timeout, mutes, and deafens lifted."
            ),
            color=config.COLOR_SUCCESS,
            timestamp=datetime.datetime.now()
        )
        embed.set_footer(text="RAI SENTINEL 🛡️ Voice Isolation Engine", icon_url=config.RAI_ICON_URL)
        await self.log_mod_action(guild, embed)

    @commands.hybrid_command(name="freeze", aliases=["isolate", "jailvc", "silencevc"], description="Freeze a noisy/trolling member and isolate them in the Freeze Chamber.")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(
        member="Member making extreme noise or trolling in voice",
        minutes="Duration in minutes (0 for permanent until unfreeze)",
        reason="Reason for voice freeze"
    )
    async def freeze_command(self, ctx: commands.Context, member: discord.Member, minutes: int = 10, *, reason: str = "Extreme noise / mic spamming"):
        await ctx.defer()
        if member.top_role >= ctx.author.top_role and ctx.author.id != ctx.guild.owner_id:
            return await ctx.send("❌ You cannot freeze a member with an equal or higher role.", ephemeral=True)

        await self.execute_freeze(ctx.guild, member, ctx.author, minutes=minutes, reason=reason)
        embed = discord.Embed(
            title="🧊 Member Frozen & Timed Out",
            description=(
                f"✅ **{member.mention}** has been moved to the **Freeze Chamber**, server muted, and timed out for `{minutes} minute(s)`.\n"
                f"**Reason:** `{reason}`"
            ),
            color=0x3498DB
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="unfreeze", aliases=["unisolate", "unjailvc"], description="Unfreeze an isolated member and restore voice access.")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member to unfreeze and release")
    async def unfreeze_command(self, ctx: commands.Context, member: discord.Member):
        await ctx.defer()
        g_key = str(ctx.guild.id)
        u_key = str(member.id)
        if g_key not in self.frozen_members or u_key not in self.frozen_members[g_key]:
            # Still attempt to clear mute/deafen and timeout
            if member.voice:
                try:
                    await member.edit(mute=False, deafen=False)
                except Exception:
                    pass
            try:
                await member.timeout(None)
            except Exception:
                pass
            return await ctx.send(f"ℹ️ {member.mention} was not registered in the active freeze list (restrictions cleared).", ephemeral=True)

        await self.execute_unfreeze(ctx.guild, member, ctx.author)
        embed = discord.Embed(
            title="🔓 Member Unfrozen",
            description=f"✅ **{member.mention}** has been released from the Freeze Chamber and timeout lifted by {ctx.author.mention}.",
            color=config.COLOR_SUCCESS
        )
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="soundboard_timeout", aliases=["sbtimeout", "sbmute"], description="Apply a 15-minute voice & soundboard timeout to a member.")
    @commands.has_permissions(moderate_members=True)
    @app_commands.describe(member="Member interrupting with soundboard", minutes="Timeout minutes (default: 15)", reason="Reason for timeout")
    async def soundboard_timeout_cmd(self, ctx: commands.Context, member: discord.Member, minutes: int = 15, reason: str = "Disruptive Soundboard / Noise Interruption in VC"):
        await ctx.defer()
        
        # Apply Discord voice & chat timeout
        try:
            await member.timeout(datetime.timedelta(minutes=minutes), reason=f"Soundboard Timeout by {ctx.author.name}: {reason}")
        except Exception as e:
            logger.error(f"Failed to timeout member: {e}")

        # Server mute if in voice
        if member.voice:
            try:
                await member.edit(mute=True, reason=f"Soundboard Timeout: {reason}")
            except Exception:
                pass

        embed = discord.Embed(
            title="🔇 15-Minute Soundboard & Voice Timeout Applied",
            description=(
                f"✅ **{member.mention}** has been placed on a **{minutes}-minute Soundboard & Voice Timeout** by {ctx.author.mention}!\n\n"
                f"⏳ **Duration:** `{minutes} Minutes`\n"
                f"📝 **Reason:** `{reason}`\n"
                f"🛡️ **Status:** Voice Muted & Discord Timed Out"
            ),
            color=config.COLOR_WARNING,
            timestamp=datetime.datetime.now()
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="RAI SENTINEL 🛡️ Voice Moderation", icon_url=config.RAI_ICON_URL)

        await ctx.send(embed=embed)

        # Log action to mod-logs
        log_chan = discord.utils.get(ctx.guild.text_channels, name="📋・mod-logs")
        if log_chan:
            try:
                await log_chan.send(embed=embed)
            except Exception:
                pass


    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Enforces isolation on frozen members and automatically detects extreme noise/spam."""
        if member.bot:
            return

        guild = member.guild
        g_key = str(guild.id)
        u_key = str(member.id)

        # 1. Check if user is currently frozen
        if g_key in self.frozen_members and u_key in self.frozen_members[g_key]:
            freeze_info = self.frozen_members[g_key][u_key]
            expires_at = freeze_info.get("expires_at")

            # Check expiration
            if expires_at and expires_at != "PERMANENT":
                try:
                    exp_dt = datetime.datetime.fromisoformat(expires_at)
                    if datetime.datetime.now() >= exp_dt:
                        # Expired: Auto unfreeze
                        await self.execute_unfreeze(guild, member, guild.me)
                        return
                except Exception:
                    pass

            # Member is still frozen!
            chamber = await self.get_or_create_freeze_chamber(guild)

            # If member is in voice but NOT in the freeze chamber -> yank them right back
            if after.channel and after.channel.id != chamber.id:
                try:
                    await member.edit(
                        voice_channel=chamber,
                        mute=True,
                        deafen=True,
                        reason="Auto-Enforcing Freeze Chamber Isolation"
                    )
                except Exception:
                    pass

            # Ensure they remain muted & deafened in the chamber
            elif after.channel and after.channel.id == chamber.id:
                if not after.mute or not after.deaf:
                    try:
                        await member.edit(mute=True, deafen=True, reason="Enforcing Freeze Chamber Silence")
                    except Exception:
                        pass
            return

        # 2. Automated Voice Spam & Noise Detection
        # Detects rapid channel hopping, earrape mic-spamming, or rapid connect/disconnect trolling
        if not member.guild_permissions.moderate_members and not member.guild_permissions.administrator:
            now = time.time()
            u_id = member.id
            if u_id not in self.voice_spam_tracker:
                self.voice_spam_tracker[u_id] = []

            # Keep actions within last 4 seconds
            self.voice_spam_tracker[u_id] = [t for t in self.voice_spam_tracker[u_id] if now - t < 4.0]
            self.voice_spam_tracker[u_id].append(now)

            # If member triggers 4 or more rapid voice actions in 4 seconds (e.g. channel hopping or rapid mic noise)
            if len(self.voice_spam_tracker[u_id]) >= 4:
                self.voice_spam_tracker[u_id].clear()
                # Automatically Freeze and Timeout for 10 minutes
                await self.execute_freeze(
                    guild=guild,
                    member=member,
                    moderator=guild.me,
                    minutes=10,
                    reason="🚨 [AUTOMOD] Extreme Voice Noise / Mic Spamming / Rapid Channel Hopping"
                )


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))

