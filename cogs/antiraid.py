import time
import logging
from collections import defaultdict, deque
from typing import Dict, Optional
import discord
from discord import app_commands
from discord.ext import commands

import database

logger = logging.getLogger("AntiRaid")

class AntiRaid(commands.Cog):
    """Real-Time Anti-Raid System detecting mass join waves, bot token storms, and suspicious velocity."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Deque of join timestamps per guild
        self.join_tracker: Dict[int, deque] = defaultdict(lambda: deque(maxlen=100))

    async def get_log_channel(self, guild: discord.Guild, settings: dict) -> Optional[discord.TextChannel]:
        log_id = settings.get("log_channel_id")
        if log_id:
            channel = guild.get_channel(log_id)
            if channel and isinstance(channel, discord.TextChannel):
                return channel
        for name in ["security-logs", "mod-logs", "audit-logs"]:
            channel = discord.utils.get(guild.text_channels, name=name)
            if channel:
                return channel
        return None

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        settings = await database.get_guild_settings(guild.id)
        if not settings.get("antiraid_enabled", 1):
            return

        now = time.time()
        tracker = self.join_tracker[guild.id]
        tracker.append(now)

        # Count joins within last 10 seconds
        recent_joins = [t for t in tracker if now - t <= 10]
        join_threshold = 10

        is_raid_active = bool(settings.get("raid_mode", 0))

        # 1. Trigger automated Raid Mode if threshold crossed
        if len(recent_joins) >= join_threshold and not is_raid_active:
            await database.update_guild_setting(guild.id, "raid_mode", 1)
            is_raid_active = True
            logger.warning(f"🚨 [RAID DETECTED] {len(recent_joins)} joins in 10s in {guild.name}! Activating Raid Mode.")

            log_channel = await self.get_log_channel(guild, settings)
            embed = discord.Embed(
                title="🚨 MASS RAID DETECTED • RAID MODE ACTIVATED 🚨",
                description=(
                    f"**Suspicious member join velocity triggered emergency protection!**\n"
                    f"• **Join Velocity:** `{len(recent_joins)} members` in `< 10 seconds`\n"
                    f"• **Status:** **Raid Mode is now [ACTIVE]**\n"
                    f"• **Protective Actions:** New arrivals are quarantined and restricted from public channels."
                ),
                color=0xFF0033
            )
            embed.set_footer(text="Use /raidmode off when the wave has ceased.")
            embed.timestamp = discord.utils.utcnow()

            if log_channel:
                try:
                    await log_channel.send(content="@everyone 🚨 **MASS RAID SHIELD ACTIVATED**", embed=embed, delete_after=60)
                except Exception:
                    try:
                        await log_channel.send(embed=embed, delete_after=60)
                    except Exception:
                        pass

            await database.record_security_event(
                guild.id,
                "MASS_RAID_TRIGGERED",
                f"Velocity: {len(recent_joins)} joins in 10s. Raid Mode enabled.",
                severity="CRITICAL"
            )

        # 2. If Raid Mode is active, apply quarantine or restrict member
        if is_raid_active:
            quarantine_id = settings.get("quarantine_role_id") or settings.get("unverified_role_id")
            if quarantine_id:
                quarantine_role = guild.get_role(quarantine_id)
                if quarantine_role and quarantine_role < guild.me.top_role:
                    try:
                        await member.add_roles(quarantine_role, reason="[Anti-Raid] Auto-quarantine during active raid mode")
                    except Exception as e:
                        logger.error(f"Failed to apply quarantine role to {member}: {e}")

            # Notify member in DM
            try:
                await member.send(
                    f"🛡️ **Notice from {guild.name}**: The server is currently under **Raid Protection Mode**. "
                    f"Your access has been temporarily restricted until staff review the security status."
                )
            except Exception:
                pass

        # 3. Account Age Shield (Anti-Alt Detection)
        account_age_hours = (discord.utils.utcnow() - member.created_at).total_seconds() / 3600
        if account_age_hours < 48:
            log_channel = await self.get_log_channel(guild, settings)
            if log_channel:
                alt_embed = discord.Embed(
                    title="⚠️ ANTI-ALT SHIELD • SUSPICIOUS ACCOUNT DETECTED",
                    description=(
                        f"**New member joined with a very recently created Discord account!**\n\n"
                        f"• **User:** {member.mention} (`{member.name}` • ID: `{member.id}`)\n"
                        f"• **Account Age:** `{account_age_hours:.1f} hours` (< 48h limit)\n"
                        f"• **Created At:** <t:{int(member.created_at.timestamp())}:R>\n"
                        f"• **Action Taken:** Flagged for surveillance / Requires standard verification"
                    ),
                    color=0xFFAA00
                )
                alt_embed.set_thumbnail(url=member.display_avatar.url)
                alt_embed.set_footer(text="RAI SENTINEL 🛡️ Autonomous Server Defense Engine")
                alt_embed.timestamp = discord.utils.utcnow()
                try:
                    await log_channel.send(embed=alt_embed, delete_after=120)
                except Exception:
                    pass

    # -------------------------------------------------------------
    # 2. ANTI-GHOSTPING INTERCEPTION
    # -------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        user_mentions = [m for m in message.mentions if not m.bot and m.id != message.author.id]
        role_mentions = [r for r in message.role_mentions]

        if not user_mentions and not role_mentions:
            return

        settings = await database.get_guild_settings(message.guild.id)
        log_channel = await self.get_log_channel(message.guild, settings)
        if log_channel:
            all_mentions = [m.mention for m in user_mentions] + [r.mention for r in role_mentions]
            embed = discord.Embed(
                title="👻 GHOST-PING INTERCEPTED",
                description=(
                    f"A deleted message contained targeted mentions!\n\n"
                    f"• **Offender:** {message.author.mention} (`{message.author.name}` • ID: `{message.author.id}`)\n"
                    f"• **Channel:** {message.channel.mention}\n"
                    f"• **Mentioned Target(s):** {', '.join(all_mentions)}\n"
                    f"• **Deleted Message:** {message.content[:400] if message.content else '*No text content*'}"
                ),
                color=0xFF5500
            )
            embed.set_footer(text="RAI SENTINEL 🛡️ Ghost-Ping Surveillance")
            embed.timestamp = discord.utils.utcnow()
            try:
                await log_channel.send(embed=embed, delete_after=90)
            except Exception:
                pass

    @app_commands.command(name="raidmode", description="Turn server-wide Raid Protection Mode ON or OFF.")
    @app_commands.describe(status="Choose whether Raid Mode is ON or OFF")
    @app_commands.choices(status=[
        app_commands.Choice(name="ON (Activate Emergency Join Shield)", value="on"),
        app_commands.Choice(name="OFF (Resume Standard Operations)", value="off")
    ])
    async def raidmode_command(self, interaction: discord.Interaction, status: str):
        if not interaction.user.guild_permissions.administrator and not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You require `Administrator` or `Manage Server` permission.", ephemeral=True)

        is_on = (status.lower() == "on")
        await database.update_guild_setting(interaction.guild.id, "raid_mode", 1 if is_on else 0)

        color = 0xFF0033 if is_on else 0x00FF88
        embed = discord.Embed(
            title=f"🛡️ Raid Protection Mode: {'[ACTIVATED]' if is_on else '[DEACTIVATED]'}",
            description=(
                f"**Raid Mode is now {'ON' if is_on else 'OFF'}.**\n"
                + ("• New members will be automatically quarantined.\n• Stricter verification required." if is_on else "• Normal joining resumed.\n• Standard verification rules apply.")
            ),
            color=color
        )
        embed.set_footer(text=f"Action by {interaction.user.name}")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

        await database.record_security_event(
            interaction.guild.id,
            "RAID_MODE_TOGGLED",
            f"Set to {status.upper()} by {interaction.user} ({interaction.user.id})",
            severity="MEDIUM"
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(AntiRaid(bot))
