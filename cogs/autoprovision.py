import time
import asyncio
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands, tasks

import database

logger = logging.getLogger("AutoProvision")

class AutoProvision(commands.Cog):
    """Zero-Setup Auto-Provisioning Engine: Self-initializes channels, roles, SQLite structure backups, and threat cooldowns."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.threat_cooldown_watchdog.start()

    def cog_unload(self):
        self.threat_cooldown_watchdog.cancel()

    @commands.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        logger.info("🛡️ [Auto-Provision] Checking server infrastructure across all guilds...")
        for guild in self.bot.guilds:
            try:
                await self.auto_provision_guild(guild)
            except Exception as e:
                logger.error(f"Auto-provision error in {guild.name}: {e}")

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        logger.info(f"🛡️ [Auto-Provision] Sentinel joined new guild: {guild.name}. Initializing autonomous defense...")
        try:
            await self.auto_provision_guild(guild)
        except Exception as e:
            logger.error(f"Auto-provision error on join {guild.name}: {e}")

    async def auto_provision_guild(self, guild: discord.Guild):
        settings = await database.get_guild_settings(guild.id)

        # 1. Take Snapshot of Channels & Roles for Disaster Recovery
        channel_count = 0
        for ch in guild.channels:
            try:
                await database.save_channel_snapshot(guild.id, ch)
                channel_count += 1
            except Exception:
                pass

        role_count = 0
        for r in guild.roles:
            if r != guild.default_role:
                try:
                    await database.save_role_snapshot(guild.id, r)
                    role_count += 1
                except Exception:
                    pass
        logger.info(f"📸 [SQLite Backup] Saved recovery snapshot of {channel_count} channels and {role_count} roles for '{guild.name}'")

        # 2. Check or Create Private #security-logs Channel
        log_channel = None
        log_id = settings.get("log_channel_id")
        if log_id:
            log_channel = guild.get_channel(log_id)

        if not log_channel:
            # Look for existing named channels including small-caps
            for ch in guild.text_channels:
                if ch.id == 1546593526073135107 or "sentinel" in ch.name.lower() or "ꜱᴇɴᴛɪɴᴇʟ" in ch.name or "audit" in ch.name.lower() or "ᴀᴜᴅɪᴛ" in ch.name or "security-logs" in ch.name.lower():
                    log_channel = ch
                    await database.update_guild_setting(guild.id, "log_channel_id", ch.id)
                    break

        # Auto-create if not found and permissions allow
        if not log_channel and guild.me.guild_permissions.manage_channels:
            try:
                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(view_channel=False),
                    guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, embed_links=True)
                }
                # Allow administrators to view
                for r in guild.roles:
                    if r.permissions.administrator:
                        overwrites[r] = discord.PermissionOverwrite(view_channel=True, send_messages=True)

                log_channel = await guild.create_text_channel(
                    name="security-logs",
                    overwrites=overwrites,
                    topic="🛡️ Automated RAI SENTINEL security audit logs, incident alerts, and anti-nuke telemetry.",
                    reason="[Auto-Provision] Created dedicated private security logs channel"
                )
                await database.update_guild_setting(guild.id, "log_channel_id", log_channel.id)
                logger.info(f"✅ Auto-created private #{log_channel.name} channel in {guild.name}")

                init_embed = discord.Embed(
                    title="🛡️ RAI SENTINEL • Autonomous Security Online",
                    description=(
                        "**Welcome to your automated server security feed.**\n\n"
                        "• **Anti-Nuke Engine:** `ACTIVE` (Monitors channel/role deletions, mass bans & kicks)\n"
                        "• **Anti-Raid Velocity:** `ACTIVE` (Monitors join storms)\n"
                        "• **Anti-Spam Filter:** `ACTIVE` (Progressive timeout escalation)\n"
                        "• **Anti-Link & Phish:** `ACTIVE` (Scam & unauthorized invite blocker)\n"
                        "• **Anti-Mass Mention:** `ACTIVE` (Interception for @everyone & ghost pings)\n"
                        "• **SQLite Disaster Snapshots:** `ACTIVE` (Automatic recovery backup taken)\n\n"
                        "No manual setup required. This channel is private and restricted to server staff."
                    ),
                    color=0x00FF88
                )
                init_embed.set_footer(text="Zero-Setup Server Security Engine")
                init_embed.timestamp = discord.utils.utcnow()
                await log_channel.send(embed=init_embed)
            except Exception as e:
                logger.error(f"Could not auto-create security-logs channel: {e}")

        # 3. Check Roles
        if guild.me.guild_permissions.manage_roles:
            # Check Verified Role
            verified_role = discord.utils.get(guild.roles, id=1549504522953695269)
            if not verified_role:
                for r in guild.roles:
                    if "verified" in r.name.lower() or "member" in r.name.lower():
                        verified_role = r
                        break
            if verified_role:
                await database.update_guild_setting(guild.id, "verified_role_id", verified_role.id)

    # -------------------------------------------------------------
    # REAL-TIME SQLITE STRUCTURE BACKUPS
    # -------------------------------------------------------------
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        try:
            await database.save_channel_snapshot(channel.guild.id, channel)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        try:
            await database.save_channel_snapshot(after.guild.id, after)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        try:
            await database.save_role_snapshot(role.guild.id, role)
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        try:
            await database.save_role_snapshot(after.guild.id, after)
        except Exception:
            pass

    # -------------------------------------------------------------
    # AUTOMATIC COOLDOWN & AUTO-UNLOCK WATCHDOG
    # -------------------------------------------------------------
    @tasks.loop(minutes=2)
    async def threat_cooldown_watchdog(self):
        """Scans guilds under emergency lockdown or raid mode. Auto-unlocks after 15 mins of calm."""
        for guild in self.bot.guilds:
            try:
                settings = await database.get_guild_settings(guild.id)
                is_locked = bool(settings.get("lockdown", 0))
                is_raid = bool(settings.get("raid_mode", 0))

                if not is_locked and not is_raid:
                    continue

                # Query latest security event timestamp
                async with database.get_db() as db:
                    cur = await db.execute(
                        "SELECT strftime('%s', timestamp) FROM security_events WHERE guild_id = ? ORDER BY id DESC LIMIT 1",
                        (guild.id,)
                    )
                    row = await cur.fetchone()

                now = time.time()
                last_event_time = float(row[0]) if row and row[0] else now

                # If 15 minutes (900 seconds) have passed without new critical incidents, auto-de-escalate!
                if now - last_event_time >= 900:
                    logger.info(f"🟢 [Threat Mitigated] 15 minutes of calm detected in '{guild.name}'. Auto-de-escalating defense.")
                    
                    # 1. Reset database states
                    await database.update_guild_setting(guild.id, "lockdown", 0)
                    await database.update_guild_setting(guild.id, "raid_mode", 0)

                    # 2. Lift public channel lockdowns
                    unlocked_count = 0
                    for ch in guild.text_channels:
                        overwrites = ch.overwrites_for(guild.default_role)
                        if overwrites.send_messages is False:
                            try:
                                overwrites.send_messages = None
                                await ch.set_permissions(guild.default_role, overwrite=overwrites, reason="[Auto-Cooldown] Threat mitigated, unlocking channel.")
                                unlocked_count += 1
                            except Exception:
                                pass

                    # 3. Notify security log channel
                    log_id = settings.get("log_channel_id")
                    log_channel = guild.get_channel(log_id) if log_id else None
                    if log_channel:
                        embed = discord.Embed(
                            title="🟢 THREAT MITIGATED • AUTOMATIC DE-ESCALATION",
                            description=(
                                f"**Server has returned to normal operational status.**\n\n"
                                f"• **Calm Period:** No hostile actions detected for 15 minutes.\n"
                                f"• **Emergency Lockdown:** Lifted (`{unlocked_count}` channels restored).\n"
                                f"• **Raid Mode:** Deactivated (Standard onboarding active)."
                            ),
                            color=0x00FF88
                        )
                        embed.timestamp = discord.utils.utcnow()
                        try:
                            await log_channel.send(embed=embed)
                        except Exception:
                            pass
            except Exception as e:
                logger.error(f"Watchdog error in {guild.name}: {e}")

    # -------------------------------------------------------------
    # SLASH COMMANDS: /backup
    # -------------------------------------------------------------
    backup_group = app_commands.Group(name="backup", description="Server disaster recovery snapshots and restoration.")

    @backup_group.command(name="snapshot", description="Take a fresh SQLite backup snapshot of all server channels and roles.")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_snapshot_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        ch_count = 0
        for ch in guild.channels:
            try:
                await database.save_channel_snapshot(guild.id, ch)
                ch_count += 1
            except Exception:
                pass

        role_count = 0
        for r in guild.roles:
            if r != guild.default_role:
                try:
                    await database.save_role_snapshot(guild.id, r)
                    role_count += 1
                except Exception:
                    pass

        embed = discord.Embed(
            title="📸 Disaster Recovery Snapshot Created",
            description=(
                f"Successfully backed up server infrastructure to persistent SQLite vault:\n\n"
                f"• **Channels Stored:** `{ch_count}`\n"
                f"• **Roles Stored:** `{role_count}`\n"
                f"• **Snapshot Timestamp:** <t:{int(time.time())}:F>"
            ),
            color=0x00FF88
        )
        embed.set_footer(text="RAI SENTINEL • Anti-Nuke Recovery Vault")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @backup_group.command(name="status", description="View current disaster recovery snapshot statistics.")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_status_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        channels = await database.get_all_channel_snapshots(interaction.guild_id)
        roles = await database.get_all_role_snapshots(interaction.guild_id)

        embed = discord.Embed(
            title="🛡️ Disaster Recovery Vault Status",
            color=0x70A1FF
        )
        embed.add_field(name="📁 Backed Up Channels", value=f"`{len(channels)}` channels", inline=True)
        embed.add_field(name="🎭 Backed Up Roles", value=f"`{len(roles)}` roles", inline=True)
        embed.add_field(name="🔒 Vault Engine", value="`SQLite3 Persistent WAL`", inline=True)
        embed.set_footer(text="RAI SENTINEL • Disaster Recovery")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @backup_group.command(name="restore", description="Restore deleted channels and roles from the disaster recovery snapshot.")
    @app_commands.checks.has_permissions(administrator=True)
    async def backup_restore_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        channels_snap = await database.get_all_channel_snapshots(guild.id)
        roles_snap = await database.get_all_role_snapshots(guild.id)

        if not channels_snap and not roles_snap:
            return await interaction.followup.send("❌ No snapshot records found in vault for this server.", ephemeral=True)

        existing_channel_names = {c.name.lower() for c in guild.channels}
        existing_role_names = {r.name.lower() for r in guild.roles}

        restored_roles = 0
        for r_data in roles_snap:
            r_name = r_data["name"]
            if r_name.lower() not in existing_role_names:
                try:
                    await guild.create_role(
                        name=r_name,
                        color=discord.Color(r_data.get("color", 0)),
                        permissions=discord.Permissions(r_data.get("permissions", 0)),
                        hoist=bool(r_data.get("hoist", 0)),
                        reason="[Disaster Recovery] Restoring missing role from vault"
                    )
                    restored_roles += 1
                except Exception as e:
                    logger.warning(f"Could not restore role {r_name}: {e}")

        restored_channels = 0
        # 1. Restore categories first
        category_map = {}
        for c_data in channels_snap:
            if c_data.get("channel_type") == "category":
                c_name = c_data["name"]
                cat = discord.utils.get(guild.categories, name=c_name)
                if not cat:
                    try:
                        cat = await guild.create_category(name=c_name, reason="[Disaster Recovery] Restoring category")
                        restored_channels += 1
                    except Exception:
                        pass
                if cat:
                    category_map[c_data["channel_id"]] = cat

        # 2. Restore text and voice channels
        for c_data in channels_snap:
            c_type = c_data.get("channel_type")
            if c_type == "category":
                continue
            c_name = c_data["name"]
            if c_name.lower() not in existing_channel_names:
                target_cat = category_map.get(c_data.get("category_id"))
                try:
                    if c_type == "voice":
                        await guild.create_voice_channel(name=c_name, category=target_cat, reason="[Disaster Recovery] Restoring voice channel")
                    else:
                        await guild.create_text_channel(name=c_name, category=target_cat, topic=c_data.get("topic") or None, reason="[Disaster Recovery] Restoring text channel")
                    restored_channels += 1
                except Exception as e:
                    logger.warning(f"Could not restore channel {c_name}: {e}")

        embed = discord.Embed(
            title="🛡️ Disaster Recovery Completed",
            description=(
                f"Restoration process completed from vault snapshot:\n\n"
                f"• **Restored Channels:** `{restored_channels}`\n"
                f"• **Restored Roles:** `{restored_roles}`\n\n"
                f"Any channels or roles that were missing have been reconstructed."
            ),
            color=0x2ED573
        )
        embed.set_footer(text="RAI SENTINEL • Autonomous Infrastructure Restoration")
        await interaction.followup.send(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AutoProvision(bot))
