import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

import config

RADIO_STATIONS = {
    "lofi": {
        "name": "☕ Lofi Hip Hop / Chill Beats",
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
    },
    "jazz": {
        "name": "🎷 Smooth Classic Jazz Cafe",
        "url": "https://ice5.somafm.com/sonicuniverse-128-mp3",
        "thumb": "https://cdn-icons-png.flaticon.com/512/461/461238.png",
        "desc": "Classy jazz melodies and coffeehouse rhythm."
    },
    "rock": {
        "name": "🎸 Classic & Modern Rock",
        "url": "https://ice1.somafm.com/indiepop-128-mp3",
        "thumb": "https://cdn-icons-png.flaticon.com/512/3659/3659784.png",
        "desc": "Indie and alternative rock anthems."
    }
}

class Radio(commands.Cog):
    """24/7 Live Radio Stations and 24/7 Voice Channel Stay Mode."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="radio", description="Stream continuous 24/7 live themed radio stations.")
    @app_commands.describe(station="Select a 24/7 radio station")
    @app_commands.choices(station=[
        app_commands.Choice(name="☕ Lofi Hip Hop / Study Beats", value="lofi"),
        app_commands.Choice(name="🌆 Synthwave / 80s Retrowave", value="synthwave"),
        app_commands.Choice(name="🎮 Gaming EDM / Simulator", value="gaming"),
        app_commands.Choice(name="🌊 Chillout Lounge / Ambient", value="chill"),
        app_commands.Choice(name="🎷 Smooth Jazz Cafe", value="jazz"),
        app_commands.Choice(name="🎸 Indie & Alternative Rock", value="rock"),
    ])
    async def radio(self, ctx: commands.Context, station: Optional[app_commands.Choice[str]] = None):
        key = station.value if station else "lofi"
        st_data = RADIO_STATIONS.get(key, RADIO_STATIONS["lofi"])

        music_cog = self.bot.get_cog("Music")
        if not music_cog:
            return await ctx.send("❌ Music cog not available.", ephemeral=True)

        voice_client = await music_cog.ensure_voice(ctx)
        if not voice_client:
            return

        player = music_cog.get_or_create_player(ctx.guild)
        player.voice_client = voice_client
        player.text_channel = ctx.channel

        from cogs.music import Song
        radio_song = Song(
            data={
                "title": f"📻 24/7 Live Radio: {st_data['name']}",
                "url": st_data["url"],
                "webpage_url": st_data["url"],
                "duration": 0,
                "thumbnail": st_data["thumb"],
                "uploader": "RAI VIBES 💗 Live Radio"
            },
            requester=ctx.author,
            source_type="radio"
        )

        player.queue.appendleft(radio_song)
        if player.voice_client.is_playing() or player.voice_client.is_paused():
            player.skip()

        embed = discord.Embed(
            title=f"⚡ Tuning into 24/7 Radio Station",
            description=f"**{st_data['name']}**\n{st_data['desc']}",
            color=config.COLOR_GOLD
        )
        embed.set_thumbnail(url=st_data["thumb"])
        embed.add_field(name="Requested By", value=ctx.author.mention, inline=True)
        embed.set_footer(text="RAI VIBES 💗 Live Broadcast", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Auto-starts 24/7 Radio when someone joins the 24-7 Radio channel!"""
        if member.bot:
            return

        if after.channel and ("24-7" in after.channel.name.lower() or "radio" in after.channel.name.lower()):
            music_cog = self.bot.get_cog("Music")
            if not music_cog:
                return

            guild = after.channel.guild
            voice_client = guild.voice_client

            # If not connected or in a different channel, join and play 24/7 Lofi Radio
            if not voice_client or voice_client.channel != after.channel:
                try:
                    if voice_client:
                        await voice_client.disconnect(force=True)
                    voice_client = await after.channel.connect(timeout=20.0, reconnect=True, self_deaf=True)
                except Exception as e:
                    print(f"[Radio Auto-Join Error] {e}")
                    return

                player = music_cog.get_or_create_player(guild)
                player.voice_client = voice_client
                player.mode_247 = True

                from cogs.music import Song
                st_data = RADIO_STATIONS["lofi"]
                radio_song = Song(
                    data={
                        "title": f"📻 24/7 Live Radio: {st_data['name']}",
                        "url": st_data["url"],
                        "webpage_url": st_data["url"],
                        "duration": 0,
                        "thumbnail": st_data["thumb"],
                        "uploader": "RAI VIBES 💗 Live Radio"
                    },
                    requester=member,
                    source_type="radio"
                )

                player.queue.clear()
                player.queue.appendleft(radio_song)
                if player.voice_client and (player.voice_client.is_playing() or player.voice_client.is_paused()):
                    player.skip()

                # Find a text channel to notify
                text_channel = discord.utils.get(guild.text_channels, name="🎵・song-requests") or discord.utils.get(guild.text_channels, name="💬・general-chat")
                if text_channel:
                    player.text_channel = text_channel
                    embed = discord.Embed(
                        title="📻 24/7 Live Radio Station Auto-Activated!",
                        description=f"Now streaming non-stop in **{after.channel.name}**:\n**{st_data['name']}** — *{st_data['desc']}*",
                        color=config.COLOR_GOLD
                    )
                    embed.set_thumbnail(url=st_data["thumb"])
                    embed.set_footer(text="RAI VIBES 💗 • 24/7 Live Radio Engine", icon_url=config.RAI_ICON_URL)
                    try:
                        await text_channel.send(embed=embed)
                    except Exception:
                        pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Radio(bot))
