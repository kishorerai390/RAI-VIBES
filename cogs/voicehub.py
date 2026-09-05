import discord
from discord.ext import commands
from discord import app_commands
import logging
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


class VoiceControlView(discord.ui.View):
    """Persistent 24/7 Voice Room Controls for Dynamic Voice Hub."""
    def __init__(self):
        super().__init__(timeout=None)

    def get_user_vc(self, interaction: discord.Interaction) -> Optional[discord.VoiceChannel]:
        return getattr(getattr(interaction.user, "voice", None), "channel", None)

    @discord.ui.button(label="Lock", style=discord.ButtonStyle.danger, emoji="🔒", custom_id="vc_lock")
    async def lock(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to lock it.", ephemeral=True)
        await vc.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.response.send_message("🔒 **Room Locked!** Only users you permit can join.", ephemeral=True)

    @discord.ui.button(label="Unlock", style=discord.ButtonStyle.success, emoji="🔓", custom_id="vc_unlock")
    async def unlock(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to unlock it.", ephemeral=True)
        await vc.set_permissions(interaction.guild.default_role, connect=None)
        await interaction.response.send_message("🔓 **Room Unlocked!** Everyone can join.", ephemeral=True)

    @discord.ui.button(label="Rename", style=discord.ButtonStyle.primary, emoji="🏷️", custom_id="vc_rename")
    async def rename(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to rename it.", ephemeral=True)
        await interaction.response.send_modal(RenameVoiceModal())

    @discord.ui.button(label="Limit", style=discord.ButtonStyle.secondary, emoji="👥", custom_id="vc_limit")
    async def limit(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to change limits.", ephemeral=True)
        await interaction.response.send_modal(LimitVoiceModal())

    @discord.ui.button(label="Ghost (Hide)", style=discord.ButtonStyle.secondary, emoji="👻", custom_id="vc_ghost")
    async def ghost(self, interaction: discord.Interaction, button: discord.ui.Button):
        vc = self.get_user_vc(interaction)
        if not vc:
            return await interaction.response.send_message("❌ You must be inside your voice channel to ghost it.", ephemeral=True)
        current_perms = vc.overwrites_for(interaction.guild.default_role)
        is_hidden = current_perms.view_channel is False
        new_state = None if is_hidden else False
        await vc.set_permissions(interaction.guild.default_role, view_channel=new_state)
        status = "Visible to everyone" if is_hidden else "Hidden / Ghosted"
        await interaction.response.send_message(f"👻 Voice room is now **{status}**!", ephemeral=True)


class VoiceHub(commands.Cog):
    """Dynamic Join-to-Create temporary private voice channels with interactive controls."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.temp_channels = {}  # channel_id: owner_id

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        guild = member.guild

        # 1. User Joined the "Join to Create" channel
        if after.channel and ("join to create" in after.channel.name.lower() or "➕" in after.channel.name):
            category = after.channel.category
            room_name = f"🎧 {member.display_name}'s Lounge"
            
            overwrites = {
                guild.default_role: discord.PermissionOverwrite(connect=True, speak=True),
                member: discord.PermissionOverwrite(connect=True, speak=True, mute_members=True, move_members=True, manage_channels=True)
            }

            try:
                temp_vc = await guild.create_voice_channel(
                    name=room_name,
                    category=category,
                    bitrate=after.channel.bitrate,
                    overwrites=overwrites,
                    reason=f"Join-to-Create Voice Room for {member.name}"
                )
                self.temp_channels[temp_vc.id] = member.id
                await member.move_to(temp_vc)
                logger.info(f"Created temporary voice room '{room_name}' for {member.name}")

                # Send interactive control dashboard in text-in-voice
                embed = discord.Embed(
                    title=f"🎛️ Voice Room Controls • {member.display_name}",
                    description=(
                        f"Welcome to your private voice channel, {member.mention}!\n\n"
                        f"Use the buttons below to customize and secure your room:\n"
                        f"• 🔒 **Lock / 🔓 Unlock**: Control who can enter\n"
                        f"• 🏷️ **Rename**: Customize room title\n"
                        f"• 👥 **Limit**: Set max member count\n"
                        f"• 👻 **Ghost**: Hide room from other members\n\n"
                        f"*This room will automatically delete when everyone leaves.*"
                    ),
                    color=config.COLOR_PRIMARY
                )
                embed.set_footer(text="Apex Voice Hub • Instant Controls", icon_url=config.RAI_ICON_URL)
                
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
    @commands.hybrid_command(name="vlock", description="Lock your active temporary voice channel.")
    async def vlock(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must be in your voice channel to use this command.", ephemeral=True)
        vc = ctx.author.voice.channel
        if vc.id not in self.temp_channels or self.temp_channels[vc.id] != ctx.author.id:
            return await ctx.send("❌ You can only lock voice channels you own.", ephemeral=True)
        
        await vc.set_permissions(ctx.guild.default_role, connect=False)
        await ctx.send("🔒 Voice channel locked!", ephemeral=True)

    @commands.hybrid_command(name="vunlock", description="Unlock your active temporary voice channel.")
    async def vunlock(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must be in your voice channel to use this command.", ephemeral=True)
        vc = ctx.author.voice.channel
        if vc.id not in self.temp_channels or self.temp_channels[vc.id] != ctx.author.id:
            return await ctx.send("❌ You can only unlock voice channels you own.", ephemeral=True)
        
        await vc.set_permissions(ctx.guild.default_role, connect=None)
        await ctx.send("🔓 Voice channel unlocked!", ephemeral=True)

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
