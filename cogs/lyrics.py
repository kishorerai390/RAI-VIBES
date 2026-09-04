import re
import urllib.parse
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

import config

class Lyrics(commands.Cog):
    """Song Lyrics Lookup for RAI VIBES 💗."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def fetch_lyrics(self, song_title: str) -> Optional[dict]:
        """Fetches lyrics using lyrics API."""
        # Clean title (remove (Official Video), [HQ], feat, etc.)
        clean_title = re.sub(r"\(.*?\)|\[.*?\]|ft\..*|feat\..*", "", song_title, flags=re.IGNORECASE).strip()
        encoded = urllib.parse.quote(clean_title)
        api_url = f"https://some-random-api.com/lyrics?title={encoded}"

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(api_url, timeout=10) as resp:
                    if resp.status == 200:
                        return await resp.json()
        except Exception:
            pass
        return None

    @commands.hybrid_command(name="lyrics", aliases=["ly"], description="Get lyrics for the currently playing song or search by name.")
    @app_commands.describe(song="Optional song name to search lyrics for")
    async def lyrics(self, ctx: commands.Context, *, song: Optional[str] = None):
        await ctx.defer()

        target_song = song
        if not target_song:
            music_cog = self.bot.get_cog("Music")
            player = music_cog.get_player(ctx.guild.id) if music_cog else None
            if player and player.current:
                target_song = player.current.title
            else:
                return await ctx.send("❌ No music currently playing. Please specify a song name: `/lyrics <song>`")

        data = await self.fetch_lyrics(target_song)
        if not data or "lyrics" not in data:
            return await ctx.send(f"❌ Could not find lyrics for: `{target_song}`")

        lyrics_text = data.get("lyrics", "")
        if len(lyrics_text) > 4000:
            lyrics_text = lyrics_text[:3990] + "...\n*(Lyrics truncated)*"

        embed = discord.Embed(
            title=f"📜 Lyrics: {data.get('title', target_song)}",
            description=lyrics_text,
            color=config.COLOR_PRIMARY
        )
        embed.set_author(name=data.get("author", "RAI VIBES 💗 Lyrics"), icon_url=config.RAI_ICON_URL)
        if data.get("thumbnail", {}).get("genius"):
            embed.set_thumbnail(url=data["thumbnail"]["genius"])
        embed.set_footer(text="RAI VIBES 💗 • Lyrics Finder", icon_url=config.RAI_ICON_URL)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Lyrics(bot))
