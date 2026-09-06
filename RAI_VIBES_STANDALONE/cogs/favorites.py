import json
from pathlib import Path
import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List

import config

FAVORITES_FILE = Path(__file__).resolve().parent.parent / "data" / "favorites.json"

def load_favorites() -> Dict[str, List[dict]]:
    if not FAVORITES_FILE.exists():
        FAVORITES_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    try:
        with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_favorites(data: Dict[str, List[dict]]):
    FAVORITES_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

class Favorites(commands.Cog):
    """Save and play your favorite songs directly on RAI VIBES 💗."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_group(name="favorite", aliases=["fav"], description="Manage your personal favorite music tracks.")
    async def favorite(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send("⚡ Use `/favorite add`, `/favorite list`, or `/favorite play`!", ephemeral=True)

    @favorite.command(name="add", description="Save currently playing song to your personal favorites.")
    async def add(self, ctx: commands.Context):
        music_cog = self.bot.get_cog("Music")
        player = music_cog.get_player(ctx.guild.id) if music_cog else None

        if not player or not player.current:
            return await ctx.send("❌ Nothing is currently playing to save as favorite.", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_favorites()
        if user_id not in data:
            data[user_id] = []

        # Check for duplicates
        if any(item["title"] == player.current.title for item in data[user_id]):
            return await ctx.send(f"⚠️ `{player.current.title}` is already in your favorites!", ephemeral=True)

        data[user_id].append({
            "title": player.current.title,
            "url": player.current.webpage_url,
            "duration": player.current.duration,
            "thumbnail": player.current.thumbnail,
            "uploader": player.current.uploader
        })
        save_favorites(data)

        embed = discord.Embed(
            title="❤️ Added to Favorites",
            description=f"Saved **[{player.current.title}]({player.current.webpage_url})** to your personal collection!",
            color=config.COLOR_GOLD
        )
        embed.set_thumbnail(url=player.current.thumbnail)
        embed.set_footer(text=f"Total Favorites: {len(data[user_id])}", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @favorite.command(name="list", description="View all your saved favorite tracks.")
    async def list_favs(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        data = load_favorites()
        favs = data.get(user_id, [])

        if not favs:
            return await ctx.send("❤️ You haven't added any favorite songs yet. Use `/favorite add` while playing a track!", ephemeral=True)

        embed = discord.Embed(
            title=f"❤️ {ctx.author.display_name}'s Favorite Tracks",
            color=config.COLOR_PRIMARY
        )
        embed.set_author(name="RAI VIBES 💗 Favorites", icon_url=config.RAI_ICON_URL)

        lines = []
        for i, item in enumerate(favs[:20], 1):
            lines.append(f"`{i}.` [{item['title'][:40]}]({item['url']}) - `{item['uploader'][:20]}`")

        embed.description = "\n".join(lines)
        embed.set_footer(text=f"Showing {min(len(favs), 20)} of {len(favs)} songs • Use /favorite play to enqueue all", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @favorite.command(name="play", description="Queue all your saved favorite tracks.")
    async def play_favs(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        data = load_favorites()
        favs = data.get(user_id, [])

        if not favs:
            return await ctx.send("❤️ Your favorites list is empty.", ephemeral=True)

        music_cog = self.bot.get_cog("Music")
        if not music_cog:
            return await ctx.send("❌ Music engine not available.", ephemeral=True)

        voice_client = await music_cog.ensure_voice(ctx)
        if not voice_client:
            return

        player = music_cog.get_or_create_player(ctx.guild)
        player.voice_client = voice_client
        player.text_channel = ctx.channel

        from cogs.music import Song
        for item in favs:
            song = Song(
                data={
                    "title": item["title"],
                    "search_query": item["title"],
                    "url": None,
                    "webpage_url": item["url"],
                    "duration": item["duration"],
                    "thumbnail": item["thumbnail"],
                    "uploader": item["uploader"]
                },
                requester=ctx.author,
                source_type="favorite"
            )
            player.queue.append(song)

        embed = discord.Embed(
            title="⚡ Enqueued Personal Favorites",
            description=f"Added **{len(favs)} favorite track(s)** to the RAI VIBES 💗 queue!",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=favs[0]["thumbnail"] if favs else config.RAI_ICON_URL)
        embed.set_footer(text="RAI VIBES 💗 • Command The Power", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Favorites(bot))
