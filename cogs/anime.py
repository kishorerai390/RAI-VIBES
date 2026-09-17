import logging
import re
import html
import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from typing import Optional

logger = logging.getLogger("Anime")

ANILIST_API_URL = "https://graphql.anilist.co"

ANILIST_QUERY = """
query ($search: String, $type: MediaType) {
  Media (search: $search, type: $type) {
    id
    title {
      romaji
      english
      native
    }
    type
    format
    status
    description
    episodes
    chapters
    volumes
    averageScore
    genres
    bannerImage
    coverImage {
      extraLarge
      large
      color
    }
    siteUrl
    seasonYear
  }
}
"""

def clean_html(raw_html: Optional[str]) -> str:
    if not raw_html:
        return "No synopsis available."
    clean = re.sub(r"<br\s*/?>", "\n", raw_html)
    clean = re.sub(r"<.*?>", "", clean)
    clean = html.unescape(clean)
    if len(clean) > 500:
        clean = clean[:497] + "..."
    return clean

class Anime(commands.Cog):
    """Anime & Manga Interactive Search Engine powered by AniList."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="anime", description="Search for any anime title, ratings, genres, and synopsis!")
    @app_commands.describe(title="Name of the anime (e.g. Demon Slayer, Jujutsu Kaisen, Frieren)")
    async def anime_search(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer()

        variables = {"search": title, "type": "ANIME"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    ANILIST_API_URL,
                    json={"query": ANILIST_QUERY, "variables": variables},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send(f"❌ Could not find anime matching `{title}`.", ephemeral=True)
                    data = await resp.json()

            media = data.get("data", {}).get("Media")
            if not media:
                return await interaction.followup.send(f"❌ No anime found for `{title}`.", ephemeral=True)

            eng_title = media["title"].get("english") or media["title"].get("romaji")
            romaji_title = media["title"].get("romaji")
            score = media.get("averageScore")
            score_text = f"⭐ `{score}%`" if score else "N/A"
            episodes = media.get("episodes") or "Unknown"
            status = media.get("status", "UNKNOWN").replace("_", " ").title()
            year = media.get("seasonYear") or "N/A"
            genres = ", ".join(media.get("genres", [])[:4]) or "Various"
            synopsis = clean_html(media.get("description"))

            # Color theme
            embed_color = 0xFF69B4
            if media.get("coverImage", {}).get("color"):
                try:
                    embed_color = int(media["coverImage"]["color"].lstrip("#"), 16)
                except Exception:
                    pass

            embed = discord.Embed(
                title=f"🌸 {eng_title}",
                url=media.get("siteUrl", "https://anilist.co"),
                description=f"*{romaji_title}*\n\n{synopsis}",
                color=embed_color
            )

            if media.get("coverImage", {}).get("large"):
                embed.set_thumbnail(url=media["coverImage"]["large"])
            if media.get("bannerImage"):
                embed.set_image(url=media["bannerImage"])

            embed.add_field(name="📊 Score", value=score_text, inline=True)
            embed.add_field(name="🎞️ Episodes", value=f"`{episodes}`", inline=True)
            embed.add_field(name="📅 Year", value=f"`{year}`", inline=True)
            embed.add_field(name="📌 Status", value=f"`{status}`", inline=True)
            embed.add_field(name="🎭 Genres", value=f"`{genres}`", inline=True)

            embed.set_footer(text="RAI FAM 💗 Anime Hub • Powered by AniList", icon_url="https://anilist.co/img/icons/icon.svg")

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="View on AniList", url=media.get("siteUrl", "https://anilist.co"), emoji="🔗"))

            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error querying anime '{title}': {e}")
            await interaction.followup.send(f"❌ An error occurred searching for anime: `{e}`", ephemeral=True)

    @app_commands.command(name="manga", description="Search for any manga or light novel title on AniList!")
    @app_commands.describe(title="Name of the manga (e.g. Berserk, Chainsaw Man, Solo Leveling)")
    async def manga_search(self, interaction: discord.Interaction, title: str):
        await interaction.response.defer()

        variables = {"search": title, "type": "MANGA"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    ANILIST_API_URL,
                    json={"query": ANILIST_QUERY, "variables": variables},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status != 200:
                        return await interaction.followup.send(f"❌ Could not find manga matching `{title}`.", ephemeral=True)
                    data = await resp.json()

            media = data.get("data", {}).get("Media")
            if not media:
                return await interaction.followup.send(f"❌ No manga found for `{title}`.", ephemeral=True)

            eng_title = media["title"].get("english") or media["title"].get("romaji")
            romaji_title = media["title"].get("romaji")
            score = media.get("averageScore")
            score_text = f"⭐ `{score}%`" if score else "N/A"
            chapters = media.get("chapters") or "Ongoing"
            status = media.get("status", "UNKNOWN").replace("_", " ").title()
            genres = ", ".join(media.get("genres", [])[:4]) or "Various"
            synopsis = clean_html(media.get("description"))

            embed_color = 0x9B59B6
            if media.get("coverImage", {}).get("color"):
                try:
                    embed_color = int(media["coverImage"]["color"].lstrip("#"), 16)
                except Exception:
                    pass

            embed = discord.Embed(
                title=f"📖 {eng_title}",
                url=media.get("siteUrl", "https://anilist.co"),
                description=f"*{romaji_title}*\n\n{synopsis}",
                color=embed_color
            )

            if media.get("coverImage", {}).get("large"):
                embed.set_thumbnail(url=media["coverImage"]["large"])
            if media.get("bannerImage"):
                embed.set_image(url=media["bannerImage"])

            embed.add_field(name="📊 Score", value=score_text, inline=True)
            embed.add_field(name="📚 Chapters", value=f"`{chapters}`", inline=True)
            embed.add_field(name="📌 Status", value=f"`{status}`", inline=True)
            embed.add_field(name="🎭 Genres", value=f"`{genres}`", inline=True)

            embed.set_footer(text="RAI FAM 💗 Manga Hub • Powered by AniList", icon_url="https://anilist.co/img/icons/icon.svg")

            view = discord.ui.View()
            view.add_item(discord.ui.Button(label="View on AniList", url=media.get("siteUrl", "https://anilist.co"), emoji="🔗"))

            await interaction.followup.send(embed=embed, view=view)

        except Exception as e:
            logger.error(f"Error querying manga '{title}': {e}")
            await interaction.followup.send(f"❌ An error occurred searching for manga: `{e}`", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Anime(bot))
