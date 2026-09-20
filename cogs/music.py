import os
import sys
import re
import asyncio
import functools
import random
import time
from collections import deque
from typing import Optional, List, Dict, Any
import logging

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View, Button
import yt_dlp

logger = logging.getLogger("Music")

import config
from utils.ffmpeg_setup import get_ffmpeg_executable
from utils.spotify import is_spotify_url, resolve_spotify, is_apple_music_url, resolve_apple_music
from utils.views import MusicPlayerView, QueuePaginationView
from utils.filters import get_filter_string

# Silence yt-dlp bug reports and setup high quality audio extractor
yt_dlp.utils.bug_reports_message = lambda *args, **kargs: ""

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "skip_download": True,
    "socket_timeout": 15,
    "retries": 3,
    "extractor_args": {
        "youtube": {
            "player_client": ["ios", "android", "mweb"]
        }
    }
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)


class Song:
    """Represents an audio track queued for playback."""
    def __init__(self, data: dict, requester: discord.Member, source_type: str = "youtube"):
        self.data = data
        self.requester = requester
        self.source_type = source_type
        self.title = data.get("title", "Unknown Title")
        self.url = data.get("url")  # Stream URL for FFmpeg
        self.webpage_url = data.get("webpage_url", "https://youtube.com")
        self.duration = int(data.get("duration") or 0)
        self.thumbnail = data.get("thumbnail") or config.RAI_ICON_URL
        self.uploader = data.get("uploader") or data.get("artist") or "RAI VIBES 💗 Sound"

    @staticmethod
    def _is_valid_result(res: Optional[dict]) -> bool:
        if not res or not isinstance(res, dict):
            return False
        if "entries" in res:
            valid_entries = [e for e in res["entries"] if e is not None and (e.get("url") or e.get("webpage_url") or e.get("id"))]
            return len(valid_entries) > 0
        return bool(res.get("url") or res.get("webpage_url") or res.get("id"))

    @classmethod
    async def create_source(cls, search: str, requester: discord.Member, loop: asyncio.AbstractEventLoop = None):
        """Extracts streamable info using yt-dlp asynchronously with smart single-track preference and fallback."""
        loop = loop or asyncio.get_event_loop()
        
        # Sanitize query by removing any command prefixes and leftover emojis
        cleaned_search = re.sub(r'^[💗💖🌸✨\s]+', '', search.strip()).strip()
        prefixes_to_strip = [
            "/play ", "!play ", "play ", "/p ", "!p ", "p ", "/search ", "!search ", "search ",
            "/play", "!play", "play", "/p", "!p"
        ]
        for prefix in prefixes_to_strip:
            if cleaned_search.lower().startswith(prefix):
                cleaned_search = cleaned_search[len(prefix):].strip()
                break

        is_url = cleaned_search.startswith("http://") or cleaned_search.startswith("https://")
        if is_url:
            to_search = cleaned_search
        else:
            # Clean symbols, emojis, and noise characters that cause search engine failures
            sanitized = re.sub(r'[^\w\s\-\.\'\,\(\)]', ' ', cleaned_search)
            sanitized = re.sub(r'\s+', ' ', sanitized).strip()
            query_str = sanitized if sanitized else cleaned_search
            to_search = f"ytsearch1:{query_str}"

        data = None
        try:
            partial_extract = functools.partial(
                ytdl.extract_info,
                to_search,
                download=False,
                process=True
            )
            data = await loop.run_in_executor(None, partial_extract)
        except Exception as e:
            print(f"[YTDL Primary Error] {to_search}: {e}")
            data = None

        # Fallback 1: If search failed and not a direct URL, try clean keywords
        if not cls._is_valid_result(data) and not is_url:
            try:
                simplified = re.sub(r'[\(\[][^()]*?[\)\]]', '', query_str)
                simplified = re.sub(r'\s+', ' ', re.sub(r'[^\w\s]', ' ', simplified)).strip()
                if simplified and simplified != query_str:
                    fb_extract = functools.partial(
                        ytdl.extract_info,
                        f"ytsearch1:{simplified}",
                        download=False,
                        process=True
                    )
                    data = await loop.run_in_executor(None, fb_extract)
            except Exception as e:
                print(f"[YTDL Fallback 1 Error] {simplified}: {e}")
                data = None

        # Fallback 2: SoundCloud search
        if not cls._is_valid_result(data) and not is_url:
            try:
                clean_sc = re.sub(r'[\(\[][^()]*?[\)\]]', '', query_str).strip()
                if ' - ' in clean_sc:
                    clean_sc = clean_sc.split(' - ')[0].strip()
                print(f"[Audio Fallback] Attempting SoundCloud search for: '{clean_sc}'")
                sc_extract = functools.partial(
                    ytdl.extract_info,
                    f"scsearch1:{clean_sc}",
                    download=False,
                    process=True
                )
                data = await loop.run_in_executor(None, sc_extract)
            except Exception as e:
                print(f"[YTDL SoundCloud Error] {clean_sc}: {e}")
                data = None

        if not cls._is_valid_result(data):
            return None

        if "entries" in data:
            entries = [e for e in data["entries"] if e is not None]
            if not entries:
                return None
            
            # Smart Single-Track Filter: prefer individual tracks over long compilation mixes
            selected_entry = entries[0]
            query_lower = search.lower()
            wants_compilation = any(k in query_lower for k in ["mix", "compilation", "playlist", "jukebox", "album", "top "])
            
            if not wants_compilation and len(entries) > 1:
                # Look for the first single track (under 10 minutes and not titled as a mix)
                for entry in entries:
                    t_lower = entry.get("title", "").lower()
                    dur = entry.get("duration") or 0
                    is_mix = any(k in t_lower for k in ["top 5", "top 10", "top 20", "jukebox", "compilation", "full album", "all songs", "nonstop", "non-stop"])
                    if not is_mix and 30 <= dur <= 600:
                        selected_entry = entry
                        break
            data = selected_entry

        extractor = str(data.get("extractor", "")).lower()
        src_type = "soundcloud" if "soundcloud" in extractor else "youtube"
        return cls(data, requester=requester, source_type=src_type)

    @classmethod
    async def search_multiple(cls, query: str, limit: int = 5, loop: asyncio.AbstractEventLoop = None) -> List[dict]:
        """Searches top 5 YouTube results for interactive selection."""
        loop = loop or asyncio.get_event_loop()
        partial_extract = functools.partial(
            ytdl.extract_info,
            f"ytsearch{limit}:{query}",
            download=False,
            process=True
        )
        data = await loop.run_in_executor(None, partial_extract)
        if not data or "entries" not in data:
            return []
        return [e for e in data["entries"] if e is not None][:limit]


class SearchSelectView(View):
    """Interactive Dropdown & Button selector for multiple matching search results."""
    def __init__(self, music_cog, ctx, results: List[dict], is_queue_mode: bool = False):
        super().__init__(timeout=60)
        self.music_cog = music_cog
        self.ctx = ctx
        self.results = results
        self.is_queue_mode = is_queue_mode
        self.message: Optional[discord.Message] = None

        options = []
        for i, item in enumerate(results):
            dur = time.strftime("%M:%S", time.gmtime(item.get("duration", 0)))
            title = item.get("title", f"Track {i+1}")[:80]
            options.append(discord.SelectOption(
                label=f"{i+1}. {title[:50]}",
                description=f"⏱️ {dur} • 👤 {item.get('uploader', 'Artist')[:35]}",
                value=str(i)
            ))

        select = Select(placeholder="⚡ Choose which track to play...", options=options, row=0)
        select.callback = self.select_callback
        self.add_item(select)

        # Quick 1-tap numbered buttons for mobile users
        btn_emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣"]
        for i in range(min(len(results), 5)):
            btn = Button(label=f"Track {i+1}", emoji=btn_emojis[i], style=discord.ButtonStyle.secondary, row=1 if i < 3 else 2)
            btn.callback = self.make_button_callback(i)
            self.add_item(btn)

        cancel_btn = Button(label="Cancel", emoji="❌", style=discord.ButtonStyle.danger, row=2)
        cancel_btn.callback = self.cancel_callback
        self.add_item(cancel_btn)

    def _get_author_id(self) -> Optional[int]:
        return getattr(getattr(self.ctx, "author", None), "id", None) or getattr(getattr(self.ctx, "user", None), "id", None)

    def make_button_callback(self, idx: int):
        async def btn_callback(interaction: discord.Interaction):
            await self.process_selection(interaction, idx)
        return btn_callback

    async def select_callback(self, interaction: discord.Interaction):
        selected_idx = int(interaction.data["values"][0])
        await self.process_selection(interaction, selected_idx)

    async def cancel_callback(self, interaction: discord.Interaction):
        author_id = self._get_author_id()
        if author_id and interaction.user.id != author_id:
            return await interaction.response.send_message("❌ This search menu belongs to another user.", ephemeral=True)
        await interaction.response.edit_message(content="✨ Song selection canceled.", embed=None, view=None)
        await asyncio.sleep(3)
        try:
            target_msg = self.message or interaction.message
            if target_msg:
                await target_msg.delete()
        except Exception:
            pass

    async def process_selection(self, interaction: discord.Interaction, selected_idx: int):
        author_id = self._get_author_id()
        if author_id and interaction.user.id != author_id:
            return await interaction.response.send_message("❌ This search menu belongs to another user.", ephemeral=True)

        selected_data = self.results[selected_idx]
        voice_client = await self.music_cog.ensure_voice(interaction)
        if not voice_client:
            return

        player = self.music_cog.get_or_create_player(interaction.guild)
        player.voice_client = voice_client
        player.text_channel = interaction.channel

        song = Song(selected_data, requester=interaction.user, source_type="youtube")
        is_queued = player.enqueue_track(song, is_queue_mode=self.is_queue_mode)

        if is_queued:
            est_sec = 0
            if player.current:
                cur_elapsed = int(time.time() - player.start_time) if player.start_time else 0
                est_sec += max(0, player.current.duration - cur_elapsed)
            for q_song in list(player.queue)[:-1]:
                est_sec += max(0, q_song.duration)
            est_str = time.strftime("%M:%S", time.gmtime(est_sec)) if est_sec > 0 else "Playing Next"
            dur_str = time.strftime("%M:%S", time.gmtime(song.duration)) if song.duration > 0 else "Live"

            card_title = "📥 Enqueued to Playback Queue" if self.is_queue_mode else "🎵 Song Added to Queue"
            embed = discord.Embed(
                title=card_title,
                description=f"**[{song.title}]({song.webpage_url})**",
                color=config.COLOR_PRIMARY
            )
            embed.set_thumbnail(url=song.thumbnail)
            embed.add_field(name="⏱️ Track Duration", value=f"`{dur_str}`", inline=True)
            embed.add_field(name="📍 Position in Queue", value=f"`#{len(player.queue)}`", inline=True)
            embed.add_field(name="⏳ Estimated Time", value=f"`{est_str}`", inline=True)
            embed.set_footer(text=f"Requested by {interaction.user.display_name} • RAI VIBES 💗", icon_url=interaction.user.display_avatar.url)
            await interaction.response.edit_message(content=None, embed=embed, view=None)
            asyncio.create_task(self.music_cog._auto_delete(interaction.message, 10))
        else:
            embed = discord.Embed(
                description=f"🎶 **Starting playback:** [{song.title}]({song.webpage_url})",
                color=config.COLOR_PRIMARY
            )
            await interaction.response.edit_message(content=None, embed=embed, view=None)
            asyncio.create_task(self.music_cog._auto_delete(interaction.message, 3))


class ResumePlaybackView(View):
    """Interactive prompt to resume playback where you left off."""
    def __init__(self, player: 'GuildMusicPlayer', snapshot: dict):
        super().__init__(timeout=180)
        self.player = player
        self.snapshot = snapshot
        pos_sec = snapshot.get("position", 0)
        pos_str = time.strftime("%M:%S", time.gmtime(pos_sec))
        
        btn_resume = Button(label=f"Continue ({pos_str})", emoji="▶️", style=discord.ButtonStyle.success)
        btn_resume.callback = self.resume_callback
        self.add_item(btn_resume)
        
        btn_restart = Button(label="Replay (0:00)", emoji="🔄", style=discord.ButtonStyle.primary)
        btn_restart.callback = self.restart_callback
        self.add_item(btn_restart)
        
        btn_dismiss = Button(label="Dismiss", emoji="❌", style=discord.ButtonStyle.secondary)
        btn_dismiss.callback = self.dismiss_callback
        self.add_item(btn_dismiss)

    async def resume_callback(self, interaction: discord.Interaction):
        song = self.snapshot.get("song")
        pos_sec = self.snapshot.get("position", 0)
        if not song:
            return await interaction.response.send_message("❌ Track no longer available.", ephemeral=True)
            
        vc = await self.player.cog.ensure_voice(interaction)
        if not vc:
            return
            
        self.player.voice_client = vc
        self.player.text_channel = interaction.channel
        self.player.current = song
        self.player.start_time = time.time() - pos_sec
        await self.player.restart_current_with_filters()
        self.player.paused_snapshot = None
        
        pos_str = time.strftime("%M:%S", time.gmtime(pos_sec))
        embed = discord.Embed(
            title="▶️ Resumed Playback",
            description=f"Resumed **[{song.title}]({song.webpage_url})** from `{pos_str}`!",
            color=config.COLOR_PRIMARY
        )
        await interaction.response.edit_message(content=None, embed=embed, view=None)

    async def restart_callback(self, interaction: discord.Interaction):
        song = self.snapshot.get("song")
        if not song:
            return await interaction.response.send_message("❌ Track no longer available.", ephemeral=True)
            
        vc = await self.player.cog.ensure_voice(interaction)
        if not vc:
            return
            
        self.player.voice_client = vc
        self.player.text_channel = interaction.channel
        self.player.current = song
        self.player.start_time = time.time()
        await self.player.restart_current_with_filters()
        self.player.paused_snapshot = None
        
        embed = discord.Embed(
            title="🔄 Replaying from Start",
            description=f"Now playing **[{song.title}]({song.webpage_url})** from the beginning!",
            color=config.COLOR_PRIMARY
        )
        await interaction.response.edit_message(content=None, embed=embed, view=None)

    async def dismiss_callback(self, interaction: discord.Interaction):
        self.player.paused_snapshot = None
        await interaction.response.edit_message(content="✨ Dismissed resume prompt.", embed=None, view=None)


class GuildMusicPlayer:
    """Manages audio playback, queue, state, and UI for a specific Discord Guild."""
    def __init__(self, cog, guild: discord.Guild):
        self.cog = cog
        self.guild = guild
        self.bot = cog.bot
        self.queue = deque()
        self.history = deque(maxlen=20)
        self._voice_client: Optional[discord.VoiceClient] = None
        self.current: Optional[Song] = None
        self.current_source: Optional[discord.AudioSource] = None
        self.loop_mode: str = "off"  # "off", "track", "queue"
        self.volume: int = config.DEFAULT_VOLUME
        self.text_channel: Optional[discord.TextChannel] = None
        self.now_playing_message: Optional[discord.Message] = None
        
        # Smart Resume snapshot
        self.paused_snapshot: Optional[dict] = None
        
        # Audio Filters & Effects
        self.active_filters: List[str] = []
        self.custom_speed: float = 1.0
        self.mode_247: bool = True
        self.autoplay: bool = True

        self.play_next_song = asyncio.Event()
        self.audio_task: Optional[asyncio.Task] = None
        self.start_time: float = 0.0
        self.is_restarting_for_filters: bool = False

    @property
    def voice_client(self) -> Optional[discord.VoiceClient]:
        return self.guild.voice_client

    @voice_client.setter
    def voice_client(self, vc: Optional[discord.VoiceClient]):
        self._voice_client = vc

    @property
    def is_connected(self) -> bool:
        vc = self.guild.voice_client
        return vc is not None and vc.is_connected()

    def get_volume_factor(self) -> float:
        """Returns the psychoacoustic volume gain multiplier (0.0 to 2.0)."""
        if self.volume <= 0:
            return 0.0
        if self.volume <= 100:
            # Perceptual logarithmic-response curve (squared amplitude)
            return float((self.volume / 100.0) ** 2)
        # Linear boost up to 200% (2.0x gain)
        return float(min(2.0, 1.0 + ((self.volume - 100) / 100.0)))

    def set_volume(self, val: int):
        self.volume = max(0, min(200, val))
        vol_factor = self.get_volume_factor()

        # Update player current_source
        if self.current_source and hasattr(self.current_source, "volume"):
            self.current_source.volume = vol_factor

        # Update active voice_client source directly
        vc = self.guild.voice_client
        if vc and vc.source and hasattr(vc.source, "volume"):
            vc.source.volume = vol_factor

        print(f"[Volume] Guild {self.guild.name} ({self.guild.id}) adjusted volume to {self.volume}% (gain: {vol_factor:.3f})")

    def pause(self, user=None):
        vc = self.guild.voice_client
        if vc and vc.is_playing():
            vc.pause()
            if self.current:
                elapsed = max(0, int(time.time() - self.start_time)) if self.start_time else 0
                self.paused_snapshot = {
                    "song": self.current,
                    "position": elapsed,
                    "user_id": user.id if user else (self.current.requester.id if self.current.requester else None),
                    "channel_id": self.text_channel.id if self.text_channel else None
                }

    def resume(self):
        vc = self.guild.voice_client
        if vc and vc.is_paused():
            vc.resume()
            self.paused_snapshot = None

    def skip(self):
        vc = self.guild.voice_client
        if vc and (vc.is_playing() or vc.is_paused()):
            vc.stop()

    def is_radio_playing(self) -> bool:
        """Returns True ONLY if the current audio stream is the 24/7 background radio station."""
        if not self.current:
            return False
        return getattr(self.current, "source_type", None) == "radio"

    def enqueue_track(self, song: Song, is_queue_mode: bool = False) -> bool:
        """
        Enqueues a song:
        - If an actual USER track is actively playing, the new song is appended to the queue and returns True (queued).
        - If idle, or if 24/7 background radio is streaming, the user song starts playing immediately and returns False (playing now).
        """
        vc = self.guild.voice_client
        is_playing = bool(vc and (vc.is_playing() or vc.is_paused()))

        # An active user track is playing if current track exists, is not 24/7 radio, and VC is playing
        user_song_active = bool(
            self.current is not None
            and getattr(self.current, "source_type", None) != "radio"
            and is_playing
        )

        if user_song_active:
            self.queue.append(song)
            return True

        # If idle or 24/7 background radio is streaming, start user track immediately!
        if self.is_radio_playing():
            self.queue.appendleft(song)
            self.skip()  # Stop the infinite radio stream immediately so user track plays right now
        else:
            self.queue.append(song)
            self.play_next_song.set()

        return False

    def shuffle(self):
        temp = list(self.queue)
        random.shuffle(temp)
        self.queue = deque(temp)

    async def stop(self):
        if self.current:
            elapsed = max(0, int(time.time() - self.start_time)) if self.start_time else 0
            if elapsed > 10:
                self.paused_snapshot = {
                    "song": self.current,
                    "position": elapsed,
                    "user_id": self.current.requester.id if self.current.requester else None,
                    "channel_id": self.text_channel.id if self.text_channel else None
                }
        self.queue.clear()
        self.loop_mode = "off"
        self.active_filters.clear()
        self.custom_speed = 1.0
        if self.voice_client:
            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()
            await self.voice_client.disconnect(force=True)
            self.voice_client = None

    def create_progress_bar(self, current_sec: int, total_sec: int, length: int = 14) -> str:
        if total_sec <= 0:
            return "🔴 **LIVE STREAM / RADIO**"
        progress = min(1.0, max(0.0, current_sec / total_sec))
        filled = int(progress * length)
        bar = "━" * filled + "●" + "─" * (length - filled)
        cur_str = time.strftime("%M:%S", time.gmtime(current_sec)) if current_sec < 3600 else time.strftime("%H:%M:%S", time.gmtime(current_sec))
        tot_str = time.strftime("%M:%S", time.gmtime(total_sec)) if total_sec < 3600 else time.strftime("%H:%M:%S", time.gmtime(total_sec))
        return f"`{cur_str}` {bar} `{tot_str}`"

    def build_now_playing_embed(self) -> discord.Embed:
        if not self.current:
            embed = discord.Embed(
                title="⚡ RAI VIBES 💗 PLAYER",
                description="No music currently playing. Use `/play` or `/radio` to summon the rhythm!",
                color=config.COLOR_PRIMARY
            )
            return embed

        elapsed = int(time.time() - self.start_time) if self.start_time else 0
        is_paused = bool(self.voice_client and self.voice_client.is_paused())
        status_text = "⏸️ Paused" if is_paused else "🎶 Now Playing"

        loop_badge = "🔂 Track" if self.loop_mode == "track" else ("🔁 Queue" if self.loop_mode == "queue" else "Off")
        filters_badge = ", ".join(self.active_filters) if self.active_filters else "Normal"
        if self.custom_speed != 1.0:
            filters_badge += f" ({self.custom_speed}x)"

        pbar = self.create_progress_bar(elapsed, self.current.duration)

        embed = discord.Embed(
            color=0xFF1493 if not is_paused else 0x5865F2
        )
        embed.set_author(name=f"RAI VIBES 💗 • {status_text}", icon_url=config.RAI_ICON_URL)
        embed.set_thumbnail(url=self.current.thumbnail or config.RAI_ICON_URL)

        desc = (
            f"### 🎵 [{self.current.title[:65]}]({self.current.webpage_url})\n\n"
            f"{pbar}\n\n"
            f"╭── 🎧 **Playback Info**\n"
            f"│ 👤 **Artist:** `{self.current.uploader[:30]}`\n"
            f"│ 🔊 **Volume:** `{self.volume}%`  •  🔁 **Loop:** `{loop_badge}`\n"
            f"│ 🎛️ **Audio FX:** `{filters_badge}`  •  📜 **Queue:** `{len(self.queue)} songs`\n"
            f"╰── 📥 **Requested by:** {self.current.requester.mention}"
        )
        embed.description = desc
        embed.set_footer(text="RAI VIBES 💗 • High Fidelity Sound Engine", icon_url=config.RAI_ICON_URL)
        return embed

    def build_queue_embed(self, page: int = 0, per_page: int = 5) -> discord.Embed:
        embed = discord.Embed(
            title=f"Queue for {self.guild.name}",
            color=config.COLOR_PRIMARY
        )

        # Now Playing section
        if self.current:
            req_mention = self.current.requester.mention if self.current.requester else "Community"
            now_playing_desc = (
                f"**Now Playing**\n"
                f"[{self.current.title}]({self.current.webpage_url})\n"
                f"⊕ {req_mention}\n\n"
            )
        else:
            now_playing_desc = "**Now Playing**\n*Nothing currently playing*\n\n"

        total_songs = len(self.queue)
        total_pages = max(1, (total_songs + per_page - 1) // per_page)
        page = max(0, min(page, total_pages - 1))
        start = page * per_page
        end = start + per_page
        page_songs = list(self.queue)[start:end]

        if not page_songs:
            queue_desc = "*No upcoming songs in queue. Use `/play` or `➕` to add tracks!*"
        else:
            song_blocks = []
            for i, song in enumerate(page_songs, start=start + 1):
                if song.duration >= 3600:
                    dur_str = f"{song.duration // 3600}:{(song.duration % 3600) // 60:02d}:{song.duration % 60:02d}"
                elif song.duration > 0:
                    dur_str = f"{song.duration // 60}:{song.duration % 60:02d}"
                else:
                    dur_str = "Live"

                artist = song.uploader or "Artist"
                s_req = f"⊕ {song.requester.mention}" if song.requester else "⊕ Community"
                song_blocks.append(f"**{i}. {song.title}**\n{artist} • {dur_str} • {s_req}")

            queue_desc = "\n\n".join(song_blocks)

        embed.description = f"{now_playing_desc}{queue_desc}"

        # Calculate Total Duration across all songs in queue + currently playing
        total_seconds = sum(s.duration for s in self.queue if s.duration > 0)
        if self.current and self.current.duration > 0:
            total_seconds += self.current.duration

        if total_seconds >= 3600:
            total_dur_str = f"{total_seconds // 3600}:{(total_seconds % 3600) // 60:02d}:{total_seconds % 60:02d}"
        else:
            total_dur_str = f"{total_seconds // 60}:{total_seconds % 60:02d}"

        embed.set_footer(
            text=f"{total_songs} songs in queue • Page {page + 1}/{total_pages} • Total Duration: {total_dur_str}"
        )
        return embed

    async def restart_current_with_filters(self):
        """Applies new audio filters by restarting current track with calculated seek position."""
        if not self.current or not self.voice_client:
            return

        elapsed = max(0, int(time.time() - self.start_time)) if self.start_time else 0
        self.is_restarting_for_filters = True
        
        ffmpeg_bin = get_ffmpeg_executable()
        filter_args = get_filter_string(self.active_filters, self.custom_speed)
        
        # Ensure fresh stream URL if needed
        stream_url = self.current.url
        if not stream_url or "googlevideo.com" in stream_url:
            try:
                fresh_info = await self.bot.loop.run_in_executor(
                    None,
                    functools.partial(ytdl.extract_info, self.current.webpage_url, download=False, process=True)
                )
                if fresh_info:
                    stream_url = fresh_info.get("url") or stream_url
                    self.current.url = stream_url
            except Exception:
                pass

        seek_opt = f"-ss {elapsed} " if (getattr(self.current, "duration", 0) > 0 and elapsed > 0) else ""
        before_opt = f"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 {seek_opt}-nostdin".strip()
        ffmpeg_opt = f"-vn -bufsize 4096k -threads 2 {filter_args}".strip()

        def after_playing(err):
            if err:
                print(f"[Filter Audio Error] {err}")
            if not self.is_restarting_for_filters:
                self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

        try:
            if self.voice_client.is_playing() or self.voice_client.is_paused():
                self.voice_client.stop()
                await asyncio.sleep(0.15)

            raw_source = discord.FFmpegPCMAudio(
                stream_url,
                executable=ffmpeg_bin,
                before_options=before_opt,
                options=ffmpeg_opt
            )
            self.current_source = discord.PCMVolumeTransformer(raw_source, volume=self.get_volume_factor())
            self.start_time = time.time() - elapsed
            self.voice_client.play(self.current_source, after=after_playing)
            self.is_restarting_for_filters = False

            if self.text_channel:
                embed = self.build_now_playing_embed()
                view = MusicPlayerView(self.cog, self.guild.id)
                if self.now_playing_message:
                    try:
                        await self.now_playing_message.delete()
                    except Exception:
                        pass
                try:
                    self.now_playing_message = await self.text_channel.send(embed=embed, view=view)
                except Exception:
                    pass
        except Exception as e:
            print(f"[Filter Restart Error] {e}")
            self.is_restarting_for_filters = False

    async def player_loop(self):
        """Infinite loop driving track queue transitions and audio streaming."""
        await self.bot.wait_until_ready()
        ffmpeg_bin = get_ffmpeg_executable()

        while not self.bot.is_closed():
            self.play_next_song.clear()

            if self.loop_mode == "track" and self.current:
                song = self.current
            else:
                if self.loop_mode == "queue" and self.current:
                    self.queue.append(self.current)

                if not self.queue:
                    # Smart Autoplay / Endless Radio
                    last_song = self.current or (self.history[-1] if self.history else None)
                    if self.autoplay and self.is_connected and last_song and last_song.title:
                        try:
                            # Search related tracks
                            query_ref = f"{last_song.uploader} official music" if last_song.uploader and "RAI VIBES" not in last_song.uploader else f"{last_song.title} mix"
                            extract_fn = functools.partial(ytdl.extract_info, f"ytsearch5:{query_ref}", download=False, process=True)
                            rec_data = await self.bot.loop.run_in_executor(None, extract_fn)
                            entries = rec_data.get("entries") if rec_data else None
                            if entries:
                                played_titles = {h.title.lower() for h in self.history}
                                if last_song:
                                    played_titles.add(last_song.title.lower())

                                candidate = None
                                for ent in entries:
                                    if ent and ent.get("title") and ent.get("title").lower() not in played_titles:
                                        candidate = ent
                                        break

                                if candidate:
                                    rec_song = Song(candidate, requester=self.bot.user, source_type="autoplay")
                                    self.queue.append(rec_song)
                                    if self.text_channel:
                                        auto_embed = discord.Embed(
                                            title="📻 Smart Autoplay • Seamless Continuity",
                                            description=f"Queue was empty. Next up: **[{rec_song.title}]({rec_song.webpage_url})**\n*(Selected based on `{last_song.title[:45]}`)*",
                                            color=config.COLOR_PRIMARY
                                        )
                                        auto_embed.set_footer(text="RAI VIBES 💗 • Intelligent Radio | Toggle with /autoplay", icon_url=config.RAI_ICON_URL)
                                        await self.text_channel.send(embed=auto_embed)
                        except Exception as e:
                            print(f"[Autoplay Error] {e}")

                if not self.queue:
                    self.current = None
                    try:
                        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="24/7 Pure Music 💗 | /play"))
                    except Exception:
                        pass
                    # Wait for inactivity timeout or new songs
                    try:
                        timeout_val = None if self.mode_247 else config.INACTIVITY_TIMEOUT
                        if timeout_val:
                            await asyncio.wait_for(self.wait_for_song(), timeout=timeout_val)
                        else:
                            await self.wait_for_song()
                    except asyncio.TimeoutError:
                        if not self.mode_247 and self.text_channel and self.is_connected:
                            embed = discord.Embed(
                                title="⚡ RAI VIBES 💗 Rest Mode",
                                description="Left voice channel due to inactivity. Call me back with `/play` anytime!",
                                color=config.COLOR_DARK
                            )
                            await self.text_channel.send(embed=embed)
                        if not self.mode_247:
                            await self.stop()
                            break

                if not self.queue:
                    continue

                song = self.queue.popleft()
                self.current = song
                self.history.append(song)

            if not song.url:
                try:
                    q_cand = song.data.get("search_query") or song.title
                    resolved_song = await Song.create_source(q_cand, song.requester, self.bot.loop)
                    if not resolved_song:
                        # Fallback attempt: clean title
                        clean_t = re.sub(r'[\(\[][^()]*?[\)\]]', '', song.title).strip()
                        if ' - ' in clean_t:
                            clean_t = clean_t.split(' - ')[0].strip()
                        if clean_t and clean_t != q_cand:
                            await asyncio.sleep(0.3)
                            resolved_song = await Song.create_source(clean_t, song.requester, self.bot.loop)

                    if not resolved_song:
                        if self.text_channel:
                            await self.text_channel.send(f"⚠️ Could not stream `{song.title}`. Skipping.")
                        await asyncio.sleep(1.0)
                        continue
                    song.url = resolved_song.url
                    song.webpage_url = resolved_song.webpage_url
                    song.duration = resolved_song.duration
                    song.thumbnail = resolved_song.thumbnail or song.thumbnail
                    song.uploader = resolved_song.uploader
                except Exception as e:
                    if self.text_channel:
                        await self.text_channel.send(f"⚠️ Error loading audio for `{song.title}`: {e}")
                    await asyncio.sleep(1.0)
                    continue

            def after_playing(err):
                if err:
                    print(f"[RAI VIBES 💗 Audio Error] {err}")
                if not self.is_restarting_for_filters:
                    self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

            # Ensure voice client is connected before playing
            self.voice_client = self.guild.voice_client
            if not self.voice_client or not self.voice_client.is_connected():
                self.queue.appendleft(song)
                self.current = None
                await self.wait_for_voice()
                continue

            try:
                # Ensure stream URL exists
                stream_url = song.url
                if not stream_url:
                    try:
                        fresh_info = await self.bot.loop.run_in_executor(None, functools.partial(ytdl.extract_info, song.webpage_url, download=False, process=True))
                        if fresh_info:
                            stream_url = fresh_info.get("url") or stream_url
                    except Exception:
                        pass

                # Fallback: recover via SoundCloud if stream_url is missing
                if not stream_url:
                    try:
                        clean_query = re.sub(r'[\(\[][^()]*?[\)\]]', '', song.title).strip()
                        if ' - ' in clean_query:
                            clean_query = clean_query.split(' - ')[0].strip()
                        sc_song = await Song.create_source(f"scsearch1:{clean_query}", song.requester, self.bot.loop)
                        if sc_song and sc_song.url:
                            stream_url = sc_song.url
                            song.url = sc_song.url
                            song.webpage_url = sc_song.webpage_url
                            song.source_type = "soundcloud"
                    except Exception:
                        pass

                if not stream_url:
                    if self.text_channel:
                        await self.text_channel.send(f"⚠️ Audio source unavailable for `{song.title}`. Skipping to next track.")
                    self.play_next_song.set()
                    continue

                # AI Radio DJ Commentary Hook (if enabled)
                if not self.is_restarting_for_filters and self.voice_client and self.voice_client.is_connected():
                    try:
                        ai_dj_cog = self.bot.get_cog("AIDJ")
                        if ai_dj_cog and ai_dj_cog.is_enabled(self.guild.id):
                            await ai_dj_cog.play_transition(self.voice_client, song)
                    except Exception as e:
                        print(f"[AI DJ Hook Error] {e}")

                filter_args = get_filter_string(self.active_filters, self.custom_speed)
                ffmpeg_opt = f"-vn -bufsize 4096k -threads 2 {filter_args}".strip()

                raw_source = discord.FFmpegPCMAudio(
                    stream_url,
                    executable=ffmpeg_bin,
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin",
                    options=ffmpeg_opt
                )
                self.current_source = discord.PCMVolumeTransformer(raw_source, volume=self.get_volume_factor())
                self.start_time = time.time()
                if self.voice_client and self.voice_client.is_connected():
                    if self.voice_client.is_playing() or self.voice_client.is_paused():
                        self.voice_client.stop()
                        await asyncio.sleep(0.15)
                    self.voice_client.play(self.current_source, after=after_playing)
                    # Real-time Dynamic Presence on Discord
                    try:
                        clean_t = song.title[:45]
                        await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=f"{clean_t} 🎵"))
                    except Exception:
                        pass
                else:
                    self.queue.appendleft(song)
                    self.current = None
                    continue
            except Exception as e:
                print(f"[Player Error] Failed to stream: {e}")
                if self.text_channel:
                    await self.text_channel.send(f"❌ Audio error on `{song.title}`: {e}")
                self.play_next_song.set()

            if self.text_channel and not self.is_restarting_for_filters:
                try:
                    from cogs.telemetry import record_song_play
                    record_song_play(song.title)
                except Exception:
                    pass
                if self.now_playing_message:
                    try:
                        await self.now_playing_message.delete()
                    except Exception:
                        pass
                embed = self.build_now_playing_embed()
                view = MusicPlayerView(self.cog, self.guild.id)
                try:
                    self.now_playing_message = await self.text_channel.send(embed=embed, view=view)
                except Exception as e:
                    print(f"[Embed Error] {e}")

            await self.play_next_song.wait()

            # Automatic Failover: If YouTube track exited prematurely (< 3.0s), seamlessly recover via SoundCloud
            played_duration = (time.time() - self.start_time) if self.start_time else 0
            if (
                played_duration < 3.0
                and song
                and getattr(song, "source_type", "youtube") == "youtube"
                and not self.is_restarting_for_filters
            ):
                print(f"[Audio Failover] Track '{song.title}' exited prematurely ({played_duration:.1f}s). Attempting SoundCloud failover...")
                try:
                    clean_query = re.sub(r'[\(\[][^()]*?[\)\]]', '', song.title).strip()
                    if " - " in clean_query:
                        clean_query = clean_query.split(" - ")[0].strip()
                    sc_song = await Song.create_source(f"scsearch1:{clean_query}", song.requester, self.bot.loop)
                    if sc_song and sc_song.url:
                        sc_song.source_type = "soundcloud"
                        print(f"[Audio Failover] Successfully recovered '{song.title}' via SoundCloud: {sc_song.title}")
                        self.queue.appendleft(sc_song)
                        if self.text_channel:
                            await self.text_channel.send(f"🔄 **Recovered audio stream via high-speed backup:** [{sc_song.title}]({sc_song.webpage_url})")
                except Exception as sc_err:
                    print(f"[Audio Failover Error] {sc_err}")

    async def wait_for_song(self):
        while not self.queue:
            await asyncio.sleep(1)

    async def wait_for_voice(self):
        while not self.voice_client or not self.voice_client.is_connected():
            self.voice_client = self.guild.voice_client
            if self.voice_client and self.voice_client.is_connected():
                return
            await asyncio.sleep(1.0)


class Music(commands.Cog):
    """RAI VIBES 💗 Music System - The Ultimate High-Performance Sound Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: Dict[int, GuildMusicPlayer] = {}

    @staticmethod
    async def _auto_delete(msg: Any, delay: int = 15):
        """Silently deletes temporary enqueue or feedback cards after delay to prevent channel spam."""
        if not msg:
            return
        try:
            await asyncio.sleep(delay)
            await msg.delete()
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # ZERO-PREFIX LISTENER FOR #song-requests
    # -------------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Zero-prefix song request engine for #song-requests channel."""
        if not message.guild or message.author.bot:
            return

        ch_name = getattr(message.channel, "name", "").lower()
        raw_ch_name = getattr(message.channel, "name", "")
        if message.channel.id != 1545534637122527332 and not any(k in ch_name for k in ["song-request", "requests"]) and "ꜱᴏɴɢ" not in raw_ch_name:
            return

        content = message.content.strip()
        if not content:
            return

        # Ignore commands starting with standard prefixes
        if content.startswith(("!", "/", "?", ".", "-", "$")):
            return

        # Delete the user's message immediately to preserve pristine channel aesthetic
        try:
            await message.delete()
        except Exception:
            pass

        # Check if user is in a voice channel
        user_vc = getattr(getattr(message.author, "voice", None), "channel", None)
        if not user_vc:
            notice = await message.channel.send(
                embed=discord.Embed(
                    description=f"⚠️ {message.author.mention} **You must be in a voice channel** (e.g. `🌧️ | LO-FI ZONE`) to request music!",
                    color=config.COLOR_WARNING
                )
            )
            asyncio.create_task(self._auto_delete(notice, 7))
            return

        voice_client = await self.ensure_voice(message)
        if not voice_client:
            return

        player = self.get_or_create_player(message.guild)
        player.voice_client = voice_client
        player.text_channel = message.channel

        status_card = None
        try:
            status_card = await message.channel.send(
                embed=discord.Embed(
                    description=f"🔍 Searching & buffering **`{content[:50]}`** for {message.author.mention}...",
                    color=config.COLOR_PRIMARY
                )
            )
        except Exception:
            pass

        try:
            if is_spotify_url(content):
                spotify_tracks = await resolve_spotify(content)
                if spotify_tracks:
                    if len(spotify_tracks) == 1:
                        t = spotify_tracks[0]
                        song_obj = await Song.create_source(t["search_query"], message.author, self.bot.loop)
                        if song_obj:
                            if t.get("thumbnail"):
                                song_obj.thumbnail = t["thumbnail"]
                            is_queued = player.enqueue_track(song_obj)
                            card_desc = f"**[{song_obj.title}]({song_obj.webpage_url})**\n📥 Added to queue by {message.author.mention}" if is_queued else f"🎶 Now streaming: **[{song_obj.title}]({song_obj.webpage_url})**"
                            card = await message.channel.send(
                                embed=discord.Embed(
                                    title="⚡ Spotify Track Added",
                                    description=card_desc,
                                    color=config.COLOR_PRIMARY
                                )
                            )
                            asyncio.create_task(self._auto_delete(card, 10))
                    else:
                        space = max(0, config.MAX_QUEUE_SIZE - len(player.queue))
                        batch = spotify_tracks[:space]
                        for t in batch:
                            s = await Song.create_source(t["search_query"], message.author, self.bot.loop)
                            if s:
                                player.enqueue_track(s)
                        card = await message.channel.send(
                            embed=discord.Embed(
                                title="⚡ Spotify Playlist Enqueued",
                                description=f"Enqueued **{len(batch)} tracks** for {message.author.mention}!",
                                color=config.COLOR_PRIMARY
                            )
                        )
                        asyncio.create_task(self._auto_delete(card, 10))
            else:
                song_obj = await Song.create_source(content, message.author, self.bot.loop)
                if song_obj:
                    is_queued = player.enqueue_track(song_obj)
                    dur_str = time.strftime("%M:%S", time.gmtime(song_obj.duration)) if song_obj.duration > 0 else "Live"
                    card_title = "🎵 Song Added to Queue" if is_queued else "🎶 Starting Playback"
                    card = await message.channel.send(
                        embed=discord.Embed(
                            title=card_title,
                            description=f"**[{song_obj.title}]({song_obj.webpage_url})**\n⏱️ `{dur_str}` • Requested by {message.author.mention}",
                            color=config.COLOR_PRIMARY
                        )
                    )
                    asyncio.create_task(self._auto_delete(card, 10))
                else:
                    err = await message.channel.send(
                        embed=discord.Embed(
                            description=f"❌ No audio stream found for: `{content[:50]}`",
                            color=config.COLOR_ERROR
                        )
                    )
                    asyncio.create_task(self._auto_delete(err, 6))
        except Exception as e:
            logger.error(f"Error in zero-prefix song request: {e}")
        finally:
            if status_card:
                asyncio.create_task(self._auto_delete(status_card, 1))

    def get_player(self, guild_id: int) -> Optional[GuildMusicPlayer]:
        return self.players.get(guild_id)

    def get_or_create_player(self, guild: discord.Guild) -> GuildMusicPlayer:
        if guild.id not in self.players:
            player = GuildMusicPlayer(self, guild)
            self.players[guild.id] = player
            player.audio_task = self.bot.loop.create_task(player.player_loop())
        else:
            player = self.players[guild.id]
            if not player.audio_task or player.audio_task.done():
                player.audio_task = self.bot.loop.create_task(player.player_loop())
        return player

    async def ensure_voice(self, ctx_or_interaction) -> Optional[discord.VoiceClient]:
        """Ensures the bot connects to or moves to the user's active voice channel."""
        guild = ctx_or_interaction.guild
        if not guild:
            return None

        voice_client = guild.voice_client

        author = getattr(ctx_or_interaction, "author", None) or getattr(ctx_or_interaction, "user", None)
        user_vc = None

        if author:
            # 1. Check direct author.voice.channel
            user_vc = getattr(getattr(author, "voice", None), "channel", None)

            # 2. Member lookup from guild if author was User or cache missing
            if not user_vc and hasattr(author, "id"):
                member = guild.get_member(author.id)
                if member and member.voice:
                    user_vc = member.voice.channel

            # 3. Direct channel member scan across guild voice and stage channels
            if not user_vc and hasattr(author, "id"):
                for ch in guild.voice_channels + guild.stage_channels:
                    if any(m.id == author.id for m in ch.members):
                        user_vc = ch
                        break

        # Target VC must be the user's voice channel or the bot's current active voice channel
        target_vc = user_vc or (voice_client.channel if voice_client and voice_client.is_connected() else None)

        # If user ran command directly inside a voice channel's text chat, target that voice channel
        if not target_vc:
            ch_obj = getattr(ctx_or_interaction, "channel", None)
            if ch_obj and isinstance(ch_obj, (discord.VoiceChannel, discord.StageChannel)):
                target_vc = ch_obj

        if not target_vc:
            embed = discord.Embed(
                title="🎧 Voice Channel Required",
                description=(
                    "❌ **You must be in a voice channel to play music!**\n\n"
                    "👉 Please join a voice channel (e.g. **・𝗹𝗼-𝗳𝗶・** or **・𝗿𝗮𝗶-𝗳𝗮𝗺-𝗹𝗼𝘂𝗻𝗴𝗲・**) and send your command again!"
                ),
                color=config.COLOR_DANGER
            )
            embed.set_footer(text="RAI VIBES 💗 • Rythm Sound Engine", icon_url=config.RAI_ICON_URL)
            try:
                if hasattr(ctx_or_interaction, "send"):
                    await ctx_or_interaction.send(embed=embed)
                elif hasattr(ctx_or_interaction, "response"):
                    if not ctx_or_interaction.response.is_done():
                        await ctx_or_interaction.response.send_message(embed=embed, ephemeral=True)
                    else:
                        await ctx_or_interaction.followup.send(embed=embed, ephemeral=True)
            except Exception:
                pass
            return None

        # Clean up any dead/zombie voice_client before connecting
        if voice_client and not voice_client.is_connected():
            try:
                await voice_client.disconnect(force=True)
            except Exception:
                pass
            voice_client = None

        if not voice_client or not voice_client.is_connected():
            try:
                voice_client = await target_vc.connect(timeout=25.0, reconnect=True, self_deaf=False)
                print(f"[Voice Connect] Successfully connected to '{target_vc.name}' in '{guild.name}'")
            except discord.ClientException:
                voice_client = guild.voice_client
                if user_vc and voice_client and voice_client.channel != user_vc:
                    try:
                        await voice_client.move_to(user_vc)
                    except Exception:
                        pass
            except Exception as e:
                print(f"[Voice Connect Error] {e}")
                voice_client = guild.voice_client
        elif user_vc and voice_client.channel != user_vc:
            try:
                await voice_client.move_to(user_vc)
                print(f"[Voice Move] Moved RAI VIBES to {user_vc.name}")
            except Exception as e:
                print(f"[Voice Move Error] {e}")

        return voice_client or guild.voice_client

    # =========================================================================
    # COMMAND: CONTROLLER / REMOTE / PANEL
    # =========================================================================
    @commands.hybrid_command(
        name="controller",
        aliases=["remote", "panel", "player", "controls"],
        description="Open the Rythm-style interactive music controller remote."
    )
    async def controller_cmd(self, ctx: commands.Context):
        voice_client = await self.ensure_voice(ctx)
        if not voice_client:
            return

        player = self.get_or_create_player(ctx.guild)
        player.voice_client = voice_client
        player.text_channel = ctx.channel

        from utils.views import RythmControllerView
        view = RythmControllerView(player, self)
        content = view.build_content()

        if ctx.interaction:
            await ctx.interaction.response.send_message(content=content, view=view, ephemeral=True)
        else:
            await ctx.send(content=content, view=view)

    @commands.hybrid_command(
        name="controllersetup",
        aliases=["setupcontroller", "musicpanel", "playerpanel"],
        description="Deploy a permanent, persistent interactive music controller in a channel."
    )
    @commands.has_permissions(manage_channels=True)
    async def controller_setup(self, ctx: commands.Context, channel: Optional[discord.TextChannel] = None):
        target_channel = channel or ctx.channel
        player = self.get_or_create_player(ctx.guild)
        player.text_channel = target_channel

        from utils.views import MusicPlayerView
        view = MusicPlayerView(self, guild_id=ctx.guild.id)

        embed = discord.Embed(
            title="🎛️ RAI VIBES 💗 MASTER AUDIO CONTROLLER",
            description=(
                "✨ **Welcome to the Interactive Music Sanctuary!**\n\n"
                "Control playback, toggle audio filters, view lyrics, and manage the queue directly using the buttons below—**no commands needed!**\n\n"
                "✦ ───────────────────────────── ✦\n"
                "• **`⏯️` Play/Pause**: Toggle audio streaming\n"
                "• **`⏭️` Skip**: Advance to the next track\n"
                "• **`🔁` Loop**: Toggle Track Loop / Queue Repeat / Off\n"
                "• **`🔀` Shuffle**: Randomize remaining playlist tracks\n"
                "• **`⏹️` Stop**: Halt playback and clear queue\n"
                "• **`🔉 / 🔊`**: Adjust volume up or down\n"
                "• **`📜` Queue**: Browse upcoming songs with pagination\n"
                "• **`🎤` Lyrics**: Synchronized Genius lyrics on-screen\n"
                "• **`💖` Fav**: Save current track to your personal favorites\n"
                "• **`⚡ Nightcore` • `🔊 Bass Boost` • `🌌 8D Audio` • `☕ Lo-Fi`**: Audiophile Filters\n"
                "✦ ───────────────────────────── ✦\n"
                "💡 *Tip: Type `/play <song>` or click `➕` in Queue to stream any song from YouTube or Spotify!*"
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_image(url="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1200&q=80")
        embed.set_footer(text="RAI VIBES 💗 • High-Fidelity 24/7 Community Music Engine", icon_url=config.RAI_ICON_URL)

        msg = await target_channel.send(embed=embed, view=view)
        player.persistent_controller_message = msg

        # Save to persistent file so bot remembers this controller across restarts
        try:
            from pathlib import Path
            import json
            cfg_file = Path(__file__).resolve().parent.parent / "data" / "persistent_controllers.json"
            cfg_file.parent.mkdir(parents=True, exist_ok=True)
            data = {}
            if cfg_file.exists():
                with open(cfg_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            data[str(ctx.guild.id)] = {
                "channel_id": target_channel.id,
                "message_id": msg.id
            }
            with open(cfg_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save persistent controller: {e}")

        await ctx.send(f"✅ **Persistent Music Controller deployed in {target_channel.mention}!**", ephemeral=True)


    # =========================================================================
    # COMMAND: PLAY / P
    # =========================================================================
    @commands.hybrid_command(name="play", aliases=["p"], description="Play music or enqueue tracks from YouTube or Spotify.")
    @app_commands.describe(
        song="The song name, artist, or YouTube/Spotify song link to play",
        queue="Playlist URL, album link, or tracks to add directly to playback queue"
    )
    async def play(
        self,
        ctx: commands.Context,
        song: Optional[str] = None,
        *,
        queue: Optional[str] = None
    ):
        if ctx.interaction:
            try:
                await ctx.defer()
            except Exception:
                pass
        
        voice_client = await self.ensure_voice(ctx)
        if not voice_client:
            return

        player = self.get_or_create_player(ctx.guild)
        player.voice_client = voice_client
        player.text_channel = ctx.channel

        # Handle prefix compatibility & distinguish song vs queue modes
        is_queue_mode = False
        effective_query = None

        if not ctx.interaction:
            # Invoked via message prefix (e.g. !play, !p, or mention)
            effective_query = song or queue
            if song and queue:
                if song.lower() in ("queue", "q", "playlist", "pl"):
                    effective_query = queue
                    is_queue_mode = True
                elif song.lower() in ("song", "track", "s"):
                    effective_query = queue
                    is_queue_mode = False
                else:
                    # Multi-word title like: !play kannitheevu ponna
                    effective_query = f"{song} {queue}".strip()
                    is_queue_mode = False
            elif queue:
                effective_query = queue
                is_queue_mode = True
            elif effective_query:
                # If query is a Spotify playlist or album, treat as queue mode
                if is_spotify_url(effective_query) and any(x in effective_query for x in ["playlist", "album"]):
                    is_queue_mode = True
                else:
                    is_queue_mode = False
        else:
            # Invoked via slash command (/play)
            if song:
                effective_query = song
                is_queue_mode = False
            elif queue:
                effective_query = queue
                is_queue_mode = True
            else:
                effective_query = None
                is_queue_mode = False

        query = effective_query

        # If user ran /play with neither option provided
        if not query:
            if player.voice_client and player.voice_client.is_paused():
                player.voice_client.resume()
                embed = discord.Embed(
                    description="▶️ **Resumed music playback!**",
                    color=config.COLOR_SUCCESS
                )
                if ctx.interaction:
                    return await ctx.interaction.followup.send(embed=embed)
                return await ctx.send(embed=embed)
            elif player.queue and not (player.voice_client and player.voice_client.is_playing()):
                self.play_next(ctx.guild)
                embed = discord.Embed(
                    description="▶️ **Resumed playing queue!**",
                    color=config.COLOR_PRIMARY
                )
                if ctx.interaction:
                    return await ctx.interaction.followup.send(embed=embed)
                return await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    title="🎵 How to use /play",
                    description=(
                        "Choose one of the options:\n\n"
                        "• **`/play song: [name/link]`** — Search and play an individual song or track\n"
                        "• **`/play queue: [link/name]`** — Enqueue a playlist, album, or tracks directly to the queue"
                    ),
                    color=config.COLOR_PRIMARY
                )
                embed.set_footer(text="RAI VIBES 💗 Music Engine", icon_url=config.RAI_ICON_URL)
                if ctx.interaction:
                    return await ctx.interaction.followup.send(embed=embed)
                return await ctx.send(embed=embed)

        # Check queue limit
        if len(player.queue) >= config.MAX_QUEUE_SIZE:
            msg = f"⚠️ **Queue is full ({config.MAX_QUEUE_SIZE}/{config.MAX_QUEUE_SIZE} songs).** Please wait for songs to finish or remove tracks."
            if ctx.interaction:
                return await ctx.interaction.followup.send(msg, ephemeral=True)
            return await ctx.send(msg)

        # Check if Spotify or Apple Music URL
        is_sp = is_spotify_url(query)
        is_am = is_apple_music_url(query)
        if is_sp or is_am:
            source_label = "Apple Music" if is_am else "Spotify"
            resolved_tracks = await resolve_apple_music(query) if is_am else await resolve_spotify(query)
            if not resolved_tracks:
                msg = f"❌ Could not parse {source_label} link. Please ensure it is a valid track, album, or playlist."
                if ctx.interaction:
                    return await ctx.interaction.followup.send(msg, ephemeral=True)
                return await ctx.send(msg)

            if len(resolved_tracks) == 1:
                t = resolved_tracks[0]
                song_obj = await Song.create_source(t["search_query"], ctx.author, self.bot.loop)
                if not song_obj:
                    msg = f"❌ Could not find audio for {source_label} track: `{t['title']}`"
                    if ctx.interaction:
                        return await ctx.interaction.followup.send(msg, ephemeral=True)
                    return await ctx.send(msg)
                if t.get("thumbnail"):
                    song_obj.thumbnail = t["thumbnail"]
                
                is_queued = player.enqueue_track(song_obj, is_queue_mode=is_queue_mode)

                if is_queued:
                    est_sec = 0
                    if player.current:
                        cur_elapsed = int(time.time() - player.start_time) if player.start_time else 0
                        est_sec += max(0, player.current.duration - cur_elapsed)
                    for q_song in list(player.queue)[:-1]:
                        est_sec += max(0, q_song.duration)
                    est_str = time.strftime("%M:%S", time.gmtime(est_sec)) if est_sec > 0 else "Playing Next"
                    dur_str = time.strftime("%M:%S", time.gmtime(song_obj.duration)) if song_obj.duration > 0 else "Live"

                    card_title = "📥 Enqueued to Playback Queue" if is_queue_mode else "🎵 Song Added to Queue"
                    embed = discord.Embed(
                        title=card_title,
                        description=f"**[{song_obj.title}]({song_obj.webpage_url})**",
                        color=config.COLOR_PRIMARY
                    )
                    embed.set_thumbnail(url=song_obj.thumbnail or config.RAI_ICON_URL)
                    embed.add_field(name="⏱️ Track Duration", value=f"`{dur_str}`", inline=True)
                    embed.add_field(name="📍 Position in Queue", value=f"`#{len(player.queue)}`", inline=True)
                    embed.add_field(name="⏳ Estimated Time", value=f"`{est_str}`", inline=True)
                    embed.set_footer(text=f"Requested by {ctx.author.display_name} • {source_label} • RAI VIBES 💗", icon_url=ctx.author.display_avatar.url)
                    
                    if ctx.interaction:
                        sent = await ctx.interaction.followup.send(embed=embed)
                        if sent:
                            asyncio.create_task(self._auto_delete(sent, 10))
                    else:
                        sent = await ctx.send(embed=embed)
                        if sent:
                            asyncio.create_task(self._auto_delete(sent, 10))
                else:
                    if ctx.interaction:
                        sent = await ctx.interaction.followup.send(
                            embed=discord.Embed(
                                description=f"🎶 **Starting playback:** [{song_obj.title}]({song_obj.webpage_url})",
                                color=config.COLOR_PRIMARY
                            )
                        )
                        if sent:
                            asyncio.create_task(self._auto_delete(sent, 3))
            else:
                remaining_space = max(0, config.MAX_QUEUE_SIZE - len(player.queue))
                added_tracks = resolved_tracks[:remaining_space]

                is_radio = player.is_radio_playing()
                for t in added_tracks:
                    unresolved_song = Song(
                        data={
                            "title": f"{t['title']} - {t.get('artist', source_label)}",
                            "search_query": t["search_query"],
                            "thumbnail": t.get("thumbnail", ""),
                            "duration": 0,
                            "webpage_url": "https://apple.com" if is_am else "https://spotify.com"
                        },
                        requester=ctx.author,
                        source_type="apple_music" if is_am else "spotify"
                    )
                    player.queue.append(unresolved_song)

                if is_radio:
                    player.skip()
                elif not player.current and not (player.voice_client and player.voice_client.is_playing()):
                    player.play_next_song.set()

                embed = discord.Embed(
                    title=f"⚡ {source_label} Playlist / Album Enqueued!",
                    description=f"Added **{len(added_tracks)} tracks** from {source_label} to the RAI VIBES 💗 queue (Queue: `{len(player.queue)}/{config.MAX_QUEUE_SIZE}`).",
                    color=config.COLOR_PRIMARY
                )
                embed.set_thumbnail(url=resolved_tracks[0].get("thumbnail", config.RAI_ICON_URL))
                embed.set_footer(text=f"RAI VIBES 💗 • {source_label} Engine", icon_url=config.RAI_ICON_URL)
                
                if ctx.interaction:
                    sent = await ctx.interaction.followup.send(embed=embed)
                    if sent:
                        asyncio.create_task(self._auto_delete(sent, 15))
                else:
                    sent = await ctx.send(embed=embed)
                    if sent:
                        asyncio.create_task(self._auto_delete(sent, 15))
            return

        # Direct YouTube / Keyword Search
        try:
            status_msg = None
            if not ctx.interaction:
                try:
                    status_msg = await ctx.send(f"🔍 **Searching & buffering:** `{query[:60]}`...")
                except Exception:
                    pass

            is_direct_url = query.startswith("http://") or query.startswith("https://")

            # If searching by name and multiple tracks exist, ask the user which one they want to play:
            if not is_direct_url:
                results = await Song.search_multiple(query, limit=5, loop=self.bot.loop)
                if not results:
                    if status_msg:
                        try:
                            await status_msg.delete()
                        except Exception:
                            pass
                    if ctx.interaction:
                        return await ctx.interaction.followup.send(f"❌ No results found for: `{query}`", ephemeral=True)
                    return await ctx.send(f"❌ No results found for: `{query}`")

                if len(results) > 1:
                    if status_msg:
                        try:
                            await status_msg.delete()
                        except Exception:
                            pass

                    embed = discord.Embed(
                        title=f"⚡ Multiple Matches Found: \"{query[:40]}\"",
                        description="Select which version you want to play using the **dropdown** or **number buttons** below:",
                        color=config.COLOR_PRIMARY
                    )
                    embed.set_thumbnail(url=results[0].get("thumbnail") or config.RAI_ICON_URL)
                    for i, item in enumerate(results, 1):
                        dur = time.strftime("%M:%S", time.gmtime(item.get("duration", 0)))
                        embed.add_field(
                            name=f"`{i}.` {item.get('title', 'Track')[:45]}",
                            value=f"⏱️ `{dur}` • 👤 `{item.get('uploader', 'Artist')[:28]}`",
                            inline=False
                        )
                    embed.set_footer(text="Tap Track 1-5 or choose from dropdown • RAI VIBES 💗", icon_url=config.RAI_ICON_URL)

                    view = SearchSelectView(self, ctx, results, is_queue_mode=is_queue_mode)
                    if ctx.interaction:
                        view.message = await ctx.interaction.followup.send(embed=embed, view=view)
                    else:
                        view.message = await ctx.send(embed=embed, view=view)
                    return

            song_obj = await Song.create_source(query, ctx.author, self.bot.loop)
            if not song_obj:
                if status_msg:
                    try:
                        await status_msg.delete()
                    except Exception:
                        pass
                if ctx.interaction:
                    return await ctx.interaction.followup.send(f"❌ No results found for: `{query}`", ephemeral=True)
                return await ctx.send(f"❌ No results found for: `{query}`")

            is_queued = player.enqueue_track(song_obj, is_queue_mode=is_queue_mode)

            if status_msg and not is_queued:
                try:
                    await status_msg.delete()
                except Exception:
                    pass

            if is_queued:
                # Calculate estimated time until playing (Rythm Style)
                est_sec = 0
                if player.current:
                    cur_elapsed = int(time.time() - player.start_time) if player.start_time else 0
                    est_sec += max(0, player.current.duration - cur_elapsed)
                for q_song in list(player.queue)[:-1]:
                    est_sec += max(0, q_song.duration)

                est_str = time.strftime("%M:%S", time.gmtime(est_sec)) if est_sec > 0 else "Playing Next"
                dur_str = time.strftime("%M:%S", time.gmtime(song_obj.duration)) if song_obj.duration > 0 else "Live"

                card_title = "📥 Enqueued to Playback Queue" if is_queue_mode else "🎵 Song Added to Queue"
                embed = discord.Embed(
                    title=card_title,
                    description=f"**[{song_obj.title}]({song_obj.webpage_url})**",
                    color=config.COLOR_PRIMARY
                )
                embed.set_thumbnail(url=song_obj.thumbnail or config.RAI_ICON_URL)
                embed.add_field(name="⏱️ Track Duration", value=f"`{dur_str}`", inline=True)
                embed.add_field(name="📍 Position in Queue", value=f"`#{len(player.queue)}`", inline=True)
                embed.add_field(name="⏳ Estimated Time", value=f"`{est_str}`", inline=True)
                embed.set_footer(text=f"Requested by {ctx.author.display_name} • RAI VIBES 💗", icon_url=ctx.author.display_avatar.url)
                
                if status_msg:
                    try:
                        await status_msg.delete()
                    except Exception:
                        pass

                if ctx.interaction:
                    sent = await ctx.interaction.followup.send(embed=embed)
                    if sent:
                        asyncio.create_task(self._auto_delete(sent, 10))
                else:
                    sent = await ctx.send(embed=embed)
                    if sent:
                        asyncio.create_task(self._auto_delete(sent, 10))
            else:
                if status_msg:
                    try:
                        await status_msg.delete()
                    except Exception:
                        pass
                if ctx.interaction:
                    sent = await ctx.interaction.followup.send(
                        embed=discord.Embed(
                            description=f"🎶 **Starting playback:** [{song_obj.title}]({song_obj.webpage_url})",
                            color=config.COLOR_PRIMARY
                        )
                    )
                    if sent:
                        asyncio.create_task(self._auto_delete(sent, 3))

        except Exception as e:
            if ctx.interaction:
                await ctx.interaction.followup.send(f"❌ Error while queuing track: `{e}`", ephemeral=True)
            else:
                await ctx.send(f"❌ Error while queuing track: `{e}`")


    # =========================================================================
    # COMMAND: PAUSE & RESUME
    # =========================================================================
    @commands.hybrid_command(name="pause", description="Pause current music playback.")
    async def pause(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player or not player.is_connected or not player.voice_client.is_playing():
            return await ctx.send("❌ Nothing is currently playing.", ephemeral=True)
        player.pause(ctx.author)
        await ctx.send("⏸️ **Playback paused.** Use `!resume` or `/resume` to continue.")

    @commands.hybrid_command(name="resume", aliases=["unpause"], description="Resume paused music playback.")
    async def resume(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player or not player.is_connected or not player.voice_client.is_paused():
            return await ctx.send("❌ Audio is not paused.", ephemeral=True)
        player.resume()
        await ctx.send("▶️ **Playback resumed!**")

    # =========================================================================
    # COMMAND: SKIP
    # =========================================================================
    @commands.hybrid_command(name="skip", aliases=["s", "next"], description="Skip the currently playing song.")
    async def skip(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player or not player.is_connected or not (player.voice_client.is_playing() or player.voice_client.is_paused()):
            return await ctx.send("❌ Nothing is playing to skip.", ephemeral=True)
        
        current_title = player.current.title if player.current else "Track"
        player.skip()
        await ctx.send(f"⏭️ **Skipped:** `{current_title}`")

    # =========================================================================
    # COMMAND: SKIPTO / JUMP
    # =========================================================================
    @commands.command(name="skipto", aliases=["jump"])
    async def skipto(self, ctx: commands.Context, index: int):
        player = self.get_player(ctx.guild.id)
        if not player or not player.queue:
            return await ctx.send("❌ Queue is empty.", ephemeral=True)
        if not 1 <= index <= len(player.queue):
            return await ctx.send(f"❌ Invalid track position. Choose between 1 and {len(player.queue)}.", ephemeral=True)

        for _ in range(index - 1):
            player.queue.popleft()

        target_song = player.queue[0].title if player.queue else "Track"
        player.skip()
        await ctx.send(f"⏭️ **Skipped directly to track #{index}:** `{target_song}`")

    # =========================================================================
    # COMMAND: JOIN / SUMMON
    # =========================================================================
    @commands.hybrid_command(name="join", aliases=["summon", "connect", "j"], description="Summon RAI VIBES 💗 to your active voice channel.")
    async def join(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ Please connect to a voice channel first!", ephemeral=True)
        
        target_vc = ctx.author.voice.channel
        vc = await self.ensure_voice(ctx)
        if vc and vc.is_connected():
            player = self.get_or_create_player(ctx.guild)
            player.voice_client = vc
            player.text_channel = ctx.channel
            await ctx.send(f"🎧 **Joined:** {target_vc.mention}! Ready to play music.")
        else:
            await ctx.send("❌ Could not connect to your voice channel.", ephemeral=True)

    # =========================================================================
    # COMMAND: STOP / DISCONNECT
    # =========================================================================
    @commands.hybrid_command(name="stop", aliases=["leave", "disconnect", "dc"], description="Stop music, clear queue, and leave voice.")
    async def stop(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player or not player.is_connected:
            return await ctx.send("❌ RAI VIBES 💗 is not in a voice channel.", ephemeral=True)
        
        await player.stop()
        await ctx.send("⏹️ **Disconnected and cleared the queue.**")

    # =========================================================================
    # COMMAND: NOW PLAYING / NP
    # =========================================================================
    @commands.hybrid_command(name="nowplaying", aliases=["np", "current"], description="Display the currently playing song with interactive controls.")
    async def nowplaying(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player or not player.current:
            return await ctx.send("❌ No track currently playing.", ephemeral=True)

        embed = player.build_now_playing_embed()
        view = MusicPlayerView(self, ctx.guild.id)

        card_file = None
        try:
            from utils.canvas import generate_nowplaying_card
            import urllib.request
            thumb_bytes = None
            if player.current.thumbnail:
                try:
                    req = urllib.request.Request(player.current.thumbnail, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=3) as r:
                        thumb_bytes = r.read()
                except Exception:
                    pass

            elapsed = int(time.time() - player.start_time) if player.start_time else 0
            req_name = player.current.requester.display_name if player.current.requester else "Community"
            card_buf = generate_nowplaying_card(
                thumbnail_bytes=thumb_bytes,
                title=player.current.title,
                artist=player.current.uploader or "Artist",
                duration_sec=player.current.duration or 0,
                elapsed_sec=elapsed,
                requester_name=req_name
            )
            card_file = discord.File(fp=card_buf, filename="nowplaying.png")
            embed.set_image(url="attachment://nowplaying.png")
        except Exception:
            pass

        if card_file:
            await ctx.send(embed=embed, view=view, file=card_file)
        else:
            await ctx.send(embed=embed, view=view)

    # =========================================================================
    # COMMAND: QUEUE / Q
    # =========================================================================
    @commands.hybrid_command(name="queue", aliases=["q"], description="Display upcoming songs in the queue.")
    async def queue(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player or (not player.current and not player.queue):
            return await ctx.send("📜 **The queue is currently empty.** Add tracks with `!play <song>` or `/play`!", ephemeral=True)

        embed = player.build_queue_embed(page=0)
        view = QueuePaginationView(player, music_cog=self, current_page=0)
        await ctx.send(embed=embed, view=view)

    # =========================================================================
    # COMMAND: VOLUME
    # =========================================================================
    @commands.hybrid_command(name="volume", aliases=["vol", "v"], description="Adjust RAI VIBES 💗 player volume (0% - 200%).")
    @app_commands.describe(level="Volume level from 0 to 200 (Super Boost)")
    async def volume(self, ctx: commands.Context, level: int):
        player = self.get_player(ctx.guild.id)
        if not player or not player.is_connected:
            return await ctx.send("❌ RAI VIBES 💗 is not connected to a voice channel.", ephemeral=True)

        if not 0 <= level <= 200:
            return await ctx.send("❌ Volume must be between 0 and 200.", ephemeral=True)

        player.set_volume(level)
        boost_indicator = " 🔥 *(Super Boost)*" if level > 100 else ""
        await ctx.send(f"🔊 **Volume adjusted to {level}%!**{boost_indicator}")

    # =========================================================================
    # COMMAND: LOOP / REPEAT
    # =========================================================================
    @commands.hybrid_command(name="loop", aliases=["repeat"], description="Toggle repeat mode: off, track, or queue.")
    @app_commands.choices(mode=[
        app_commands.Choice(name="Disable Loop (Off)", value="off"),
        app_commands.Choice(name="Repeat Current Track", value="track"),
        app_commands.Choice(name="Repeat Entire Queue", value="queue"),
    ])
    async def loop(self, ctx: commands.Context, mode: Optional[app_commands.Choice[str]] = None):
        player = self.get_player(ctx.guild.id)
        if not player:
            return await ctx.send("❌ RAI VIBES 💗 is not currently active.", ephemeral=True)

        if mode is None:
            if player.loop_mode == "off":
                player.loop_mode = "track"
            elif player.loop_mode == "track":
                player.loop_mode = "queue"
            else:
                player.loop_mode = "off"
        else:
            player.loop_mode = mode.value

        await ctx.send(f"🔁 **Loop mode set to:** `{player.loop_mode.upper()}`")

    # =========================================================================
    # COMMAND: SHUFFLE
    # =========================================================================
    @commands.hybrid_command(name="shuffle", aliases=["sh"], description="Shuffle songs in the current queue.")
    async def shuffle(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player or len(player.queue) < 2:
            return await ctx.send("❌ Need at least 2 songs in queue to shuffle.", ephemeral=True)

        player.shuffle()
        await ctx.send(f"🔀 **Shuffled {len(player.queue)} songs in the queue!**")

    # =========================================================================
    # COMMAND: REMOVE
    # =========================================================================
    @commands.command(name="remove", aliases=["rm"])
    async def remove(self, ctx: commands.Context, index: int):
        player = self.get_player(ctx.guild.id)
        if not player or not player.queue:
            return await ctx.send("❌ Queue is empty.", ephemeral=True)

        if not 1 <= index <= len(player.queue):
            return await ctx.send(f"❌ Invalid position. Choose between 1 and {len(player.queue)}.", ephemeral=True)

        removed_song = player.queue[index - 1]
        del player.queue[index - 1]
        await ctx.send(f"🗑️ **Removed track #{index}:** `{removed_song.title}`")

    # =========================================================================
    # COMMAND: CLEAR QUEUE
    # =========================================================================
    @commands.command(name="clearqueue", aliases=["cq", "emptyqueue", "qclear"])
    async def clearqueue(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player or not player.queue:
            return await ctx.send("❌ Queue is already empty.", ephemeral=True)

        count = len(player.queue)
        player.queue.clear()
        await ctx.send(f"🗑️ **Cleared {count} tracks from the queue.**")

    # =========================================================================
    # COMMAND: REPLAY / RESTART
    # =========================================================================
    @commands.command(name="replay", aliases=["restart"])
    async def replay(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player or not player.current or not player.voice_client:
            return await ctx.send("❌ No track is currently playing.", ephemeral=True)

        player.start_time = time.time()
        await player.restart_current_with_filters()
        await ctx.send(f"🔄 **Replaying:** `{player.current.title}`")

    # =========================================================================
    # COMMAND: SEEK
    # =========================================================================
    @commands.command(name="seek")
    async def seek(self, ctx: commands.Context, timestamp: str):
        player = self.get_player(ctx.guild.id)
        if not player or not player.current or not player.voice_client:
            return await ctx.send("❌ No track is currently playing.", ephemeral=True)

        seconds = 0
        try:
            if ":" in timestamp:
                parts = [int(p) for p in timestamp.split(":")]
                if len(parts) == 2:
                    seconds = parts[0] * 60 + parts[1]
                elif len(parts) == 3:
                    seconds = parts[0] * 3600 + parts[1] * 60 + parts[2]
            else:
                seconds = int(timestamp)
        except Exception:
            return await ctx.send("❌ Invalid format! Use `mm:ss` (e.g. `1:30`) or total seconds.", ephemeral=True)

        if player.current.duration > 0 and seconds > player.current.duration:
            return await ctx.send(f"❌ Timestamp exceeds song duration ({time.strftime('%M:%S', time.gmtime(player.current.duration))}).", ephemeral=True)

        player.start_time = time.time() - seconds
        await player.restart_current_with_filters()
        seek_str = time.strftime('%M:%S', time.gmtime(seconds))
        await ctx.send(f"⏩ **Seeked to:** `{seek_str}`")

    # =========================================================================
    # COMMAND: AUTOPLAY / SMART RADIO
    # =========================================================================
    @commands.hybrid_command(name="autoplay", description="Toggle smart endless autoplay when the queue runs out.")
    @app_commands.describe(status="Choose whether to enable or disable autoplay ('on' or 'off')")
    async def autoplay(self, ctx: commands.Context, status: Optional[str] = None):
        player = self.get_player(ctx.guild.id)
        if not player:
            return await ctx.send("❌ Player not initialized.", ephemeral=True)

        if status:
            val = status.lower().strip() in ["on", "enable", "true", "yes", "1"]
            player.autoplay = val
        else:
            player.autoplay = not player.autoplay

        state_str = "ENABLED 📻" if player.autoplay else "DISABLED ⏹️"
        color = config.COLOR_PRIMARY if player.autoplay else config.COLOR_DARK
        embed = discord.Embed(
            title=f"📻 Autoplay / Smart Radio: {state_str}",
            description=(
                "When your queue is empty, RAI VIBES will automatically queue recommended tracks based on your taste!"
                if player.autoplay else
                "Autoplay disabled. Music will pause when the queue finishes."
            ),
            color=color
        )
        embed.set_footer(text="RAI VIBES 💗 • Intelligent Music Engine", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="search", description="Search YouTube for top 5 matches and pick with interactive buttons.")
    @app_commands.describe(query="Song title or artist to search for")
    async def search(self, ctx: commands.Context, *, query: str):
        if ctx.interaction:
            try:
                await ctx.defer()
            except Exception:
                pass

        voice_client = await self.ensure_voice(ctx)
        if not voice_client:
            return

        embed = discord.Embed(
            description=f"🔎 **Searching top results for:** `{query}`...",
            color=config.COLOR_PRIMARY
        )
        msg = await (ctx.interaction.followup.send(embed=embed) if ctx.interaction else ctx.send(embed=embed))

        results = await Song.search_multiple(query, max_results=5, loop=self.bot.loop)
        if not results:
            err_embed = discord.Embed(
                description=f"❌ No search results found for `{query}`.",
                color=config.COLOR_ERROR
            )
            return await msg.edit(embed=err_embed)

        search_embed = discord.Embed(
            title=f"🔎 TOP SEARCH RESULTS • '{query[:30]}'",
            description="Select a track from the dropdown menu or tap a button below:",
            color=config.COLOR_PRIMARY
        )
        for i, item in enumerate(results):
            dur = time.strftime("%M:%S", time.gmtime(item.get("duration", 0)))
            search_embed.add_field(
                name=f"{i+1}. {item.get('title', 'Unknown')[:48]}",
                value=f"⏱️ `{dur}` • 👤 `{item.get('uploader', 'Artist')[:25]}`",
                inline=False
            )
        search_embed.set_footer(text="RAI VIBES 💗 • Music Picker", icon_url=config.RAI_ICON_URL)

        view = SearchResultView(self, ctx, results, message=msg)
        await msg.edit(embed=search_embed, view=view)

    @commands.command(name="sleeptimer", aliases=["sleep"])
    async def sleeptimer(self, ctx: commands.Context, minutes: int):
        if minutes <= 0 or minutes > 240:
            return await ctx.send("❌ Sleep timer must be between 1 and 240 minutes.", ephemeral=True)

        player = self.get_player(ctx.guild.id)
        if not player or not player.is_connected:
            return await ctx.send("❌ Bot is not currently connected to voice.", ephemeral=True)

        embed = discord.Embed(
            title="🌙 AUDIO SLEEP TIMER ACTIVATED",
            description=f"Music will gently stop in **{minutes} minutes**.\nRest easy and sweet dreams! 💤",
            color=0x9B59B6
        )
        embed.set_footer(text="RAI VIBES 💗 • Sleep Well", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

        async def _sleep_countdown():
            await asyncio.sleep(minutes * 60)
            p = self.get_player(ctx.guild.id)
            if p and p.voice_client and p.voice_client.is_connected():
                p.queue.clear()
                p.mode_247 = False
                await p.voice_client.disconnect()
                if p.text_channel:
                    try:
                        await p.text_channel.send("🌙 **Sleep timer expired.** Playback stopped. Goodnight! 💤")
                    except Exception:
                        pass

        self.bot.loop.create_task(_sleep_countdown())

    @commands.command(name="history", aliases=["recent", "recentlyplayed"])
    async def history_cmd(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player or not player.history:
            return await ctx.send("ℹ️ No recently played songs recorded yet for this session.", ephemeral=True)

        embed = discord.Embed(
            title="🕒 RECENTLY PLAYED MUSIC HISTORY",
            description=f"Showing the last **{min(15, len(player.history))}** tracks played in this server.\nUse the dropdown below to instantly re-queue any track!",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="RAI VIBES 💗 • Playback History Engine", icon_url=config.RAI_ICON_URL)

        for i, s in enumerate(reversed(list(player.history)[-15:]), 1):
            dur = time.strftime("%M:%S", time.gmtime(s.duration)) if s.duration else "Live"
            embed.add_field(
                name=f"{i}. {s.title[:65]}",
                value=f"⏱️ `{dur}` • 👤 `{s.uploader[:25] if s.uploader else 'Artist'}` • 📥 Requested by `{s.requester.display_name if s.requester else 'Community'}`",
                inline=False
            )

        view = HistoryRequeueView(self, player)
        await ctx.send(embed=embed, view=view)

    @commands.command(name="artist")
    async def artist_cmd(self, ctx: commands.Context, *, name: str):
        if ctx.interaction:
            await ctx.defer()

        import urllib.request, urllib.parse, json
        encoded = urllib.parse.quote(name)
        url = f"https://itunes.apple.com/search?term={encoded}&entity=song&limit=5"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception:
            data = None

        if not data or not data.get("results"):
            msg = f"❌ No artist or tracks found matching `{name}`."
            return await (ctx.interaction.followup.send(msg) if ctx.interaction else ctx.send(msg))

        results = data["results"]
        first = results[0]
        artist_name = first.get("artistName", name)
        genre = first.get("primaryGenreName", "Pop / Hip-Hop / Indie")
        artwork = first.get("artworkUrl100", "").replace("100x100bb", "600x600bb")

        embed = discord.Embed(
            title=f"🎤 ARTIST SPOTLIGHT • {artist_name.upper()}",
            description=f"🏷️ **Primary Genre:** `{genre}`\n🎧 **Verified Profile & Discography**\n\n### 🔥 Top 5 Popular Songs:",
            color=config.COLOR_PRIMARY
        )
        if artwork:
            embed.set_thumbnail(url=artwork)
        embed.set_footer(text="RAI VIBES 💗 • Music Discovery Studio", icon_url=config.RAI_ICON_URL)

        for i, track in enumerate(results, 1):
            track_name = track.get("trackName", "Track")
            album_name = track.get("collectionName", "Single")
            preview_url = track.get("previewUrl", "")
            val = f"💿 Album: *{album_name}*"
            if preview_url:
                val += f"\n🔗 [Audio Preview]({preview_url})"
            embed.add_field(
                name=f"{i}. {track_name}",
                value=val,
                inline=False
            )

        await (ctx.interaction.followup.send(embed=embed) if ctx.interaction else ctx.send(embed=embed))

    @commands.hybrid_command(name="visualizer", aliases=["viz"], description="Display live audio waveform visualizer for the current track.")
    async def visualizer_cmd(self, ctx: commands.Context):
        player = self.get_player(ctx.guild.id)
        if not player or not player.current:
            return await ctx.send("❌ No track currently streaming.", ephemeral=True)

        bars = [" ▂▃▅▆▇", "  ▂▄▆█", " ▃▅▇█▇", " ▂▃▄▅▆", "  ▃▅▆█", " ▂▄▅▇█"]
        wave = " ".join(random.choice(bars) for _ in range(8))
        elapsed = int(time.time() - player.start_time) if player.start_time else 0
        dur_str = time.strftime("%M:%S", time.gmtime(elapsed))
        tot_str = time.strftime("%M:%S", time.gmtime(player.current.duration)) if player.current.duration else "Live"

        embed = discord.Embed(
            title=f"📊 ┊ 𝐀𝐔𝐃𝐈𝐎  𝐒𝐏𝐄𝐂𝐓𝐑𝐔𝐌: {player.current.title[:45]}",
            description=(
                f"```fix\n"
                f"[{wave}]\n"
                f"[{wave}]\n"
                f"```\n"
                f"⏱️ **Timestamp:** `{dur_str} / {tot_str}`\n"
                f"🎛️ **Sample Rate:** `48,000 Hz` • **Channels:** `2 (Stereo)` • **Codec:** `Opus / PCM`\n"
                f"🔊 **Volume Output:** `{player.volume}%`"
            ),
            color=0x00F2FE
        )
        embed.set_thumbnail(url=player.current.thumbnail or config.RAI_ICON_URL)
        embed.set_footer(text="RAI VIBES 💗 • Real-Time DSP Visualizer", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="import", aliases=["importer"], description="Batch import any public Spotify or YouTube playlist into queue.")
    @app_commands.describe(url="Spotify or YouTube playlist link")
    async def import_cmd(self, ctx: commands.Context, url: str):
        if ctx.interaction:
            await ctx.defer()

        voice_client = await self.ensure_voice(ctx)
        if not voice_client:
            return await ctx.send("❌ Please connect to a voice channel first!", ephemeral=True)

        player = self.get_or_create_player(ctx.guild)
        player.voice_client = voice_client

        if is_spotify_url(url):
            tracks = await resolve_spotify(url)
            if not tracks:
                return await ctx.send("❌ Could not load Spotify playlist. Ensure it is public.")

            batch = tracks[:25]
            added = 0
            for t in batch:
                s = await Song.create_source(t["search_query"], ctx.author, self.bot.loop)
                if s:
                    player.enqueue_track(s, is_queue_mode=True)
                    added += 1

            embed = discord.Embed(
                title="📥 ┊ 𝐒𝐏𝐎𝐓𝐈𝐅𝐘  𝐏𝐋𝐀𝐘𝐋𝐈𝐒𝐓  𝐈𝐌𝐏𝐎𝐑𝐓𝐄𝐃",
                description=f"✅ Enqueued **{added} tracks** into queue for {ctx.author.mention}!",
                color=0x1DB954
            )
            embed.set_footer(text="RAI VIBES 💗 • Spotify Importer", icon_url=config.RAI_ICON_URL)
            await (ctx.interaction.followup.send(embed=embed) if ctx.interaction else ctx.send(embed=embed))
        else:
            await self.play(ctx, queue=url)


class HistorySelect(Select):
    def __init__(self, cog, player: GuildMusicPlayer, history_list: list):
        self.cog = cog
        self.player = player
        options = []
        for i, s in enumerate(reversed(history_list[-15:])):
            title = s.title[:90]
            options.append(discord.SelectOption(
                label=f"{i+1}. {title}"[:100],
                value=str(i),
                description=f"By {s.uploader}"[:100] if s.uploader else "Music Stream",
                emoji="🎵"
            ))
        super().__init__(placeholder="Select a recently played song to re-queue...", min_values=1, max_values=1, options=options)
        self.history_items = list(reversed(history_list[-15:]))

    async def callback(self, interaction: discord.Interaction):
        idx = int(self.values[0])
        song = self.history_items[idx]
        user_vc = getattr(getattr(interaction.user, "voice", None), "channel", None)
        if not user_vc:
            return await interaction.response.send_message("❌ Please join a voice channel first!", ephemeral=True)

        await interaction.response.defer()
        vc = await self.cog.ensure_voice(interaction)
        if not vc:
            return await interaction.followup.send("❌ Could not connect to voice channel.", ephemeral=True)

        song_obj = await Song.create_source(song.webpage_url or song.title, interaction.user, self.cog.bot.loop)
        if song_obj:
            is_queued = self.player.enqueue_track(song_obj)
            desc = f"📥 Re-queued: **[{song_obj.title}]({song_obj.webpage_url})**" if is_queued else f"🎶 Now streaming: **[{song_obj.title}]({song_obj.webpage_url})**"
            await interaction.followup.send(embed=discord.Embed(description=desc, color=config.COLOR_PRIMARY))
        else:
            await interaction.followup.send("❌ Could not re-queue that track.", ephemeral=True)


class HistoryRequeueView(View):
    def __init__(self, cog, player: GuildMusicPlayer):
        super().__init__(timeout=120)
        self.add_item(HistorySelect(cog, player, list(player.history)))


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))


