import time
import asyncio
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

class CommandCategorySelect(discord.ui.Select):
    def __init__(self):
        options = [
            discord.SelectOption(
                label="Music Core",
                value="music",
                description="Play, queue, search, skip, volume, loop & playback controls",
                emoji="🎵"
            ),
            discord.SelectOption(
                label="Audio FX & Filters",
                value="filters",
                description="Bassboost, 8D Audio, Nightcore, Slowed+Reverb, Karaoke",
                emoji="🎛️"
            ),
            discord.SelectOption(
                label="24/7 Radio & Streams",
                value="radio",
                description="24/7 Lo-Fi Chill, Synthwave, EDM, Lyrics & Favorites",
                emoji="📻"
            ),
            discord.SelectOption(
                label="Dynamic Voice Rooms",
                value="voicehub",
                description="Join-to-Create, Lock/Unlock, Ghost (Hide), Limit, Invite",
                emoji="🎙️"
            ),
            discord.SelectOption(
                label="Soundboard & Minigames",
                value="fun",
                description="Instant SFX soundboard, Music Trivia, Connect4, Polls",
                emoji="🎮"
            ),
            discord.SelectOption(
                label="Utility & System",
                value="utility",
                description="Ping telemetry, uptime stats, guardian watchdog status",
                emoji="⚙️"
            ),
        ]
        super().__init__(
            placeholder="📂 Select a Command Category...",
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        cat = self.values[0]
        embed = discord.Embed(color=config.COLOR_PRIMARY)
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="RAI VIBES 💗 • Premium Discord Audio Engine", icon_url=config.RAI_ICON_URL)

        if cat == "music":
            embed.title = "🎵 Music Core Commands"
            embed.description = "**High-Fidelity Audio Streaming • YouTube & Spotify Support**"
            embed.add_field(
                name="▶️ Playback",
                value=(
                    "`/play <query>` (`!p`) — Play song or playlist URL\n"
                    "`/search <query>` — Interactive top 5 results menu\n"
                    "`/pause` / `/resume` — Pause or resume track\n"
                    "`/skip` (`!s`) — Skip current song\n"
                    "`/stop` (`!dc`) — Stop playback, clear queue & disconnect"
                ),
                inline=False
            )
            embed.add_field(
                name="📋 Queue & Track Management",
                value=(
                    "`/queue` (`!q`) — View active music queue with pages\n"
                    "`/nowplaying` (`!np`) — Live interactive player card\n"
                    "`/volume <0-100>` — Change playback loudness\n"
                    "`/loop <off|track|queue>` — Toggle song/queue repeat\n"
                    "`/shuffle` — Randomize upcoming queue order\n"
                    "`/remove <index>` — Remove a specific song from queue"
                ),
                inline=False
            )

        elif cat == "filters":
            embed.title = "🎛️ Audio FX & Equalizer"
            embed.description = "**Studio Quality Real-Time Audio DSP Processing**"
            embed.add_field(
                name="🔊 Equalizer Presets",
                value=(
                    "`/bassboost <low|med|high|extreme>` — Boost punchy sub-bass\n"
                    "`/spatial8d` (`/8d`) — Immersive 360° headphone rotation\n"
                    "`/nightcore` — High speed & pitch aesthetic\n"
                    "`/slowed` — Slowed + Reverb midnight vibes\n"
                    "`/vaporwave` — Retro slowed VHS aesthetic\n"
                    "`/karaoke` — Vocal attenuation for live singing\n"
                    "`/speed <0.5-2.0>` — Custom track playback speed\n"
                    "`/filter_reset` — Clear all applied filters instantly"
                ),
                inline=False
            )

        elif cat == "radio":
            embed.title = "📻 24/7 Radio & Lo-Fi Lounge"
            embed.description = "**Continuous 24/7 Streaming Without Pauses**"
            embed.add_field(
                name="📡 Live Stations",
                value=(
                    "`/radio <station>` — Stream Lo-Fi, Synthwave, EDM, Rock, Jazz\n"
                    "`/stay247` (`/247`) — Toggle 24/7 permanent voice stay\n"
                    "`/lyrics [song]` — Live synced lyrics lookup\n"
                    "`/favorite add|list|play` — Bookmark and play saved songs"
                ),
                inline=False
            )

        elif cat == "voicehub":
            embed.title = "🎙️ Dynamic Join-to-Create Voice Hub"
            embed.description = "**On-Demand Private Voice Channels & Ghost Privacy**"
            embed.add_field(
                name="🔒 Privacy & Room Controls",
                value=(
                    "`➕ | Create Nexus VC` — Join to auto-spawn private room\n"
                    "`/vlock` / `/vunlock` — Lock or unlock room for others\n"
                    "`/vghost` (`/vhide`) — Make voice room completely invisible\n"
                    "`/vpermit @user` — Reveal hidden room to specific members\n"
                    "`/vrevoke @user` — Remove access & hide room from user\n"
                    "`/vkick @user` — Disconnect member from your room\n"
                    "`/vname <title>` — Rename your private voice room\n"
                    "`/vlimit <0-99>` — Set max member capacity\n"
                    "`/vstatus <text>` — Set custom room activity status"
                ),
                inline=False
            )

        elif cat == "fun":
            embed.title = "🎮 Soundboard & Interactive Minigames"
            embed.description = "**Entertainment, Sound Effects & Community Games**"
            embed.add_field(
                name="🔊 Soundboard & Games",
                value=(
                    "`/soundboard` — Interactive instant SFX player (Airhorn, Meme, etc.)\n"
                    "`/quiz` — Multiplayer music trivia quiz challenge\n"
                    "`/tictactoe @user` — Interactive button Tic-Tac-Toe\n"
                    "`/connect4 @user` — Interactive Connect 4 board game\n"
                    "`/truthordare` — Random community Truth or Dare prompt\n"
                    "`/poll <question>` — Create multi-choice interactive poll\n"
                    "`/qotd` — Question of the Day prompt"
                ),
                inline=False
            )

        elif cat == "utility":
            embed.title = "⚙️ Utilities & System Telemetry"
            embed.description = "**Diagnostic & Server Maintenance Tools**"
            embed.add_field(
                name="🛠️ Commands",
                value=(
                    "`/c` (`/commands`) — Open this interactive Rythm-style directory\n"
                    "`/ping` — Check WebSocket & API latency\n"
                    "`/info` — View bot uptime, user count & specs\n"
                    "`/guardian` — View AI self-healing watchdog health\n"
                    "`/cleartags` — Remove outdated nickname prefixes"
                ),
                inline=False
            )

        await interaction.response.edit_message(embed=embed)


class CommandDirectoryView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(CommandCategorySelect())


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

    @commands.hybrid_command(name="c", aliases=["commands", "cmds", "help"], description="Browse all RAI VIBES 💗 commands (Rythm style).")
    async def c_command(self, ctx: commands.Context):
        embed = discord.Embed(
            title="⚡ RAI VIBES 💗 • Command Directory",
            description=(
                "**Command The Power • Hear The Rhythm**\n\n"
                "Welcome to the **RAI VIBES** sound & utility engine! "
                "Select a category below to explore available commands.\n\n"
                "🎵 **Music Core** — Playback, queue, volume & loop\n"
                "🎛️ **Audio FX** — Bassboost, 8D audio, slowed & reverb\n"
                "📻 **24/7 Radio** — Non-stop Lo-Fi, EDM, Synthwave\n"
                "🎙️ **Dynamic Voice Hub** — Private rooms, Ghost mode, lock/limits\n"
                "🎮 **Soundboard & Games** — SFX soundboard, Music Trivia, Minigames\n"
                "⚙️ **System & Utility** — Latency, guardian watchdog, info\n\n"
                "*Tip: You can type `/c` or `/help` anytime to open this directory.*"
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="RAI VIBES 💗 • Select category below", icon_url=config.RAI_ICON_URL)

        view = CommandDirectoryView()
        await ctx.send(embed=embed, view=view)

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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Automated 2-hour Disboard bump reminder listener."""
        if not message.guild:
            return

        # Disboard Bot ID: 302050872383242240
        if message.author.id == 302050872383242240:
            # Check if bump was successful
            is_bump_success = False
            for embed in message.embeds:
                desc = embed.description or ""
                if "Bump done" in desc or "bump done" in desc or "thumbsup" in desc:
                    is_bump_success = True
                    break
            
            if "Bump done" in message.content or is_bump_success:
                bump_chan = message.channel
                await bump_chan.send("⏱️ **Bump detected!** I will remind you in **2 hours** to bump RAI FAM again! 🚀✨")
                
                await asyncio.sleep(7200) # 2 Hours
                
                reminder_embed = discord.Embed(
                    title="🚀 TIME TO BUMP RAI FAM! 🌸",
                    description=(
                        "Hey everyone! It's been 2 hours since the last bump.\n\n"
                        "👉 Type **`/bump`** right now to push **RAI FAM 💗** to the top of the Discord directory!"
                    ),
                    color=0x00F5D4
                )
                reminder_embed.set_footer(text="Disboard Server Growth Engine • RAI FAM 💗", icon_url=config.RAI_ICON_URL)
                try:
                    await bump_chan.send(content="🔔 <@&1545516411659620383> **It's Bump Time!**", embed=reminder_embed)
                except Exception:
                    await bump_chan.send(embed=reminder_embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))

