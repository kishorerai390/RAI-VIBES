import json
import logging
import urllib.parse
import aiohttp
import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Optional

import config

logger = logging.getLogger("AnimeFeed")

ANIME_UPDATES_CHANNEL_ID = 1546097792915873842
HIANIME_BASE_URL = "https://hianime.at"

class AnimeStreamButton(discord.ui.View):
    """Interactive button to stream directly on HiAnime.at."""
    def __init__(self, anime_title: str):
        super().__init__(timeout=None)
        search_query = urllib.parse.quote_plus(anime_title)
        stream_url = f"{HIANIME_BASE_URL}/search?keyword={search_query}"
        self.add_item(discord.ui.Button(label="Stream on HiAnime.at", url=stream_url, emoji="▶️", style=discord.ButtonStyle.link))
        self.add_item(discord.ui.Button(label="Join Cinema Theater", url="https://discord.com/channels/1457382179981099090/1545502762467328185", emoji="🍿", style=discord.ButtonStyle.link))


class AnimeFeed(commands.Cog):
    """HiAnime.at Anime Search, Trending Spotlights & Automated Release Feeds."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_anime_spotlight.start()

    def cog_unload(self):
        self.daily_anime_spotlight.cancel()

    async def fetch_anime(self, query: str) -> Optional[dict]:
        """Fetch anime details from Jikan public API."""
        url = f"https://api.jikan.moe/v4/anime?q={urllib.parse.quote(query)}&limit=1"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        results = data.get("data", [])
                        if results:
                            return results[0]
        except Exception as e:
            logger.error(f"Error fetching anime '{query}': {e}")
        return None

    async def fetch_top_anime(self) -> list:
        """Fetch top airing anime."""
        url = "https://api.jikan.moe/v4/top/anime?filter=airing&limit=5"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=10) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return data.get("data", [])
        except Exception as e:
            logger.error(f"Error fetching top anime: {e}")
        return []

    @tasks.loop(hours=24)
    async def daily_anime_spotlight(self):
        """Posts daily trending anime spotlight to #📺・anime-updates."""
        await self.bot.wait_until_ready()
        channel = self.bot.get_channel(ANIME_UPDATES_CHANNEL_ID)
        if not channel:
            return

        top_list = await self.fetch_top_anime()
        if not top_list:
            return

        featured = top_list[0]
        title = featured.get("title_english") or featured.get("title", "Popular Anime")
        score = featured.get("score", "N/A")
        episodes = featured.get("episodes") or "Ongoing"
        synopsis = (featured.get("synopsis") or "No synopsis available.")[:400] + "..."
        image_url = featured.get("images", {}).get("jpg", {}).get("large_image_url")

        genres = [g["name"] for g in featured.get("genres", [])]
        genres_str = ", ".join(genres) if genres else "Action, Adventure"

        embed = discord.Embed(
            title=f"🌸 DAILY HIANIME SPOTLIGHT: {title} ✨",
            description=(
                f"### 🍿 Trending on [HiAnime.at]({HIANIME_BASE_URL})\n\n"
                f"{synopsis}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• ⭐ **Rating:** `{score} / 10`\n"
                f"• 📺 **Episodes:** `{episodes}`\n"
                f"• 🏷️ **Genres:** `{genres_str}`\n"
                f"• 🎬 **Watch Parties:** <#1545502762467328185> & <#1545803585550426234>\n\n"
                f"👉 **Click below to stream in 1080p Ultra-HD!**"
            ),
            color=0xFF2A85
        )
        if image_url:
            embed.set_image(url=image_url)
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
        embed.set_footer(text="RAI FAM 💗 • Official HiAnime.at Release Hub", icon_url=config.RAI_ICON_URL)

        view = AnimeStreamButton(title)
        try:
            await channel.send(embed=embed, view=view)
            logger.info(f"Published Daily Anime Spotlight for '{title}' in #anime-updates")
        except Exception as e:
            logger.error(f"Failed to post anime spotlight: {e}")

    @daily_anime_spotlight.before_loop
    async def before_spotlight(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(name="anime", description="Search any anime and get direct 1080p streaming links on HiAnime.at!")
    @app_commands.describe(title="Name of the anime to search (e.g. Solo Leveling, Jujutsu Kaisen)")
    async def anime_search(self, ctx: commands.Context, *, title: str):
        await ctx.defer()
        anime = await self.fetch_anime(title)
        if not anime:
            return await ctx.send(f"❌ Could not find anime matching **'{title}'**. Try searching directly on **[HiAnime.at](https://hianime.at)**!", ephemeral=True)

        anime_title = anime.get("title_english") or anime.get("title", title)
        jp_title = anime.get("title_japanese") or ""
        score = anime.get("score", "N/A")
        episodes = anime.get("episodes") or "Ongoing"
        status = anime.get("status", "Unknown")
        synopsis = (anime.get("synopsis") or "No synopsis available.")[:450] + "..."
        image_url = anime.get("images", {}).get("jpg", {}).get("large_image_url")

        genres = [g["name"] for g in anime.get("genres", [])]
        genres_str = ", ".join(genres) if genres else "Anime"

        embed = discord.Embed(
            title=f"📺 {anime_title}",
            description=(
                f"*{jp_title}*\n\n"
                f"{synopsis}\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"• ⭐ **MAL Score:** `{score}/10`\n"
                f"• 🎬 **Episodes:** `{episodes}` ({status})\n"
                f"• 🏷️ **Genres:** `{genres_str}`\n"
                f"• ⚡ **Stream Quality:** `1080p HD & 4K`"
            ),
            color=0xFF2A85
        )
        if image_url:
            embed.set_thumbnail(url=image_url)
        embed.set_footer(text="RAI FAM 💗 • Powered by HiAnime.at", icon_url=config.RAI_ICON_URL)

        view = AnimeStreamButton(anime_title)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="trendinganime", aliases=["topanime"], description="View top trending anime series currently airing.")
    async def trending_anime(self, ctx: commands.Context):
        await ctx.defer()
        top_list = await self.fetch_top_anime()
        if not top_list:
            return await ctx.send("❌ Could not load trending anime right now. Visit **[HiAnime.at](https://hianime.at)**!", ephemeral=True)

        embed = discord.Embed(
            title="🔥 TOP TRENDING ANIME ON HIANIME.AT 🌸",
            description="Here are the hottest anime series streaming right now:\n",
            color=0xFF2A85
        )

        for i, a in enumerate(top_list[:5], 1):
            t = a.get("title_english") or a.get("title", "Unknown")
            score = a.get("score", "N/A")
            eps = a.get("episodes") or "Ongoing"
            search_q = urllib.parse.quote_plus(t)
            embed.add_field(
                name=f"#{i} {t}",
                value=f"• ⭐ **Rating:** `{score}` | 📺 **Eps:** `{eps}`\n• 👉 **[Watch on HiAnime.at]({HIANIME_BASE_URL}/search?keyword={search_q})**",
                inline=False
            )

        if top_list and top_list[0].get("images", {}).get("jpg", {}).get("large_image_url"):
            embed.set_thumbnail(url=top_list[0]["images"]["jpg"]["large_image_url"])
        embed.set_footer(text="RAI FAM 💗 • Stream all episodes free on HiAnime.at", icon_url=config.RAI_ICON_URL)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AnimeFeed(bot))
