import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

import config

RADIO_STATIONS = {
    "tamilnadu_fm": {
        "name": "📻 Tamil Nadu FM Live 24/7",
        "url": "https://stream.zeno.fm/f3wvbbqmdg8uv",
        "thumb": "https://cdn-icons-png.flaticon.com/512/3844/3844724.png",
        "desc": "Official 24/7 Tamil Nadu Live FM Radio broadcasting non-stop Tamil hits."
    },
    "sooriyan_fm": {
        "name": "☀️ Sooriyan Tamil FM 24/7",
        "url": "https://stream.zeno.fm/e01v1k5g158uv",
        "thumb": "https://cdn-icons-png.flaticon.com/512/869/869869.png",
        "desc": "High-energy Tamil cinema chartbusters and superhit songs."
    },
    "tamil_lofi": {
        "name": "☕ Tamil Slowed & Lofi Beats 24/7",
        "url": "https://stream.zeno.fm/e2981u30c18uv",
        "thumb": "https://cdn-icons-png.flaticon.com/512/3075/3075908.png",
        "desc": "Relaxing aesthetic Tamil lofi and midnight chill vibes."
    },
    "tamil_ar": {
        "name": "👑 AR Rahman Classics 24/7",
        "url": "https://stream.zeno.fm/65x759p158quv",
        "thumb": "https://cdn-icons-png.flaticon.com/512/461/461238.png",
        "desc": "24/7 legendary AR Rahman musical masterworks and OSTs."
    },
    "vanavil_fm": {
        "name": "🌈 Vanavil Tamil FM 24/7",
        "url": "https://stream.zeno.fm/08w2b84p158uv",
        "thumb": "https://cdn-icons-png.flaticon.com/512/2917/2917995.png",
        "desc": "Evergreen golden Tamil melodies and Ilayaraja hits."
    },
    "lofi": {
        "name": "☕ Global Lofi Hip Hop / Chill Beats",
        "url": "https://play.streamafrica.net/lofiradio",
        "thumb": "https://cdn-icons-png.flaticon.com/512/3075/3075908.png",
        "desc": "Relaxing lo-fi beats to study, work, or vibe to."
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
        """Connects to a voice channel and starts streaming 24/7 Tamil Nadu FM radio continuously."""
        music_cog = self.bot.get_cog("Music")
        if not music_cog:
            return

        guild = channel.guild
        voice_client = guild.voice_client

        if not voice_client or voice_client.channel != channel:
            try:
                if voice_client:
                    await voice_client.disconnect(force=True)
                voice_client = await channel.connect(timeout=25.0, reconnect=True, self_deaf=True)
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

        player.queue.clear()
        player.queue.appendleft(radio_song)
        if player.voice_client and (player.voice_client.is_playing() or player.voice_client.is_paused()):
            player.skip()

        text_channel = discord.utils.get(guild.text_channels, name="🎵・song-requests") or discord.utils.get(guild.text_channels, name="💬・general-chat")
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

    @commands.Cog.listener()
    async def on_ready(self):
        """Auto-connect to 24-7 Radio channel on bot startup!"""
        await asyncio.sleep(5)
        for guild in self.bot.guilds:
            radio_vc = discord.utils.get(guild.voice_channels, name="📻 | 24-7 RADIO") or next((vc for vc in guild.voice_channels if "24-7" in vc.name.lower() or "radio" in vc.name.lower()), None)
            if radio_vc:
                print(f"[Radio] Auto-joining 24/7 Tamil Nadu FM in {radio_vc.name} ({guild.name})...")
                await self.start_radio_in_channel(radio_vc, "tamilnadu_fm")

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Auto-starts 24/7 Tamil Nadu FM when someone enters the 24-7 Radio channel!"""
        if member.bot:
            return

        if after.channel and ("24-7" in after.channel.name.lower() or "radio" in after.channel.name.lower()):
            guild = after.channel.guild
            voice_client = guild.voice_client
            if not voice_client or voice_client.channel != after.channel or not voice_client.is_playing():
                print(f"[Radio] Member {member.name} joined {after.channel.name}, starting Tamil Nadu FM...")
                await self.start_radio_in_channel(after.channel, "tamilnadu_fm", requester=member)

    @commands.hybrid_command(name="tamilnadufm", aliases=["tnfm", "tamilfm", "tamil"], description="Stream 24/7 Live Tamil Nadu FM Radio non-stop!")
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
        embed.set_footer(text="RAI VIBES 💗 Live Broadcast", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Radio(bot))
