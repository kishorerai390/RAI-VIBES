import discord
from discord.ext import commands
from discord import app_commands
import random
from typing import Optional

import config

AI_RESPONSES = {
    "movie": [
        "If you want mind-bending sci-fi, watch **Interstellar** or **Inception**. If you want pure adrenaline, put on **Mad Max: Fury Road**!",
        "For a cozy night with great vibes, stream **Spirited Away** or **The Grand Budapest Hotel** with the squad in `🎥・Cinema Theater 1`.",
        "Check out **Spider-Man: Across the Spider-Verse** — the visual animation and soundtrack are absolute 10/10 masterworks."
    ],
    "music": [
        "Try putting on our **Lo-Fi Chill Radio** (`/radio lofi`) or queuing up some synthwave with `/bassboost` enabled!",
        "For late night chill vibes, queue up The Weeknd's *After Hours* or Daft Punk's *Random Access Memories*.",
        "Looking for deep beats? Try French 79, Lane 8, or ODESZA for atmospheric study and chillout sessions."
    ],
    "anime": [
        "Top anime recommendation: **Jujutsu Kaisen** for high-octane action, or **Frieren: Beyond Journey's End** for stunning storytelling!",
        "If you love mystery and mind games, **Death Note** and **Attack on Titan** are unmissable classics.",
        "For stunning aesthetic visuals and emotional themes, **Your Name** and **A Silent Voice** are peak cinema."
    ],
    "general": [
        "Welcome to the Apex Lounge! I'm here to ensure the music stays loud (up to 200%), movies stay streaming, and the vibes remain high. What's on your mind?",
        "Everything in RAI FAM💗 is set up for good times. Feel free to hop into any voice lounge, queue your favorite tracks, or host a watch party!",
        "Need a tune? Drop `/play <song>` or mention me directly! Need a movie? Check `/imdb` or `/pick_movie`!"
    ]
}

class AIAssistant(commands.Cog):
    """Conversational AI Lounge & Media Recommendation Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="ask_apex", description="Ask the APEX AI assistant anything about movies, music, or chilling out.")
    @app_commands.describe(query="Your question or topic")
    async def ask_apex(self, ctx: commands.Context, query: str):
        q_lower = query.lower()
        
        # Categorize intelligent response
        if any(w in q_lower for w in ["movie", "film", "cinema", "watch", "show", "series"]):
            resp = random.choice(AI_RESPONSES["movie"])
            prefix = "🎬 **Cinema Insights:**"
        elif any(w in q_lower for w in ["music", "song", "track", "album", "radio", "beats", "bass"]):
            resp = random.choice(AI_RESPONSES["music"])
            prefix = "🎵 **Audio Recommendation:**"
        elif any(w in q_lower for w in ["anime", "manga", "weeb", "japan", "animation"]):
            resp = random.choice(AI_RESPONSES["anime"])
            prefix = "🌸 **Anime Pick:**"
        elif "who are you" in q_lower or "what can you do" in q_lower:
            resp = (
                "I am **APEX VIBES** (RAI VIBES 💗)! ⚡\n"
                "I run 200% volume audio playback, 24/7 radio stations, audio filters, movie schedules, "
                "dynamic temporary voice rooms, trivia mini-games, and automated server management for **RAI FAM💗**!"
            )
            prefix = "⚡ **About APEX VIBES:**"
        else:
            resp = random.choice(AI_RESPONSES["general"])
            prefix = "🤖 **Apex AI:**"

        embed = discord.Embed(
            title=f"🤖 Apex Assistant • Query",
            description=f"**You asked:** *\"{query}\"*\n\n{prefix}\n{resp}",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/4712/4712035.png")
        embed.set_footer(text="Powered by Apex Vibes AI", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="recommend", description="Get an instant top-tier recommendation for movies, anime, music, or games.")
    @app_commands.describe(category="What type of recommendation do you want?")
    @app_commands.choices(category=[
        app_commands.Choice(name="🎬 Movie / Cinema", value="movie"),
        app_commands.Choice(name="🎵 Music / Beats", value="music"),
        app_commands.Choice(name="🌸 Anime Masterpiece", value="anime"),
    ])
    async def recommend(self, ctx: commands.Context, category: app_commands.Choice[str]):
        picks = AI_RESPONSES.get(category.value, AI_RESPONSES["general"])
        selected = random.choice(picks)

        embed = discord.Embed(
            title=f"✨ Recommended For You: {category.name}",
            description=selected,
            color=config.COLOR_GOLD
        )
        embed.set_footer(text="Ask for another anytime with /recommend", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AIAssistant(bot))
