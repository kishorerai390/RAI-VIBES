import asyncio
import unicodedata
import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Optional, Literal

import config

RADIO_STATIONS = {
    "tamilnadu_fm": {
        "name": "📻 Tamil Panpalai Gold 24/7",
        "url": "https://tamilpanpalai.radioca.st/ind",
        "thumb": "https://cdn-icons-png.flaticon.com/512/3844/3844724.png",
        "desc": "Official 24/7 Tamil Panpalai broadcasting non-stop golden Tamil hits & melodies."
    },
    "sooriyan_fm": {
        "name": "📻 AIR Kodai Tamil FM 24/7",
        "url": "https://air.pc.cdn.bitgravity.com/air/live/pbaudio051/chunklist.m3u8",
        "thumb": "https://cdn-icons-png.flaticon.com/512/869/869869.png",
        "desc": "Official All India Radio Kodai FM Live Tamil Broadcast."
    },
    "tamil_lofi": {
        "name": "📻 Tube Tamil FM Radio 24/7",
        "url": "http://s2.voscast.com:12084/;stream1619441439791/1",
        "thumb": "https://cdn-icons-png.flaticon.com/512/3075/3075908.png",
        "desc": "Relaxing aesthetic Tamil melodies and midnight chill vibes."
    },
    "tamil_ar": {
        "name": "📻 Tamil Panpalai Classics 24/7",
        "url": "https://tamilpanpalai.radioca.st/ind",
        "thumb": "https://cdn-icons-png.flaticon.com/512/461/461238.png",
        "desc": "24/7 legendary AR Rahman & Ilayaraja musical masterworks."
    },
    "vanavil_fm": {
        "name": "🌈 Tube Tamil Hits 24/7",
        "url": "http://s2.voscast.com:12084/;stream1619441439791/1",
        "thumb": "https://cdn-icons-png.flaticon.com/512/2917/2917995.png",
        "desc": "Evergreen golden Tamil melodies and hit songs."
    },
    "lofi": {
        "name": "☕ SomaFM Groove Salad (24/7 Lofi & Chill)",
        "url": "https://ice5.somafm.com/groovesalad-128-mp3",
        "thumb": "https://cdn-icons-png.flaticon.com/512/3075/3075908.png",
        "desc": "World renowned chilled ambient/downtempo beats to study, relax, or vibe to."
    },
    "synthwave": {
        "name": "🌆 Synthwave / Cyberpunk 80s",
        "url": "https://stream.nightride.fm/nightride.mp3",
        "thumb": "https://cdn-icons-png.flaticon.com/512/4397/4397571.png",
        "desc": "Retro-futuristic 80s outrun & electronic vibes."
    },
    "gaming": {
        "name": "🎮 Gaming & High Energy EDM",
        "url": "https://stream.simulatorradio.com/stream.mp3",
        "thumb": "https://cdn-icons-png.flaticon.com/512/686/686589.png",
        "desc": "Energetic background gaming & electronic dance beats."
    },
    "chill": {
        "name": "🌊 Chillout Lounge & Ambient",
        "url": "https://stream.nightride.fm/chillsynth.mp3",
        "thumb": "https://cdn-icons-png.flaticon.com/512/2917/2917995.png",
        "desc": "Soothing ambient soundscapes and lounge music."
    },
    "binaural_study": {
        "name": "🧠 432Hz Deep Focus & Binaural Study Waves",
        "url": "https://ice5.somafm.com/dronezone-128-mp3",
        "thumb": "https://cdn-icons-png.flaticon.com/512/3233/3233514.png",
        "desc": "Atmospheric soundscapes and deep theta wave focus music for study & productivity."
    },
    "anime_lofi": {
        "name": "🍜 Tokyo Nights Anime Chill & Melodies",
        "url": "https://ice5.somafm.com/groovesalad-128-mp3",
        "thumb": "https://cdn-icons-png.flaticon.com/512/3075/3075908.png",
        "desc": "Chill anime-inspired instrumental lo-fi and calming night beats."
    },
    "phonk_drift": {
        "name": "🏎️ Drift Phonk & Bass Energy",
        "url": "https://stream.simulatorradio.com/stream.mp3",
        "thumb": "https://cdn-icons-png.flaticon.com/512/4397/4397571.png",
        "desc": "High-octane drift phonk, cowbell beats, and adrenaline electronic audio."
    },
    "citypop": {
        "name": "🏙️ 80s Japanese City Pop & Future Funk",
        "url": "https://stream.nightride.fm/nightride.mp3",
        "thumb": "https://cdn-icons-png.flaticon.com/512/2917/2917995.png",
        "desc": "Nostalgic 80s groove, retro anime aesthetics, and disco funk."
    }
}

class Radio(commands.Cog):
    """24/7 Live Radio Stations, Tamil Nadu FM & Voice Channel Stay Mode."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_streamed_station = "lofi"
        self.auto_stay_247_task.start()

    def cog_unload(self):
        self.auto_stay_247_task.cancel()

    async def start_radio_in_channel(
        self,
        channel: discord.VoiceChannel,
        station_key: str = "tamilnadu_fm",
        requester: Optional[discord.Member] = None,
        notify: bool = True
    ):
        """Connects to a voice channel and starts streaming radio continuously."""
        music_cog = self.bot.get_cog("Music")
        if not music_cog:
            return

        guild = channel.guild
        voice_client = guild.voice_client

        if not voice_client or voice_client.channel != channel:
            try:
                voice_client = await channel.connect(timeout=25.0, reconnect=True, self_deaf=False)
            except Exception as e:
                print(f"[Radio Connect Error] {e}")
                return

        player = music_cog.get_or_create_player(guild)
        player.voice_client = voice_client
        player.mode_247 = True

        from cogs.music import Song
        st_data = RADIO_STATIONS.get(station_key, RADIO_STATIONS["lofi"])
        radio_song = Song(
            data={
                "title": f"📻 {st_data['name']}",
                "url": st_data["url"],
                "webpage_url": st_data["url"],
                "duration": 0,
                "thumbnail": st_data["thumb"],
                "uploader": "24/7 Continuous Music Engine"
            },
            requester=requester or guild.me,
            source_type="radio"
        )

        # Do not clear queue if active tracks exist unless explicitly requested
        player.queue.appendleft(radio_song)
        if player.voice_client and (player.voice_client.is_playing() or player.voice_client.is_paused()):
            player.skip()
        else:
            player.play_next_song.set()

        if notify:
            text_channel = (
                discord.utils.get(guild.text_channels, name="song-requests")
                or discord.utils.get(guild.text_channels, name="🎵・song-requests")
                or discord.utils.get(guild.text_channels, name="general-chat")
                or discord.utils.get(guild.text_channels, name="💬・general-chat")
            )
            if text_channel:
                player.text_channel = text_channel
                embed = discord.Embed(
                    title=f"📻 24/7 Live Broadcast Started!",
                    description=f"Now streaming continuously in **{channel.name}**:\n### **{st_data['name']}**\n*{st_data['desc']}*",
                    color=config.COLOR_PRIMARY
                )
                embed.set_thumbnail(url=st_data["thumb"])
                embed.set_footer(text="AURA ✦ • Continuous 24/7 Music Engine", icon_url=config.RAI_ICON_URL)
                try:
                    await text_channel.send(embed=embed)
                except Exception:
                    pass

    @tasks.loop(seconds=15)
    async def auto_stay_247_task(self):
        """Autonomous supervisor ensuring AURA streams music 24/7 non-stop in the server."""
        try:
            guild = self.bot.get_guild(1457382179981099090)
            if not guild:
                return

            def match_vc(c, keywords):
                norm = unicodedata.normalize('NFKD', c.name).lower()
                return any(k in norm for k in keywords)

            # Target 24/7 Channel: 🎧 | 24/7 Music Studio or 🌧️ | Midnight Lo-Fi
            target_vc = (
                guild.get_channel(1550186760779211003)
                or guild.get_channel(1550196959841878098)
                or next((c for c in guild.voice_channels if match_vc(c, ["music", "studio", "lo-fi", "lofi", "beats"])), None)
            )
            if not target_vc:
                return

            vc = guild.voice_client
            # 1. Connect if disconnected
            if not vc or not vc.is_connected():
                await self.start_radio_in_channel(target_vc, station_key=self._last_streamed_station, notify=False)
                return

            # 2. Lock 24/7 mode & resume continuous stream if idle
            music_cog = self.bot.get_cog("Music")
            if music_cog:
                player = music_cog.get_player(guild.id)
                if player:
                    player.mode_247 = True
                    # If not playing anything, not paused, and queue empty -> start 24/7 stream
                    if not vc.is_playing() and not vc.is_paused() and not player.current and not player.queue:
                        await self.start_radio_in_channel(vc.channel, station_key=self._last_streamed_station, notify=False)
        except Exception:
            pass

    @auto_stay_247_task.before_loop
    async def before_auto_stay(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(name="tamilnadufm", description="Stream 24/7 Live Tamil Nadu FM Radio non-stop!")
    async def tamilnadufm(self, ctx: commands.Context):
        """Instant shortcut to stream 24/7 Tamil Nadu FM."""
        author = ctx.author
        if not author.voice or not author.voice.channel:
            return await ctx.send("⚡ **Please join a voice channel first to play Tamil Nadu FM!**", ephemeral=True)

        await ctx.defer()
        await self.start_radio_in_channel(author.voice.channel, station_key="tamilnadu_fm", requester=author)
        st_data = RADIO_STATIONS["tamilnadu_fm"]
        embed = discord.Embed(
            title="📻 24/7 Tamil Nadu FM Streaming!",
            description=f"**{st_data['name']}**\n{st_data['desc']}",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=st_data["thumb"])
        embed.set_footer(text="RAI VIBES 💗 Tamil Nadu FM Live", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.command(name="tnfm")
    async def tnfm(self, ctx: commands.Context):
        """Quick prefix shortcut: Stream 24/7 Tamil Nadu FM Live!"""
        await self.tamilnadufm(ctx)

    @commands.command(name="tamil")
    async def tamil(self, ctx: commands.Context):
        """Quick prefix shortcut: Stream 24/7 Non-Stop Tamil Hit Songs!"""
        await self.tamilnadufm(ctx)

    @commands.hybrid_command(name="radio", description="Stream continuous 24/7 live themed radio stations.")
    @app_commands.describe(station="Select a 24/7 radio station")
    @app_commands.choices(station=[
        app_commands.Choice(name="📻 Tamil Nadu FM Live 24/7", value="tamilnadu_fm"),
        app_commands.Choice(name="☀️ Sooriyan Tamil FM 24/7", value="sooriyan_fm"),
        app_commands.Choice(name="☕ Tamil Slowed & Lofi Beats 24/7", value="tamil_lofi"),
        app_commands.Choice(name="👑 AR Rahman Classics 24/7", value="tamil_ar"),
        app_commands.Choice(name="🌈 Vanavil Tamil FM 24/7", value="vanavil_fm"),
        app_commands.Choice(name="☕ Global Lofi Hip Hop / Study Beats", value="lofi"),
        app_commands.Choice(name="🌆 Synthwave / 80s Retrowave", value="synthwave"),
        app_commands.Choice(name="🎮 Gaming EDM / Simulator", value="gaming"),
        app_commands.Choice(name="🌊 Chillout Lounge / Ambient", value="chill"),
        app_commands.Choice(name="🧠 432Hz Deep Focus & Binaural Study", value="binaural_study"),
        app_commands.Choice(name="🍜 Tokyo Nights Anime Chill Lo-Fi", value="anime_lofi"),
        app_commands.Choice(name="🏎️ Drift Phonk & Bass Energy", value="phonk_drift"),
        app_commands.Choice(name="🏙️ 80s Japanese City Pop & Funk", value="citypop"),
    ])
    async def radio(self, ctx: commands.Context, station: Optional[app_commands.Choice[str]] = None):
        key = station.value if station else "tamilnadu_fm"
        author = ctx.author
        if not author.voice or not author.voice.channel:
            return await ctx.send("⚡ **You must join a voice channel first to tune into radio!**", ephemeral=True)

        await ctx.defer()
        await self.start_radio_in_channel(author.voice.channel, station_key=key, requester=author)
        st_data = RADIO_STATIONS.get(key, RADIO_STATIONS["tamilnadu_fm"])
        embed = discord.Embed(
            title="📻 Tuned into 24/7 Radio Station",
            description=f"**{st_data['name']}**\n{st_data['desc']}",
            color=config.COLOR_GOLD
        )
        embed.set_thumbnail(url=st_data["thumb"])
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="stay247", aliases=["alwayson", "radio247"], description="Toggle or set 24/7 mode (prevents bot from leaving voice channel).")
    @app_commands.describe(mode="Choose to explicitly Enable or Disable 24/7 mode")
    async def stay_247(self, ctx: commands.Context, mode: Optional[Literal["enable", "disable"]] = None):
        music_cog = self.bot.get_cog("Music")
        if not music_cog:
            return await ctx.send("❌ Music engine not available.", ephemeral=True)

        player = music_cog.get_or_create_player(ctx.guild)
        if mode == "enable":
            player.mode_247 = True
        elif mode == "disable":
            player.mode_247 = False
        else:
            player.mode_247 = not player.mode_247

        if player.mode_247:
            status_title = "✅ 24/7 Mode ACTIVATED"
            status_desc = "⚡ **Bot is locked into 24/7 Mode!**\nRAI VIBES 💗 will stay connected in voice channels 24/7 non-stop without leaving."
            color = config.COLOR_SUCCESS
        else:
            status_title = "❌ 24/7 Mode DEACTIVATED"
            status_desc = "⏳ **Bot will leave voice channels when inactive/empty.**"
            color = config.COLOR_DARK

        embed = discord.Embed(
            title=status_title,
            description=status_desc,
            color=color
        )
        embed.set_footer(text="RAI VIBES 💗 • 24/7 Music Engine", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="alarm", description="Schedule the bot to join voice and stream radio after set minutes.")
    @app_commands.describe(
        minutes="Minutes from now to trigger the alarm (e.g. 15, 30, 60, 480)",
        station="Radio station to wake up to (defaults to lo-fi / chill)"
    )
    @app_commands.choices(station=[
        app_commands.Choice(name="☕ Global Lofi Hip Hop / Study Beats", value="lofi"),
        app_commands.Choice(name="📻 Tamil Panpalai Gold 24/7", value="tamilnadu_fm"),
        app_commands.Choice(name="📻 AIR Kodai Tamil FM 24/7", value="sooriyan_fm"),
        app_commands.Choice(name="🌊 Chillout Lounge / Ambient", value="chill"),
        app_commands.Choice(name="🌆 Synthwave / 80s Retrowave", value="synthwave"),
    ])
    async def alarm(self, ctx: commands.Context, minutes: int, station: Optional[app_commands.Choice[str]] = None):
        if minutes < 1 or minutes > 1440:
            return await ctx.send("❌ Alarm duration must be between 1 and 1440 minutes (24 hours).", ephemeral=True)

        user_vc = getattr(getattr(ctx.author, "voice", None), "channel", None)
        if not user_vc:
            return await ctx.send("❌ Please join your desired voice channel first so the alarm knows where to stream!", ephemeral=True)

        station_key = station.value if station else "lofi"
        st_data = RADIO_STATIONS.get(station_key, RADIO_STATIONS["lofi"])

        embed = discord.Embed(
            title="⏰ VOICE RADIO ALARM SCHEDULED",
            description=(
                f"Your alarm has been set for **{minutes} minutes** from now!\n\n"
                f"📍 **Target Channel:** {user_vc.mention}\n"
                f"📻 **Station:** `{st_data['name']}`\n"
                f"🔔 The bot will automatically connect and stream peaceful wake-up melodies."
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=st_data["thumb"])
        embed.set_footer(text="RAI VIBES 💗 • Scheduled Voice Alarm", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

        async def _alarm_coro():
            await asyncio.sleep(minutes * 60)
            target_chan = self.bot.get_channel(user_vc.id)
            if target_chan and isinstance(target_chan, discord.VoiceChannel):
                await self.start_radio_in_channel(target_chan, station_key=station_key)
                try:
                    wake_embed = discord.Embed(
                        title="⏰ WAKE UP & VIBE!",
                        description=f"🔔 {ctx.author.mention} Your scheduled radio alarm has fired! Streaming **{st_data['name']}** in {target_chan.mention}.",
                        color=config.COLOR_GOLD
                    )
                    await target_chan.send(content=ctx.author.mention, embed=wake_embed)
                except Exception:
                    pass

        self.bot.loop.create_task(_alarm_coro())


async def setup(bot: commands.Bot):
    await bot.add_cog(Radio(bot))
