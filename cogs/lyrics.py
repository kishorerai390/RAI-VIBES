import re
import urllib.parse
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict

import config

class Lyrics(commands.Cog):
    """Universal Song Lyrics Engine for RAI VIBES 💗 (Powered by LRCLIB & Genius)."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def clean_title_candidates(self, raw_title: str) -> List[str]:
        """Generates cleaned search queries for accurate lyrics matching."""
        junk_patterns = [
            r"\(official\s+music\s+video\)", r"\[official\s+music\s+video\]",
            r"\(official\s+video\)", r"\[official\s+video\]",
            r"\(official\s+audio\)", r"\[official\s+audio\]",
            r"\(lyric\s+video\)", r"\[lyric\s+video\]",
            r"\(lyrical\s+video\)", r"\[lyrical\s+video\]",
            r"\(lyrics\)", r"\[lyrics\]", r"\(lyrical\)", r"\[lyrical\]",
            r"\(audio\)", r"\[audio\]", r"\(hd\)", r"\[hd\]", r"\(4k\)", r"\[4k\]",
            r"\(full\s+song\)", r"\[full\s+song\]", r"\(full\s+video\)",
            r"official\s+music\s+video", r"official\s+video", r"official\s+audio",
            r"lyric\s+video", r"lyrical\s+video", r"full\s+song", r"full\s+video"
        ]
        
        t = raw_title
        for pattern in junk_patterns:
            t = re.sub(pattern, "", t, flags=re.IGNORECASE)

        candidates = [t.strip()]
        
        if "|" in raw_title:
            candidates.append(raw_title.split("|")[0].strip())
        if "-" in raw_title:
            candidates.append(raw_title.split("-")[0].strip())
            candidates.append(raw_title.replace("-", " ").strip())

        # Parentheses & feat stripping
        broad = re.sub(r"\(.*?\)|\[.*?\]|ft\..*|feat\..*|prod\..*", "", raw_title, flags=re.IGNORECASE).strip()
        if broad and broad not in candidates:
            candidates.append(broad)

        # Remove duplicate or empty candidates while preserving order
        seen = set()
        unique_candidates = []
        for c in candidates:
            c_clean = " ".join(c.split())
            if c_clean and c_clean.lower() not in seen:
                seen.add(c_clean.lower())
                unique_candidates.append(c_clean)

        return unique_candidates

    async def fetch_lyrics(self, song_title: str) -> Optional[Dict[str, str]]:
        """Fetches lyrics using LRCLIB API with automatic SomeRandomAPI fallback."""
        candidates = self.clean_title_candidates(song_title)

        async with aiohttp.ClientSession(headers={"User-Agent": "RaiVibes/2.0"}) as session:
            # 1. Search LRCLIB (Millions of songs, Indian & Global, Synced & Plain)
            for query in candidates:
                encoded = urllib.parse.quote(query)
                lrclib_url = f"https://lrclib.net/api/search?q={encoded}"
                try:
                    async with session.get(lrclib_url, timeout=6) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data and isinstance(data, list) and len(data) > 0:
                                for item in data:
                                    lyrics = item.get("plainLyrics") or item.get("syncedLyrics")
                                    if lyrics:
                                        # Clean synced timestamps if plain is not available
                                        if not item.get("plainLyrics") and item.get("syncedLyrics"):
                                            lyrics = re.sub(r"\[\d{2}:\d{2}\.\d{2}\]", "", lyrics).strip()
                                        return {
                                            "title": item.get("trackName", query),
                                            "author": item.get("artistName", "Artist"),
                                            "lyrics": lyrics,
                                            "source": "LRCLIB"
                                        }
                except Exception:
                    pass

            # 2. Fallback: SomeRandomAPI
            for query in candidates:
                encoded = urllib.parse.quote(query)
                sra_url = f"https://some-random-api.com/lyrics?title={encoded}"
                try:
                    async with session.get(sra_url, timeout=6) as resp:
                        if resp.status == 200:
                            data = await resp.json()
                            if data and "lyrics" in data and data["lyrics"]:
                                return {
                                    "title": data.get("title", query),
                                    "author": data.get("author", "Genius"),
                                    "lyrics": data["lyrics"],
                                    "thumbnail": data.get("thumbnail", {}).get("genius"),
                                    "source": "Genius"
                                }
                except Exception:
                    pass

        return None

    @commands.hybrid_command(name="lyrics", aliases=["ly"], description="Get synchronized lyrics for the currently playing song or search by name.")
    @app_commands.describe(song="Optional song name to search lyrics for")
    async def lyrics(self, ctx: commands.Context, *, song: Optional[str] = None):
        if ctx.interaction:
            await ctx.defer()

        target_song = song
        thumbnail_url = config.RAI_ICON_URL

        if not target_song:
            music_cog = self.bot.get_cog("Music")
            player = music_cog.get_player(ctx.guild.id) if music_cog else None
            if player and player.current:
                target_song = player.current.title
                thumbnail_url = player.current.thumbnail or config.RAI_ICON_URL
            else:
                return await ctx.send("❌ No music currently playing. Please specify a song name: `!lyrics <song>` or `/lyrics <song>`")

        data = await self.fetch_lyrics(target_song)
        if not data or "lyrics" not in data or not data["lyrics"]:
            return await ctx.send(f"⚠️ Could not find synchronized lyrics for: `{target_song}`")

        lyrics_text = data["lyrics"]
        if len(lyrics_text) > 4000:
            lyrics_text = lyrics_text[:3985] + "...\n*(Lyrics truncated)*"

        embed = discord.Embed(
            title=f"🎤 {data.get('title', target_song)}",
            description=f"```fix\n{lyrics_text}\n```" if len(lyrics_text) < 1800 else lyrics_text,
            color=config.COLOR_PRIMARY
        )
        embed.set_author(name=f"{data.get('author', 'Artist')} • Lyrics", icon_url=config.RAI_ICON_URL)
        embed.set_thumbnail(url=data.get("thumbnail") or thumbnail_url)
        embed.set_footer(text=f"RAI VIBES 💗 • Source: {data.get('source', 'Synced Lyrics')}", icon_url=config.RAI_ICON_URL)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Lyrics(bot))
