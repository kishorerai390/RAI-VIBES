import time
import asyncio
import logging
from collections import defaultdict
from typing import Dict, List, Optional
import discord
from discord.ext import commands, tasks

import database
import config

logger = logging.getLogger("AntiNuke")

TRUSTED_INTERNAL_BOT_IDS = {
    1546239150775078922, # RAI VIBES
    1546245134809571470, # RAI SENTINEL
    235088799074484224,  # Rythm
    1205557263738216559, # BeatSync
    276060004262477825,  # Koya
    678344927997853742,  # Sapphire
    536991182035746816,  # Wick
    720351927581278219,  # Invite Tracker
    302050872383242240,  # DISBOARD
}

ALERT_AUTO_DELETE_SECONDS = 60 # Automatically delete alert spam after 60 seconds

class AntiNuke(commands.Cog):
    """Real-Time Anti-Nuke System protecting server against mass deletion, mass bans, and malicious actions."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Action tracker: tracker[guild_id][user_id][action_type] = list of timestamps
        self.tracker: Dict[int, Dict[int, Dict[str, List[float]]]] = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self.cleanup_security_logs_task.start()

    def cog_unload(self):
        self.cleanup_security_logs_task.cancel()

    def is_trusted_actor(self, guild: discord.Guild, actor: Optional[discord.User | discord.Member]) -> bool:
        """Returns True if actor is a trusted bot, server owner, or immune administrator."""
        if not actor:
            return True
        if actor.id == self.bot.user.id or actor.id == guild.owner_id:
            return True
        if actor.id in TRUSTED_INTERNAL_BOT_IDS:
            return True
        if getattr(actor, "bot", False):
            return True
        return False

    @tasks.loop(seconds=30)
    async def cleanup_security_logs_task(self):
        """Periodically purges security alert messages older than 60s from security-logs channels."""
        await self.bot.wait_until_ready()
        now = discord.utils.utcnow()
        for guild in self.bot.guilds:
            channels_to_check = set()
            try:
                settings = await database.get_guild_settings(guild.id)
                log_chan = await self.get_log_channel(guild, settings)
                if log_chan:
                    channels_to_check.add(log_chan)
            except Exception:
                pass
            for name in ["security-logs", "mod-logs", "audit-logs", "staff-logs"]:
                ch = discord.utils.get(guild.text_channels, name=name)
                if ch:
                    channels_to_check.add(ch)

            for ch in channels_to_check:
                try:
                    async for msg in ch.history(limit=40):
                        age = (now - msg.created_at).total_seconds()
                        if age >= ALERT_AUTO_DELETE_SECONDS:
                            is_alert = (
                                msg.author.id == self.bot.user.id or
                                "@everyone" in (msg.content or "") or
                                (msg.embeds and any(
                                    "ALERT" in (e.title or "") or 
                                    "DEFENSE" in (e.title or "") or 
                                    "Interception" in (e.title or "") or
                                    "ANTI-NUKE" in (e.title or "") or
                                    "Shield" in (e.title or "")
                                    for e in msg.embeds
                                ))
                            )
                            if is_alert:
                                try:
                                    await msg.delete()
                                except Exception:
                                    pass
                except Exception:
                    pass

    def record_action(self, guild_id: int, user_id: int, action_type: str, time_window: int) -> int:
        now = time.time()
        timestamps = self.tracker[guild_id][user_id][action_type]
        # Clean expired timestamps outside time window
        timestamps = [t for t in timestamps if now - t <= time_window]
        timestamps.append(now)
        self.tracker[guild_id][user_id][action_type] = timestamps
        return len(timestamps)

    async def get_log_channel(self, guild: discord.Guild, settings: dict) -> Optional[discord.TextChannel]:
        log_id = settings.get("log_channel_id")
        if log_id:
            channel = guild.get_channel(log_id)
            if channel and isinstance(channel, discord.TextChannel):
                return channel
        # Fallback to standard named security log channels
        for name in ["security-logs", "mod-logs", "audit-logs", "staff-logs"]:
            channel = discord.utils.get(guild.text_channels, name=name)
            if channel:
                return channel
        return None

    async def neutralize_attacker(self, guild: discord.Guild, attacker: discord.Member, reason: str):
        """Strip dangerous permissions or ban the rogue user immediately."""
        try:
            # 1. Strip all roles below bot's highest role that have admin/manage permissions
            dangerous_roles = [
                r for r in attacker.roles
                if r != guild.default_role and r < guild.me.top_role and (
                    r.permissions.administrator or
                    r.permissions.manage_guild or
                    r.permissions.manage_channels or
                    r.permissions.manage_roles or
                    r.permissions.ban_members or
                    r.permissions.kick_members
                )
            ]
            if dangerous_roles:
                await attacker.remove_roles(*dangerous_roles, reason=f"[Anti-Nuke] Stripping dangerous roles: {reason}")
                logger.info(f"Stripped {len(dangerous_roles)} dangerous roles from attacker {attacker}")

            # 2. Ban attacker from guild
            await guild.ban(attacker, reason=f"[Anti-Nuke Triggered] {reason}", delete_message_days=0)
            logger.info(f"Successfully banned attacker {attacker} ({attacker.id}) from {guild.name}")
        except Exception as e:
            logger.error(f"Failed to neutralize attacker {attacker}: {e}")

    async def send_security_alert(self, guild: discord.Guild, attacker: discord.User, action_type: str, count: int, limit: int, restored: bool = False):
        settings = await database.get_guild_settings(guild.id)
        log_channel = await self.get_log_channel(guild, settings)

        embed = discord.Embed(
            title="🚨 CRITICAL SECURITY ALERT • ANTI-NUKE TRIGGERED 🚨",
            description=f"**Unauthorized mass destruction detected!** The Anti-Nuke defense system has neutralized the attacker.",
            color=0xFF0033
        )
        embed.add_field(name="👤 Offender / Attacker", value=f"{attacker.mention} (`{attacker.name}` • ID: `{attacker.id}`)", inline=False)
        embed.add_field(name="⚡ Violating Action", value=f"Mass **{action_type}** ({count}/{limit} in sliding window)", inline=True)
        embed.add_field(name="🛡️ Action Taken", value="**Banned & Roles Stripped**", inline=True)
        embed.add_field(name="🔄 Auto-Restoration", value="✅ **Attempted Automatic Re-creation**" if restored else "ℹ️ Not applicable", inline=True)
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1006/1006771.png")
        embed.set_footer(text="RAI SENTINEL 🛡️ Autonomous Server Defense Engine")
        embed.timestamp = discord.utils.utcnow()

        if log_channel:
            try:
                await log_channel.send(
                    content="@everyone 🚨 **SERVER EMERGENCY DEFENSE ACTIVATED**",
                    embed=embed,
                    delete_after=ALERT_AUTO_DELETE_SECONDS
                )
            except Exception:
                try:
                    await log_channel.send(embed=embed, delete_after=ALERT_AUTO_DELETE_SECONDS)
                except Exception:
                    pass

        # Also attempt to notify Server Owner via DM
        if guild.owner:
            try:
                await guild.owner.send(
                    f"🚨 **EMERGENCY NOTICE for '{guild.name}'**: Anti-Nuke triggered against `{attacker}` for mass `{action_type}`! Attacker was banned.",
                    embed=embed
                )
            except Exception:
                pass

        await database.record_security_event(
            guild.id,
            f"ANTI_NUKE_{action_type.upper()}",
            f"Attacker: {attacker} ({attacker.id}) tripped limit {count}/{limit}. Action: Banned.",
            severity="CRITICAL"
        )

    # -------------------------------------------------------------
    # 1. CHANNEL DELETION & CREATION MONITORING
    # -------------------------------------------------------------
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        settings = await database.get_guild_settings(guild.id)
        if not settings.get("antinuke_enabled", 1):
            return

        time_window = settings.get("time_window", 10)
        limit = settings.get("channel_delete_limit", 3)

        await asyncio.sleep(0.5)  # Allow audit log entry propagation
        try:
            async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.channel_delete):
                if entry.target and entry.target.id == channel.id:
                    actor = entry.user
                    if self.is_trusted_actor(guild, actor):
                        return
                    if await database.is_whitelisted(guild, actor):
                        return

                    count = self.record_action(guild.id, actor.id, "channel_delete", time_window)
                    if count >= limit:
                        member = guild.get_member(actor.id)
                        if member:
                            await self.neutralize_attacker(guild, member, f"Mass Channel Deletion ({count}/{limit})")

                        # Auto-restore channel from SQLite snapshot or current channel object
                        restored = False
                        try:
                            snap = await database.get_channel_snapshot(guild.id, channel.id)
                            cat = channel.category
                            topic = getattr(channel, "topic", None)
                            pos = channel.position
                            c_name = channel.name
                            c_type = "voice" if isinstance(channel, discord.VoiceChannel) else ("category" if isinstance(channel, discord.CategoryChannel) else "text")

                            if snap:
                                c_name = snap.get("name") or c_name
                                c_type = snap.get("channel_type") or c_type
                                topic = snap.get("topic") or topic
                                if snap.get("position") is not None:
                                    pos = snap["position"]
                                if snap.get("category_id"):
                                    cat_obj = guild.get_channel(snap["category_id"])
                                    if cat_obj and isinstance(cat_obj, discord.CategoryChannel):
                                        cat = cat_obj

                            if c_type == "voice":
                                await guild.create_voice_channel(name=c_name, category=cat, position=pos)
                                restored = True
                            elif c_type == "category":
                                await guild.create_category(name=c_name, position=pos)
                                restored = True
                            else:
                                await guild.create_text_channel(name=c_name, category=cat, position=pos, topic=topic or None)
                                restored = True
                        except Exception as e:
                            logger.error(f"Failed to auto-restore channel {channel.name}: {e}")

                        await self.send_security_alert(guild, actor, "Channel Deletion", count, limit, restored=restored)
                    break
        except discord.Forbidden:
            logger.warning(f"Anti-Nuke: Missing View Audit Log permission in {guild.name}")
        except Exception as e:
            logger.error(f"Error in on_guild_channel_delete: {e}")

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        settings = await database.get_guild_settings(guild.id)
        if not settings.get("antinuke_enabled", 1):
            return

        time_window = settings.get("time_window", 10)
        limit = 4

        await asyncio.sleep(0.5)
        try:
            async for entry in guild.audit_logs(limit=2, action=discord.AuditLogAction.channel_create):
                if entry.target and entry.target.id == channel.id:
                    actor = entry.user
                    if self.is_trusted_actor(guild, actor):
                        return
                    if await database.is_whitelisted(guild, actor):
                        return

                    count = self.record_action(guild.id, actor.id, "channel_create", time_window)
                    if count >= limit:
                        member = guild.get_member(actor.id)
                        if member:
                            await self.neutralize_attacker(guild, member, f"Mass Channel Spam Creation ({count}/{limit})")
                        try:
                            await channel.delete(reason="[Anti-Nuke] Spammed channel deletion")
                        except Exception:
                            pass
                        await self.send_security_alert(guild, actor, "Channel Creation Spam", count, limit)
                    break
        except Exception as e:
            logger.error(f"Error in on_guild_channel_create: {e}")

    # -------------------------------------------------------------
    # 2. ROLE DELETION & CREATION MONITORING
    # -------------------------------------------------------------
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        guild = role.guild
        settings = await database.get_guild_settings(guild.id)
        if not settings.get("antinuke_enabled", 1):
            return

        time_window = settings.get("time_window", 10)
        limit = settings.get("role_delete_limit", 3)

        await asyncio.sleep(0.5)
        try:
            async for entry in guild.audit_logs(limit=3, action=discord.AuditLogAction.role_delete):
                if entry.target and entry.target.id == role.id:
                    actor = entry.user
                    if self.is_trusted_actor(guild, actor):
                        return
                    if await database.is_whitelisted(guild, actor):
                        return

                    count = self.record_action(guild.id, actor.id, "role_delete", time_window)
                    if count >= limit:
                        member = guild.get_member(actor.id)
                        if member:
                            await self.neutralize_attacker(guild, member, f"Mass Role Deletion ({count}/{limit})")

                        # Auto-restore role from SQLite snapshot or current role object
                        restored = False
                        try:
                            snap = await database.get_role_snapshot(guild.id, role.id)
                            name = role.name
                            color = role.color
                            permissions = role.permissions
                            hoist = role.hoist

                            if snap:
                                name = snap.get("name") or name
                                if snap.get("color") is not None:
                                    color = discord.Color(snap["color"])
                                if snap.get("permissions") is not None:
                                    permissions = discord.Permissions(snap["permissions"])
                                if snap.get("hoist") is not None:
                                    hoist = bool(snap["hoist"])

                            await guild.create_role(name=name, color=color, permissions=permissions, hoist=hoist)
                            restored = True
                        except Exception as e:
                            logger.error(f"Failed to auto-restore role {role.name}: {e}")

                        await self.send_security_alert(guild, actor, "Role Deletion", count, limit, restored=restored)
                    break
        except Exception as e:
            logger.error(f"Error in on_guild_role_delete: {e}")

    # -------------------------------------------------------------
    # 3. MASS BAN & KICK MONITORING
    # -------------------------------------------------------------
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        settings = await database.get_guild_settings(guild.id)
        if not settings.get("antinuke_enabled", 1):
            return

        time_window = settings.get("time_window", 10)
        limit = settings.get("ban_limit", 4)

        await asyncio.sleep(0.5)
        try:
            async for entry in guild.audit_logs(limit=2, action=discord.AuditLogAction.ban):
                if entry.target and entry.target.id == user.id:
                    actor = entry.user
                    if self.is_trusted_actor(guild, actor):
                        return
                    if await database.is_whitelisted(guild, actor):
                        return

                    count = self.record_action(guild.id, actor.id, "member_ban", time_window)
                    if count >= limit:
                        member = guild.get_member(actor.id)
                        if member:
                            await self.neutralize_attacker(guild, member, f"Mass Member Ban Wave ({count}/{limit})")
                        await self.send_security_alert(guild, actor, "Mass Ban", count, limit)
                    break
        except Exception as e:
            logger.error(f"Error in on_member_ban: {e}")

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        settings = await database.get_guild_settings(guild.id)
        if not settings.get("antinuke_enabled", 1):
            return

        time_window = settings.get("time_window", 10)
        limit = settings.get("kick_limit", 4)

        await asyncio.sleep(0.5)
        try:
            async for entry in guild.audit_logs(limit=2, action=discord.AuditLogAction.kick):
                if entry.target and entry.target.id == member.id:
                    actor = entry.user
                    if self.is_trusted_actor(guild, actor):
                        return
                    if await database.is_whitelisted(guild, actor):
                        return

                    count = self.record_action(guild.id, actor.id, "member_kick", time_window)
                    if count >= limit:
                        attacker_member = guild.get_member(actor.id)
                        if attacker_member:
                            await self.neutralize_attacker(guild, attacker_member, f"Mass Member Kick Wave ({count}/{limit})")
                        await self.send_security_alert(guild, actor, "Mass Kick", count, limit)
                    break
        except Exception as e:
            logger.error(f"Error in on_member_remove: {e}")

    # -------------------------------------------------------------
    # 4. WEBHOOK MONITORING
    # -------------------------------------------------------------
    @commands.Cog.listener()
    async def on_webhooks_update(self, channel: discord.abc.GuildChannel):
        guild = channel.guild
        settings = await database.get_guild_settings(guild.id)
        if not settings.get("antinuke_enabled", 1):
            return

        time_window = settings.get("time_window", 10)
        limit = 3

        await asyncio.sleep(0.5)
        try:
            async for entry in guild.audit_logs(limit=2, action=discord.AuditLogAction.webhook_create):
                actor = entry.user
                if self.is_trusted_actor(guild, actor):
                    return
                if await database.is_whitelisted(guild, actor):
                    return

                count = self.record_action(guild.id, actor.id, "webhook_create", time_window)
                if count >= limit:
                    member = guild.get_member(actor.id)
                    if member:
                        await self.neutralize_attacker(guild, member, f"Unauthorized Mass Webhook Creation ({count}/{limit})")
                    # Delete unauthorized webhook
                    if entry.target:
                        try:
                            await entry.target.delete(reason="[Anti-Nuke] Rogue webhook creation")
                        except Exception:
                            pass
                    await self.send_security_alert(guild, actor, "Webhook Spam", count, limit)
                break
        except Exception as e:
            logger.error(f"Error in on_webhooks_update: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(AntiNuke(bot))
