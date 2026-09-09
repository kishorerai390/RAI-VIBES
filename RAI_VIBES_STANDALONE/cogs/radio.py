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
    }
}

class Radio(commands.Cog):
    """24/7 Live Radio Stations, Tamil Nadu FM & Voice Channel Stay Mode."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def start_radio_in_channel(self, channel: discord.VoiceChannel, station_key: str = "tamilnadu_fm", requester: Optional[discord.Member] = None):
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
        st_data = RADIO_STATIONS.get(station_key, RADIO_STATIONS["tamilnadu_fm"])
        radio_song = Song(
            data={
                "title": f"📻 {st_data['name']}",
                "url": st_data["url"],
                "webpage_url": st_data["url"],
                "duration": 0,
                "thumbnail": st_data["thumb"],
                "uploader": "Tamil Nadu Live Radio 24/7"
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

        text_channel = (
            discord.utils.get(guild.text_channels, name="song-requests")
            or discord.utils.get(guild.text_channels, name="🎵・song-requests")
            or discord.utils.get(guild.text_channels, name="general-chat")
            or discord.utils.get(guild.text_channels, name="💬・general-chat")
        )
        if text_channel:
            player.text_channel = text_channel
            embed = discord.Embed(
                title="📻 Tamil Nadu FM 24/7 Live Broadcast!",
                description=f"Now streaming continuously in **{channel.name}**:\n### **{st_data['name']}**\n*{st_data['desc']}*",
                color=config.COLOR_PRIMARY
            )
            embed.set_thumbnail(url=st_data["thumb"])
            embed.set_footer(text="RAI VIBES 💗 • Non-Stop Tamil Nadu FM Engine", icon_url=config.RAI_ICON_URL)
            try:
                await text_channel.send(embed=embed)
            except Exception:
                pass

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

    @commands.hybrid_command(name="tnfm", description="Quick shortcut: Stream 24/7 Tamil Nadu FM Live!")
    async def tnfm(self, ctx: commands.Context):
        await self.tamilnadufm(ctx)

    @commands.hybrid_command(name="tamil", description="Quick shortcut: Stream 24/7 Non-Stop Tamil Hit Songs!")
    async def tamil(self, ctx: commands.Context):
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

    @commands.hybrid_command(name="stay247", aliases=["247", "alwayson"], description="Toggle or set 24/7 mode (prevents bot from leaving voice channel).")
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


async def setup(bot: commands.Bot):
    await bot.add_cog(Radio(bot))
