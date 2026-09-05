import re
import urllib.parse
import aiohttp
import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, List, Dict

import config

class Lyrics(commands.Cog):
    """Universal Song Lyrics Engine for RAI VIBES 💗 (Powered by LRCLIB, Genius & LRCLIB Synced Engine)."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def clean_title_candidates(self, raw_title: str) -> List[str]:
        """Generates cleaned search queries for accurate lyrics matching."""
        # Strip @ symbols but preserve creator handles
        t = raw_title.replace("@", "")

        junk_patterns = [
            r"\([^)]*(?:music|official|video|audio|lyric|lyrics|lyrical|song|hd|4k|remastered|visualizer|prod|prod\.|feat|feat\.|ft|ft\.|full)[^)]*\)",
            r"\[[^\]]*(?:music|official|video|audio|lyric|lyrics|lyrical|song|hd|4k|remastered|visualizer|prod|prod\.|feat|feat\.|ft|ft\.|full)[^\]]*\]",
            r"(?:official\s+music\s+video|official\s+video|music\s+video|official\s+audio|lyric\s+video|lyrical\s+video|full\s+song|full\s+video)"
        ]
        cleaned = t
        for p in junk_patterns:
            cleaned = re.sub(p, "", cleaned, flags=re.IGNORECASE)

        candidates = []

        # Split by common metadata separators
        parts = [p.strip() for p in re.split(r"[\-\|\/:]", cleaned) if p.strip()]

        # 1. Individual segments (e.g., 'Radhimaa', 'SaiAbhyankkar')
        for p in parts:
            p_clean = re.sub(r"[^\w\s\']", " ", p).strip()
            p_clean = re.sub(r"\s+", " ", p_clean)
            if len(p_clean) >= 2 and p_clean not in candidates:
                candidates.append(p_clean)

        # 2. Combined artist + track segments
        if len(parts) >= 2:
            c1 = f"{parts[0]} {parts[1]}".strip()
            c2 = f"{parts[1]} {parts[0]}".strip()
            if c1 not in candidates:
                candidates.append(c1)
            if c2 not in candidates:
                candidates.append(c2)

        # 3. Overall cleaned string
        overall = re.sub(r"[^\w\s\']", " ", cleaned).strip()
        overall = re.sub(r"\s+", " ", overall)
        if overall and overall not in candidates:
            candidates.append(overall)

        return [c for c in candidates if len(c) > 1]

    async def fetch_lyrics(self, song_title: str) -> Optional[Dict[str, str]]:
        """Fetches lyrics using LRCLIB API with automatic SomeRandomAPI fallback."""
        candidates = self.clean_title_candidates(song_title)

        async with aiohttp.ClientSession(headers={"User-Agent": "RaiVibes/2.0"}) as session:
            # 1. Search LRCLIB (Millions of songs, Indian, Cinema & Global, Synced & Plain)
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
