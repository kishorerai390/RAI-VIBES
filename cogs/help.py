import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Select
from typing import Optional

import config

HELP_CATEGORIES = {
    "core": {
        "label": "Core Music Playback",
        "emoji": "🎵",
        "description": "Essential streaming, queue, and playback commands",
        "color": 0xFF69B4,
        "fields": [
            ("`/play <song or url>`", "Stream any song or playlist from YouTube, Spotify, or SoundCloud."),
            ("`/controller`", "Open the interactive button controller remote."),
            ("`/pause` & `/resume`", "Pause or unpause current audio streaming."),
            ("`/skip`", "Vote or skip immediately to the next queued song."),
            ("`/queue`", "Browse upcoming songs with interactive pagination."),
            ("`/nowplaying`", "View real-time progress bar, track details, and requester."),
            ("`/volume <percentage>`", "Adjust volume from 0% to 200% with audio boost."),
            ("`/loop <track|queue|off>`", "Set repeat mode for the current song or entire playlist."),
            ("`/shuffle`", "Randomize the playback order of queued songs."),
            ("`/seek <time>`", "Fast-forward or jump directly to a timestamp (e.g. `1:30`).")
        ]
    },
    "filters": {
        "label": "Audiophile Studio & FX",
        "emoji": "🎧",
        "description": "8D Spatial audio, Bass Boost, Nightcore, Karaoke & FX",
        "color": 0x9B59B6,
        "fields": [
            ("`/filters <preset>`", "Apply audio filters: `8d`, `bassboost`, `nightcore`, `vaporwave`, `karaoke`."),
            ("`/8d`", "Immersive 360-degree rotating spatial surround sound."),
            ("`/bassboost <level>`", "Sub-bass boost (`low`, `medium`, `high`, `hardcore`)."),
            ("`/nightcore`", "High-energy pitch and tempo speedup."),
            ("`/vaporwave`", "Slowed + reverb retro aesthetic vibe."),
            ("`/karaoke`", "Real-time vocal frequency cancellation for singing along."),
            ("`/loudnorm`", "EBU R128 loudness normalization to balance quiet & loud songs."),
            ("`/ambience <preset>`", "Stream soothing background audio loops (`rain`, `fireplace`, `cafe`, `waves`).")
        ]
    },
    "radio": {
        "label": "24/7 Live Radio Sanctuaries",
        "emoji": "📻",
        "description": "Non-stop live radio streams & stay-in-VC mode",
        "color": 0xF1C40F,
        "fields": [
            ("`/radio <station>`", "Stream 24/7 curated live radio (Tamil Nadu FM, AIR Kodai, SomaFM Lofi, Synthwave, Gaming)."),
            ("`/tamilnadufm` (or `!tnfm`)", "Instant shortcut: Stream Tamil Panpalai Gold 24/7 non-stop."),
            ("`/stay247 <enable|disable>`", "Keep the bot in the voice lounge 24/7 even when empty.")
        ]
    },
    "aidj": {
        "label": "AI DJ & Smart Discovery",
        "emoji": "🤖",
        "description": "AI-powered song recommendations and mood matching",
        "color": 0x00CEC9,
        "fields": [
            ("`/aidj <mood>`", "AI DJ curates songs dynamically based on the requested vibe or channel mood."),
            ("`/favorite add`", "Save the currently playing song to your personal favorites."),
            ("`/favorite play`", "Queue your saved favorite tracks into the voice channel."),
            ("`/lyrics [song]`", "Fetch synchronized Genius lyrics with album art.")
        ]
    },
    "games": {
        "label": "Music Trivia & Party Games",
        "emoji": "🎮",
        "description": "Competitive music quiz and interactive soundboard",
        "color": 0xFF7675,
        "fields": [
            ("`/quiz <rounds>`", "Start a server-wide music trivia contest where members race to guess the song!"),
            ("`/soundboard`", "Browse and trigger funny sound effects and meme audio in voice.")
        ]
    },
    "admin": {
        "label": "DJ Controls & Server Settings",
        "emoji": "⚙️",
        "description": "Server controller setup, DJ role, and permissions",
        "color": 0x747D8C,
        "fields": [
            ("`/controllersetup [channel]`", "Deploy a permanent, persistent interactive player panel in your music channel!"),
            ("`/dj role <role>`", "Set a dedicated DJ role for advanced playback management."),
            ("`/dj mode <on|off>`", "Restrict skipping and volume controls to DJ role holders."),
            ("`/forceskip`", "Bypass voting and skip immediately (Admin/DJ only).")
        ]
    }
}


class HelpCategorySelect(Select):
    def __init__(self):
        options = []
        for key, data in HELP_CATEGORIES.items():
            options.append(discord.SelectOption(
                label=data["label"],
                value=key,
                emoji=data["emoji"],
                description=data["description"]
            ))
        super().__init__(
            placeholder="Choose a command category to explore...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="help_category_select"
        )

    async def callback(self, interaction: discord.Interaction):
        chosen = self.values[0]
        cat = HELP_CATEGORIES[chosen]

        embed = discord.Embed(
            title=f"{cat['emoji']} {cat['label']}",
            description=f"*{cat['description']}*\n\n✦ ───────────────────────────── ✦",
            color=cat["color"]
        )
        for cmd_name, cmd_desc in cat["fields"]:
            embed.add_field(name=cmd_name, value=cmd_desc, inline=False)

        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="RAI VIBES 💗 • Use /controller for instant 1-click buttons!", icon_url=config.RAI_ICON_URL)

        await interaction.response.edit_message(embed=embed, view=self.view)


class HelpMenuView(View):
    def __init__(self):
        super().__init__(timeout=180)
        self.add_item(HelpCategorySelect())


class Help(commands.Cog):
    """Interactive categorized Command Guide & Explorer for RAI VIBES 💗."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Open the interactive categorized command guide.")
    async def help_cmd(self, ctx: commands.Context, category: Optional[str] = None):
        """Browse all 59+ commands grouped neatly into 6 interactive categories."""
        embed = discord.Embed(
            title="🌸 RAI VIBES 💗 COMMAND EXPLORER",
            description=(
                "✨ **Welcome to the RAI VIBES 💗 Command Center!**\n\n"
                "We offer a massive suite of **59+ features** ranging from audiophile filters to 24/7 radio and AI DJ recommendations.\n\n"
                "🎯 **No typing needed:** Use **`/controller`** anytime for an interactive player with buttons!\n\n"
                "📂 **Select a category from the dropdown menu below** to view detailed command lists:\n"
                "• 🎵 **Core Music Playback** — Play, skip, queue, volume, loop\n"
                "• 🎧 **Audiophile Studio & FX** — 8D audio, bass boost, nightcore, karaoke\n"
                "• 📻 **24/7 Live Radio** — Tamil Nadu FM, lofi, synthwave, ambient\n"
                "• 🤖 **AI DJ & Discovery** — Mood matching, lyrics, favorites\n"
                "• 🎮 **Trivia & Soundboard** — Music quiz, SFX soundboard\n"
                "• ⚙️ **DJ & Server Settings** — Persistent controller setup, DJ role"
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_image(url="https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=1200&q=80")
        embed.set_footer(text="RAI VIBES 💗 • Premium Community Audio Engine", icon_url=config.RAI_ICON_URL)

        view = HelpMenuView()
        await ctx.send(embed=embed, view=view, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Help(bot))
