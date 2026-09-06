import discord
from discord.ext import commands, tasks
from discord import app_commands
import logging
import re
import os
import json
from typing import Optional

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

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.temp_channels = {}  # channel_id: owner_id
        self.temp_db_path = os.path.join("data", "temp_vcs.json")
        self._load_temp_channels()
        self.cleanup_temp_channels_task.start()

    def cog_unload(self):
        self.cleanup_temp_channels_task.cancel()

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
        if channel.id in self.temp_channels:
            return True
        # Also check name patterns in case bot restarted
        name = channel.name
        if any(name.startswith(p) for p in self.TEMP_PREFIXES) and any(name.endswith(s) for s in self.TEMP_SUFFIXES):
            return True
        return False

    @tasks.loop(seconds=30)
    async def cleanup_temp_channels_task(self):
        """Periodically scans for and deletes any empty temporary voice channels."""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            for channel in guild.voice_channels:
                if self.is_temporary_channel(channel) and len(channel.members) == 0:
                    try:
                        if channel.id in self.temp_channels:
                            del self.temp_channels[channel.id]
                            self._save_temp_channels()
                        await channel.delete(reason="Periodic cleanup: temporary voice room was empty.")
                        logger.info(f"Swept & deleted empty temp voice channel '{channel.name}' in {guild.name}")
                    except Exception as e:
                        logger.debug(f"Failed to delete channel {channel.name}: {e}")

    @cleanup_temp_channels_task.before_loop
    async def before_cleanup_task(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild = member.guild

        # 1. User Joined a "Join to Create" / Chamber generator channel
        if after.channel and ("join to create" in after.channel.name.lower() or "➕" in after.channel.name or "chamber" in after.channel.name.lower()):
            category = after.channel.category
            ch_name_lower = after.channel.name.lower()

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
                        f"*This room will automatically delete when everyone leaves.*"
                    ),
                    color=config.COLOR_PRIMARY
                )
                embed.set_footer(text="RAI VIBES 💗 • Dynamic Voice Hub", icon_url=config.RAI_ICON_URL)
                
                view = VoiceControlView()
                await temp_vc.send(content=member.mention, embed=embed, view=view)

            except Exception as e:
                logger.error(f"Failed to create temp voice channel: {e}")

        # 2. User Left a temporary voice channel -> Delete if empty
        if before.channel and self.is_temporary_channel(before.channel):
            if len(before.channel.members) == 0:
                if before.channel.id in self.temp_channels:
                    del self.temp_channels[before.channel.id]
                    self._save_temp_channels()
                try:
                    await before.channel.delete(reason="Temporary voice channel is empty.")
                    logger.info(f"Deleted empty temp voice channel '{before.channel.name}'")
                except Exception as e:
                    logger.error(f"Failed to delete temp channel: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceHub(bot))

