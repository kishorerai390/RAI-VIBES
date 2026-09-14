import time
import asyncio
import discord
from discord.ext import commands
import config

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

    @commands.hybrid_command(name="serverinfo", aliases=["sinfo", "server", "guildinfo", "guild"], description="Display detailed server information (Everglow style).")
    async def serverinfo(self, ctx: commands.Context):
        guild = ctx.guild
        if not guild:
            return await ctx.send("❌ This command can only be used inside a server.")

        # Gather data
        total_members = guild.member_count or len(guild.members)
        bot_members = len([m for m in guild.members if m.bot])
        human_members = total_members - bot_members

        text_channels = len(guild.text_channels)
        voice_channels = len(guild.voice_channels)
        afk_ch = guild.afk_channel.mention if guild.afk_channel else "None"

        roles_count = len(guild.roles)
        emojis_count = len(guild.emojis)
        stickers_count = len(guild.stickers)

        boost_level = guild.premium_tier
        boost_count = guild.premium_subscription_count or 0
        booster_role = guild.premium_subscriber_role
        booster_role_str = booster_role.mention if booster_role else "None"

        # Verification Level
        verification_map = {
            discord.VerificationLevel.none: "None",
            discord.VerificationLevel.low: "Low",
            discord.VerificationLevel.medium: "Medium",
            discord.VerificationLevel.high: "High",
            discord.VerificationLevel.highest: "Highest",
        }
        verification_str = verification_map.get(guild.verification_level, str(guild.verification_level).capitalize())

        # Content Filter
        filter_map = {
            discord.ContentFilter.disabled: "Disabled",
            discord.ContentFilter.no_role: "Members Without Roles",
            discord.ContentFilter.all_members: "All Members",
        }
        filter_str = filter_map.get(guild.explicit_content_filter, "All Members")

        # 2FA
        mfa_str = "Enabled" if guild.mfa_level else "Disabled"

        # System channels
        rules_str = guild.rules_channel.mention if guild.rules_channel else "None"
        updates_str = guild.public_updates_channel.mention if guild.public_updates_channel else "None"
        system_str = guild.system_channel.mention if guild.system_channel else "No"

        # Format creation time like: Monday, 6 July, 2026 07:39 AM
        created_str = guild.created_at.strftime("%A, %d %B, %Y %I:%M %p")
        vanity_str = guild.vanity_url_code or "None"

        # Dark aesthetic embed color
        embed = discord.Embed(color=0x2B2D31)
        
        # Author: Server Name + Icon
        icon_url = guild.icon.url if guild.icon else None
        embed.set_author(name=f"{guild.name}", icon_url=icon_url)
        if icon_url:
            embed.set_thumbnail(url=icon_url)

        # General Field
        general_val = (
            f"> **ID:** {guild.id}\n"
            f"> **Owner:** <@{guild.owner_id}>\n"
            f"> **Created:** {created_str}\n"
            f"> **Region:** Auto\n"
            f"> **Vanity URL:** {vanity_str}"
        )
        embed.add_field(name="General", value=general_val, inline=False)

        # Members
        members_val = (
            f"> **Total:** {total_members}\n"
            f"> **Humans:** {human_members}\n"
            f"> **Bots:** {bot_members}"
        )
        embed.add_field(name="Members", value=members_val, inline=True)

        # Channels
        channels_val = (
            f"> **AFK:** {afk_ch}\n"
            f"> **Text:** {text_channels}\n"
            f"> **Voice:** {voice_channels}"
        )
        embed.add_field(name="Channels", value=channels_val, inline=True)

        # Roles & Media
        roles_media_val = (
            f"> **Roles:** {roles_count}\n"
            f"> **Emojis:** {emojis_count}\n"
            f"> **Stickers:** {stickers_count}"
        )
        embed.add_field(name="Roles & Media", value=roles_media_val, inline=True)

        # Boosting
        boosting_val = (
            f"> **Level:** {boost_level}\n"
            f"> **Boosts:** {boost_count}\n"
            f"> **Booster Role:** {booster_role_str}"
        )
        embed.add_field(name="Boosting", value=boosting_val, inline=True)

        # Security
        security_val = (
            f"> **Verification:** {verification_str}\n"
            f"> **Content Filter:** {filter_str}\n"
            f"> **2FA Requirement:** {mfa_str}"
        )
        embed.add_field(name="Security", value=security_val, inline=True)

        # System Channels
        system_val = (
            f"> **Rules:** {rules_str}\n"
            f"> **Updates:** {updates_str}\n"
            f"> **System Msgs:** {system_str}"
        )
        embed.add_field(name="System Channels", value=system_val, inline=True)

        # Footer
        author_user = ctx.author
        author_avatar = author_user.display_avatar.url if author_user else None
        curr_time = discord.utils.utcnow().strftime("%I:%M %p")
        embed.set_footer(text=f"Requested By {author_user.name} • Today at {curr_time}", icon_url=author_avatar)

        view = ServerInfoButtonsView(guild)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="userinfo", aliases=["ui", "whois", "user"], description="Display detailed member profile & badge information (Everglow style).")
    @discord.app_commands.describe(member="The member to view (defaults to yourself)")
    async def userinfo(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        created_str = member.created_at.strftime("%A, %d %B, %Y %I:%M %p")
        joined_str = member.joined_at.strftime("%A, %d %B, %Y %I:%M %p") if member.joined_at else "Unknown"

        embed = discord.Embed(color=0x2B2D31)
        avatar_url = member.display_avatar.url
        embed.set_author(name=f"{member.name} ({member.display_name})", icon_url=avatar_url)
        embed.set_thumbnail(url=avatar_url)

        # General Identity
        general_val = (
            f"> **Username:** {member.name}\n"
            f"> **Nickname:** {member.nick or 'None'}\n"
            f"> **ID:** {member.id}\n"
            f"> **Created:** {created_str}\n"
            f"> **Bot:** {'Yes' if member.bot else 'No'}"
        )
        embed.add_field(name="Identity", value=general_val, inline=False)

        # Membership
        role_count = max(0, len(member.roles) - 1)
        top_role = member.top_role.mention if member.top_role else "None"
        timeout_status = "Yes" if getattr(member, "is_timed_out", lambda: False)() else "No"
        membership_val = (
            f"> **Joined Server:** {joined_str}\n"
            f"> **Top Role:** {top_role}\n"
            f"> **Roles:** {role_count}\n"
            f"> **Timed Out:** {timeout_status}"
        )
        embed.add_field(name="Membership", value=membership_val, inline=True)

        # Presence & Badges
        booster_status = f"Since {member.premium_since.strftime('%b %d, %Y')}" if member.premium_since else "Not Boosting"
        status_str = str(getattr(member, "status", "offline")).capitalize()
        activity_str = member.activity.name if member.activity else "None"
        presence_val = (
            f"> **Status:** {status_str}\n"
            f"> **Activity:** {activity_str}\n"
            f"> **Booster:** {booster_status}"
        )
        embed.add_field(name="Presence & Badges", value=presence_val, inline=True)

        # Footer
        curr_time = discord.utils.utcnow().strftime("%I:%M %p")
        embed.set_footer(text=f"Requested By {ctx.author.name} • Today at {curr_time}", icon_url=ctx.author.display_avatar.url)

        view = UserInfoButtonsView(member, self.bot)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="avatar", aliases=["av", "pfp"], description="Display member avatar in full resolution.")
    @discord.app_commands.describe(member="The member whose avatar you want to view (defaults to yourself)")
    async def avatar(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        avatar_url = member.display_avatar.url
        embed = discord.Embed(title=f"🖼️ {member.display_name}'s Avatar", color=0x2B2D31)
        embed.set_image(url=avatar_url)
        embed.description = f"[Open High-Res Avatar]({avatar_url})"
        embed.set_footer(text=f"Requested By {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        view = discord.ui.View(timeout=120)
        view.add_item(discord.ui.Button(label="Download", url=avatar_url, style=discord.ButtonStyle.link))
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="banner", aliases=["ubanner"], description="Display member's custom profile banner in full resolution.")
    @discord.app_commands.describe(member="The member whose banner you want to view (defaults to yourself)")
    async def banner(self, ctx: commands.Context, member: discord.Member = None):
        member = member or ctx.author
        user = await self.bot.fetch_user(member.id)
        if not user.banner:
            return await ctx.send(f"❌ **{member.display_name}** does not have a custom profile banner.")
        
        banner_url = user.banner.url
        embed = discord.Embed(title=f"🎨 {member.display_name}'s Profile Banner", color=0x2B2D31)
        embed.set_image(url=banner_url)
        embed.description = f"[Open High-Res Banner]({banner_url})"
        embed.set_footer(text=f"Requested By {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        
        view = discord.ui.View(timeout=120)
        view.add_item(discord.ui.Button(label="Download", url=banner_url, style=discord.ButtonStyle.link))
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="membercount", aliases=["mc", "stats"], description="Display detailed server headcount telemetry.")
    async def membercount(self, ctx: commands.Context):
        guild = ctx.guild
        total = guild.member_count or len(guild.members)
        bots = len([m for m in guild.members if m.bot])
        humans = total - bots
        online = len([m for m in guild.members if m.status != discord.Status.offline])
        
        embed = discord.Embed(title=f"👥 {guild.name} • Member Statistics", color=0x2B2D31)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
        embed.description = (
            f"> 👥 **Total Headcount:** `{total:,}`\n"
            f"> 👤 **Human Members:** `{humans:,}`\n"
            f"> 🤖 **Bot Integrations:** `{bots:,}`\n"
            f"> 🟢 **Online Activity:** `{online:,}` members\n"
            f"> 🚀 **Server Boosters:** `{guild.premium_subscription_count} boosts` (Tier {guild.premium_tier})\n"
            f"> 🎭 **Roles Created:** `{len(guild.roles)}`"
        )
        embed.set_footer(text="RAI FAM 💗 • Real-Time Census Telemetry", icon_url=guild.icon.url if guild.icon else None)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="coinflip", aliases=["flip", "coin"], description="Flip a coin (Heads or Tails).")
    async def coinflip(self, ctx: commands.Context):
        import random
        result = random.choice(["Heads 🪙", "Tails 🪙"])
        embed = discord.Embed(
            title="🪙 Coin Flip Result",
            description=f"> Result: **{result}**",
            color=0x2B2D31
        )
        embed.set_footer(text=f"Flipped by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="roll", aliases=["dice"], description="Roll a dice (default 1-6).")
    @discord.app_commands.describe(sides="Number of sides on the dice (default: 6)")
    async def roll(self, ctx: commands.Context, sides: int = 6):
        import random
        if sides < 2 or sides > 1000:
            return await ctx.send("❌ Dice sides must be between 2 and 1,000.")
        val = random.randint(1, sides)
        embed = discord.Embed(
            title="🎲 Dice Roll Result",
            description=f"> Rolled a **D{sides}**: **`{val}`** 🎲",
            color=0x2B2D31
        )
        embed.set_footer(text=f"Rolled by {ctx.author.name}", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="poll", description="Create an interactive community poll with live voting buttons.")
    @discord.app_commands.describe(
        question="The question to poll",
        option1="First option",
        option2="Second option",
        option3="Third option (optional)",
        option4="Fourth option (optional)"
    )
    async def poll(self, ctx: commands.Context, question: str, option1: str, option2: str, option3: str = None, option4: str = None):
        opts = [o for o in [option1, option2, option3, option4] if o]
        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        desc = f"**{question}**\n\n"
        for i, opt in enumerate(opts):
            desc += f"{emojis[i]} **{opt}**\n`░░░░░░░░░░` **0.0%** (0 votes)\n\n"
        desc += "📊 *Total Votes: 0*"

        embed = discord.Embed(title="📊 Community Poll", description=desc, color=0x2B2D31)
        embed.set_footer(text=f"Poll created by {ctx.author.name} • Vote below!", icon_url=ctx.author.display_avatar.url)
        view = PollView(question, opts)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="afk", description="Set an AFK status so the bot notifies members who ping you.")
    @discord.app_commands.describe(reason="Reason for being AFK (default: AFK)")
    async def afk(self, ctx: commands.Context, reason: str = "AFK"):
        user_id = ctx.author.id
        if not hasattr(self.bot, "afk_users"):
            self.bot.afk_users = {}
        self.bot.afk_users[user_id] = {
            "reason": reason,
            "time": time.time(),
            "orig_nick": ctx.author.nick
        }
        
        nick_note = ""
        try:
            current_name = ctx.author.display_name
            if not current_name.startswith("[AFK]"):
                new_nick = f"[AFK] {current_name}"[:32]
                await ctx.author.edit(nick=new_nick, reason="Member enabled AFK status")
                nick_note = " • Updated nickname to `[AFK]`"
        except Exception:
            pass

        embed = discord.Embed(
            title="💤 AFK Status Enabled",
            description=f"> You are now AFK: **{reason}**{nick_note}\n> I will notify anyone who mentions you and automatically remove your AFK when you chat.",
            color=0x2B2D31
        )
        embed.set_footer(text=f"{ctx.author.name} is away", icon_url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        if not hasattr(self.bot, "afk_users"):
            self.bot.afk_users = {}

        # 1. Check if the sender was AFK -> Remove AFK
        if message.author.id in self.bot.afk_users:
            data = self.bot.afk_users.pop(message.author.id)
            try:
                if message.author.display_name.startswith("[AFK]"):
                    orig = data.get("orig_nick")
                    await message.author.edit(nick=orig, reason="Member returned from AFK")
            except Exception:
                pass
            welcome_back = await message.channel.send(
                f"👋 Welcome back {message.author.mention}! I have cleared your AFK status.",
                delete_after=6
            )

        # 2. Check if any mentioned users are AFK -> Notify sender
        if message.mentions:
            for mentioned in message.mentions:
                if mentioned.id in self.bot.afk_users and mentioned.id != message.author.id:
                    m_data = self.bot.afk_users[mentioned.id]
                    elapsed_sec = int(time.time() - m_data["time"])
                    minutes, seconds = divmod(elapsed_sec, 60)
                    hours, minutes = divmod(minutes, 60)
                    time_ago = f"{hours}h {minutes}m ago" if hours else f"{minutes}m ago" if minutes else f"{seconds}s ago"
                    
                    afk_reply = discord.Embed(
                        description=f"💤 **{mentioned.display_name}** is currently AFK: *{m_data['reason']}* ({time_ago})",
                        color=0x2B2D31
                    )
                    await message.channel.send(embed=afk_reply, delete_after=10)
                    break





class PollView(discord.ui.View):
    def __init__(self, question: str, options: list):
        super().__init__(timeout=86400)
        self.question = question
        self.options = options
        self.votes = {i: set() for i in range(len(options))}

        emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
        for i, opt in enumerate(options):
            btn = discord.ui.Button(label=f"{opt[:40]}", emoji=emojis[i], custom_id=f"poll_opt_{i}", style=discord.ButtonStyle.secondary)
            btn.callback = self.make_callback(i)
            self.add_item(btn)

    def make_callback(self, opt_idx: int):
        async def callback(interaction: discord.Interaction):
            user_id = interaction.user.id
            for voters in self.votes.values():
                voters.discard(user_id)
            self.votes[opt_idx].add(user_id)

            total_votes = sum(len(v) for v in self.votes.values())
            desc = f"**{self.question}**\n\n"
            emojis = ["1️⃣", "2️⃣", "3️⃣", "4️⃣"]
            for i, opt in enumerate(self.options):
                count = len(self.votes[i])
                pct = (count / total_votes * 100) if total_votes > 0 else 0
                bar_len = int(pct / 10)
                bar = "█" * bar_len + "░" * (10 - bar_len)
                desc += f"{emojis[i]} **{opt}**\n`{bar}` **{pct:.1f}%** ({count} votes)\n\n"
            desc += f"📊 *Total Votes: {total_votes}*"

            embed = interaction.message.embeds[0]
            embed.description = desc
            await interaction.response.edit_message(embed=embed, view=self)
        return callback


class ServerInfoButtonsView(discord.ui.View):

    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=180)
        self.guild = guild

    @discord.ui.button(label="Server Icon", style=discord.ButtonStyle.secondary)
    async def server_icon(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.guild.icon:
            return await interaction.response.send_message("❌ This server does not have an icon.", ephemeral=True)
        embed = discord.Embed(title=f"🖼️ Icon • {self.guild.name}", color=0x2B2D31)
        embed.set_image(url=self.guild.icon.url)
        embed.description = f"[Download Icon]({self.guild.icon.url})"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Server Banner", style=discord.ButtonStyle.secondary)
    async def server_banner(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.guild.banner:
            return await interaction.response.send_message("❌ This server does not have a server banner.", ephemeral=True)
        embed = discord.Embed(title=f"🎨 Banner • {self.guild.name}", color=0x2B2D31)
        embed.set_image(url=self.guild.banner.url)
        embed.description = f"[Download Banner]({self.guild.banner.url})"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Splash", style=discord.ButtonStyle.secondary)
    async def server_splash(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.guild.splash:
            return await interaction.response.send_message("❌ This server does not have an invite splash background.", ephemeral=True)
        embed = discord.Embed(title=f"✨ Splash • {self.guild.name}", color=0x2B2D31)
        embed.set_image(url=self.guild.splash.url)
        embed.description = f"[Download Splash]({self.guild.splash.url})"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Features", style=discord.ButtonStyle.secondary)
    async def server_features(self, interaction: discord.Interaction, button: discord.ui.Button):
        features = self.guild.features
        if not features:
            desc = "> No special features enabled."
        else:
            desc = "\n".join(f"> • `{feat.replace('_', ' ').title()}`" for feat in sorted(features))
        embed = discord.Embed(title=f"🌟 Features • {self.guild.name}", description=desc, color=0x2B2D31)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class UserInfoButtonsView(discord.ui.View):
    def __init__(self, member: discord.Member, bot: commands.Bot):
        super().__init__(timeout=180)
        self.member = member
        self.bot = bot

    @discord.ui.button(label="Avatar", style=discord.ButtonStyle.secondary)
    async def view_avatar(self, interaction: discord.Interaction, button: discord.ui.Button):
        avatar_url = self.member.display_avatar.url
        embed = discord.Embed(title=f"🖼️ Avatar • {self.member.name}", color=0x2B2D31)
        embed.set_image(url=avatar_url)
        embed.description = f"[Download Avatar]({avatar_url})"
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Banner", style=discord.ButtonStyle.secondary)
    async def view_banner(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            user = await self.bot.fetch_user(self.member.id)
            if not user.banner:
                return await interaction.response.send_message("❌ This user does not have a custom profile banner.", ephemeral=True)
            embed = discord.Embed(title=f"🎨 Banner • {self.member.name}", color=0x2B2D31)
            embed.set_image(url=user.banner.url)
            embed.description = f"[Download Banner]({user.banner.url})"
            await interaction.response.send_message(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Could not fetch banner: {e}", ephemeral=True)

    @discord.ui.button(label="Roles", style=discord.ButtonStyle.secondary)
    async def view_roles(self, interaction: discord.Interaction, button: discord.ui.Button):
        roles = [r.mention for r in reversed(self.member.roles) if not r.is_default()]
        roles_str = " ".join(roles) if roles else "No custom roles assigned."
        embed = discord.Embed(
            title=f"🎭 Roles ({len(roles)}) • {self.member.name}",
            description=roles_str[:4000],
            color=0x2B2D31
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Permissions", style=discord.ButtonStyle.secondary)
    async def view_perms(self, interaction: discord.Interaction, button: discord.ui.Button):
        perms = [p[0].replace("_", " ").title() for p in self.member.guild_permissions if p[1]]
        desc = "\n".join(f"> • `{p}`" for p in perms[:25])
        embed = discord.Embed(
            title=f"🛡️ Key Permissions • {self.member.name}",
            description=desc or "> Standard Member Permissions",
            color=0x2B2D31
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)



async def setup(bot: commands.Bot):
    await bot.add_cog(General(bot))


