import sys
import time
from pathlib import Path
from typing import Optional
import discord
from discord.ui import View, button, Button, Modal, TextInput, Select

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

    async def send_msg(self, interaction: discord.Interaction, text: str = None, embed: discord.Embed = None, view: View = None):
        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(content=text, embed=embed, view=view, ephemeral=True)
            else:
                await interaction.followup.send(content=text, embed=embed, view=view, ephemeral=True)
        except Exception:
            pass

    async def get_player(self, interaction: discord.Interaction):
        cog = self.music_cog or interaction.client.get_cog("Music")
        if not interaction.guild:
            await self.send_msg(interaction, "❌ This button can only be used in a server.")
            return None

        if not cog:
            await self.send_msg(interaction, "❌ Music module is currently initializing.")
            return None

        player = cog.get_or_create_player(interaction.guild)
        
        # If bot is not in voice, attempt auto-connection if user is in a voice channel
        vc = interaction.guild.voice_client
        if (not vc or not vc.is_connected()) and getattr(getattr(interaction.user, "voice", None), "channel", None):
            try:
                vc = await cog.ensure_voice(interaction)
            except Exception:
                vc = interaction.guild.voice_client

        player.voice_client = vc
        if interaction.channel:
            player.text_channel = interaction.channel

        return player

    @button(label="Pause", style=discord.ButtonStyle.success, emoji="⏯️", row=0, custom_id="music_btn_pause")
    async def pause_resume_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        vc = interaction.guild.voice_client
        if not vc or not vc.is_connected():
            # If user in voice, auto-connect
            if getattr(getattr(interaction.user, "voice", None), "channel", None):
                cog = self.music_cog or interaction.client.get_cog("Music")
                vc = await cog.ensure_voice(interaction)
                player.voice_client = vc

        if not vc or not vc.is_connected():
            return await self.send_msg(interaction, "⚡ Please join a voice channel and use `/play <song>` to start music!")

        if vc.is_paused():
            player.resume()
            button.label = "Pause"
            button.style = discord.ButtonStyle.success
            await self.send_msg(interaction, "▶️ **Resumed playback!**")
        elif vc.is_playing():
            player.pause(interaction.user)
            button.label = "Resume"
            button.style = discord.ButtonStyle.primary
            await self.send_msg(interaction, "⏸️ **Paused playback!**")
        elif player.current or player.queue:
            player.play_next_song.set()
            await self.send_msg(interaction, "▶️ **Starting audio queue...**")
        else:
            await self.send_msg(interaction, "ℹ️ No audio is currently streaming. Add tracks with `/play <song>`!")

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
            await self.send_msg(interaction, f"⏭️ **Skipped:** `{current_title}`")
        elif player.queue:
            player.play_next_song.set()
            await self.send_msg(interaction, "⏭️ **Skipped to next queued track!**")
        else:
            await self.send_msg(interaction, "ℹ️ Queue is empty. Use `/play <song>` to add tracks!")

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

        await self.send_msg(interaction, mode_text)
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
            return await self.send_msg(interaction, "ℹ️ Queue needs at least 2 songs to shuffle.")

        player.shuffle()
        await self.send_msg(interaction, "🔀 **Queue shuffled successfully!**")

    @button(label="Stop", style=discord.ButtonStyle.danger, emoji="⏹️", row=0, custom_id="music_btn_stop")
    async def stop_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        await player.stop()
        await self.send_msg(interaction, "⏹️ **Playback stopped & queue cleared.**")

    @button(label="Vol -", style=discord.ButtonStyle.secondary, emoji="🔉", row=1, custom_id="music_btn_voldown")
    async def vol_down_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        new_vol = max(0, player.volume - 10)
        player.set_volume(new_vol)
        await self.send_msg(interaction, f"🔉 **Volume:** `{new_vol}%`")
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
        await self.send_msg(interaction, f"🔊 **Volume:** `{new_vol}%`{boost}")
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
        await self.send_msg(interaction, embed=embed, view=view)

    @button(label="Fav", style=discord.ButtonStyle.secondary, emoji="💖", row=1, custom_id="music_btn_fav")
    async def fav_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player or not player.current:
            return await self.send_msg(interaction, "❌ No song is currently playing to add to favorites.")

        fav_cog = interaction.client.get_cog("Favorites")
        if not fav_cog:
            return await self.send_msg(interaction, "❌ Favorites module is unavailable.")

        from cogs.favorites import load_favorites, save_favorites
        user_id = str(interaction.user.id)
        data = load_favorites()
        if user_id not in data:
            data[user_id] = []

        if any(item.get("title") == player.current.title for item in data[user_id]):
            return await self.send_msg(interaction, f"⚠️ `{player.current.title}` is already in your favorites!")

        data[user_id].append({
            "title": player.current.title,
            "url": player.current.webpage_url,
            "duration": player.current.duration,
            "thumbnail": player.current.thumbnail,
            "artist": player.current.data.get("uploader", "Unknown")
        })
        save_favorites(data)
        await self.send_msg(interaction, f"💖 **Added to Favorites:** `{player.current.title}`\nPlay anytime with `/favorite play`!")

    @button(label="Lyrics", style=discord.ButtonStyle.secondary, emoji="🎤", row=1, custom_id="music_btn_lyrics")
    async def lyrics_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return

        target_title = None
        if player.current:
            target_title = player.current.title
        elif player.history:
            target_title = player.history[-1].title

        if not target_title:
            return await self.send_msg(interaction, "❌ No song is currently playing. Search lyrics with `/lyrics <song>`!")

        lyrics_cog = interaction.client.get_cog("Lyrics")
        lyrics_data = await lyrics_cog.fetch_lyrics(target_title) if lyrics_cog else None

        if not lyrics_data or "lyrics" not in lyrics_data:
            return await self.send_msg(interaction, f"⚠️ Could not find lyrics for `{target_title[:50]}`.")

        try:
            lyrics_text = lyrics_data.get("lyrics", "")
            if len(lyrics_text) > 4000:
                lyrics_text = lyrics_text[:3990] + "...\n*(Lyrics truncated)*"

            embed = discord.Embed(
                title=f"🎤 Lyrics: {lyrics_data.get('title', target_title)}",
                description=f"```fix\n{lyrics_text}\n```" if len(lyrics_text) < 1800 else lyrics_text,
                color=config.COLOR_PRIMARY
            )
            embed.set_author(name=lyrics_data.get("author", "RAI VIBES 💗 Lyrics Engine"), icon_url=config.RAI_ICON_URL)
            
            thumb = lyrics_data.get("thumbnail")
            if isinstance(thumb, str) and thumb.startswith("http"):
                embed.set_thumbnail(url=thumb)
            elif isinstance(thumb, dict) and thumb.get("genius"):
                embed.set_thumbnail(url=thumb["genius"])
            elif player.current and player.current.thumbnail:
                embed.set_thumbnail(url=player.current.thumbnail)

            embed.set_footer(text=f"RAI VIBES 💗 • Source: {lyrics_data.get('source', 'Synced Lyrics')}", icon_url=config.RAI_ICON_URL)
            await self.send_msg(interaction, embed=embed)
        except Exception as e:
            await self.send_msg(interaction, f"❌ Error displaying lyrics: {e}")

    async def toggle_filter(self, interaction: discord.Interaction, filter_name: str, display_name: str):
        player = await self.get_player(interaction)
        if not player:
            return await self.send_msg(interaction, "❌ Music player is not active.")

        # If current track is missing but voice client is actively playing (e.g. 24/7 radio stream)
        if not player.current and player.voice_client and player.voice_client.is_playing():
            radio_cog = interaction.client.get_cog("Radio")
            st_key = getattr(radio_cog, "_last_streamed_station", "lofi") if radio_cog else "lofi"
            try:
                from cogs.radio import RADIO_STATIONS
                from cogs.music import Song
                st_data = RADIO_STATIONS.get(st_key, RADIO_STATIONS["lofi"])
                player.current = Song(
                    data={
                        "title": f"📻 {st_data['name']}",
                        "url": st_data["url"],
                        "webpage_url": st_data["url"],
                        "duration": 0,
                        "thumbnail": st_data["thumb"],
                        "uploader": "24/7 Continuous Music Engine"
                    },
                    requester=interaction.guild.me,
                    source_type="radio"
                )
            except Exception:
                pass

        if not player.current:
            return await self.send_msg(interaction, "❌ No track is currently streaming. Use `/play <song>` to start music first!")

        if filter_name in player.active_filters:
            player.active_filters.remove(filter_name)
            await player.restart_current_with_filters()
            await self.send_msg(interaction, f"➡️ **Audio filter disabled:** `{display_name}`")
        else:
            if filter_name.startswith("bassboost_"):
                player.active_filters = [f for f in player.active_filters if not f.startswith("bassboost_")]
            player.active_filters.append(filter_name)
            await player.restart_current_with_filters()
            await self.send_msg(interaction, f"⚡ **Audio filter activated:** `{display_name}`!")

        if player.now_playing_message:
            try:
                await player.now_playing_message.edit(embed=player.build_now_playing_embed(), view=self)
            except Exception:
                pass

    @button(label="Nightcore", style=discord.ButtonStyle.secondary, emoji="⚡", row=2, custom_id="music_btn_nc")
    async def nightcore_button(self, interaction: discord.Interaction, button: Button):
        await self.toggle_filter(interaction, "nightcore", "Nightcore")

    @button(label="Bass Boost", style=discord.ButtonStyle.secondary, emoji="🔊", row=2, custom_id="music_btn_bb")
    async def bass_button(self, interaction: discord.Interaction, button: Button):
        await self.toggle_filter(interaction, "bassboost_medium", "Bass Boost [Medium]")

    @button(label="8D Audio", style=discord.ButtonStyle.secondary, emoji="🌌", row=2, custom_id="music_btn_8d")
    async def spatial_button(self, interaction: discord.Interaction, button: Button):
        await self.toggle_filter(interaction, "8d", "8D Spatial 360")

    @button(label="Lo-Fi Chill", style=discord.ButtonStyle.secondary, emoji="☕", row=2, custom_id="music_btn_slow")
    async def lofi_button(self, interaction: discord.Interaction, button: Button):
        await self.toggle_filter(interaction, "slowed", "Lo-Fi Slowed + Reverb")

    @button(label="More FX", style=discord.ButtonStyle.primary, emoji="🎛️", row=2, custom_id="music_btn_fx")
    async def fx_menu_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player or not player.current:
            return await self.send_msg(interaction, "❌ No song is currently streaming.")
        view = AudioEffectsControlView(player, self)
        await self.send_msg(interaction, "🎛️ **Audio Studio & FX Console** — Select an enhancement below:", view=view)

    @button(label="Controller Remote", style=discord.ButtonStyle.secondary, emoji="📱", row=3, custom_id="music_btn_remote")
    async def remote_button(self, interaction: discord.Interaction, button: Button):
        player = await self.get_player(interaction)
        if not player:
            return
        view = RythmControllerView(player, self.music_cog or interaction.client.get_cog("Music"))
        await interaction.response.send_message(content=view.build_content(), view=view, ephemeral=True)


class AudioEffectsControlView(View):
    """Interactive popup to manage advanced audio effects and speed."""
    def __init__(self, player, parent_view):
        super().__init__(timeout=60)
        self.player = player
        self.parent_view = parent_view

    @button(label="Karaoke (Vocal Cut)", style=discord.ButtonStyle.secondary, emoji="🎤", row=0)
    async def karaoke_btn(self, interaction: discord.Interaction, button: Button):
        await self.parent_view.toggle_filter(interaction, "karaoke", "Karaoke (Vocal Cut)")

    @button(label="Vaporwave", style=discord.ButtonStyle.secondary, emoji="📼", row=0)
    async def vaporwave_btn(self, interaction: discord.Interaction, button: Button):
        await self.parent_view.toggle_filter(interaction, "vaporwave", "Vaporwave Retro")

    @button(label="Speed 1.25x", style=discord.ButtonStyle.secondary, emoji="⏩", row=0)
    async def speed_fast_btn(self, interaction: discord.Interaction, button: Button):
        self.player.custom_speed = 1.25 if self.player.custom_speed != 1.25 else 1.0
        await self.player.restart_current_with_filters()
        await interaction.response.send_message(f"⏩ **Playback Speed:** `{self.player.custom_speed}x`", ephemeral=True)

    @button(label="Speed 0.85x", style=discord.ButtonStyle.secondary, emoji="⏪", row=1)
    async def speed_slow_btn(self, interaction: discord.Interaction, button: Button):
        self.player.custom_speed = 0.85 if self.player.custom_speed != 0.85 else 1.0
        await self.player.restart_current_with_filters()
        await interaction.response.send_message(f"⏪ **Playback Speed:** `{self.player.custom_speed}x`", ephemeral=True)

    @button(label="Reset All Audio FX", style=discord.ButtonStyle.danger, emoji="🔄", row=1)
    async def reset_fx_btn(self, interaction: discord.Interaction, button: Button):
        self.player.active_filters.clear()
        self.player.custom_speed = 1.0
        await self.player.restart_current_with_filters()
        await interaction.response.send_message("✨ **All audio filters reset to Natural Sound!**", ephemeral=True)
        if self.player.now_playing_message:
            try:
                await self.player.now_playing_message.edit(embed=self.player.build_now_playing_embed(), view=self.parent_view)
            except Exception:
                pass


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
            try:
                await interaction.response.edit_message(embed=embed, view=self)
            except Exception:
                pass

    @button(label="Next", style=discord.ButtonStyle.secondary, emoji="➡️")
    async def next_button(self, interaction: discord.Interaction, button: Button):
        total_pages = max(1, (len(self.player.queue) + 9) // 10)
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_buttons()
            embed = self.player.build_queue_embed(self.current_page)
            try:
                await interaction.response.edit_message(embed=embed, view=self)
            except Exception:
                pass


class AddSongModal(Modal, title="Add Song to Queue"):
    song_query = TextInput(
        label="Song Title, Artist, YouTube or Spotify URL",
        placeholder="e.g. Kannitheevu Ponna, Shape of You, or Spotify link...",
        required=True,
        max_length=400
    )

    def __init__(self, player, music_cog):
        super().__init__()
        self.player = player
        self.music_cog = music_cog

    async def on_submit(self, interaction: discord.Interaction):
        query = self.song_query.value.strip()
        await interaction.response.defer(ephemeral=True)
        try:
            from cogs.music import Song
            song_obj = await Song.create_source(query, interaction.user, self.music_cog.bot.loop)
            if song_obj:
                is_queued = self.player.enqueue_track(song_obj)
                desc = f"📥 **Added to queue:** [{song_obj.title}]({song_obj.webpage_url})" if is_queued else f"🎶 **Now streaming:** [{song_obj.title}]({song_obj.webpage_url})"
                await interaction.followup.send(embed=discord.Embed(description=desc, color=config.COLOR_PRIMARY), ephemeral=True)
            else:
                await interaction.followup.send("❌ Could not find or load that track.", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Error adding track: {e}", ephemeral=True)


class SearchSongModal(Modal, title="Search Music"):
    keywords = TextInput(
        label="Search Keywords",
        placeholder="Enter song title or artist name...",
        required=True,
        max_length=200
    )

    def __init__(self, player, music_cog):
        super().__init__()
        self.player = player
        self.music_cog = music_cog

    async def on_submit(self, interaction: discord.Interaction):
        query = self.keywords.value.strip()
        await interaction.response.defer(ephemeral=True)
        import yt_dlp
        ydl_opts = {
            "format": "bestaudio/best",
            "default_search": f"ytsearch5:{query}",
            "quiet": True,
            "skip_download": True
        }
        loop = self.music_cog.bot.loop
        try:
            data = await loop.run_in_executor(None, lambda: yt_dlp.YoutubeDL(ydl_opts).extract_info(f"ytsearch5:{query}", download=False))
            entries = data.get("entries", []) if data else []
            if not entries:
                return await interaction.followup.send(f"❌ No results found for `{query}`.", ephemeral=True)

            view = SearchSelectView(self.player, self.music_cog, entries)
            await interaction.followup.send(f"🔍 **Search Results for:** `{query}`\n*Select a song below to stream or enqueue:*", view=view, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Search error: {e}", ephemeral=True)


class SearchSelectView(View):
    def __init__(self, player, music_cog, entries):
        super().__init__(timeout=60)
        self.player = player
        self.music_cog = music_cog
        self.entries = entries[:5]
        options = []
        for i, entry in enumerate(self.entries):
            title = entry.get("title", f"Result {i+1}")[:80]
            dur = int(entry.get("duration") or 0)
            dur_str = time.strftime("%M:%S", time.gmtime(dur)) if dur > 0 else "Live"
            options.append(discord.SelectOption(
                label=f"{i+1}. {title[:50]}",
                description=f"⏱️ {dur_str} • {entry.get('uploader', 'Unknown')[:30]}",
                value=str(i),
                emoji="🎵"
            ))
        select = Select(placeholder="Choose a song to play...", options=options)
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        idx = int(interaction.data["values"][0])
        entry = self.entries[idx]
        await interaction.response.defer(ephemeral=True)
        from cogs.music import Song
        song_obj = await Song.create_source(entry.get("webpage_url") or entry.get("url"), interaction.user, self.music_cog.bot.loop)
        if song_obj:
            is_queued = self.player.enqueue_track(song_obj)
            desc = f"📥 **Enqueued:** [{song_obj.title}]({song_obj.webpage_url})" if is_queued else f"🎶 **Now Playing:** [{song_obj.title}]({song_obj.webpage_url})"
            await interaction.followup.send(embed=discord.Embed(description=desc, color=config.COLOR_PRIMARY), ephemeral=True)
        else:
            await interaction.followup.send("❌ Could not load selected track.", ephemeral=True)


class SetVolumeModal(Modal, title="Set Player Volume"):
    volume_val = TextInput(
        label="Volume Level (0 - 200%)",
        placeholder="e.g. 80, 100, 150...",
        default="100",
        required=True,
        max_length=3
    )

    def __init__(self, player):
        super().__init__()
        self.player = player

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.volume_val.value.strip())
            val = max(0, min(200, val))
            self.player.set_volume(val)
            boost = " 🔥 *(Volume Boost Active)*" if val > 100 else ""
            await interaction.response.send_message(f"🔊 **Volume updated:** `{val}%`{boost}", ephemeral=True)
        except ValueError:
            await interaction.response.send_message("❌ Please enter a valid number between 0 and 200.", ephemeral=True)


class RythmControllerView(View):
    """Rythm-style Complete Interactive Remote Music Controller for RAI VIBES 💗."""
    def __init__(self, player, music_cog=None):
        super().__init__(timeout=300)
        self.player = player
        self.music_cog = music_cog
        self.update_pause_button()

    def update_pause_button(self):
        vc = self.player.voice_client if self.player else None
        is_paused = vc.is_paused() if vc else False
        for item in self.children:
            if getattr(item, "custom_id", None) == "rythm_pause":
                item.emoji = "▶️" if is_paused else "⏸️"
                break

    def build_content(self) -> str:
        player = self.player
        if player and player.current:
            played_sec = int(time.time() - player.start_time) if player.start_time else 0
            dur_sec = player.current.duration
            dur_str = time.strftime("%M:%S", time.gmtime(dur_sec)) if dur_sec > 0 else "Live"
            curr_str = time.strftime("%M:%S", time.gmtime(played_sec)) if dur_sec > 0 else "0:00"
            title = player.current.title[:55]
            header = f"{title} ({curr_str} / {dur_str})"
        else:
            header = "No song currently playing (0:00 / 0:00)"

        return (
            f"{header}\n\n"
            f"Playback\n\n"
            f"Music\n\n"
            f"Controls\n\n"
            f"Library"
        )

    # --- ROW 0: PLAYBACK ---
    @button(emoji="⏮️", style=discord.ButtonStyle.secondary, row=0, custom_id="rythm_prev")
    async def prev_btn(self, interaction: discord.Interaction, btn: Button):
        player = self.player
        if not player or not player.voice_client:
            return await interaction.response.send_message("❌ Bot is not connected to voice.", ephemeral=True)

        played_sec = (time.time() - player.start_time) if player.start_time else 0
        if played_sec > 3.0:
            player.replay()
            await interaction.response.send_message("⏮️ **Replaying current track from start!**", ephemeral=True)
        elif player.history:
            prev_song = player.history[-1]
            from cogs.music import Song
            song_obj = await Song.create_source(prev_song.webpage_url or prev_song.title, interaction.user, self.music_cog.bot.loop)
            if song_obj:
                player.queue.appendleft(song_obj)
                player.voice_client.stop()
                await interaction.response.send_message(f"⏮️ **Playing previous track:** `{song_obj.title}`", ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ No previous track available.", ephemeral=True)

    @button(emoji="⏸️", style=discord.ButtonStyle.secondary, row=0, custom_id="rythm_pause")
    async def pause_btn(self, interaction: discord.Interaction, btn: Button):
        player = self.player
        vc = player.voice_client if player else None
        if not vc:
            return await interaction.response.send_message("❌ Bot is not connected to voice.", ephemeral=True)

        if vc.is_paused():
            player.resume()
            btn.emoji = "⏸️"
            await interaction.response.edit_message(content=self.build_content(), view=self)
        elif vc.is_playing():
            player.pause(interaction.user)
            btn.emoji = "▶️"
            await interaction.response.edit_message(content=self.build_content(), view=self)
        else:
            await interaction.response.send_message("ℹ️ Nothing is currently playing.", ephemeral=True)

    @button(emoji="⏭️", style=discord.ButtonStyle.secondary, row=0, custom_id="rythm_skip")
    async def skip_btn(self, interaction: discord.Interaction, btn: Button):
        player = self.player
        vc = player.voice_client if player else None
        if not vc:
            return await interaction.response.send_message("❌ Bot is not connected to voice.", ephemeral=True)

        if vc.is_playing() or vc.is_paused():
            skipped_title = player.current.title if player.current else "Track"
            vc.stop()
            await interaction.response.send_message(f"⏭️ **Skipped:** `{skipped_title}`", ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ Queue is empty.", ephemeral=True)

    @button(emoji="✖️", style=discord.ButtonStyle.secondary, row=0, custom_id="rythm_stop")
    async def stop_btn(self, interaction: discord.Interaction, btn: Button):
        player = self.player
        if player:
            await player.stop()
            await interaction.response.send_message("✖️ **Playback stopped and queue cleared.**", ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ Player inactive.", ephemeral=True)

    # --- ROW 1: MUSIC ---
    @button(emoji="☰", style=discord.ButtonStyle.secondary, row=1, custom_id="rythm_queue")
    async def queue_btn(self, interaction: discord.Interaction, btn: Button):
        player = self.player
        embed = player.build_queue_embed(page=0)
        view = QueuePaginationView(player)
        await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

    @button(emoji="🎵", style=discord.ButtonStyle.secondary, row=1, custom_id="rythm_np")
    async def np_btn(self, interaction: discord.Interaction, btn: Button):
        embed = self.player.build_now_playing_embed()
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @button(emoji="➕", style=discord.ButtonStyle.secondary, row=1, custom_id="rythm_add")
    async def add_btn(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.send_modal(AddSongModal(self.player, self.music_cog))

    @button(emoji="🔍", style=discord.ButtonStyle.secondary, row=1, custom_id="rythm_search")
    async def search_btn(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.send_modal(SearchSongModal(self.player, self.music_cog))

    @button(emoji="🎤", style=discord.ButtonStyle.secondary, row=1, custom_id="rythm_lyrics")
    async def lyrics_btn(self, interaction: discord.Interaction, btn: Button):
        player = self.player
        if not player or not player.current:
            return await interaction.response.send_message("❌ No track currently streaming.", ephemeral=True)

        lyrics_cog = interaction.client.get_cog("Lyrics")
        lyrics_data = await lyrics_cog.fetch_lyrics(player.current.title) if lyrics_cog else None
        if not lyrics_data or "lyrics" not in lyrics_data:
            return await interaction.response.send_message(f"⚠️ Could not find lyrics for `{player.current.title[:45]}`.", ephemeral=True)

        lyrics_text = lyrics_data.get("lyrics", "")
        if len(lyrics_text) > 3900:
            lyrics_text = lyrics_text[:3900] + "...\n*(Lyrics truncated)*"

        embed = discord.Embed(
            title=f"🎤 Lyrics: {lyrics_data.get('title', player.current.title)}",
            description=f"```fix\n{lyrics_text}\n```" if len(lyrics_text) < 1800 else lyrics_text,
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text=f"RAI VIBES 💗 • Lyrics Engine", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # --- ROW 2: CONTROLS ---
    @button(emoji="🤍", style=discord.ButtonStyle.secondary, row=2, custom_id="rythm_fav")
    async def fav_btn(self, interaction: discord.Interaction, btn: Button):
        player = self.player
        if not player or not player.current:
            return await interaction.response.send_message("❌ No song currently streaming.", ephemeral=True)

        from cogs.favorites import load_favorites, save_favorites
        user_id = str(interaction.user.id)
        data = load_favorites()
        if user_id not in data:
            data[user_id] = []

        if any(item.get("title") == player.current.title for item in data[user_id]):
            return await interaction.response.send_message(f"⚠️ `{player.current.title}` is already in your favorites!", ephemeral=True)

        data[user_id].append({
            "title": player.current.title,
            "url": player.current.webpage_url,
            "duration": player.current.duration,
            "thumbnail": player.current.thumbnail,
            "artist": player.current.data.get("uploader", "Unknown")
        })
        save_favorites(data)
        btn.emoji = "💖"
        await interaction.response.send_message(f"💖 **Added to Favorites:** `{player.current.title}`\nPlay anytime with `/favorite play`!", ephemeral=True)

    @button(emoji="🔊", style=discord.ButtonStyle.secondary, row=2, custom_id="rythm_vol")
    async def vol_btn(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.send_modal(SetVolumeModal(self.player))

    @button(emoji="🎛️", style=discord.ButtonStyle.secondary, row=2, custom_id="rythm_fx")
    async def fx_btn(self, interaction: discord.Interaction, btn: Button):
        view = AudioEffectsControlView(self.player, self)
        await interaction.response.send_message("🎛️ **Audio Studio & FX Console** — Select an enhancement below:", view=view, ephemeral=True)

    @button(emoji="📻", style=discord.ButtonStyle.secondary, row=2, custom_id="rythm_radio")
    async def radio_btn(self, interaction: discord.Interaction, btn: Button):
        radio_cog = interaction.client.get_cog("Radio")
        if radio_cog:
            await radio_cog.start_radio_stream(interaction, "lofi")
        else:
            await interaction.response.send_message("📻 24/7 Radio engine unavailable.", ephemeral=True)

    # --- ROW 3: LIBRARY ---
    @button(emoji="📂", style=discord.ButtonStyle.secondary, row=3, custom_id="rythm_playlists")
    async def playlists_btn(self, interaction: discord.Interaction, btn: Button):
        fav_cog = interaction.client.get_cog("Favorites")
        if fav_cog:
            from cogs.favorites import load_playlists
            data = load_playlists()
            u_data = data.get(str(interaction.user.id), {})
            p_names = list(u_data.keys())
            if p_names:
                msg = f"📂 **Your Saved Playlists:**\n" + "\n".join(f"• **{n}** ({len(u_data[n])} tracks) — `/playlist play {n}`" for n in p_names[:10])
            else:
                msg = "📂 You haven't created any playlists yet. Use `/playlist create <name>` or `/favorite play`!"
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            await interaction.response.send_message("📂 Playlists engine unavailable.", ephemeral=True)

    @button(emoji="⏱️", style=discord.ButtonStyle.secondary, row=3, custom_id="rythm_history")
    async def history_btn(self, interaction: discord.Interaction, btn: Button):
        if not self.player.history:
            return await interaction.response.send_message("⏱️ No recently played tracks in this session.", ephemeral=True)
        from cogs.music import HistoryRequeueView
        view = HistoryRequeueView(self.music_cog, self.player)
        await interaction.response.send_message("⏱️ **Recently Played Tracks** — Select to re-queue:", view=view, ephemeral=True)

    @button(emoji="🔀", style=discord.ButtonStyle.secondary, row=3, custom_id="rythm_shuffle")
    async def shuffle_btn(self, interaction: discord.Interaction, btn: Button):
        if len(self.player.queue) < 2:
            return await interaction.response.send_message("ℹ️ Queue needs at least 2 songs to shuffle.", ephemeral=True)
        self.player.shuffle()
        await interaction.response.send_message("🔀 **Queue shuffled successfully!**", ephemeral=True)

    @button(emoji="🔁", style=discord.ButtonStyle.secondary, row=3, custom_id="rythm_loop")
    async def loop_btn(self, interaction: discord.Interaction, btn: Button):
        player = self.player
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
