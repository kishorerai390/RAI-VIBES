import time
import discord
from discord.ext import commands
import config

class General(commands.Cog):
    """General & Information commands for RAI VIBES 💗 Bot."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()

    @commands.hybrid_command(name="ping", description="Check RAI VIBES 💗 response latency.")
    async def ping(self, ctx: commands.Context):
        start = time.monotonic()
        msg = await ctx.send("⚡ Calculating Asgardian latency...")
        end = time.monotonic()
        ws_ping = round(self.bot.latency * 1000)
        api_ping = round((end - start) * 1000)

        embed = discord.Embed(
            title="⚡ RAI VIBES 💗 • Latency Telemetry",
            color=config.COLOR_PRIMARY
        )
        embed.add_field(name="📶 WebSocket Latency", value=f"`{ws_ping}ms`", inline=True)
        embed.add_field(name="⚡ REST API Latency", value=f"`{api_ping}ms`", inline=True)
        embed.set_footer(text="RAI VIBES 💗 • Command The Power", icon_url=config.RAI_ICON_URL)
        await msg.edit(content=None, embed=embed)

    @commands.hybrid_command(name="help", description="Show full list of RAI VIBES 💗 music & control commands.")
    async def help_command(self, ctx: commands.Context):
        embed = discord.Embed(
            title="⚡ RAI VIBES 💗 • Music Bot Commands",
            description=(
                "**Command The Power • Hear The Rhythm**\n"
                "Ultimate Discord Sound Engine with Bassboost, Equalizer, 24/7 Radio, and Spotify/YouTube support."
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)

        music_cmds = (
            "• `/play <query>` (`!p`) - Play song/playlist from YouTube or Spotify\n"
            "• `/search <query>` - Interactive top 5 results menu\n"
            "• `/pause` / `/resume` - Control audio playback\n"
            "• `/skip` (`!s`) - Skip to next track\n"
            "• `/stop` (`!dc`) - Stop playback, clear queue & leave voice\n"
            "• `/nowplaying` (`!np`) - Interactive player embed with buttons\n"
            "• `/queue` (`!q`) - View active queue with page navigation\n"
            "• `/volume <0-100>` - Adjust player volume\n"
            "• `/loop <off|track|queue>` - Set repeat mode\n"
            "• `/shuffle` - Randomize queue\n"
            "• `/remove <index>` - Remove track from queue"
        )
        embed.add_field(name="🎵 Music Commands", value=music_cmds, inline=False)

        filter_cmds = (
            "• `/bassboost <off|low|medium|high|extreme>` - Boost sub-bass\n"
            "• `/karaoke` - Attenuate/remove vocals for karaoke singing\n"
            "• `/nightcore` - Nightcore pitch & speed\n"
            "• `/slowed` - Slowed + Reverb aesthetic\n"
            "• `/spatial8d` (`/8d`) - 8D 360° headphone rotation\n"
            "• `/vaporwave` - Retro vaporwave vibe\n"
            "• `/speed <0.5-2.0>` - Custom playback speed\n"
            "• `/filter_reset` - Clear all audio filters"
        )
        embed.add_field(name="🎛️ Audio Filters & Equalizer", value=filter_cmds, inline=False)

        radio_favs = (
            "• `/radio <station>` - Stream 24/7 Lofi, Synthwave, EDM, Rock, Jazz\n"
            "• `/stay247` (`/247`) - Toggle 24/7 voice channel stay\n"
            "• `/lyrics [song]` - Live song lyrics lookup\n"
            "• `/favorite add|list|play` - Personal song bookmarks"
        )
        embed.add_field(name="📻 24/7 Radio & Utilities", value=radio_favs, inline=False)

        embed.set_footer(text="RAI VIBES 💗 • Ancient Echoes, Modern Energy", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="info", description="Display bot system status, guilds, and uptime.")
    async def info(self, ctx: commands.Context):
        uptime_sec = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s" if days else f"{hours}h {minutes}m {seconds}s"
        total_members = sum(g.member_count or 0 for g in self.bot.guilds)
        total_voice = len(self.bot.voice_clients)

        embed = discord.Embed(
            title="⚡ RAI VIBES 💗 • Status & System Stats",
            description="**Ancient Echoes • Modern Energy**",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.add_field(name="👑 Bot Version", value="`v2.5.0 Ultra`", inline=True)
        embed.add_field(name="⏳ Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="🌐 Guilds", value=f"`{len(self.bot.guilds)} servers`", inline=True)
        embed.add_field(name="👥 Total Users", value=f"`{total_members:,}`", inline=True)
        embed.add_field(name="🔊 Active Voice Streams", value=f"`{total_voice}`", inline=True)
        embed.add_field(name="⚡ Engine", value="`FFmpeg Equalizer + yt-dlp`", inline=True)
        embed.set_footer(text="RAI VIBES 💗 • The Powerful Discord Bot", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="guardian", aliases=["sentinel", "health"], description="Check RAI GUARDIAN auto-healing status & uptime telemetry.")
    async def guardian(self, ctx: commands.Context):
        import json
        from pathlib import Path

        status_file = Path(__file__).resolve().parent.parent / "data" / "guardian_status.json"
        status_data = {}
        if status_file.exists():
            try:
                with open(status_file, "r", encoding="utf-8") as f:
                    status_data = json.load(f)
            except Exception:
                pass

        g_status = status_data.get("guardian_status", "ACTIVE (MONITORING)")
        recovers = status_data.get("total_recovers", 0)
        last_reason = status_data.get("last_crash_reason", "None")

        uptime_sec = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        uptime_str = f"{days}d {hours}h {minutes}m {seconds}s" if days else f"{hours}h {minutes}m {seconds}s"

        embed = discord.Embed(
            title="🛡️ RAI GUARDIAN • Self-Healing Watchdog",
            description="**Autonomous 24/7 Bot Supervisor & Error Recovery Engine**",
            color=0x2ECC71 if recovers == 0 else config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.add_field(name="🟢 Watchdog State", value=f"`{g_status}`", inline=True)
        embed.add_field(name="⚡ Auto-Healing", value="`ENABLED (Active)`", inline=True)
        embed.add_field(name="🛠️ Auto-Recoveries", value=f"`{recovers} incidents resolved`", inline=True)
        embed.add_field(name="⏱️ Live Bot Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="🔒 Voice Anchor", value="`✨ Lo-Fi Chillroom`", inline=True)
        embed.add_field(name="📋 Last Incident", value=f"`{last_reason}`", inline=True)
        embed.set_footer(text="RAI GUARDIAN • 99.9% Uptime SLA • Powered by AI", icon_url=config.RAI_ICON_URL)

        await ctx.send(embed=embed)

    @commands.hybrid_command(name="cleartags", aliases=["removetags", "untag"], description="Remove 'RF | ' tag prefix from member nicknames.")
    async def cleartags(self, ctx: commands.Context):
        import re
        guild = ctx.guild
        owner_id = guild.owner_id
        cleaned = 0
        for member in guild.members:
            if member.bot or member.id == owner_id:
                continue
            nick = member.nick
            if not nick:
                continue
            clean_nick = re.sub(r'^(?:RF\s*\|\s*|RF\s*・\s*|RF\s*\|\s*|RF\s+)', '', nick, flags=re.IGNORECASE).strip()
            global_name = member.global_name or member.name
            if clean_nick != nick:
                try:
                    target_nick = clean_nick if clean_nick != global_name else None
                    await member.edit(nick=target_nick, reason="Remove RF clan tag")
                    cleaned += 1
                except Exception:
                    pass
        await ctx.send(f"✅ Cleaned RF tags from **{cleaned}** member(s)!")

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))
