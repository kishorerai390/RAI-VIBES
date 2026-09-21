import logging
import discord
from discord import app_commands
from discord.ext import commands

import database
import config

logger = logging.getLogger("SecurityDashboard")

class SecurityDashboard(commands.Cog):
    """Central Security Command Center: Real-time telemetry status, emergency lockdown, and module switches."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    security_group = app_commands.Group(name="security", description="Security command center, module status, and emergency lockdown.")

    @security_group.command(name="status", description="Display the complete server defense and security module status.")
    async def security_status(self, interaction: discord.Interaction):
        guild = interaction.guild
        settings = await database.get_guild_settings(guild.id)
        whitelist_data = await database.get_whitelist(guild.id)

        antinuke = "🟢 ACTIVE" if settings.get("antinuke_enabled", 1) else "🔴 DISABLED"
        antiraid = "🟢 ACTIVE" if settings.get("antiraid_enabled", 1) else "🔴 DISABLED"
        antispam = "🟢 ACTIVE" if settings.get("antispam_enabled", 1) else "🔴 DISABLED"
        antilink = "🟢 ACTIVE" if settings.get("antilink_enabled", 1) else "🔴 DISABLED"
        antimention = "🟢 ACTIVE" if settings.get("antimention_enabled", 1) else "🔴 DISABLED"
        
        raid_mode = "🚨 [ACTIVE]" if settings.get("raid_mode", 0) else "⚪ STANDBY"
        lockdown = "🔒 [LOCKED]" if settings.get("lockdown", 0) else "🟢 NORMAL"

        whitelisted_count = len(whitelist_data.get("users", []))
        whitelisted_roles_count = len(whitelist_data.get("roles", []))

        embed = discord.Embed(
            title=f"🛡️ Security Telemetry & Defense Status • {guild.name}",
            description="**Real-time shield monitoring against raids, rogue moderators, and server attacks.**",
            color=0x00FF88 if not settings.get("raid_mode") and not settings.get("lockdown") else 0xFF0033
        )
        
        # Module statuses
        embed.add_field(
            name="⚔️ Automated Shields",
            value=(
                f"• **Anti-Nuke Engine:** {antinuke}\n"
                f"• **Anti-Raid Velocity:** {antiraid}\n"
                f"• **Anti-Spam Filter:** {antispam}\n"
                f"• **Anti-Link & Phish:** {antilink}\n"
                f"• **Anti-Mass Mention:** {antimention}"
            ),
            inline=True
        )

        # Operational States
        embed.add_field(
            name="🚨 Operational States",
            value=(
                f"• **Raid Mode Shield:** {raid_mode}\n"
                f"• **Server Lockdown:** {lockdown}\n"
                f"• **Verification Role:** <@&{settings.get('verified_role_id')}>" if settings.get('verified_role_id') else "• **Verification:** 🟢 System Active\n"
                f"• **Whitelisted Users:** `{whitelisted_count}`\n"
                f"• **Whitelisted Roles:** `{whitelisted_roles_count}`"
            ),
            inline=True
        )

        # Anti-Nuke Thresholds
        c_del = settings.get("channel_delete_limit", 3)
        r_del = settings.get("role_delete_limit", 3)
        b_lim = settings.get("ban_limit", 4)
        k_lim = settings.get("kick_limit", 4)
        win = settings.get("time_window", 10)

        embed.add_field(
            name="⚙️ Anti-Nuke Thresholds (Audit Log Watchers)",
            value=(
                f"• Channel Delete: `{c_del} / {win}s`\n"
                f"• Role Delete: `{r_del} / {win}s`\n"
                f"• Member Ban: `{b_lim} / {win}s`\n"
                f"• Member Kick: `{k_lim} / {win}s`"
            ),
            inline=False
        )

        embed.set_footer(text="RAI SENTINEL 🛡️ Autonomous Server Defense Engine", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

    @security_group.command(name="lockdown", description="Initiate a server-wide emergency lockdown.")
    async def security_lockdown(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You require `Administrator` permission to trigger emergency lockdown.", ephemeral=True)

        await interaction.response.defer(thinking=True)
        guild = interaction.guild
        await database.update_guild_setting(guild.id, "lockdown", 1)

        locked_count = 0
        for channel in guild.text_channels:
            # Only lock channels where @everyone currently has permissions
            overwrites = channel.overwrites_for(guild.default_role)
            if overwrites.send_messages is not False:
                try:
                    overwrites.send_messages = False
                    await channel.set_permissions(guild.default_role, overwrite=overwrites, reason=f"[Emergency Lockdown] Triggered by {interaction.user.name}")
                    locked_count += 1
                except Exception:
                    pass

        embed = discord.Embed(
            title="🔒 SERVER-WIDE EMERGENCY LOCKDOWN ACTIVATED",
            description=(
                f"**All public text channels have been locked!**\n"
                f"• **Locked Channels:** `{locked_count}`\n"
                f"• **Triggered By:** {interaction.user.mention}\n"
                f"• Standard members cannot send messages until `/security unlock` is issued."
            ),
            color=0xFF0000
        )
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)

        await database.record_security_event(
            guild.id,
            "EMERGENCY_LOCKDOWN_TRIGGERED",
            f"Lockdown activated by {interaction.user.name} ({interaction.user.id}). {locked_count} channels locked.",
            severity="CRITICAL"
        )

    @security_group.command(name="unlock", description="Lift emergency lockdown and restore public chat permissions.")
    async def security_unlock(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You require `Administrator` permission.", ephemeral=True)

        await interaction.response.defer(thinking=True)
        guild = interaction.guild
        await database.update_guild_setting(guild.id, "lockdown", 0)

        unlocked_count = 0
        for channel in guild.text_channels:
            overwrites = channel.overwrites_for(guild.default_role)
            if overwrites.send_messages is False:
                try:
                    overwrites.send_messages = None  # Reset to default/inherit
                    await channel.set_permissions(guild.default_role, overwrite=overwrites, reason=f"[Lockdown Lifted] Triggered by {interaction.user.name}")
                    unlocked_count += 1
                except Exception:
                    pass

        embed = discord.Embed(
            title="🔓 EMERGENCY LOCKDOWN LIFTED",
            description=f"**Normal communications resumed.**\n• **Channels Restored:** `{unlocked_count}`\n• **Authorized By:** {interaction.user.mention}",
            color=0x00FF88
        )
        embed.timestamp = discord.utils.utcnow()
        await interaction.followup.send(embed=embed)

        await database.record_security_event(
            guild.id,
            "EMERGENCY_LOCKDOWN_LIFTED",
            f"Lockdown lifted by {interaction.user.name} ({interaction.user.id}). {unlocked_count} channels unlocked.",
            severity="LOW"
        )

    @security_group.command(name="audit", description="View recent security incidents, anti-nuke triggers, and defense telemetry.")
    async def security_audit(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You require `Manage Server` permission to view security audit logs.", ephemeral=True)

        events = await database.get_recent_security_events(interaction.guild.id, limit=8)
        if not events:
            return await interaction.response.send_message("🛡️ **Clean Defense Telemetry**: No security incidents or defense triggers recorded recently.", ephemeral=True)

        embed = discord.Embed(
            title=f"🛡️ Security Threat Telemetry • {interaction.guild.name}",
            description="Recent automated sentinel actions, threshold alerts, and incident records:",
            color=0x00FF88
        )

        for ev in events:
            sev = ev.get("severity", "MEDIUM")
            badge = "🔴" if sev == "CRITICAL" else ("🟠" if sev == "HIGH" else "🟡")
            ev_type = ev.get("event_type", "EVENT").replace("_", " ")
            details = ev.get("details", "")
            ts = ev.get("timestamp", "")
            embed.add_field(
                name=f"{badge} {ev_type}",
                value=f"{details}\n*Recorded at: {ts}*",
                inline=False
            )

        embed.set_footer(text="RAI SENTINEL 🛡️ Telemetry Watchdog", icon_url=self.bot.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @security_group.command(name="backup", description="Create an immediate snapshot backup of server channels, roles, and settings.")
    async def security_backup(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You require `Administrator` permission to trigger server backups.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        # 1. Capture Channel Snapshots
        channel_count = 0
        for ch in guild.channels:
            try:
                await database.save_channel_snapshot(guild.id, ch)
                channel_count += 1
            except Exception:
                pass

        # 2. Capture Role Snapshots
        role_count = 0
        for role in guild.roles:
            try:
                await database.save_role_snapshot(guild.id, role)
                role_count += 1
            except Exception:
                pass

        # 3. Export to JSON backup file
        import json
        from pathlib import Path
        import time

        backup_dir = Path(__file__).resolve().parent.parent / "data" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup_file = backup_dir / f"backup_{guild.id}_{int(time.time())}.json"

        snapshot = {
            "guild_id": guild.id,
            "guild_name": guild.name,
            "timestamp": int(time.time()),
            "channels": [
                {
                    "id": c.id,
                    "name": c.name,
                    "type": str(c.type),
                    "position": c.position,
                    "category": c.category.name if getattr(c, "category", None) else None
                }
                for c in guild.channels
            ],
            "roles": [
                {
                    "id": r.id,
                    "name": r.name,
                    "color": r.color.value,
                    "permissions": r.permissions.value,
                    "position": r.position
                }
                for r in guild.roles if not r.is_default()
            ]
        }

        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(snapshot, f, indent=2)

        await database.record_security_event(
            guild.id,
            "SNAPSHOT_BACKUP_CREATED",
            f"Server backup generated by {interaction.user.name} ({interaction.user.id}). Saved {channel_count} channels and {role_count} roles.",
            severity="LOW"
        )

        embed = discord.Embed(
            title="💾 SERVER SNAPSHOT BACKUP CREATED",
            description=(
                f"**Full server layout snapshot captured successfully!**\n\n"
                f"• **Channels Captured:** `{channel_count}`\n"
                f"• **Roles Captured:** `{role_count}`\n"
                f"• **Backup Archive:** `{backup_file.name}`\n"
                f"• **Status:** Stored securely in SQLite & JSON vault"
            ),
            color=0x00F5D4
        )
        embed.set_footer(text="RAI SENTINEL 🛡️ Autonomous Recovery Vault", icon_url=self.bot.user.display_avatar.url)
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(SecurityDashboard(bot))

