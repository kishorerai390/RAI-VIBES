import sys
from pathlib import Path
import discord
from discord.ui import View, button, Button

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import config

class MusicPlayerView(View):
    """Interactive Discord UI button controls for RAI VIBES 💗 Music Player."""
    def __init__(self, music_cog, guild_id: int):
        super().__init__(timeout=None)
        self.music_cog = music_cog
        self.guild_id = guild_id

    async def get_player(self, interaction: discord.Interaction):
        player = self.music_cog.get_player(self.guild_id)
        if not player or not player.is_connected:
            await interaction.response.send_message(
                "❌ **RAI VIBES 💗 is not currently active in a voice channel.**",
                ephemeral=True
            )
            return None
        if interaction.user not in player.voice_client.channel.members:
            await interaction.response.send_message(
                "⚡ **You must be in the same voice channel to control RAI VIBES 💗.**",
                ephemeral=True
            )
            return None
        return player

    @button(label="Pause / Resume", style=discord.ButtonStyle.primary, emoji="⏯️", row=0)
    async def pause_resume_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        if player.voice_client.is_paused():
            player.voice_client.resume()
            await interaction.response.send_message("▶️ **Resumed playback!**", ephemeral=True)
        elif player.voice_client.is_playing():
            player.voice_client.pause()
            await interaction.response.send_message("⏸️ **Paused playback!**", ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ No audio is currently streaming.", ephemeral=True)

    @button(label="Skip", style=discord.ButtonStyle.secondary, emoji="⏭️", row=0)
    async def skip_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        if player.voice_client.is_playing() or player.voice_client.is_paused():
            current_title = player.current.title if player.current else "Track"
            player.skip()
            await interaction.response.send_message(f"⏭️ **Skipped:** `{current_title}`", ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ Nothing is playing to skip.", ephemeral=True)

    @button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️", row=0)
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        await player.stop()
        await interaction.response.send_message("⏹️ **RAI VIBES 💗 stopped and cleared the queue.**", ephemeral=True)

    @button(label="Loop", style=discord.ButtonStyle.secondary, emoji="🔁", row=0)
    async def loop_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        # Toggle: off -> track -> queue -> off
        if player.loop_mode == "off":
            player.loop_mode = "track"
            mode_text = "🔂 **Loop Mode: Track Repeat**"
        elif player.loop_mode == "track":
            player.loop_mode = "queue"
            mode_text = "🔁 **Loop Mode: Queue Repeat**"
        else:
            player.loop_mode = "off"
            mode_text = "➡️ **Loop Mode: Disabled (Off)**"

        await interaction.response.send_message(mode_text, ephemeral=True)

    @button(label="Shuffle", style=discord.ButtonStyle.secondary, emoji="🔀", row=1)
    async def shuffle_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        if len(player.queue) < 2:
            await interaction.response.send_message("ℹ️ Queue needs at least 2 songs to shuffle.", ephemeral=True)
            return

        player.shuffle()
        await interaction.response.send_message("🔀 **RAI VIBES 💗 queue shuffled!**", ephemeral=True)

    @button(label="Queue", style=discord.ButtonStyle.primary, emoji="📜", row=1)
    async def queue_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        embed = player.build_queue_embed(page=0)
        view = QueuePaginationView(player)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @button(label="Vol -10%", style=discord.ButtonStyle.secondary, emoji="🔉", row=1)
    async def vol_down_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        new_vol = max(0, player.volume - 10)
        player.set_volume(new_vol)
        await interaction.response.send_message(f"🔉 **Volume set to {new_vol}%**", ephemeral=True)

    @button(label="Vol +10%", style=discord.ButtonStyle.secondary, emoji="🔊", row=1)
    async def vol_up_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        new_vol = min(200, player.volume + 10)
        player.set_volume(new_vol)
        boost = " 🔥 *(Super Boost)*" if new_vol > 100 else ""
        await interaction.response.send_message(f"🔊 **Volume set to {new_vol}%**{boost}", ephemeral=True)


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
