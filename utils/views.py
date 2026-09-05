import sys
from pathlib import Path
from typing import Optional
import discord
from discord.ui import View, button, Button

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

class MusicPlayerView(View):
    """Interactive Persistent Discord UI button controls for RAI VIBES 💗 Music Player."""
    def __init__(self, music_cog=None, guild_id: Optional[int] = None):
        super().__init__(timeout=None)
        self.music_cog = music_cog
        self.guild_id = guild_id

    async def get_player(self, interaction: discord.Interaction):
        cog = self.music_cog or interaction.client.get_cog("Music")
        guild_id = self.guild_id or (interaction.guild.id if interaction.guild else None)
        if not cog or not guild_id:
            return None
        
        player = cog.get_player(guild_id)
        if not player or not player.is_connected or not interaction.guild.voice_client:
            await interaction.response.send_message(
                "⚡ **RAI VIBES 💗 is currently inactive.** Start playback anytime using `/play <song>` or `!play <song>`!",
                ephemeral=True
            )
            return None
        if not interaction.guild.voice_client.channel:
            return None
        if interaction.user not in interaction.guild.voice_client.channel.members:
            await interaction.response.send_message(
                f"⚡ **You must join {interaction.guild.voice_client.channel.mention} to control RAI VIBES 💗.**",
                ephemeral=True
            )
            return None
        return player

    @button(label="Pause", style=discord.ButtonStyle.success, emoji="⏯️", row=0, custom_id="music_btn_pause")
    async def pause_resume_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            return await interaction.response.send_message("❌ **RAI VIBES 💗 is not connected to a voice channel.**", ephemeral=True)

        if vc.is_paused():
            player.resume()
            button.label = "Pause"
            button.style = discord.ButtonStyle.success
            await interaction.response.send_message("▶️ **Resumed playback!**", ephemeral=True)
        elif vc.is_playing():
            player.pause(interaction.user)
            button.label = "Resume"
            button.style = discord.ButtonStyle.primary
            await interaction.response.send_message("⏸️ **Paused playback!**", ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ No audio is currently streaming.", ephemeral=True)

        if player.now_playing_message:
            try:
                await player.now_playing_message.edit(embed=player.build_now_playing_embed(), view=self)
            except Exception:
                pass

    @button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️", row=0, custom_id="music_btn_skip")
    async def skip_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        vc = interaction.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            current_title = player.current.title if player.current else "Track"
            vc.stop()
            await interaction.response.send_message(f"⏭️ **Skipped:** `{current_title}`", ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ Nothing is playing to skip.", ephemeral=True)

    @button(label="Loop", style=discord.ButtonStyle.secondary, emoji="🔁", row=0, custom_id="music_btn_loop")
    async def loop_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        if player.loop_mode == "off":
            player.loop_mode = "track"
            button.style = discord.ButtonStyle.primary
            mode_text = "🔂 **Loop Mode: Track Repeat**"
        elif player.loop_mode == "track":
            player.loop_mode = "queue"
            button.style = discord.ButtonStyle.primary
            mode_text = "🔁 **Loop Mode: Queue Repeat**"
        else:
            player.loop_mode = "off"
            button.style = discord.ButtonStyle.secondary
            mode_text = "➡️ **Loop Mode: Disabled (Off)**"

        await interaction.response.send_message(mode_text, ephemeral=True)
        if player.now_playing_message:
            try:
                await player.now_playing_message.edit(embed=player.build_now_playing_embed(), view=self)
            except Exception:
                pass

    @button(label="Shuffle", style=discord.ButtonStyle.secondary, emoji="🔀", row=0, custom_id="music_btn_shuffle")
    async def shuffle_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        if len(player.queue) < 2:
            await interaction.response.send_message("ℹ️ Queue needs at least 2 songs to shuffle.", ephemeral=True)
            return

        player.shuffle()
        await interaction.response.send_message("🔀 **Queue shuffled successfully!**", ephemeral=True)

    @button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️", row=0, custom_id="music_btn_stop")
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        await player.stop()
        await interaction.response.send_message("⏹️ **Playback stopped & queue cleared.**", ephemeral=True)

    @button(label="Vol -", style=discord.ButtonStyle.secondary, emoji="🔉", row=1, custom_id="music_btn_voldown")
    async def vol_down_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        new_vol = max(0, player.volume - 10)
        player.set_volume(new_vol)
        await interaction.response.send_message(f"🔉 **Volume:** `{new_vol}%`", ephemeral=True)
        if player.now_playing_message:
            try:
                await player.now_playing_message.edit(embed=player.build_now_playing_embed(), view=self)
            except Exception:
                pass

    @button(label="Vol +", style=discord.ButtonStyle.secondary, emoji="🔊", row=1, custom_id="music_btn_volup")
    async def vol_up_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        new_vol = min(200, player.volume + 10)
        player.set_volume(new_vol)
        boost = " 🔥 *(Boost)*" if new_vol > 100 else ""
        await interaction.response.send_message(f"🔊 **Volume:** `{new_vol}%`{boost}", ephemeral=True)
        if player.now_playing_message:
            try:
                await player.now_playing_message.edit(embed=player.build_now_playing_embed(), view=self)
            except Exception:
                pass

    @button(label="Queue", style=discord.ButtonStyle.primary, emoji="📜", row=1, custom_id="music_btn_queue")
    async def queue_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        embed = player.build_queue_embed(page=0)
        view = QueuePaginationView(player)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @button(label="Bass", style=discord.ButtonStyle.secondary, emoji="🎛️", row=1, custom_id="music_btn_bass")
    async def bass_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        if "bassboost" in player.active_filters:
            player.active_filters.remove("bassboost")
            button.style = discord.ButtonStyle.secondary
            state_msg = "Disabled (Flat EQ)"
        else:
            player.active_filters.append("bassboost")
            button.style = discord.ButtonStyle.success
            state_msg = "Enabled 🔥 (Heavy Bass)"

        await interaction.response.send_message(f"🎛️ **Bass Boost:** `{state_msg}`", ephemeral=True)
        await player.restart_current_with_filters()
        if player.now_playing_message:
            try:
                await player.now_playing_message.edit(embed=player.build_now_playing_embed(), view=self)
            except Exception:
                pass

    @button(label="Lyrics", style=discord.ButtonStyle.secondary, emoji="🎤", row=1, custom_id="music_btn_lyrics")
    async def lyrics_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player or not player.current:
            return await interaction.response.send_message("❌ No song currently playing to fetch lyrics for.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        lyrics_cog = interaction.client.get_cog("Lyrics")
        lyrics_data = await lyrics_cog.fetch_lyrics(player.current.title) if lyrics_cog else None

        if not lyrics_data or "lyrics" not in lyrics_data:
            return await interaction.followup.send(f"⚠️ Could not find synchronized lyrics for `{player.current.title[:50]}`.", ephemeral=True)

        lyrics_text = lyrics_data.get("lyrics", "")
        if len(lyrics_text) > 4000:
            lyrics_text = lyrics_text[:3990] + "...\n*(Lyrics truncated)*"

        embed = discord.Embed(
            title=f"🎤 Lyrics: {lyrics_data.get('title', player.current.title)}",
            description=f"```fix\n{lyrics_text}\n```" if len(lyrics_text) < 1800 else lyrics_text,
            color=config.COLOR_PRIMARY
        )
        embed.set_author(name=lyrics_data.get("author", "RAI VIBES 💗 Lyrics Engine"), icon_url=config.RAI_ICON_URL)
        if lyrics_data.get("thumbnail", {}).get("genius"):
            embed.set_thumbnail(url=lyrics_data["thumbnail"]["genius"])
        embed.set_footer(text="RAI VIBES 💗 • Lyrics Dashboard", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)


class QueuePaginationView(View):
    """Pagination buttons for viewing large song queues."""
    def __init__(self, player, current_page: int = 0):
        super().__init__(timeout=60)
        self.player = player
        self.current_page = current_page
        self.update_buttons()

    def update_buttons(self):
        total_pages = max(1, (len(self.player.queue) + 9) // 10)
        self.prev_button.disabled = self.current_page <= 0
        self.next_button.disabled = self.current_page >= total_pages - 1

    @button(label="Previous", style=discord.ButtonStyle.secondary, emoji="⬅️")
    async def prev_button(self, interaction: discord.Interaction, button: Button):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_buttons()
            embed = self.player.build_queue_embed(self.current_page)
            await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Next", style=discord.ButtonStyle.secondary, emoji="➡️")
    async def next_button(self, interaction: discord.Interaction, button: Button):
        total_pages = max(1, (len(self.player.queue) + 9) // 10)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            embed = self.player.build_queue_embed(self.current_page)
            await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Clear Queue", style=discord.ButtonStyle.danger, emoji="🗑️")
    async def clear_button(self, interaction: discord.Interaction, button: Button):
        if interaction.user not in self.player.voice_client.channel.members:
            await interaction.response.send_message("❌ You must be in the voice channel to clear the queue.", ephemeral=True)
            return

        self.player.queue.clear()
        embed = self.player.build_queue_embed(0)
        self.update_buttons()
        await interaction.response.edit_message(embed=embed, view=self)
