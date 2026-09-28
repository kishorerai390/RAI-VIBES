import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select, Button
from typing import Optional, Dict, Any

import config

COMMAND_CATEGORIES: Dict[str, Dict[str, Any]] = {
    "music": {
        "label": "Music & Audio Suite",
        "emoji": "🎵",
        "bot": "RAI VIBES 💗",
        "description": "High-fidelity streaming, interactive player, queue & lyrics",
        "color": 0xFF69B4,
        "commands": [
            ("`/play <song or url>`", "Stream any track or playlist from YouTube, Spotify, or SoundCloud."),
            ("`/controller`", "Open the interactive button controller remote."),
            ("`/pause` & `/resume`", "Instantly pause or unpause current audio stream."),
            ("`/skip`", "Vote or skip immediately to the next queued track."),
            ("`/queue`", "Browse upcoming track playlist with pagination."),
            ("`/nowplaying`", "View real-time progress bar, track details, and requester."),
            ("`/volume <0-200>`", "Adjust volume with studio audio boost capabilities."),
            ("`/loop <track|queue|off>`", "Set repeat mode for single track or entire playlist."),
            ("`/shuffle`", "Randomize upcoming song order in queue."),
            ("`/lyrics [song]`", "Fetch synchronized live Genius lyrics with album artwork."),
            ("`/import <url>`", "Batch import public Spotify or YouTube playlists into queue."),
            ("`/favorite <add|list|play>`", "Save and stream your personal favorite song library.")
        ]
    },
    "voice_audio": {
        "label": "Studio FX, Radio & Voice Hub",
        "emoji": "🎧",
        "bot": "RAI VIBES 💗",
        "description": "8D Spatial, Equalizer, 24/7 Live Radio & Dynamic Lounges",
        "color": 0x9B59B6,
        "commands": [
            ("`/filter <effect>`", "Apply audio filters: `8d`, `bassboost`, `nightcore`, `vaporwave`, `slowed`."),
            ("`/equalizer`", "Open the live 10-band interactive studio audio equalizer switchboard."),
            ("`/loudnorm`", "Automatic loudness normalization (EBU R128) for balanced volume."),
            ("`/karaoke`", "Real-time vocal frequency cancellation for singing along."),
            ("`/radio [station]`", "Stream 24/7 curated live radio (Tamil Nadu FM, AIR Kodai, Lofi, Synthwave)."),
            ("`/stay247 <on|off>`", "Keep the bot streaming in your voice channel 24/7 even when empty."),
            ("`/voicepanel`", "Open the 4x4 interactive temporary voice room control panel."),
            ("`/vctune`", "Auto-optimize all server voice bitrates up to maximum 384kbps."),
            ("`/quiethours`", "Configure automated late-night quiet hours to suppress join pings."),
            ("`➕┃・ᴊᴏɪɴ ᴛᴏ ᴄʀᴇᴀᴛᴇ`", "Auto-spawns dynamic Thor Apex personal voice lounges.")
        ]
    },
    "economy": {
        "label": "Economy, Jobs & Cyber Casino",
        "emoji": "🪙",
        "bot": "RAI PLAY 🎮",
        "description": "Daily coins, jobs, high-stakes casino, jackpot & bank heists",
        "color": 0xF1C40F,
        "commands": [
            ("`/daily`", "Claim your daily Rai Coins allowance and maintain your streak multiplier!"),
            ("`/balance [member]`", "Inspect your Rai Coins wallet, daily streak, and reputation points."),
            ("`/pay <member> <amount>`", "Send coins directly to another member with zero tax."),
            ("`/eco <work|crime|rob|richest>`", "Perform jobs, take street risks, and browse the richest server barons."),
            ("`/casino <slots|blackjack|coinflip|dice|spin>`", "High-stakes cyber casino games with coin multiplier payouts."),
            ("`/heist [vault]`", "💼 Cooperative Bank Heist: Assemble a crew, crack the vault, and split the loot."),
            ("`/lottery <buy|pool|draw>`", "Participate in the server-wide progressive jackpot lottery."),
            ("`/duel <opponent> <bet>`", "Challenge a squadmate to a high-noon quick-draw gunfight."),
            ("`/rps <opponent> <bet>`", "Challenge a squadmate to a Rock-Paper-Scissors coin challenge.")
        ]
    },
    "gaming": {
        "label": "LFG Squads, Raids & Party Games",
        "emoji": "⚔️",
        "bot": "RAI PLAY 🎮",
        "description": "1-Click Squad Matchmaking, Co-Op Boss Raids & Party Games",
        "color": 0xE74C3C,
        "commands": [
            ("`/lfg <game> [slots] [note]`", "Publish 1-Click LFG request with automatic private squad room generation."),
            ("`/lfgpanel`", "Deploy persistent 1-Click LFG Squad Matchmaking Hub in gaming chat."),
            ("`/squad <create|join|leave|info>`", "Form and manage your dedicated server gaming clan."),
            ("`/raid`", "Inspect the active server Co-Op Boss Raid health and phase."),
            ("`/attack` & `/heal`", "Strike the raid boss for coin bounties or restore squadmate shields."),
            ("`/party <hub|activity|trivia|math|scramble>`", "Launch Discord voice activities and fast chat minigames."),
            ("`/typerace`", "Start a lightning-fast typing speed challenge in chat."),
            ("`/streamer <add|remove|list>`", "Manage automated Twitch and YouTube livestream announcements.")
        ]
    },
    "progression": {
        "label": "Leveling, Milestones & Shop",
        "emoji": "🏆",
        "bot": "RAI PLAY 🎮",
        "description": "Thor Apex Prestige Tiers, Seasonal Battle Pass & Perk Store",
        "color": 0x2ECC71,
        "commands": [
            ("`/rank [member]`", "Inspect your unified Thor Apex card, voice/chat XP, and level."),
            ("`/leaderboard`", "View Top 10 most active members on the server."),
            ("`/milestones`", "Browse Thor Apex prestige tiers (`Rookie` ➔ `Thor Immortal`) & coin rewards."),
            ("`/battlepass`", "View Seasonal Battle Pass progression and claim free/premium loot."),
            ("`/bpleaderboard`", "Inspect the top seasonal Battle Pass grinders."),
            ("`/shop`", "Spend Rai Coins on exclusive roles, VIP badges, and perks."),
            ("`/exchange`", "Convert accumulated XP/Coins into custom cosmetic rewards.")
        ]
    },
    "sentinel": {
        "label": "Aegis Defense & Panic Lockdown",
        "emoji": "🛡️",
        "bot": "RAI SENTINEL 🛡️",
        "description": "Panic Protocol, Anti-Nuke, Anti-Raid & Staff Moderation",
        "color": 0x00F2FE,
        "commands": [
            ("`/panic <on|off|status>`", "🚨 Emergency Fortress Mode: Locks chat and auto-timeouts all unverified joiners."),
            ("`/quarantine <member>`", "Isolate suspicious raid accounts to the Quarantine observation channel."),
            ("`/unquarantine <member>`", "Restore member permissions after review."),
            ("`/security`", "Open the Aegis Command Center with module status and telemetry."),
            ("`/raidmode <status>`", "Enable server-wide high security gate during aggressive join spikes."),
            ("`/lockdown` & `/unlock`", "Instantly lock down public channels to stop spam raids."),
            ("`/ticketsetup [channel]`", "Deploy persistent 1-click private staff support tickets."),
            ("`/warn <member> [reason]`", "Issue official strike infractions to rule breakers."),
            ("`/strikes <member>`", "View complete moderation history and active strikes for a user."),
            ("`/freeze` & `/unfreeze`", "Mute and isolate noisy members in the Freeze Chamber."),
            ("`/clear [amount]`", "Bulk purge recent messages from any channel.")
        ]
    },
    "esports": {
        "label": "Esports, Scrims & Map Veto",
        "emoji": "🎯",
        "bot": "RAI SENTINEL 🛡️",
        "description": "5v5 Scrim splits, competitive map veto & tournament brackets",
        "color": 0xFF4757,
        "commands": [
            ("`/scrim split`", "Tactically split 10 players in voice into Team Alpha and Team Bravo."),
            ("`/scrim merge`", "Merge scrim teams back into the central debrief lounge."),
            ("`/veto <game> <team1> <team2>`", "Start an interactive competitive map ban/pick phase (Valorant, CS2, BGMI)."),
            ("`/tournament <create|bracket|setwinner>`", "Championship tournament single-elimination bracket manager."),
            ("`/code <code> [game]`", "Share custom lobby room code with 1-click squad copy button.")
        ]
    },
    "social": {
        "label": "Social, Pets & Profiles",
        "emoji": "👥",
        "bot": "RAI PLAY 🎮",
        "description": "Cyber Profiles, Virtual Pets, Quotes & Anime Search",
        "color": 0x5865F2,
        "commands": [
            ("`/profile [member]`", "Display your luxury unified server profile codex and badges."),
            ("`/setbio <quote>`", "Set your personal catchphrase displayed on your profile card."),
            ("`/badges [member]`", "Inspect collected achievements, donor tiers, and prestige badges."),
            ("`/rep <member>`", "Award +1 Reputation point to a helpful squadmate."),
            ("`/social <action>`", "Fun social interactions: `highfive`, `fistbump`, `cheers`, `hug`, `pat`."),
            ("`/pet <adopt|feed|play|stats>`", "Adopt and train your virtual companion pet."),
            ("`/quote <message_id>`", "Transform memorable chat moments into stylized quote graphics."),
            ("`/anime <title>` & `/manga <title>`", "Instant media lookup via AniList API with ratings & synopses."),
            ("`/bump` *(Disboard)*", "Bump RAI FAM on Disboard to immediately earn **🪙 500 Coins**!")
        ]
    }
}


def build_category_embed(cat_key: str) -> discord.Embed:
    cat = COMMAND_CATEGORIES.get(cat_key, COMMAND_CATEGORIES["music"])
    embed = discord.Embed(
        title=f"{cat['emoji']} {cat['label'].upper()}",
        description=f"**Powered by:** `{cat['bot']}`\n*{cat['description']}*\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        color=cat["color"]
    )
    for cmd_syntax, cmd_desc in cat["commands"]:
        embed.add_field(name=cmd_syntax, value=cmd_desc, inline=False)

    embed.set_thumbnail(url=config.RAI_ICON_URL)
    embed.set_footer(
        text="RAI FAM 💗 • Thor Apex Command Terminal • Select another category below",
        icon_url=config.RAI_ICON_URL
    )
    return embed


def build_overview_embed() -> discord.Embed:
    embed = discord.Embed(
        title="🎮 ✦ RAI FAM • MASTER COMMAND TERMINAL ✦ 🎮",
        description=(
            "Welcome to the central command bridge for **RAI FAM💗**!\n"
            "Our ecosystem is powered by **3 dedicated autonomous engines**:\n\n"
            "🎵 **RAI VIBES 💗** (`1546239150775078922`)\n"
            "High-Fidelity Music • 24/7 Live Radio • Equalizer & FX • Dynamic Voice Suites\n\n"
            "🎮 **RAI PLAY 🎮** (`1550539920383410306`)\n"
            "Server Economy • Cyber Casino & Heists • 1-Click LFG Squads • Prestige Milestones\n\n"
            "🛡️ **RAI SENTINEL 🛡️** (`1546245134809571470`)\n"
            "Aegis Defense • Panic Lockdown Protocol • Support Tickets • Scrims & Tournaments\n\n"
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            "📂 **Select a command domain from the dropdown below to view all commands & syntax!**"
        ),
        color=0xFF007F
    )
    embed.set_thumbnail(url=config.RAI_ICON_URL)
    embed.add_field(
        name="⚡ Quick Navigation Channels",
        value=(
            "• `#💬｜ɢᴇɴᴇʀᴀʟ-ᴄʜᴀᴛ` — Casual conversation & chilling\n"
            "• `#🤖｜ʙᴏᴛ-ᴄᴏᴍᴍᴀɴᴅꜱ` — Bot interaction playground\n"
            "• `#💸｜ᴏᴡᴏ-ᴀʀᴄᴀᴅᴇ` — Casino gambling, card games & coin drops\n"
            "• `#🎮｜ɢᴀᴍɪɴɢ-ᴄʜᴀᴛ` & `#⚔️｜ʟꜰɢ-ᴍᴀᴛᴄʜᴍᴀᴋɪɴɢ` — Find squadmates & scrims\n"
            "• `#🎛️｜ᴠᴏɪᴄᴇ-ᴄᴏɴᴛʀᴏʟꜱ` — Live temporary voice room panel"
        ),
        inline=False
    )
    embed.set_image(url="https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80")
    embed.set_footer(
        text="RAI FAM 💗 • High Performance Esports & Vibes",
        icon_url=config.RAI_ICON_URL
    )
    return embed


class CommandCategorySelect(Select):
    def __init__(self):
        options = []
        for key, data in COMMAND_CATEGORIES.items():
            options.append(discord.SelectOption(
                label=data["label"],
                value=key,
                emoji=data["emoji"],
                description=f"[{data['bot']}] {data['description'][:45]}..."
            ))
        super().__init__(
            placeholder="⚡ Choose a command category to explore...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="master_cmd_category_select"
        )

    async def callback(self, interaction: discord.Interaction):
        cat_key = self.values[0]
        embed = build_category_embed(cat_key)
        await interaction.response.edit_message(embed=embed, view=self.view)


class MasterCommandHubView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(CommandCategorySelect())

    @discord.ui.button(label="Overview", emoji="🏠", style=discord.ButtonStyle.secondary, custom_id="mch_home", row=1)
    async def home_btn(self, interaction: discord.Interaction, button: Button):
        embed = build_overview_embed()
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Claim Daily", emoji="🪙", style=discord.ButtonStyle.success, custom_id="mch_daily", row=1)
    async def daily_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            "🪙 **Daily Rai Coins:** Type `/daily` right here in `#🤖｜ʙᴏᴛ-ᴄᴏᴍᴍᴀɴᴅꜱ` to claim your coins and advance your streak!",
            ephemeral=True
        )

    @discord.ui.button(label="Find Squad (LFG)", emoji="⚔️", style=discord.ButtonStyle.primary, custom_id="mch_lfg", row=1)
    async def lfg_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            "⚔️ **Squad LFG:** Type `/lfg game: Valorant slots: 2` or visit `#⚔️｜ʟꜰɢ-ᴍᴀᴛᴄʜᴍᴀᴋɪɴɢ` to auto-create a private voice squad arena!",
            ephemeral=True
        )

    @discord.ui.button(label="Prestige Milestones", emoji="🏆", style=discord.ButtonStyle.secondary, custom_id="mch_milestones", row=1)
    async def milestones_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            "🏆 **Thor Apex Milestones:** Type `/milestones` to view all prestige level tiers (`Rookie` to `Thor Immortal`) and coin rewards!",
            ephemeral=True
        )

    @discord.ui.button(label="Music Remote", emoji="🎵", style=discord.ButtonStyle.secondary, custom_id="mch_music", row=1)
    async def music_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            "🎵 **Music Remote:** Join any voice channel and type `/controller` to launch the 1-click interactive audio remote!",
            ephemeral=True
        )


class Help(commands.Cog):
    """Unified Master Command Guide & Categorized Explorer for RAI FAM."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Open the master interactive categorized command guide.")
    @app_commands.describe(category="Optional category to open directly")
    async def help_cmd(self, ctx: commands.Context, category: Optional[str] = None):
        """Browse all commands across RAI VIBES, RAI PLAY, and RAI SENTINEL."""
        if category and category.lower() in COMMAND_CATEGORIES:
            embed = build_category_embed(category.lower())
        else:
            embed = build_overview_embed()

        view = MasterCommandHubView()
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @commands.hybrid_command(name="postcommandhub", description="[ADMIN] Deploy the permanent Master Command Terminal to this channel.")
    @commands.has_permissions(administrator=True)
    async def post_command_hub(self, ctx: commands.Context):
        """Deploys the persistent interactive command directory."""
        embed = build_overview_embed()
        view = MasterCommandHubView()
        await ctx.channel.send(embed=embed, view=view)
        await ctx.send("✅ Master Command Terminal successfully deployed!", ephemeral=True)


async def setup(bot: commands.Bot):
    if "help" in bot.all_commands:
        bot.remove_command("help")
    await bot.add_cog(Help(bot))
