import discord
from discord.ext import commands
from discord import app_commands
import logging
import re
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

    @discord.ui.button(label="Permit / Invite", style=discord.ButtonStyle.primary, emoji="✉️", row=1, custom_id="vc_permit")
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


class VoiceHub(commands.Cog):
    """Dynamic Join-to-Create temporary private voice channels with interactive Ghost & Permission controls."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.temp_channels = {}  # channel_id: owner_id

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
        if before.channel and before.channel.id in self.temp_channels:
            if len(before.channel.members) == 0:
                del self.temp_channels[before.channel.id]
                try:
                    await before.channel.delete(reason="Temporary voice channel is empty.")
                    logger.info(f"Deleted empty temp voice channel '{before.channel.name}'")
                except Exception as e:
                    logger.error(f"Failed to delete temp channel: {e}")

    # Slash Commands for Voice Control
    @commands.hybrid_command(name="vlock", description="Lock your active voice channel so only permitted users can join.")
    async def vlock(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must be in your voice channel to use this command.", ephemeral=True)
        vc = ctx.author.voice.channel
        if vc.id not in self.temp_channels or self.temp_channels[vc.id] != ctx.author.id:
            return await ctx.send("❌ You can only lock voice channels you own.", ephemeral=True)
        
        await vc.set_permissions(ctx.guild.default_role, connect=False)
        await ctx.send("🔒 **Voice channel locked!**", ephemeral=True)

    @commands.hybrid_command(name="vunlock", description="Unlock your active voice channel so everyone can join.")
    async def vunlock(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must be in your voice channel to use this command.", ephemeral=True)
        vc = ctx.author.voice.channel
        if vc.id not in self.temp_channels or self.temp_channels[vc.id] != ctx.author.id:
            return await ctx.send("❌ You can only unlock voice channels you own.", ephemeral=True)
        
        await vc.set_permissions(ctx.guild.default_role, connect=None)
        await ctx.send("🔓 **Voice channel unlocked!**", ephemeral=True)

    @commands.hybrid_command(name="vghost", aliases=["vhide"], description="Ghost/hide your voice channel from everyone except invited members.")
    async def vghost(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must be in your voice channel to use this command.", ephemeral=True)
        vc = ctx.author.voice.channel
        if vc.id not in self.temp_channels or self.temp_channels[vc.id] != ctx.author.id:
            return await ctx.send("❌ You can only ghost voice channels you own.", ephemeral=True)

        current_perms = vc.overwrites_for(ctx.guild.default_role)
        is_hidden = current_perms.view_channel is False

        if is_hidden:
            await vc.set_permissions(ctx.guild.default_role, view_channel=None)
            await ctx.send("👁️ **Voice channel is now VISIBLE to everyone.**", ephemeral=True)
        else:
            await vc.set_permissions(ctx.guild.default_role, view_channel=False)
            await vc.set_permissions(ctx.author, view_channel=True, connect=True, speak=True)
            for m in vc.members:
                if not m.bot:
                    await vc.set_permissions(m, view_channel=True, connect=True, speak=True)
            await ctx.send("👻 **Voice channel is now GHOSTED (HIDDEN)!** Use `/vpermit @user` to invite friends.", ephemeral=True)

    @commands.hybrid_command(name="vpermit", aliases=["vinvite"], description="Reveal and grant access to your hidden voice channel for a specific member.")
    @app_commands.describe(member="The member to reveal and invite into your voice room")
    async def vpermit(self, ctx: commands.Context, member: discord.Member):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must be in your voice channel to use this command.", ephemeral=True)
        vc = ctx.author.voice.channel
        if vc.id not in self.temp_channels or self.temp_channels[vc.id] != ctx.author.id:
            return await ctx.send("❌ You can only permit members for voice channels you own.", ephemeral=True)

        await vc.set_permissions(member, view_channel=True, connect=True, speak=True)
        await ctx.send(f"✅ **Granted Access:** {member.mention} can now see and join `{vc.name}`!", ephemeral=True)

    @commands.hybrid_command(name="vrevoke", description="Revoke access and hide your voice channel from a specific member.")
    @app_commands.describe(member="The member to revoke access from")
    async def vrevoke(self, ctx: commands.Context, member: discord.Member):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must be in your voice channel to use this command.", ephemeral=True)
        vc = ctx.author.voice.channel
        if vc.id not in self.temp_channels or self.temp_channels[vc.id] != ctx.author.id:
            return await ctx.send("❌ You can only revoke access for voice channels you own.", ephemeral=True)

        await vc.set_permissions(member, overwrite=None)
        if member in vc.members:
            try:
                await member.move_to(None)
            except Exception:
                pass
        await ctx.send(f"🚫 **Access Revoked:** Hidden from {member.mention}.", ephemeral=True)

    @commands.hybrid_command(name="vkick", description="Disconnect a member from your active temporary voice channel.")
    @app_commands.describe(member="The member to kick from your room")
    async def vkick(self, ctx: commands.Context, member: discord.Member):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must be in your voice channel to use this command.", ephemeral=True)
        vc = ctx.author.voice.channel
        if vc.id not in self.temp_channels or self.temp_channels[vc.id] != ctx.author.id:
            return await ctx.send("❌ You can only kick members from voice channels you own.", ephemeral=True)

        if member in vc.members:
            await member.move_to(None)
            await ctx.send(f"👢 **Kicked {member.mention} from the voice channel.**", ephemeral=True)
        else:
            await ctx.send("❌ That member is not currently in your voice room.", ephemeral=True)

    @commands.hybrid_command(name="vname", description="Rename your active temporary voice channel.")
    @app_commands.describe(name="New name for your voice room")
    async def vname(self, ctx: commands.Context, name: str):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must be in your voice channel to use this command.", ephemeral=True)
        vc = ctx.author.voice.channel
        if vc.id not in self.temp_channels or self.temp_channels[vc.id] != ctx.author.id:
            return await ctx.send("❌ You can only rename voice channels you own.", ephemeral=True)
        
        await vc.edit(name=f"🎧 {name}")
        await ctx.send(f"✅ Voice channel renamed to `🎧 {name}`!", ephemeral=True)

    @commands.hybrid_command(name="vlimit", description="Set user limit for your voice room (0-99).")
    @app_commands.describe(limit="Max users (0 for unlimited)")
    async def vlimit(self, ctx: commands.Context, limit: int):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must be in your voice channel to use this command.", ephemeral=True)
        vc = ctx.author.voice.channel
        if vc.id not in self.temp_channels or self.temp_channels[vc.id] != ctx.author.id:
            return await ctx.send("❌ You can only adjust limit for channels you own.", ephemeral=True)
        
        if 0 <= limit <= 99:
            await vc.edit(user_limit=limit)
            await ctx.send(f"👥 Room limit updated to `{limit}`.", ephemeral=True)
        else:
            await ctx.send("❌ Limit must be between 0 and 99.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceHub(bot))
