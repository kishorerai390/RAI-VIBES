import os
import json
import time
import datetime
import logging
from pathlib import Path
from typing import Optional, Dict, List, Tuple

import discord
from discord import app_commands
from discord.ext import commands

import database
import config

logger = logging.getLogger("SecurityDashboard")

EXCLUDED_CATEGORIES = ["STAFF", "OPERATIONS", "ADMIN", "MANAGEMENT", "ARCHIVE", "LOGS"]
EXCLUDED_CHANNELS = [
    "sentinel-logs", "mod-logs", "audit-logs", "staff-chat", "admin-chat", 
    "tickets", "ticket", "verify", "rules", "announcements", "security-logs"
]

def is_staff_or_excluded_channel(channel: discord.abc.GuildChannel) -> bool:
    """Determine if a channel belongs to staff, logging, or system operations and should be excluded from lockdown."""
    name_lower = channel.name.lower()
    for excl in EXCLUDED_CHANNELS:
        if excl in name_lower:
            return True
            
    if getattr(channel, "category", None):
        cat_name_upper = channel.category.name.upper()
        for cat_excl in EXCLUDED_CATEGORIES:
            if cat_excl in cat_name_upper:
                return True
    return False


async def execute_panic_lockdown(
    guild: discord.Guild, 
    operator_name: str, 
    reason: str = "Hostile Raid / Emergency Containment"
) -> Tuple[int, int]:
    """Execute complete server-wide emergency lockdown."""
    settings = await database.get_guild_settings(guild.id)
    await database.update_guild_setting(guild.id, "lockdown", 1)
    await database.update_guild_setting(guild.id, "raid_mode", 1)

    verified_role_id = settings.get("verified_role_id")
    verified_role = guild.get_role(verified_role_id) if verified_role_id else None
    if not verified_role:
        for r in guild.roles:
            if "verified" in r.name.lower():
                verified_role = r
                break

    locked_text = 0
    locked_voice = 0

    # 1. Lock Public Text Channels
    for channel in guild.text_channels:
        if is_staff_or_excluded_channel(channel):
            continue

        try:
            # Overwrite for @everyone
            everyone_ov = channel.overwrites_for(guild.default_role)
            everyone_ov.send_messages = False
            everyone_ov.send_messages_in_threads = False
            everyone_ov.create_public_threads = False
            everyone_ov.create_private_threads = False
            everyone_ov.add_reactions = False
            await channel.set_permissions(guild.default_role, overwrite=everyone_ov, reason=f"[Sentinel Panic] Initiated by {operator_name}")

            # Overwrite for Verified Role if present
            if verified_role:
                v_ov = channel.overwrites_for(verified_role)
                v_ov.send_messages = False
                v_ov.send_messages_in_threads = False
                v_ov.create_public_threads = False
                v_ov.create_private_threads = False
                v_ov.add_reactions = False
                await channel.set_permissions(verified_role, overwrite=v_ov, reason=f"[Sentinel Panic] Initiated by {operator_name}")

            await channel.edit(slowmode_delay=15, reason="[Sentinel Panic] Anti-raid chat slowmode")
            locked_text += 1
        except Exception as e:
            logger.debug(f"Could not lock text channel {channel.name}: {e}")

    # 2. Lock Public Voice Channels
    for vc in guild.voice_channels:
        if is_staff_or_excluded_channel(vc):
            continue

        try:
            vc_ov = vc.overwrites_for(guild.default_role)
            vc_ov.connect = False
            vc_ov.speak = False
            await vc.set_permissions(guild.default_role, overwrite=vc_ov, reason=f"[Sentinel Panic] Initiated by {operator_name}")

            if verified_role:
                v_ov = vc.overwrites_for(verified_role)
                v_ov.connect = False
                v_ov.speak = False
                await vc.set_permissions(verified_role, overwrite=v_ov, reason=f"[Sentinel Panic] Initiated by {operator_name}")

            locked_voice += 1
        except Exception as e:
            logger.debug(f"Could not lock voice channel {vc.name}: {e}")

    # 3. Log security event
    await database.record_security_event(
        guild.id,
        "EMERGENCY_PANIC_LOCKDOWN",
        f"🚨 Panic Lockdown engaged by {operator_name}. Locked {locked_text} text & {locked_voice} voice channels. Reason: {reason}",
        severity="CRITICAL"
    )

    # 4. Broadcast Emergency Containment Embed
    broadcast_embed = discord.Embed(
        title="🚨 ┊ 𝐂𝐑𝐈𝐓𝐈𝐂𝐀𝐋  𝐒𝐄𝐑𝐕𝐄𝐑  𝐏𝐀𝐍𝐈𝐂  𝐋𝐎𝐂𝐊𝐃𝐎𝐖𝐍",
        description=(
            f"🛡️ **The Sentinel Defense Matrix has placed {guild.name} into High-Security Lockdown.**\n\n"
            f"• **Containment Reason:** `{reason}`\n"
            f"• **Authorized Operator:** `{operator_name}`\n"
            f"• **Text Channels:** Public messaging, threads, and reactions temporarily frozen.\n"
            f"• **Voice Lounges:** Audio connections restricted.\n"
            f"• **Border Control:** All incoming joins are automatically placed into quarantine.\n\n"
            f"⚡ *Please remain calm while server administrators neutralize security threats.*"
        ),
        color=0xFF0033
    )
    broadcast_embed.set_footer(text="RAI SENTINEL 🛡️ Fortress Defense Protocol", icon_url=getattr(config, "SENTINEL_ICON_URL", ""))
    broadcast_embed.timestamp = discord.utils.utcnow()

    for ch_name in ["💬｜ɢᴇɴᴇʀᴀʟ-ᴄʜᴀᴛ", "general-chat", "general", "📢｜ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛꜱ", "announcements"]:
        ch = discord.utils.get(guild.text_channels, name=ch_name)
        if ch:
            try:
                await ch.send(embed=broadcast_embed)
            except Exception:
                pass

    return locked_text, locked_voice


async def execute_panic_unlock(guild: discord.Guild, operator_name: str) -> Tuple[int, int]:
    """Lift emergency lockdown and restore normal server operations."""
    settings = await database.get_guild_settings(guild.id)
    await database.update_guild_setting(guild.id, "lockdown", 0)
    await database.update_guild_setting(guild.id, "raid_mode", 0)

    verified_role_id = settings.get("verified_role_id")
    verified_role = guild.get_role(verified_role_id) if verified_role_id else None
    if not verified_role:
        for r in guild.roles:
            if "verified" in r.name.lower():
                verified_role = r
                break

    unlocked_text = 0
    unlocked_voice = 0

    # 1. Restore Text Channels
    for channel in guild.text_channels:
        if is_staff_or_excluded_channel(channel):
            continue

        try:
            # Clear @everyone lockdown overrides
            everyone_ov = channel.overwrites_for(guild.default_role)
            everyone_ov.send_messages = None
            everyone_ov.send_messages_in_threads = None
            everyone_ov.create_public_threads = None
            everyone_ov.create_private_threads = None
            everyone_ov.add_reactions = None
            await channel.set_permissions(guild.default_role, overwrite=everyone_ov, reason=f"[Sentinel Normalcy] Restored by {operator_name}")

            # Restore Verified Role chat
            if verified_role:
                v_ov = channel.overwrites_for(verified_role)
                v_ov.send_messages = True
                v_ov.send_messages_in_threads = True
                v_ov.add_reactions = True
                await channel.set_permissions(verified_role, overwrite=v_ov, reason=f"[Sentinel Normalcy] Restored by {operator_name}")

            await channel.edit(slowmode_delay=0, reason="[Sentinel Normalcy] Reset chat slowmode")
            unlocked_text += 1
        except Exception as e:
            logger.debug(f"Could not unlock text channel {channel.name}: {e}")

    # 2. Restore Voice Channels
    for vc in guild.voice_channels:
        if is_staff_or_excluded_channel(vc):
            continue

        try:
            vc_ov = vc.overwrites_for(guild.default_role)
            vc_ov.connect = None
            vc_ov.speak = None
            await vc.set_permissions(guild.default_role, overwrite=vc_ov, reason=f"[Sentinel Normalcy] Restored by {operator_name}")

            if verified_role:
                v_ov = vc.overwrites_for(verified_role)
                v_ov.connect = True
                v_ov.speak = True
                await vc.set_permissions(verified_role, overwrite=v_ov, reason=f"[Sentinel Normalcy] Restored by {operator_name}")

            unlocked_voice += 1
        except Exception as e:
            logger.debug(f"Could not unlock voice channel {vc.name}: {e}")

    # 3. Log security event
    await database.record_security_event(
        guild.id,
        "EMERGENCY_LOCKDOWN_LIFTED",
        f"🔓 Lockdown lifted by {operator_name}. Restored {unlocked_text} text & {unlocked_voice} voice channels.",
        severity="LOW"
    )

    # 4. Broadcast All-Clear Embed
    clear_embed = discord.Embed(
        title="🔓 ┊ 𝐒𝐄𝐑𝐕𝐄𝐑  𝐃𝐄𝐅𝐄𝐍𝐒𝐄  𝐀𝐋𝐋-𝐂𝐋𝐄𝐀𝐑",
        description=(
            f"✨ **Sentinel Emergency Lockdown has been officially lifted.**\n\n"
            f"• **Restoration Operator:** `{operator_name}`\n"
            f"• **Communications Restored:** All public text channels, media sharing, and voice lounges are open.\n"
            f"• **Safety Note:** Security matrix remains actively monitoring. Please follow server rules and enjoy **{guild.name}**!"
        ),
        color=0x00FF88
    )
    clear_embed.set_footer(text="RAI SENTINEL 🛡️ Fortress Defense Protocol", icon_url=getattr(config, "SENTINEL_ICON_URL", ""))
    clear_embed.timestamp = discord.utils.utcnow()

    for ch_name in ["💬｜ɢᴇɴᴇʀᴀʟ-ᴄʜᴀᴛ", "general-chat", "general", "📢｜ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛꜱ", "announcements"]:
        ch = discord.utils.get(guild.text_channels, name=ch_name)
        if ch:
            try:
                await ch.send(embed=clear_embed)
            except Exception:
                pass

    return unlocked_text, unlocked_voice


async def execute_quarantine(guild: discord.Guild, member: discord.Member, operator_name: str, reason: str = "Hostile Raid / Exploit Containment") -> bool:
    """Strip member roles, apply quarantine role, and timeout for 24 hours."""
    settings = await database.get_guild_settings(guild.id)
    q_role_id = settings.get("quarantine_role_id") or settings.get("unverified_role_id")
    q_role = guild.get_role(q_role_id) if q_role_id else None

    if not q_role:
        for r in guild.roles:
            if "quarantin" in r.name.lower():
                q_role = r
                break

    try:
        # 1. Native Discord Timeout (24 Hours)
        await member.timeout(datetime.timedelta(days=1), reason=f"[Quarantine by {operator_name}] {reason}")
    except Exception as e:
        logger.warning(f"Could not apply timeout to {member}: {e}")

    try:
        # 2. Strip non-managed roles
        roles_to_remove = [r for r in member.roles if not r.is_default() and not r.managed and r < guild.me.top_role]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=f"[Quarantine by {operator_name}] Stripping roles")

        # 3. Add quarantine role
        if q_role and q_role < guild.me.top_role:
            await member.add_roles(q_role, reason=f"[Quarantine by {operator_name}] {reason}")
    except Exception as e:
        logger.error(f"Failed to modify roles for {member}: {e}")

    # 4. DM Notification
    try:
        await member.send(
            f"🔒 **Notice from {guild.name}**: Your account has been placed into **Quarantine Isolation** by staff.\n"
            f"• **Reason:** `{reason}`\n"
            f"• **Duration:** 24 hours (pending moderator review)\n"
            f"• If you believe this is an error, please wait for staff instructions."
        )
    except Exception:
        pass

    # 5. Log Security Event
    await database.record_security_event(
        guild.id,
        "MEMBER_QUARANTINED",
        f"🔒 Member {member} ({member.id}) quarantined by {operator_name}. Reason: {reason}",
        severity="HIGH"
    )
    return True


async def execute_unquarantine(guild: discord.Guild, member: discord.Member, operator_name: str) -> bool:
    """Lift quarantine role, restore verified role, and remove timeout."""
    settings = await database.get_guild_settings(guild.id)
    q_role_id = settings.get("quarantine_role_id")
    v_role_id = settings.get("verified_role_id")

    q_role = guild.get_role(q_role_id) if q_role_id else None
    v_role = guild.get_role(v_role_id) if v_role_id else None

    try:
        # 1. Clear timeout
        await member.timeout(None, reason=f"[Unquarantine by {operator_name}]")
    except Exception:
        pass

    try:
        # 2. Remove quarantine role
        if q_role and q_role in member.roles and q_role < guild.me.top_role:
            await member.remove_roles(q_role, reason=f"[Unquarantine by {operator_name}]")

        # 3. Grant verified role
        if v_role and v_role not in member.roles and v_role < guild.me.top_role:
            await member.add_roles(v_role, reason=f"[Unquarantine by {operator_name}] Access restored")
    except Exception as e:
        logger.error(f"Failed to restore roles for {member}: {e}")

    # 4. DM Notification
    try:
        await member.send(
            f"✨ **Notice from {guild.name}**: Your Quarantine has been lifted by {operator_name}. "
            f"Your standard membership privileges have been restored."
        )
    except Exception:
        pass

    await database.record_security_event(
        guild.id,
        "MEMBER_UNQUARANTINED",
        f"✨ Member {member} ({member.id}) released from quarantine by {operator_name}.",
        severity="MEDIUM"
    )
    return True


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

    c_del = settings.get("channel_delete_limit", 2)
    r_del = settings.get("role_delete_limit", 2)
    b_lim = settings.get("ban_limit", 3)
    k_lim = settings.get("kick_limit", 3)
    win = settings.get("time_window", 10)

    embed.add_field(
        name="⚙️ Anti-Nuke Watchdogs",
        value=(
            f"• Channel Delete: `{c_del} / {win}s`\n"
            f"• Role Delete: `{r_del} / {win}s`\n"
            f"• Member Ban: `{b_lim} / {win}s`\n"
            f"• Member Kick: `{k_lim} / {win}s`"
        ),
        inline=True
    )

    embed.set_thumbnail(url=getattr(config, "SENTINEL_ICON_URL", ""))
    embed.set_footer(text="RAI SENTINEL 🛡️ Autonomous Defense Matrix • 24/7 Security", icon_url=getattr(config, "SENTINEL_ICON_URL", ""))
    embed.timestamp = discord.utils.utcnow()
    return embed


class SentinelPanicConfirmView(discord.ui.View):
    """Confirmation prompt to verify Panic Lockdown activation."""
    def __init__(self, operator: discord.User):
        super().__init__(timeout=60)
        self.operator = operator

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.operator.id:
            await interaction.response.send_message("❌ This confirmation prompt is reserved for the initiating administrator.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="CONFIRM EMERGENCY LOCKDOWN", style=discord.ButtonStyle.danger, emoji="🚨")
    async def confirm_panic(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer(thinking=True, ephemeral=True)
        guild = interaction.guild
        locked_text, locked_voice = await execute_panic_lockdown(
            guild,
            operator_name=interaction.user.name,
            reason="Sentinel Panic Control Panel Activation"
        )
        self.stop()
        await interaction.followup.send(
            f"🚨 **EMERGENCY PANIC LOCKDOWN CONFIRMED & ENGAGED!**\n"
            f"• **Text Channels Locked:** `{locked_text}` (Messages frozen, slowmode 15s)\n"
            f"• **Voice Lounges Locked:** `{locked_voice}` (Connections disabled)\n"
            f"• **Authorized Operator:** {interaction.user.mention}\n"
            f"• Standard members cannot chat or join voice until **Restore System** is engaged.",
            ephemeral=True
        )

    @discord.ui.button(label="Cancel", style=discord.ButtonStyle.secondary, emoji="✖️")
    async def cancel_panic(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.stop()
        await interaction.response.send_message("🛡️ Panic Lockdown aborted. Server remains under normal operations.", ephemeral=True)


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

        confirm_view = SentinelPanicConfirmView(interaction.user)
        await interaction.response.send_message(
            "⚠️ **CRITICAL SECURITY ALERT • CONFIRMATION REQUIRED**\n\n"
            "Are you certain you wish to engage **Server-Wide Panic Lockdown**?\n"
            "• This will immediately freeze public messaging across all text channels.\n"
            "• Voice lounges will reject new connections.\n"
            "• All arriving members will be quarantined automatically.",
            view=confirm_view,
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
        unlocked_text, unlocked_voice = await execute_panic_unlock(guild, operator_name=interaction.user.name)

        # Update Original Panel Message if possible
        try:
            settings = await database.get_guild_settings(guild.id)
            whitelist_data = await database.get_whitelist(guild.id)
            updated_embed = build_sentinel_panel_embed(guild, settings, whitelist_data)
            await interaction.message.edit(embed=updated_embed, view=self)
        except Exception:
            pass

        await interaction.followup.send(
            f"🔓 **SERVER COMMUNICATIONS FULLY RESTORED!**\n"
            f"• **Text Channels Restored:** `{unlocked_text}` (Regular chat active)\n"
            f"• **Voice Lounges Restored:** `{unlocked_voice}` (Audio open)\n"
            f"• **Authorized Operator:** {interaction.user.mention}",
            ephemeral=True
        )

    @discord.ui.button(
        label="PURGE RAIDERS",
        style=discord.ButtonStyle.secondary,
        emoji="⚡",
        custom_id="sentinel:purge_raiders"
    )
    async def purge_raiders(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not interaction.user.guild_permissions.administrator and not interaction.user.guild_permissions.kick_members:
            return await interaction.response.send_message("❌ You require `Administrator` or `Kick Members` permission.", ephemeral=True)

        await interaction.response.defer(thinking=True, ephemeral=True)
        guild = interaction.guild
        now = discord.utils.utcnow()
        kicked = 0

        settings = await database.get_guild_settings(guild.id)
        verified_id = settings.get("verified_role_id")
        verified_role = guild.get_role(verified_id) if verified_id else None

        for member in guild.members:
            if member.bot or member.guild_permissions.administrator or member.guild_permissions.manage_guild:
                continue
            if verified_role and verified_role in member.roles:
                continue
            
            # Check if joined within last 60 minutes
            if member.joined_at and (now - member.joined_at).total_seconds() <= 3600:
                try:
                    await member.kick(reason=f"[Raid Purge by {interaction.user.name}] Recent unverified account")
                    kicked += 1
                except Exception:
                    pass

        await database.record_security_event(
            guild.id,
            "RAID_PURGE_EXECUTED",
            f"⚡ Purged {kicked} recent unverified raid accounts by {interaction.user.name}.",
            severity="MEDIUM"
        )

        await interaction.followup.send(
            f"⚡ **RAID PURGE COMPLETE!**\n"
            f"• **Accounts Removed:** `{kicked}` unverified member(s) joined within the last 60m.\n"
            f"• **Operator:** {interaction.user.mention}",
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

        events = await database.get_recent_security_events(interaction.guild.id, limit=6)
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
    """Central Security Command Center: Real-time telemetry status, emergency panic lockdown, and threat mitigation."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------------------------------------------
    # TOP-LEVEL SLASH COMMANDS FOR INSTANT CRISIS ACCESS
    # -------------------------------------------------------------
    @app_commands.command(name="panic", description="Engage or disengage instant server-wide Emergency Panic Lockdown.")
    @app_commands.describe(
        action="Choose whether to engage ON, lift OFF, or check current STATUS",
        reason="Reason for engaging panic lockdown"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="ON (Freeze all text & voice lounges)", value="on"),
        app_commands.Choice(name="OFF (Lift lockdown and restore communications)", value="off"),
        app_commands.Choice(name="STATUS (Check active shield posture)", value="status")
    ])
    async def panic_command(self, interaction: discord.Interaction, action: str, reason: Optional[str] = "Emergency Containment Protocol"):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ **Access Denied**: Administrator permission required to operate the Panic System.", ephemeral=True)

        guild = interaction.guild
        if action == "status":
            settings = await database.get_guild_settings(guild.id)
            whitelist_data = await database.get_whitelist(guild.id)
            embed = build_sentinel_panel_embed(guild, settings, whitelist_data)
            return await interaction.response.send_message(embed=embed, ephemeral=True)

        if action == "on":
            await interaction.response.defer(thinking=True)
            locked_text, locked_voice = await execute_panic_lockdown(guild, interaction.user.name, reason=reason)
            embed = discord.Embed(
                title="🚨 EMERGENCY PANIC LOCKDOWN ENGAGED",
                description=(
                    f"**The server has been placed into emergency containment.**\n\n"
                    f"• **Text Channels Frozen:** `{locked_text}`\n"
                    f"• **Voice Lounges Restricted:** `{locked_voice}`\n"
                    f"• **Reason:** `{reason}`\n"
                    f"• **Authorized Operator:** {interaction.user.mention}"
                ),
                color=0xFF0033
            )
            embed.set_footer(text="Use /panic action:OFF to lift containment.")
            return await interaction.followup.send(embed=embed)

        elif action == "off":
            await interaction.response.defer(thinking=True)
            unlocked_text, unlocked_voice = await execute_panic_unlock(guild, interaction.user.name)
            embed = discord.Embed(
                title="🔓 EMERGENCY LOCKDOWN LIFTED",
                description=(
                    f"**Server communications and voice lounges have been restored.**\n\n"
                    f"• **Text Channels Restored:** `{unlocked_text}`\n"
                    f"• **Voice Lounges Restored:** `{unlocked_voice}`\n"
                    f"• **Authorized Operator:** {interaction.user.mention}"
                ),
                color=0x00FF88
            )
            return await interaction.followup.send(embed=embed)

    @app_commands.command(name="quarantine", description="Isolate an offending member: strips roles, adds quarantine, and applies 24h timeout.")
    @app_commands.describe(member="Member to isolate", reason="Reason for quarantine isolation")
    async def quarantine_command(self, interaction: discord.Interaction, member: discord.Member, reason: Optional[str] = "Hostile raid / exploit activity"):
        if not interaction.user.guild_permissions.moderate_members and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You require `Moderate Members` or `Administrator` permission.", ephemeral=True)

        if member.top_role >= interaction.user.top_role and interaction.guild.owner_id != interaction.user.id:
            return await interaction.response.send_message("❌ You cannot quarantine a member with an equal or higher role than yourself.", ephemeral=True)

        await interaction.response.defer(thinking=True)
        await execute_quarantine(interaction.guild, member, interaction.user.name, reason=reason)
        embed = discord.Embed(
            title="🔒 MEMBER QUARANTINED & ISOLATED",
            description=(
                f"**Member has been placed into high-security isolation.**\n\n"
                f"• **Target:** {member.mention} (`{member.name}` • ID: `{member.id}`)\n"
                f"• **Timeout Applied:** `24 Hours`\n"
                f"• **Reason:** `{reason}`\n"
                f"• **Enforced By:** {interaction.user.mention}"
            ),
            color=0xFF0033
        )
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="unquarantine", description="Release an isolated member from quarantine and restore verified status.")
    @app_commands.describe(member="Member to release")
    async def unquarantine_command(self, interaction: discord.Interaction, member: discord.Member):
        if not interaction.user.guild_permissions.moderate_members and not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You require `Moderate Members` or `Administrator` permission.", ephemeral=True)

        await interaction.response.defer(thinking=True)
        await execute_unquarantine(interaction.guild, member, interaction.user.name)
        embed = discord.Embed(
            title="✨ MEMBER RELEASED FROM QUARANTINE",
            description=(
                f"**Member has been returned to standard community standing.**\n\n"
                f"• **Target:** {member.mention} (`{member.name}` • ID: `{member.id}`)\n"
                f"• **Timeout Cleared:** ✅\n"
                f"• **Verified Access Granted:** ✅\n"
                f"• **Operator:** {interaction.user.mention}"
            ),
            color=0x00FF88
        )
        await interaction.followup.send(embed=embed)

    # -------------------------------------------------------------
    # SECURITY DASHBOARD GROUP
    # -------------------------------------------------------------
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
        locked_text, locked_voice = await execute_panic_lockdown(guild, interaction.user.name)

        embed = discord.Embed(
            title="🔒 SERVER-WIDE EMERGENCY LOCKDOWN ACTIVATED",
            description=f"**All public channels have been locked!**\n• Text Channels Locked: `{locked_text}`\n• Voice Lounges Restricted: `{locked_voice}`\n• Operator: {interaction.user.mention}",
            color=0xFF0000
        )
        await interaction.followup.send(embed=embed)

    @security_group.command(name="unlock", description="Lift emergency lockdown and restore public chat permissions.")
    async def security_unlock(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            return await interaction.response.send_message("❌ You require `Administrator` permission.", ephemeral=True)

        await interaction.response.defer(thinking=True)
        guild = interaction.guild
        unlocked_text, unlocked_voice = await execute_panic_unlock(guild, interaction.user.name)

        embed = discord.Embed(
            title="🔓 EMERGENCY LOCKDOWN LIFTED",
            description=f"**Normal communications resumed.**\n• Text Channels Restored: `{unlocked_text}`\n• Voice Lounges Restored: `{unlocked_voice}`\n• Operator: {interaction.user.mention}",
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
        await view.snapshot_backup.callback(interaction)


async def setup(bot: commands.Bot):
    await bot.add_cog(SecurityDashboard(bot))
