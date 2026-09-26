import os
import json
import time
import logging
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands

import database
import config

logger = logging.getLogger("SecurityDashboard")

def build_sentinel_panel_embed(guild: discord.Guild, settings: dict, whitelist_data: dict) -> discord.Embed:
    is_locked = bool(settings.get("lockdown", 0))
    is_raid = bool(settings.get("raid_mode", 0))
    is_alert = is_locked or is_raid

    antinuke = "🟢 ACTIVE" if settings.get("antinuke_enabled", 1) else "🔴 DISABLED"
    antiraid = "🟢 ACTIVE" if settings.get("antiraid_enabled", 1) else "🔴 DISABLED"
    antispam = "🟢 ACTIVE" if settings.get("antispam_enabled", 1) else "🔴 DISABLED"
    antilink = "🟢 ACTIVE" if settings.get("antilink_enabled", 1) else "🔴 DISABLED"
    antimention = "🟢 ACTIVE" if settings.get("antimention_enabled", 1) else "🔴 DISABLED"

    lockdown_badge = "🚨 [LOCKDOWN ENGAGED]" if is_locked else "🟢 NORMAL ACCESS"
    raid_badge = "🚨 [HIGH VELOCITY RAID]" if is_raid else "⚪ STANDBY"

    whitelisted_count = len(whitelist_data.get("users", []))
    whitelisted_roles_count = len(whitelist_data.get("roles", []))

    embed = discord.Embed(
        title="🛡️ RAI SENTINEL • EMERGENCY DEFENSE & PANIC SYSTEM",
        description=(
            "**Real-time threat monitoring and autonomous server defense center.**\n"
            "Use the controls below to instantly engage lockdown shields during hostile raids, nuke attempts, or mass exploit floods."
        ),
        color=0xFF0033 if is_alert else 0x00FF88
    )

    embed.add_field(
        name="🚨 Current Defense Posture",
        value=(
            f"• **Shield Status:** {lockdown_badge}\n"
            f"• **Raid Alert:** {raid_badge}\n"
            f"• **Active Defenders:** `{whitelisted_count}` Whitelisted Admins\n"
            f"• **Protected Roles:** `{whitelisted_roles_count}` Staff Roles"
        ),
        inline=False
    )

    embed.add_field(
        name="⚔️ Automated Shield Matrix",
        value=(
            f"• Anti-Nuke Engine: {antinuke}\n"
            f"• Anti-Raid Velocity: {antiraid}\n"
            f"• Anti-Spam Filter: {antispam}\n"
            f"• Anti-Phishing Link: {antilink}\n"
            f"• Anti-Mass Mention: {antimention}"
        ),
        inline=True
    )

    c_del = settings.get("channel_delete_limit", 3)
    r_del = settings.get("role_delete_limit", 3)
    b_lim = settings.get("ban_limit", 4)
    win = settings.get("time_window", 10)

    embed.add_field(
        name="⚙️ Anti-Nuke Watchdogs",
        value=(
            f"• Channel Delete: `{c_del} / {win}s`\n"
            f"• Role Delete: `{r_del} / {win}s`\n"
            f"• Member Ban: `{b_lim} / {win}s`\n"
            f"• Auto-Quarantine: 🟢 Armed"
        ),
        inline=True
    )

    embed.set_thumbnail(url=getattr(config, "SENTINEL_ICON_URL", ""))
    embed.set_footer(text="RAI SENTINEL 🛡️ Autonomous Defense Matrix • 24/7 Security", icon_url=getattr(config, "SENTINEL_ICON_URL", ""))
    embed.timestamp = discord.utils.utcnow()
    return embed


class SentinelPanicView(discord.ui.View):
    """Persistent interactive Sentinel Panic and Security Command Panel."""
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="PANIC LOCKDOWN",
        style=discord.ButtonStyle.danger,
        emoji="🚨",
        custom_id="sentinel:panic_lockdown"
    )
    async def panic_lockdown(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ **Access Denied**: Administrator authorization required to trigger Panic Lockdown.", ephemeral=True)

        await interaction.response.defer(thinking=True, ephemeral=True)
        guild = interaction.guild

        # 1. Update Database Status
        await database.update_guild_setting(guild.id, "lockdown", 1)
        await database.update_guild_setting(guild.id, "raid_mode", 1)

        locked_text = 0
        locked_voice = 0

        # 2. Lock Public Text Channels
        for channel in guild.text_channels:
            overwrites = channel.overwrites_for(guild.default_role)
            if overwrites.send_messages is not False:
                try:
                    overwrites.send_messages = False
                    overwrites.send_messages_in_threads = False
                    overwrites.create_public_threads = False
                    overwrites.create_private_threads = False
                    await channel.set_permissions(guild.default_role, overwrite=overwrites, reason=f"[Sentinel Panic] Initiated by {interaction.user.name}")
                    await channel.edit(slowmode_delay=10, reason="[Sentinel Panic] 10s anti-raid slowmode")
                    locked_text += 1
                except Exception:
                    pass

        # 3. Lock Public Voice Channels
        for vc in guild.voice_channels:
            overwrites = vc.overwrites_for(guild.default_role)
            if overwrites.connect is not False:
                try:
                    overwrites.connect = False
                    await vc.set_permissions(guild.default_role, overwrite=overwrites, reason=f"[Sentinel Panic] Initiated by {interaction.user.name}")
                    locked_voice += 1
                except Exception:
                    pass

        # 4. Record Incident in Database
        await database.record_security_event(
            guild.id,
            "EMERGENCY_PANIC_LOCKDOWN",
            f"🚨 Panic Lockdown engaged by {interaction.user.name} ({interaction.user.id}). Locked {locked_text} text & {locked_voice} voice channels.",
            severity="CRITICAL"
        )

        # 5. Update Original Panel Message
        try:
            settings = await database.get_guild_settings(guild.id)
            whitelist_data = await database.get_whitelist(guild.id)
            updated_embed = build_sentinel_panel_embed(guild, settings, whitelist_data)
            await interaction.message.edit(embed=updated_embed, view=self)
        except Exception:
            pass

        await interaction.followup.send(
            f"🚨 **EMERGENCY PANIC LOCKDOWN ENGAGED!**\n"
            f"• **Text Channels Locked:** `{locked_text}` (Messages, threads disabled, 10s slowmode)\n"
            f"• **Voice Channels Restricted:** `{locked_voice}` (Connect disabled)\n"
            f"• **Authorized Operator:** {interaction.user.mention}\n"
            f"• Standard members cannot chat or join voice until **Restore System** is pressed.",
            ephemeral=True
        )

    @discord.ui.button(
        label="RESTORE SYSTEM",
        style=discord.ButtonStyle.success,
        emoji="🔓",
        custom_id="sentinel:panic_unlock"
    )
    async def panic_unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ **Access Denied**: Administrator authorization required to lift lockdown.", ephemeral=True)

        await interaction.response.defer(thinking=True, ephemeral=True)
        guild = interaction.guild

        # 1. Update Database Status
        await database.update_guild_setting(guild.id, "lockdown", 0)
        await database.update_guild_setting(guild.id, "raid_mode", 0)

        unlocked_text = 0
        unlocked_voice = 0

        # 2. Restore Text Channels
        for channel in guild.text_channels:
            overwrites = channel.overwrites_for(guild.default_role)
            if overwrites.send_messages is False:
                try:
                    overwrites.send_messages = None
                    overwrites.send_messages_in_threads = None
                    overwrites.create_public_threads = None
                    overwrites.create_private_threads = None
                    await channel.set_permissions(guild.default_role, overwrite=overwrites, reason=f"[Sentinel Normalcy] Restored by {interaction.user.name}")
                    await channel.edit(slowmode_delay=0, reason="[Sentinel Normalcy] Reset slowmode")
                    unlocked_text += 1
                except Exception:
                    pass

        # 3. Restore Voice Channels
        for vc in guild.voice_channels:
            overwrites = vc.overwrites_for(guild.default_role)
            if overwrites.connect is False:
                try:
                    overwrites.connect = None
                    await vc.set_permissions(guild.default_role, overwrite=overwrites, reason=f"[Sentinel Normalcy] Restored by {interaction.user.name}")
                    unlocked_voice += 1
                except Exception:
                    pass

        # 4. Record Incident in Database
        await database.record_security_event(
            guild.id,
            "EMERGENCY_LOCKDOWN_LIFTED",
            f"🔓 Lockdown lifted by {interaction.user.name} ({interaction.user.id}). Restored {unlocked_text} text & {unlocked_voice} voice channels.",
            severity="LOW"
        )

        # 5. Update Original Panel Message
        try:
            settings = await database.get_guild_settings(guild.id)
            whitelist_data = await database.get_whitelist(guild.id)
            updated_embed = build_sentinel_panel_embed(guild, settings, whitelist_data)
            await interaction.message.edit(embed=updated_embed, view=self)
        except Exception:
            pass

        await interaction.followup.send(
            f"🔓 **SERVER COMMUNICATIONS RESTORED!**\n"
            f"• **Text Channels Restored:** `{unlocked_text}` (Normal chat & threads restored)\n"
            f"• **Voice Lounges Reopened:** `{unlocked_voice}`\n"
            f"• **Authorized Operator:** {interaction.user.mention}",
            ephemeral=True
        )

    @discord.ui.button(
        label="DEFENSE TELEMETRY",
        style=discord.ButtonStyle.secondary,
        emoji="🛡️",
        custom_id="sentinel:telemetry_audit"
    )
    async def telemetry_audit(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You require `Manage Server` permission to view defense telemetry.", ephemeral=True)

        events = await database.get_recent_security_events(interaction.guild.id, limit=5)
        settings = await database.get_guild_settings(interaction.guild.id)
        whitelist_data = await database.get_whitelist(interaction.guild.id)

        embed = discord.Embed(
            title=f"🛡️ Live Sentinel Telemetry • {interaction.guild.name}",
            description="**Recent automated defense triggers & threat telemetry:**",
            color=0x00FF88
        )

        if events:
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
        else:
            embed.description = "🟢 **Clean Threat Vector**: No recent incidents or attacks logged."

        embed.set_footer(text="RAI SENTINEL 🛡️ Telemetry Watchdog", icon_url=getattr(config, "SENTINEL_ICON_URL", ""))
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(
        label="SNAPSHOT BACKUP",
        style=discord.ButtonStyle.primary,
        emoji="💾",
        custom_id="sentinel:snapshot_backup"
    )
    async def snapshot_backup(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Administrator permission required.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild

        channel_count = 0
        for ch in guild.channels:
            try:
                await database.save_channel_snapshot(guild.id, ch)
                channel_count += 1
            except Exception:
                pass

        role_count = 0
        for role in guild.roles:
            try:
                await database.save_role_snapshot(guild.id, role)
                role_count += 1
            except Exception:
                pass

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
            f"Server backup generated by {interaction.user.name}. Captured {channel_count} channels & {role_count} roles.",
            severity="LOW"
        )

        embed = discord.Embed(
            title="💾 SERVER LAYOUT SNAPSHOT SECURED",
            description=(
                f"**Complete server structure preserved in vault.**\n\n"
                f"• **Channels Captured:** `{channel_count}`\n"
                f"• **Roles Captured:** `{role_count}`\n"
                f"• **Archive File:** `{backup_file.name}`\n"
                f"• **Vault:** SQLite & JSON Safe"
            ),
            color=0x00F5D4
        )
        embed.set_footer(text="RAI SENTINEL 🛡️ Recovery Vault", icon_url=getattr(config, "SENTINEL_ICON_URL", ""))
        await interaction.followup.send(embed=embed, ephemeral=True)


class SecurityDashboard(commands.Cog):
    """Central Security Command Center: Real-time telemetry status, emergency lockdown, and module switches."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    security_group = app_commands.Group(name="security", description="Security command center, module status, and emergency lockdown.")

    @security_group.command(name="panel", description="Deploy the interactive Sentinel Panic and Emergency Defense Panel.")
    async def security_panel(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ Administrator permission required to deploy security panel.", ephemeral=True)

        guild = interaction.guild
        settings = await database.get_guild_settings(guild.id)
        whitelist_data = await database.get_whitelist(guild.id)

        embed = build_sentinel_panel_embed(guild, settings, whitelist_data)
        view = SentinelPanicView()

        await interaction.response.send_message(embed=embed, view=view)

    @security_group.command(name="status", description="Display the complete server defense and security module status.")
    async def security_status(self, interaction: discord.Interaction):
        guild = interaction.guild
        settings = await database.get_guild_settings(guild.id)
        whitelist_data = await database.get_whitelist(guild.id)

        embed = build_sentinel_panel_embed(guild, settings, whitelist_data)
        await interaction.response.send_message(embed=embed)

    @security_group.command(name="lockdown", description="Initiate a server-wide emergency lockdown.")
    async def security_lockdown(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You require `Administrator` permission.", ephemeral=True)

        await interaction.response.defer(thinking=True)
        guild = interaction.guild
        await database.update_guild_setting(guild.id, "lockdown", 1)
        await database.update_guild_setting(guild.id, "raid_mode", 1)

        locked_count = 0
        for channel in guild.text_channels:
            overwrites = channel.overwrites_for(guild.default_role)
            if overwrites.send_messages is not False:
                try:
                    overwrites.send_messages = False
                    overwrites.send_messages_in_threads = False
                    await channel.set_permissions(guild.default_role, overwrite=overwrites, reason=f"[Lockdown] By {interaction.user.name}")
                    await channel.edit(slowmode_delay=10)
                    locked_count += 1
                except Exception:
                    pass

        embed = discord.Embed(
            title="🔒 SERVER-WIDE EMERGENCY LOCKDOWN ACTIVATED",
            description=f"**All public text channels have been locked!**\n• Channels Locked: `{locked_count}`\n• Authorized By: {interaction.user.mention}",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)

    @security_group.command(name="unlock", description="Lift emergency lockdown and restore public chat permissions.")
    async def security_unlock(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You require `Administrator` permission.", ephemeral=True)

        await interaction.response.defer(thinking=True)
        guild = interaction.guild
        await database.update_guild_setting(guild.id, "lockdown", 0)
        await database.update_guild_setting(guild.id, "raid_mode", 0)

        unlocked_count = 0
        for channel in guild.text_channels:
            overwrites = channel.overwrites_for(guild.default_role)
            if overwrites.send_messages is False:
                try:
                    overwrites.send_messages = None
                    overwrites.send_messages_in_threads = None
                    await channel.set_permissions(guild.default_role, overwrite=overwrites, reason=f"[Unlock] By {interaction.user.name}")
                    await channel.edit(slowmode_delay=0)
                    unlocked_count += 1
                except Exception:
                    pass

        embed = discord.Embed(
            title="🔓 EMERGENCY LOCKDOWN LIFTED",
            description=f"**Normal communications resumed.**\n• Channels Restored: `{unlocked_count}`\n• Authorized By: {interaction.user.mention}",
            color=0x00FF88
        )
        await interaction.followup.send(embed=embed)

    @security_group.command(name="audit", description="View recent security incidents, anti-nuke triggers, and defense telemetry.")
    async def security_audit(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You require `Manage Server` permission.", ephemeral=True)

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
            embed.add_field(name=f"{badge} {ev_type}", value=f"{details}\n*Recorded at: {ts}*", inline=False)

        embed.set_footer(text="RAI SENTINEL 🛡️ Telemetry Watchdog", icon_url=getattr(config, "SENTINEL_ICON_URL", ""))
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @security_group.command(name="backup", description="Create an immediate snapshot backup of server channels, roles, and settings.")
    async def security_backup(self, interaction: discord.Interaction):
        view = SentinelPanicView()
        # Delegate to snapshot_backup on view
        await view.snapshot_backup.callback(view, interaction)


async def setup(bot: commands.Bot):
    await bot.add_cog(SecurityDashboard(bot))
