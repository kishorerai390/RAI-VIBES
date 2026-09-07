import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
import re
import os
import json
import unicodedata
import asyncio
import time
from typing import Optional, Dict

import config

logger = logging.getLogger("VoiceHub")

class RenameVoiceModal(discord.ui.Modal, title="Rename Your Voice Room"):
    new_name = discord.ui.TextInput(
        label="New Voice Channel Name",
        placeholder="e.g., Alex's Chill Lounge, Vibing Only",
        max_length=40,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        vc = getattr(getattr(interaction.user, "voice", None), "channel", None)
        if not vc:
            return await interaction.response.send_message("❌ You are not connected to a voice room.", ephemeral=True)
        try:
            old_name = vc.name
            await vc.edit(name=f"🎧 {self.new_name.value}")
            await interaction.response.send_message(f"✅ Voice room renamed from `{old_name}` to `🎧 {self.new_name.value}`!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Could not rename channel: {e}", ephemeral=True)


class LimitVoiceModal(discord.ui.Modal, title="Set Room Member Limit"):
    limit = discord.ui.TextInput(
        label="Member Limit (0 for Unlimited, up to 99)",
        placeholder="e.g. 2, 4, 10",
        max_length=2,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        vc = getattr(getattr(interaction.user, "voice", None), "channel", None)
        if not vc:
            return await interaction.response.send_message("❌ You are not connected to a voice room.", ephemeral=True)
        try:
            val = int(self.limit.value.strip())
            if 0 <= val <= 99:
                await vc.edit(user_limit=val)
                limit_text = "Unlimited" if val == 0 else str(val)
                await interaction.response.send_message(f"👥 Room limit set to **{limit_text}** members!", ephemeral=True)
            else:
                await interaction.response.send_message("❌ Please enter a number between 0 and 99.", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number.", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Error updating limit: {e}", ephemeral=True)


class SetStatusVoiceModal(discord.ui.Modal, title="Set Voice Channel Status"):
    status_text = discord.ui.TextInput(
        label="Voice Room Status / Activity",
        placeholder="e.g., Grinding Valorant 🎮, Midnight Lofi 🌙, Chill Hangout",
        max_length=80,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        vc = getattr(getattr(interaction.user, "voice", None), "channel", None)
        if not vc:
            return await interaction.response.send_message("❌ You are not connected to a voice room.", ephemeral=True)
        try:
            try:
                await vc.edit(status=self.status_text.value)
            except Exception:
                pass
            await interaction.response.send_message(f"💬 Voice status set to: **{self.status_text.value}**", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Could not update status: {e}", ephemeral=True)


class InviteUserSelectView(discord.ui.View):
    """User dropdown menu to grant access to a Ghost / Hidden voice channel."""
    def __init__(self, vc: discord.VoiceChannel, owner: discord.Member):
        super().__init__(timeout=90)
        self.vc = vc
        self.owner = owner

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="Select members to reveal & permit into your room...",
        min_values=1,
        max_values=10
    )
    async def select_members(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        if interaction.user.id != self.owner.id:
            return await interaction.response.send_message("❌ Only the voice room owner can permit members.", ephemeral=True)

        added = []
        for user in select.values:
            if isinstance(user, discord.Member) and not user.bot:
                await self.vc.set_permissions(user, view_channel=True, connect=True, speak=True)
                added.append(user.mention)

        if added:
            members_str = ", ".join(added)
            await interaction.response.send_message(
                f"✅ **Granted Hidden VC Access:** {members_str} can now see and join `{self.vc.name}`!",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ No valid members selected.", ephemeral=True)


class RevokeUserSelectView(discord.ui.View):
    """User dropdown menu to revoke access and hide channel from selected members."""
    def __init__(self, vc: discord.VoiceChannel, owner: discord.Member):
        super().__init__(timeout=90)
        self.vc = vc
        self.owner = owner

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="Select members to revoke / hide channel from...",
        min_values=1,
        max_values=10
    )
    async def revoke_members(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        if interaction.user.id != self.owner.id:
            return await interaction.response.send_message("❌ Only the voice room owner can revoke permissions.", ephemeral=True)

        revoked = []
        for user in select.values:
            if isinstance(user, discord.Member) and user.id != self.owner.id:
                await self.vc.set_permissions(user, overwrite=None)
                if user in self.vc.members:
                    try:
                        await user.move_to(None)
                    except Exception:
                        pass
                revoked.append(user.mention)

        if revoked:
            members_str = ", ".join(revoked)
            await interaction.response.send_message(
                f"🚫 **Access Revoked:** Hidden from {members_str} and removed from room.",
                ephemeral=True
            )
        else:
            await interaction.response.send_message("❌ No valid members selected.", ephemeral=True)


class KickUserSelectView(discord.ui.View):
    """User dropdown menu to disconnect a user from the room."""
    def __init__(self, vc: discord.VoiceChannel, owner: discord.Member):
        super().__init__(timeout=90)
        self.vc = vc
        self.owner = owner

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="Select member(s) to kick from this voice room...",
        min_values=1,
        max_values=5
    )
    async def kick_members(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        if interaction.user.id != self.owner.id:
            return await interaction.response.send_message("❌ Only the voice room owner can kick members.", ephemeral=True)

        kicked = []
        for user in select.values:
            if isinstance(user, discord.Member) and user.id != self.owner.id:
                if user in self.vc.members:
                    try:
                        await user.move_to(None)
                        kicked.append(user.mention)
                    except Exception:
                        pass

        if kicked:
            await interaction.response.send_message(f"👢 **Kicked from voice room:** {', '.join(kicked)}", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Selected member(s) are not in this voice channel.", ephemeral=True)


class TransferOwnerSelectView(discord.ui.View):
    """User dropdown menu to transfer voice room ownership."""
    def __init__(self, vc: discord.VoiceChannel, owner: discord.Member, cog):
        super().__init__(timeout=90)
        self.vc = vc
        self.owner = owner
        self.cog = cog

    @discord.ui.select(
        cls=discord.ui.UserSelect,
        placeholder="Select a squadmate to transfer ownership to...",
        min_values=1,
        max_values=1
    )
    async def transfer_owner(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        if interaction.user.id != self.owner.id:
            return await interaction.response.send_message("❌ Only current room owner can transfer ownership.", ephemeral=True)

        new_owner = select.values[0]
        if not isinstance(new_owner, discord.Member) or new_owner.bot or new_owner.id == self.owner.id:
            return await interaction.response.send_message("❌ Please select a valid squadmate.", ephemeral=True)

        self.cog.temp_channels[self.vc.id] = new_owner.id
        self.cog._save_temp_channels()

        # Update perms
        await self.vc.set_permissions(new_owner, connect=True, speak=True, mute_members=True, move_members=True, manage_channels=True)
        await interaction.response.send_message(f"👑 **Ownership Transferred!** {new_owner.mention} is now the host of `{self.vc.name}`!", ephemeral=False)


class VoiceControlView(discord.ui.View):
    """Persistent 24/7 Voice Room Controls for Dynamic Voice Hub."""
    def __init__(self):
        super().__init__(timeout=None)

    def get_user_vc(self, interaction: discord.Interaction) -> Optional[discord.VoiceChannel]:
        return getattr(getattr(interaction.user, "voice", None), "channel", None)

    @discord.ui.button(label="Lock", style=discord.ButtonStyle.danger, emoji="🔒", row=0, custom_id="vc_lock")
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to lock it.", ephemeral=True)
        await vc.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 **Room Locked!** Only users you permit can join.", ephemeral=True)

    @discord.ui.button(label="Unlock", style=discord.ButtonStyle.success, emoji="🔓", row=0, custom_id="vc_unlock")
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to unlock it.", ephemeral=True)
        await vc.set_permissions(interaction.guild.default_role, connect=None)
        await interaction.response.send_message("🔓 **Room Unlocked!** Everyone can join.", ephemeral=True)

    @discord.ui.button(label="Rename", style=discord.ButtonStyle.primary, emoji="🏷️", row=0, custom_id="vc_rename")
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to rename it.", ephemeral=True)
        await interaction.response.send_modal(RenameVoiceModal())

    @discord.ui.button(label="Limit", style=discord.ButtonStyle.secondary, emoji="👥", row=0, custom_id="vc_limit")
    async def limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to change limits.", ephemeral=True)
        await interaction.response.send_modal(LimitVoiceModal())

    @discord.ui.button(label="Ghost (Hide)", style=discord.ButtonStyle.secondary, emoji="👻", row=1, custom_id="vc_ghost")
    async def ghost(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to ghost/hide it.", ephemeral=True)
        
        current_perms = vc.overwrites_for(interaction.guild.default_role)
        is_hidden = current_perms.view_channel is False
        
        if is_hidden:
            # Un-ghost (make visible to @everyone again)
            await vc.set_permissions(interaction.guild.default_role, view_channel=None)
            await interaction.response.send_message("👁️ **Voice room is now VISIBLE to everyone in the server!**", ephemeral=True)
        else:
            # Ghost / Hide from @everyone
            await vc.set_permissions(interaction.guild.default_role, view_channel=False)
            # Ensure owner can always see & connect
            await vc.set_permissions(interaction.user, view_channel=True, connect=True, speak=True)
            # Ensure any current members in room can also see
            for m in vc.members:
                if not m.bot:
                    await vc.set_permissions(m, view_channel=True, connect=True, speak=True)
            await interaction.response.send_message(
                "👻 **Voice room is now GHOSTED (HIDDEN)!**\n"
                "• Completely invisible to other members in the server.\n"
                "• Only you and permitted members can see and join.\n"
                "• Click **`✉️ Permit / Invite`** to select specific members to show this room to!",
                ephemeral=True
            )

    @discord.ui.button(label="Permit", style=discord.ButtonStyle.primary, emoji="✉️", row=1, custom_id="vc_permit")
    async def permit(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to invite members.", ephemeral=True)
        
        view = InviteUserSelectView(vc, interaction.user)
        await interaction.response.send_message("✉️ **Select members below to reveal & permit into your hidden room:**", view=view, ephemeral=True)

    @discord.ui.button(label="Revoke", style=discord.ButtonStyle.danger, emoji="🚫", row=1, custom_id="vc_revoke")
    async def revoke(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to revoke access.", ephemeral=True)
        
        view = RevokeUserSelectView(vc, interaction.user)
        await interaction.response.send_message("🚫 **Select members below to revoke access & hide this channel from:**", view=view, ephemeral=True)

    @discord.ui.button(label="Kick Member", style=discord.ButtonStyle.danger, emoji="👢", row=2, custom_id="vc_kick")
    async def kick_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to kick members.", ephemeral=True)
        
        view = KickUserSelectView(vc, interaction.user)
        await interaction.response.send_message("👢 **Select member(s) to disconnect from this voice room:**", view=view, ephemeral=True)

    @discord.ui.button(label="Transfer Host", style=discord.ButtonStyle.primary, emoji="👑", row=2, custom_id="vc_transfer")
    async def transfer_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to transfer ownership.", ephemeral=True)
        
        cog = interaction.client.get_cog("VoiceHub")
        if not cog or vc.id not in cog.temp_channels or cog.temp_channels[vc.id] != interaction.user.id:
            return await interaction.response.send_message("❌ You can only transfer ownership of rooms you created.", ephemeral=True)

        view = TransferOwnerSelectView(vc, interaction.user, cog)
        await interaction.response.send_message("👑 **Select a squadmate to become the new room host:**", view=view, ephemeral=True)

    @discord.ui.button(label="Status", style=discord.ButtonStyle.secondary, emoji="💬", row=2, custom_id="vc_status")
    async def status(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to set status.", ephemeral=True)
        await interaction.response.send_modal(SetStatusVoiceModal())


class VoiceHub(commands.Cog):
    """Dynamic Join-to-Create temporary private voice channels with interactive Ghost & Permission controls."""
    TEMP_PREFIXES = ("🎧 ", "👤 ", "👥 ", "🔺 ", "🛡️ ", "⭐ ", "🌟 ")
    TEMP_SUFFIXES = ("'s Lounge", "'s Solo", "'s Duo", "'s Trio", "'s Squad", "'s 5-Man", "'s 6-Man")
    INACTIVITY_GRACE_SECONDS = 60  # Auto-delete empty temporary voice rooms after 60 seconds of inactivity

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.temp_channels = {}  # channel_id: owner_id
        self.temp_db_path = os.path.join("data", "temp_vcs.json")
        self.deletion_tasks: Dict[int, asyncio.Task] = {}
        self._load_temp_channels()

    async def cog_load(self):
        if not self.cleanup_temp_channels_task.is_running():
            self.cleanup_temp_channels_task.start()

    def cog_unload(self):
        self.cleanup_temp_channels_task.cancel()
        for task in self.deletion_tasks.values():
            task.cancel()
        self.deletion_tasks.clear()

    def _load_temp_channels(self):
        try:
            if os.path.exists(self.temp_db_path):
                with open(self.temp_db_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.temp_channels = {int(k): int(v) for k, v in data.items()}
        except Exception as e:
            logger.warning(f"Could not load temp channels: {e}")

    def _save_temp_channels(self):
        try:
            os.makedirs(os.path.dirname(self.temp_db_path), exist_ok=True)
            with open(self.temp_db_path, "w", encoding="utf-8") as f:
                json.dump({str(k): v for k, v in self.temp_channels.items()}, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save temp channels: {e}")

    def is_temporary_channel(self, channel: discord.VoiceChannel) -> bool:
        if not channel or not isinstance(channel, discord.VoiceChannel):
            return False
        if channel.id in self.temp_channels:
            return True
        # Also check name patterns in case bot restarted
        name = channel.name
        if any(name.startswith(p) for p in self.TEMP_PREFIXES) and any(name.endswith(s) for s in self.TEMP_SUFFIXES):
            return True
        return False

    def schedule_inactivity_deletion(self, channel: discord.VoiceChannel, delay: int = INACTIVITY_GRACE_SECONDS):
        """Schedules a temporary voice channel for deletion after a period of inactivity."""
        existing_task = self.deletion_tasks.get(channel.id)
        if existing_task and not existing_task.done():
            return  # Already scheduled and counting down

        async def _delayed_delete():
            try:
                logger.info(f"Temporary VC '{channel.name}' (ID: {channel.id}) is inactive/empty. Scheduled auto-deletion in {delay}s.")
                try:
                    embed = discord.Embed(
                        title="⏳ Inactivity Notice",
                        description=(
                            f"This voice room is now empty.\n"
                            f"It will be **automatically deleted in {delay} seconds** unless someone rejoins!"
                        ),
                        color=discord.Color.gold()
                    )
                    await channel.send(embed=embed, delete_after=delay)
                except Exception:
                    pass

                await asyncio.sleep(delay)

                # Fetch fresh channel state from bot cache/API
                ch = self.bot.get_channel(channel.id)
                if ch and isinstance(ch, discord.VoiceChannel):
                    if len(ch.members) == 0:
                        if ch.id in self.temp_channels:
                            del self.temp_channels[ch.id]
                            self._save_temp_channels()
                        await ch.delete(reason=f"Temporary voice channel inactive for {delay} seconds.")
                        logger.info(f"Auto-deleted inactive temp voice channel '{ch.name}' (ID: {channel.id})")
                    else:
                        logger.info(f"Temporary VC '{ch.name}' is no longer empty; cancelling auto-deletion.")
            except asyncio.CancelledError:
                logger.info(f"Auto-deletion cancelled for '{channel.name}' (ID: {channel.id}) - member rejoined.")
            except discord.NotFound:
                if channel.id in self.temp_channels:
                    del self.temp_channels[channel.id]
                    self._save_temp_channels()
            except Exception as e:
                logger.error(f"Error during delayed deletion of temp channel {channel.id}: {e}")
            finally:
                self.deletion_tasks.pop(channel.id, None)

        self.deletion_tasks[channel.id] = asyncio.create_task(_delayed_delete())

    @tasks.loop(seconds=30)
    async def cleanup_temp_channels_task(self):
        """Periodically scans for and schedules deletion for any empty temporary voice channels."""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                if self.is_temporary_channel(channel) and len(channel.members) == 0:
                    if channel.id not in self.deletion_tasks or self.deletion_tasks[channel.id].done():
                        self.schedule_inactivity_deletion(channel, delay=self.INACTIVITY_GRACE_SECONDS)

    @cleanup_temp_channels_task.before_loop
    async def before_cleanup_task(self):
        import asyncio
        while not self.bot.is_ready():
            await asyncio.sleep(1)

    @app_commands.command(name="voicepanel", description="Display the interactive Voice Room Controls dashboard.")
    async def voicepanel_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎛️ Voice Room Controls Dashboard",
            description=(
                "Use the interactive buttons below to manage your temporary voice room:\n\n"
                "• 🔒 **Lock** / 🔓 **Unlock**: Toggle public access\n"
                "• 🏷️ **Rename**: Change room title\n"
                "• 👥 **Limit**: Set maximum player capacity (0–99)\n"
                "• 👻 **Ghost (Hide)**: Make room invisible to everyone except friends\n"
                "• ✉️ **Permit**: Choose squadmates to reveal and invite into your room\n"
                "• 🚫 **Revoke**: Eject users and re-hide channel\n"
                "• 👢 **Kick**: Instantly disconnect someone from your room\n"
                "• 👑 **Transfer Host**: Pass room ownership to a squadmate\n"
                "• 💬 **Status**: Set customized activity text\n\n"
                "*Note: You must be inside your voice channel to use these controls.*"
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="RAI VIBES 💗 • Dynamic Voice Hub", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, view=VoiceControlView())

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild = member.guild

        # 1. Member joined/rejoined an existing temporary voice room that was counting down to auto-delete
        if after.channel and self.is_temporary_channel(after.channel):
            if after.channel.id in self.deletion_tasks:
                task = self.deletion_tasks.pop(after.channel.id)
                task.cancel()
                logger.info(f"Cancelled auto-deletion for '{after.channel.name}' because {member.display_name} joined.")
                try:
                    embed = discord.Embed(
                        title="✨ Voice Room Active",
                        description=f"Welcome back, {member.mention}! Scheduled room auto-deletion has been cancelled.",
                        color=discord.Color.green()
                    )
                    await after.channel.send(embed=embed, delete_after=10)
                except Exception:
                    pass

        # 2. User Joined a "Join to Create" / Chamber generator channel
        if after.channel:
            norm_name = unicodedata.normalize('NFKD', after.channel.name).lower()
            if "join to create" in norm_name or "create" in norm_name or "➕" in after.channel.name or "chamber" in norm_name:
                category = after.channel.category
                ch_name_lower = norm_name

                # Determine initial user limit based on chamber name
                initial_limit = 0
                if "solo" in ch_name_lower or "limit 1" in ch_name_lower:
                    initial_limit = 1
                    room_name = f"👤 {member.display_name}'s Solo"
                elif "duo" in ch_name_lower or "limit 2" in ch_name_lower:
                    initial_limit = 2
                    room_name = f"👥 {member.display_name}'s Duo"
                elif "trio" in ch_name_lower or "limit 3" in ch_name_lower:
                    initial_limit = 3
                    room_name = f"🔺 {member.display_name}'s Trio"
                elif "squad" in ch_name_lower or "limit 4" in ch_name_lower:
                    initial_limit = 4
                    room_name = f"🛡️ {member.display_name}'s Squad"
                elif "5-man" in ch_name_lower or "limit 5" in ch_name_lower:
                    initial_limit = 5
                    room_name = f"⭐ {member.display_name}'s 5-Man"
                elif "6-man" in ch_name_lower or "limit 6" in ch_name_lower:
                    initial_limit = 6
                    room_name = f"🌟 {member.display_name}'s 6-Man"
                else:
                    room_name = f"🎧 {member.display_name}'s Lounge"

                overwrites = {
                    guild.default_role: discord.PermissionOverwrite(connect=True, speak=True),
                    member: discord.PermissionOverwrite(connect=True, speak=True, mute_members=True, move_members=True, manage_channels=True)
                }

                try:
                    temp_vc = await guild.create_voice_channel(
                        name=room_name,
                        category=category,
                        user_limit=initial_limit,
                        bitrate=after.channel.bitrate,
                        overwrites=overwrites,
                        reason=f"Join-to-Create Voice Room for {member.name}"
                    )
                    self.temp_channels[temp_vc.id] = member.id
                    self._save_temp_channels()
                    await member.move_to(temp_vc)
                    logger.info(f"Created temporary voice room '{room_name}' (limit: {initial_limit}) for {member.name}")

                    # Send interactive control dashboard in text-in-voice
                    embed = discord.Embed(
                        title=f"🎛️ Voice Room Controls • {member.display_name}",
                        description=(
                            f"Welcome to your private voice channel, {member.mention}!\n\n"
                            f"Use the buttons below to customize and secure your room:\n"
                            f"• 🔒 **Lock / 🔓 Unlock**: Control who can enter\n"
                            f"• 🏷️ **Rename**: Customize room title\n"
                            f"• 👥 **Limit**: Set max member count\n"
                            f"• 👻 **Ghost (Hide)**: Hide room so only you & permitted friends can see it\n"
                            f"• ✉️ **Permit / Invite**: Pick members to reveal this hidden channel to\n"
                            f"• 🚫 **Revoke**: Remove access & hide room from members\n\n"
                            f"*This room will automatically delete after {self.INACTIVITY_GRACE_SECONDS} seconds of inactivity once everyone leaves.*"
                        ),
                        color=config.COLOR_PRIMARY
                    )
                    embed.set_footer(text="RAI VIBES 💗 • Dynamic Voice Hub", icon_url=config.RAI_ICON_URL)
                    
                    view = VoiceControlView()
                    await temp_vc.send(content=member.mention, embed=embed, view=view)

                except Exception as e:
                    logger.error(f"Failed to create temp voice channel: {e}")

        # 3. User Left a temporary voice channel -> Schedule auto-delete after inactivity grace period
        if before.channel and before.channel != after.channel and self.is_temporary_channel(before.channel):
            if len(before.channel.members) == 0:
                self.schedule_inactivity_deletion(before.channel, delay=self.INACTIVITY_GRACE_SECONDS)

async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceHub(bot))

