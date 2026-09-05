import os
import sys
import re
import asyncio
import functools
import random
import time
from collections import deque
from typing import Optional, List, Dict, Any

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import Select, View, Button
import yt_dlp

import config
from utils.ffmpeg_setup import get_ffmpeg_executable
from utils.spotify import is_spotify_url, resolve_spotify
from utils.views import MusicPlayerView, QueuePaginationView
from utils.filters import get_filter_string

# Silence yt-dlp bug reports and setup high quality audio extractor
yt_dlp.utils.bug_reports_message = lambda *args, **kargs: ""

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "extractaudio": True,
    "audioformat": "mp3",
    "outtmpl": "%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "extractor_args": {
        "youtube": {
            "player_client": ["android", "ios", "web_embedded", "mweb"]
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
            to_search = f"ytsearch5:{query_str}"

        try:
            partial_extract = functools.partial(
                ytdl.extract_info,
                to_search,
                download=False,
                process=True
            )
            data = await loop.run_in_executor(None, partial_extract)
        except Exception as e:
            # Fallback to SoundCloud if YouTube blocks search
            if not is_url:
                try:
                    sc_extract = functools.partial(
                        ytdl.extract_info,
                        f"scsearch5:{query_str}",
                        download=False,
                        process=True
                    )
                    data = await loop.run_in_executor(None, sc_extract)
                except Exception:
                    data = None
            else:
                data = None

        if data is None:
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

        return cls(data, requester=requester, source_type="youtube")

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
    """Dropdown selector for /search results."""
    def __init__(self, music_cog, ctx, results: List[dict]):
        super().__init__(timeout=45)
        self.music_cog = music_cog
        self.ctx = ctx
        self.results = results

        options = []
        for i, item in enumerate(results):
            dur = time.strftime("%M:%S", time.gmtime(item.get("duration", 0)))
            title = item.get("title", f"Track {i+1}")[:80]
            options.append(discord.SelectOption(
                label=f"{i+1}. {title[:50]}",
                description=f"Duration: {dur} • {item.get('uploader', 'Artist')[:35]}",
                value=str(i)
            ))

        select = Select(placeholder="⚡ Select a track to play...", options=options)
        select.callback = self.select_callback
        self.add_item(select)

    async def select_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.ctx.author.id:
            return await interaction.response.send_message("❌ This search menu belongs to another user.", ephemeral=True)

        selected_idx = int(interaction.data["values"][0])
        selected_data = self.results[selected_idx]

        voice_client = await self.music_cog.ensure_voice(interaction)
        if not voice_client:
            return

        player = self.music_cog.get_or_create_player(interaction.guild)
        player.voice_client = voice_client
        player.text_channel = interaction.channel

        song = Song(selected_data, requester=interaction.user, source_type="youtube")
        player.queue.append(song)

        embed = discord.Embed(
            title="⚡ Track Selected & Enqueued",
            description=f"[{song.title}]({song.webpage_url})",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=song.thumbnail)
        embed.add_field(name="Position in Queue", value=f"`#{len(player.queue)}`" if player.current else "`Now Playing`", inline=True)
        embed.add_field(name="Requested By", value=interaction.user.mention, inline=True)
        embed.set_footer(text="RAI VIBES 💗 Music Engine", icon_url=config.RAI_ICON_URL)

        await interaction.response.edit_message(content=None, embed=embed, view=None)


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

    def set_volume(self, val: int):
        self.volume = max(0, min(200, val))
        if self.current_source and isinstance(self.current_source, discord.PCMVolumeTransformer):
            self.current_source.volume = self.volume / 100.0

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

    def build_queue_embed(self, page: int = 0, per_page: int = 10) -> discord.Embed:
        embed = discord.Embed(
            title=f"📜 RAI VIBES 💗 • Active Queue ({len(self.queue)}/{config.MAX_QUEUE_SIZE} Tracks)",
            color=config.COLOR_PRIMARY
        )
        embed.set_author(name="RAI VIBES 💗", icon_url=config.RAI_ICON_URL)

        if self.current:
            embed.description = f"**Currently Playing:**\n[{self.current.title}]({self.current.webpage_url}) | Requested by: {self.current.requester.mention}\n\n**Up Next:**"
        else:
            embed.description = "Queue is empty."

        if not self.queue:
            embed.add_field(name="No upcoming tracks", value="Add more tracks using `/play <song or link>`!", inline=False)
            return embed

        total_pages = max(1, (len(self.queue) + per_page - 1) // per_page)
        page = max(0, min(page, total_pages - 1))
        start = page * per_page
        end = start + per_page
        page_songs = list(self.queue)[start:end]

        lines = []
        for i, song in enumerate(page_songs, start=start + 1):
            dur_str = time.strftime("%M:%S", time.gmtime(song.duration)) if song.duration > 0 else "Live"
            lines.append(f"`{i}.` [{song.title[:45]}]({song.webpage_url}) • `[{dur_str}]` • {song.requester.mention}")

        embed.add_field(name=f"Page {page + 1}/{total_pages} ({len(self.queue)} total songs)", value="\n".join(lines), inline=False)
        embed.set_footer(text=f"RAI VIBES 💗 Loop: {self.loop_mode.upper()} • Volume: {self.volume}% • Max Capacity: {config.MAX_QUEUE_SIZE}", icon_url=config.RAI_ICON_URL)
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

        before_opt = f"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {elapsed} -nostdin -probesize 10M -analyzeduration 0"
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
            self.current_source = discord.PCMVolumeTransformer(raw_source, volume=self.volume / 100.0)
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
                    self.current = None
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

            if not song.url:
                try:
                    resolved_song = await Song.create_source(song.data.get("search_query", song.title), song.requester, self.bot.loop)
                    if not resolved_song:
                        if self.text_channel:
                            await self.text_channel.send(f"⚠️ Could not stream `{song.title}`. Skipping.")
                        continue
                    song.url = resolved_song.url
                    song.webpage_url = resolved_song.webpage_url
                    song.duration = resolved_song.duration
                    song.thumbnail = resolved_song.thumbnail or song.thumbnail
                    song.uploader = resolved_song.uploader
                except Exception as e:
                    if self.text_channel:
                        await self.text_channel.send(f"⚠️ Error loading audio for `{song.title}`: {e}")
                    continue

            def after_playing(err):
                if err:
                    print(f"[RAI VIBES 💗 Audio Error] {err}")
                if not self.is_restarting_for_filters:
                    self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

            # Ensure voice client is connected before playing (Anchored to ✨ Lo-Fi Chillroom)
            if not self.voice_client or not self.voice_client.is_connected():
                lofi_vc = discord.utils.get(self.guild.voice_channels, name="✨ Lo-Fi Chillroom") or self.guild.get_channel(1545781986193309789)
                target_vc = lofi_vc or (self.guild.voice_channels[0] if self.guild.voice_channels else None)

                if target_vc:
                    try:
                        await target_vc.connect(timeout=20.0, reconnect=True, self_deaf=True)
                    except Exception:
                        pass

                # If still not connected, wait for connection
                if not self.voice_client or not self.voice_client.is_connected():
                    self.queue.appendleft(song)
                    self.current = None
                    await self.wait_for_voice()
                    continue

            try:
                # Ensure fresh streaming URL
                stream_url = song.url
                if not stream_url or "googlevideo.com" in stream_url:
                    try:
                        fresh_info = await self.bot.loop.run_in_executor(None, functools.partial(ytdl.extract_info, song.webpage_url, download=False, process=True))
                        if fresh_info:
                            stream_url = fresh_info.get("url") or stream_url
                    except Exception:
                        pass

                filter_args = get_filter_string(self.active_filters, self.custom_speed)
                ffmpeg_opt = f"-vn -bufsize 4096k -threads 2 {filter_args}".strip()

                raw_source = discord.FFmpegPCMAudio(
                    stream_url,
                    executable=ffmpeg_bin,
                    before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin -probesize 10M -analyzeduration 0",
                    options=ffmpeg_opt
                )
                self.current_source = discord.PCMVolumeTransformer(raw_source, volume=self.volume / 100.0)
                self.start_time = time.time()
                if self.voice_client and self.voice_client.is_connected():
                    if self.voice_client.is_playing() or self.voice_client.is_paused():
                        self.voice_client.stop()
                        await asyncio.sleep(0.15)
                    self.voice_client.play(self.current_source, after=after_playing)
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

    async def wait_for_song(self):
        while not self.queue:
            await asyncio.sleep(1)

    async def wait_for_voice(self):
        while not self.voice_client or not self.voice_client.is_connected():
            lofi_vc = discord.utils.get(self.guild.voice_channels, name="✨ Lo-Fi Chillroom") or self.guild.get_channel(1545781986193309789)
            target_vc = lofi_vc or (self.guild.voice_channels[0] if self.guild.voice_channels else None)
            if target_vc:
                try:
                    await target_vc.connect(timeout=20.0, reconnect=True, self_deaf=True)
                    return
                except Exception:
                    pass
            await asyncio.sleep(1.5)


class Music(commands.Cog):
    """RAI VIBES 💗 Music System - The Ultimate High-Performance Sound Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.players: Dict[int, GuildMusicPlayer] = {}

    def get_player(self, guild_id: int) -> Optional[GuildMusicPlayer]:
        return self.players.get(guild_id)

    def get_or_create_player(self, guild: discord.Guild) -> GuildMusicPlayer:
        if guild.id not in self.players:
            player = GuildMusicPlayer(self, guild)
            self.players[guild.id] = player
            player.audio_task = self.bot.loop.create_task(player.player_loop())
        return self.players[guild.id]

    async def ensure_voice(self, ctx_or_interaction) -> Optional[discord.VoiceClient]:
        """Ensures the bot is connected to voice without bouncing or reconnecting unnecessarily."""
        guild = ctx_or_interaction.guild
        voice_client = guild.voice_client

        # If already connected, return existing voice client immediately
        if voice_client is not None and voice_client.is_connected():
            return voice_client

        # Determine target voice channel (User's active VC > Lo-Fi Chillroom > First VC)
        author = getattr(ctx_or_interaction, "author", None) or getattr(ctx_or_interaction, "user", None)
        user_vc = getattr(getattr(author, "voice", None), "channel", None)
        lofi_vc = discord.utils.get(guild.voice_channels, name="✨ Lo-Fi Chillroom") or guild.get_channel(1545781986193309789)
        target_vc = user_vc or lofi_vc or (guild.voice_channels[0] if guild.voice_channels else None)

        if not target_vc:
            if hasattr(ctx_or_interaction, "send"):
                await ctx_or_interaction.send("❌ Please join a voice channel first!", ephemeral=True)
            return None

        try:
            voice_client = await target_vc.connect(timeout=20.0, reconnect=True, self_deaf=True)
        except Exception as e:
            print(f"[Voice Connect Error] {e}")
            voice_client = guild.voice_client

        return voice_client or guild.voice_client

    # =========================================================================
    # COMMAND: PLAY / P
    # =========================================================================
    @commands.hybrid_command(name="play", aliases=["p"], description="Play music from YouTube or Spotify (link or search name).")
    @app_commands.describe(query="The song name, YouTube URL, or Spotify link to play")
    async def play(self, ctx: commands.Context, *, query: str):
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

        # Check queue limit
        if len(player.queue) >= config.MAX_QUEUE_SIZE:
            msg = f"⚠️ **Queue is full ({config.MAX_QUEUE_SIZE}/{config.MAX_QUEUE_SIZE} songs).** Please wait for songs to finish or remove tracks."
            if ctx.interaction:
                return await ctx.interaction.followup.send(msg, ephemeral=True)
            return await ctx.send(msg)

        # Check if Spotify URL
        if is_spotify_url(query):
            spotify_tracks = await resolve_spotify(query)
            if not spotify_tracks:
                if ctx.interaction:
                    return await ctx.interaction.followup.send("❌ Could not parse Spotify link. Please ensure it is a valid track, album, or playlist.", ephemeral=True)
                return await ctx.send("❌ Could not parse Spotify link. Please ensure it is a valid track, album, or playlist.")

            if len(spotify_tracks) == 1:
                t = spotify_tracks[0]
                song = await Song.create_source(t["search_query"], ctx.author, self.bot.loop)
                if not song:
                    if ctx.interaction:
                        return await ctx.interaction.followup.send(f"❌ Could not find audio for Spotify track: `{t['title']}`", ephemeral=True)
                    return await ctx.send(f"❌ Could not find audio for Spotify track: `{t['title']}`")
                if t.get("thumbnail"):
                    song.thumbnail = t["thumbnail"]
                
                is_currently_playing = bool(player.current and player.voice_client and (player.voice_client.is_playing() or player.voice_client.is_paused()))
                player.queue.append(song)

                if is_currently_playing:
                    # Calculate estimated time until playing
                    est_sec = 0
                    if player.current:
                        cur_elapsed = int(time.time() - player.start_time) if player.start_time else 0
                        est_sec += max(0, player.current.duration - cur_elapsed)
                    for q_song in list(player.queue)[:-1]:
                        est_sec += max(0, q_song.duration)
                    est_str = time.strftime("%M:%S", time.gmtime(est_sec)) if est_sec > 0 else "Playing Next"
                    dur_str = time.strftime("%M:%S", time.gmtime(song.duration)) if song.duration > 0 else "Live"

                    embed = discord.Embed(
                        title="🎵 Added to queue",
                        description=f"**[{song.title}]({song.webpage_url})**",
                        color=config.COLOR_PRIMARY
                    )
                    embed.set_thumbnail(url=song.thumbnail or config.RAI_ICON_URL)
                    embed.add_field(name="⏱️ Track Duration", value=f"`{dur_str}`", inline=True)
                    embed.add_field(name="📍 Position in Queue", value=f"`#{len(player.queue)}`", inline=True)
                    embed.add_field(name="⏳ Estimated Time", value=f"`{est_str}`", inline=True)
                    embed.set_footer(text=f"Requested by {ctx.author.display_name} • RAI VIBES 💗", icon_url=ctx.author.display_avatar.url)
                    
                    if ctx.interaction:
                        await ctx.interaction.followup.send(embed=embed)
                    else:
                        await ctx.send(embed=embed)
                else:
                    if ctx.interaction:
                        try:
                            await ctx.interaction.delete_original_response()
                        except Exception:
                            pass
            else:
                remaining_space = max(0, config.MAX_QUEUE_SIZE - len(player.queue))
                added_tracks = spotify_tracks[:remaining_space]

                for t in added_tracks:
                    unresolved_song = Song(
                        data={
                            "title": f"{t['title']} - {t['artist']}",
                            "search_query": t["search_query"],
                            "thumbnail": t.get("thumbnail", ""),
                            "duration": 0,
                            "webpage_url": "https://spotify.com"
                        },
                        requester=ctx.author,
                        source_type="spotify"
                    )
                    player.queue.append(unresolved_song)

                embed = discord.Embed(
                    title="⚡ Spotify Playlist / Album Enqueued!",
                    description=f"Added **{len(added_tracks)} tracks** from Spotify to the RAI VIBES 💗 queue (Queue: `{len(player.queue)}/{config.MAX_QUEUE_SIZE}`).",
                    color=config.COLOR_PRIMARY
                )
                embed.set_thumbnail(url=spotify_tracks[0].get("thumbnail", config.RAI_ICON_URL))
                embed.set_footer(text="RAI VIBES 💗 Music Engine", icon_url=config.RAI_ICON_URL)
                
                if ctx.interaction:
                    await ctx.interaction.followup.send(embed=embed)
                else:
                    await ctx.send(embed=embed)
            return

        # Direct YouTube / Keyword Search
        try:
            song = await Song.create_source(query, ctx.author, self.bot.loop)
            if not song:
                if ctx.interaction:
                    return await ctx.interaction.followup.send(f"❌ No results found for query: `{query}`", ephemeral=True)
                return await ctx.send(f"❌ No results found for query: `{query}`")

            is_currently_playing = bool(player.current and player.voice_client and (player.voice_client.is_playing() or player.voice_client.is_paused()))
            player.queue.append(song)

            if is_currently_playing:
                # Calculate estimated time until playing (Rythm Style)
                est_sec = 0
                if player.current:
                    cur_elapsed = int(time.time() - player.start_time) if player.start_time else 0
                    est_sec += max(0, player.current.duration - cur_elapsed)
                for q_song in list(player.queue)[:-1]:
                    est_sec += max(0, q_song.duration)

                est_str = time.strftime("%M:%S", time.gmtime(est_sec)) if est_sec > 0 else "Playing Next"
                dur_str = time.strftime("%M:%S", time.gmtime(song.duration)) if song.duration > 0 else "Live"

                embed = discord.Embed(
                    title="🎵 Added to queue",
                    description=f"**[{song.title}]({song.webpage_url})**",
                    color=config.COLOR_PRIMARY
                )
                embed.set_thumbnail(url=song.thumbnail or config.RAI_ICON_URL)
                embed.add_field(name="⏱️ Track Duration", value=f"`{dur_str}`", inline=True)
                embed.add_field(name="📍 Position in Queue", value=f"`#{len(player.queue)}`", inline=True)
                embed.add_field(name="⏳ Estimated Time", value=f"`{est_str}`", inline=True)
                embed.set_footer(text=f"Requested by {ctx.author.display_name} • RAI VIBES 💗", icon_url=ctx.author.display_avatar.url)
                
                if ctx.interaction:
                    await ctx.interaction.followup.send(embed=embed)
                else:
                    await ctx.send(embed=embed)
            else:
                # If starting playback now, delete thinking message if interaction
                if ctx.interaction:
                    try:
                        await ctx.interaction.delete_original_response()
                    except Exception:
                        pass

        except Exception as e:
            if ctx.interaction:
                await ctx.interaction.followup.send(f"❌ Error while queuing track: `{e}`", ephemeral=True)
            else:
                await ctx.send(f"❌ Error while queuing track: `{e}`")

    # =========================================================================
    # COMMAND: JOIN / SUMMON
    # =========================================================================
    @commands.hybrid_command(name="join", aliases=["summon", "connect", "j"], description="Summon RAI VIBES to your current voice channel.")
    async def join(self, ctx: commands.Context):
        vc = await self.ensure_voice(ctx)
        if vc:
            await ctx.send(f"🔊 **Connected to:** `{vc.channel.name}` • Ready for music!")

    # =========================================================================
    # COMMAND: SEARCH (TOP 5 INTERACTIVE SELECTOR)
    # =========================================================================
    @commands.hybrid_command(name="search", description="Search YouTube and choose from top 5 results interactively.")
    @app_commands.describe(query="Song name or keywords to search")
    async def search(self, ctx: commands.Context, *, query: str):
        await ctx.defer()
        results = await Song.search_multiple(query, limit=5, loop=self.bot.loop)
        if not results:
            return await ctx.send(f"❌ No search results found for: `{query}`")

        embed = discord.Embed(
            title=f"⚡ Search Results for: {query[:50]}",
            description="Select an option from the dropdown menu below to add it to the queue:",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=results[0].get("thumbnail", config.RAI_ICON_URL))

        for i, item in enumerate(results, 1):
            dur = time.strftime("%M:%S", time.gmtime(item.get("duration", 0)))
            embed.add_field(
                name=f"{i}. {item.get('title', 'Track')[:45]}",
                value=f"👤 `{item.get('uploader', 'Artist')[:25]}` | ⏱️ `{dur}`",
                inline=False
            )

        view = SearchSelectView(self, ctx, results)
        await ctx.send(embed=embed, view=view)

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
    @commands.hybrid_command(name="skipto", aliases=["jump"], description="Skip directly to a specific track in the queue.")
    @app_commands.describe(index="The track position to jump to (e.g. 3)")
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
        view = QueuePaginationView(player, current_page=0)
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
    @commands.hybrid_command(name="remove", aliases=["rm"], description="Remove a specific song from queue by its position.")
    @app_commands.describe(index="The track position number from /queue")
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
    @commands.hybrid_command(name="clearqueue", aliases=["cq", "emptyqueue", "qclear"], description="Clear all upcoming songs from the queue.")
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
    @commands.hybrid_command(name="replay", aliases=["restart"], description="Replay the currently playing song from the beginning.")
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
    @commands.hybrid_command(name="seek", description="Seek to a specific timestamp in the current song (e.g. 1:30 or 90).")
    @app_commands.describe(timestamp="Time position to jump to (e.g. 1:30 or seconds)")
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
    # EVENT LISTENER: SMART RESUME ON VOICE JOIN
    # =========================================================================
    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        # Trigger when a user joins or switches into a voice channel
        if after.channel is not None and before.channel != after.channel:
            player = self.get_player(member.guild.id)
            if not player or not player.paused_snapshot:
                return

            snapshot = player.paused_snapshot
            target_user_id = snapshot.get("user_id")
            # If the member is the one who paused it (or any member if no specific author)
            if target_user_id is None or member.id == target_user_id:
                song = snapshot.get("song")
                if not song:
                    return

                pos_sec = snapshot.get("position", 0)
                pos_str = time.strftime("%M:%S", time.gmtime(pos_sec))
                tot_str = time.strftime("%M:%S", time.gmtime(song.duration)) if song.duration > 0 else "Live"

                target_channel = (
                    discord.utils.get(member.guild.text_channels, name="│🎵・song-requests")
                    or discord.utils.get(member.guild.text_channels, name="song-requests")
                    or player.text_channel
                    or member.guild.system_channel
                )

                if target_channel:
                    embed = discord.Embed(
                        title="🌸 Welcome Back • Continue Where You Left Off?",
                        description=(
                            f"Hey {member.mention}! You left off listening to:\n"
                            f"### 🎵 [{song.title}]({song.webpage_url})\n\n"
                            f"⏱️ **Paused at:** `{pos_str}` / `{tot_str}`\n"
                            f"🔊 **Target VC:** {after.channel.mention}\n\n"
                            f"Click **Continue** below to instantly resume from `{pos_str}`!"
                        ),
                        color=config.COLOR_PRIMARY
                    )
                    embed.set_thumbnail(url=song.thumbnail or config.RAI_ICON_URL)
                    embed.set_footer(text="RAI VIBES 💗 Smart Resume Engine", icon_url=config.RAI_ICON_URL)

                    view = ResumePlaybackView(player, snapshot)
                    try:
                        await target_channel.send(content=member.mention, embed=embed, view=view)
                    except Exception as e:
                        print(f"[Smart Resume Prompt Error] {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Music(bot))
