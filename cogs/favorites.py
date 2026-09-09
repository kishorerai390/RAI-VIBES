import io
import json
import time
from pathlib import Path
import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, List, Optional

import config

FAVORITES_FILE = Path(__file__).resolve().parent.parent / "data" / "favorites.json"
PLAYLISTS_FILE = Path(__file__).resolve().parent.parent / "data" / "playlists.json"

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

def load_playlists() -> Dict[str, Dict[str, List[dict]]]:
    if not PLAYLISTS_FILE.exists():
        PLAYLISTS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    try:
        with open(PLAYLISTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_playlists(data: Dict[str, Dict[str, List[dict]]]):
    PLAYLISTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(PLAYLISTS_FILE, "w", encoding="utf-8") as f:
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

    # =========================================================================
    # PLAYLIST SYSTEM (CUSTOM NAMED PLAYLISTS)
    # =========================================================================
    @commands.hybrid_group(name="playlist", aliases=["pl"], description="Manage your custom personal music playlists.")
    async def playlist(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await ctx.send(
                "⚡ **Playlist Commands:**\n"
                "• `/playlist create <name>` - Create a new empty playlist\n"
                "• `/playlist add <name> [query]` - Add playing track or song to playlist\n"
                "• `/playlist save_queue <name>` - Save currently active queue as playlist\n"
                "• `/playlist play <name>` - Enqueue an entire playlist\n"
                "• `/playlist list` - View your custom playlists\n"
                "• `/playlist view <name>` - Inspect songs in a playlist\n"
                "• `/playlist export <name>` - Export a playlist as a JSON backup file\n"
                "• `/playlist import_file <name>` - Import a playlist from a JSON backup file\n"
                "• `/playlist delete <name>` - Delete a playlist",
                ephemeral=True
            )

    @playlist.command(name="create", description="Create a new custom playlist.")
    @app_commands.describe(name="Name for your playlist (e.g. Chill, Workout, Vibes)")
    async def pl_create(self, ctx: commands.Context, name: str):
        clean_name = name.strip()
        if not clean_name or len(clean_name) > 40:
            return await ctx.send("❌ Playlist name must be between 1 and 40 characters.", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_playlists()
        if user_id not in data:
            data[user_id] = {}

        if clean_name.lower() in [k.lower() for k in data[user_id].keys()]:
            return await ctx.send(f"⚠️ You already have a playlist named `{clean_name}`!", ephemeral=True)

        data[user_id][clean_name] = []
        save_playlists(data)

        embed = discord.Embed(
            title="📂 Playlist Created",
            description=f"Successfully created playlist **`{clean_name}`**!\nAdd tracks using `/playlist add {clean_name}` or `/playlist save_queue {clean_name}`.",
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="RAI VIBES 💗 • Custom Playlists", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @playlist.command(name="add", description="Add currently playing song or search query to a playlist.")
    @app_commands.describe(name="Name of the playlist", query="Optional track title or link (defaults to currently playing track)")
    async def pl_add(self, ctx: commands.Context, name: str, query: Optional[str] = None):
        user_id = str(ctx.author.id)
        data = load_playlists()
        user_pls = data.get(user_id, {})

        matched_name = next((k for k in user_pls.keys() if k.lower() == name.strip().lower()), None)
        if not matched_name:
            return await ctx.send(f"❌ You don't have a playlist named `{name}`. Create one with `/playlist create {name}` first!", ephemeral=True)

        track_to_add = None
        if query:
            from cogs.music import Song
            resolved = await Song.create_source(query, ctx.author, self.bot.loop)
            if not resolved:
                return await ctx.send(f"❌ Could not find track for query `{query}`.", ephemeral=True)
            track_to_add = {
                "title": resolved.title,
                "url": resolved.webpage_url,
                "duration": resolved.duration,
                "thumbnail": resolved.thumbnail,
                "uploader": resolved.uploader
            }
        else:
            music_cog = self.bot.get_cog("Music")
            player = music_cog.get_player(ctx.guild.id) if music_cog else None
            if not player or not player.current:
                return await ctx.send("❌ No track currently playing. Please provide a song query or play a track first.", ephemeral=True)
            track_to_add = {
                "title": player.current.title,
                "url": player.current.webpage_url,
                "duration": player.current.duration,
                "thumbnail": player.current.thumbnail,
                "uploader": player.current.uploader
            }

        # Prevent duplicate entries
        if any(item["title"] == track_to_add["title"] for item in user_pls[matched_name]):
            return await ctx.send(f"⚠️ `{track_to_add['title']}` is already in playlist `{matched_name}`!", ephemeral=True)

        user_pls[matched_name].append(track_to_add)
        save_playlists(data)

        embed = discord.Embed(
            title="🎵 Track Added to Playlist",
            description=f"Added **[{track_to_add['title']}]({track_to_add['url']})** to **`{matched_name}`**!",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=track_to_add["thumbnail"])
        embed.set_footer(text=f"Total tracks in '{matched_name}': {len(user_pls[matched_name])}", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @playlist.command(name="save_queue", description="Save all songs currently in queue into a named playlist.")
    @app_commands.describe(name="Playlist name to save the queue into")
    async def pl_save_queue(self, ctx: commands.Context, name: str):
        music_cog = self.bot.get_cog("Music")
        player = music_cog.get_player(ctx.guild.id) if music_cog else None
        if not player or (not player.current and not player.queue):
            return await ctx.send("❌ No active queue or playing songs to save.", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_playlists()
        if user_id not in data:
            data[user_id] = {}

        clean_name = name.strip()
        matched_name = next((k for k in data[user_id].keys() if k.lower() == clean_name.lower()), clean_name)
        if matched_name not in data[user_id]:
            data[user_id][matched_name] = []

        all_songs = []
        if player.current:
            all_songs.append(player.current)
        all_songs.extend(list(player.queue))

        added_count = 0
        existing_titles = {item["title"] for item in data[user_id][matched_name]}
        for s in all_songs:
            if s.title not in existing_titles:
                data[user_id][matched_name].append({
                    "title": s.title,
                    "url": s.webpage_url,
                    "duration": s.duration,
                    "thumbnail": s.thumbnail,
                    "uploader": s.uploader
                })
                existing_titles.add(s.title)
                added_count += 1

        save_playlists(data)

        embed = discord.Embed(
            title="💾 Queue Saved to Playlist",
            description=f"Saved **{added_count} tracks** into playlist **`{matched_name}`**!\nTotal songs: `{len(data[user_id][matched_name])}`",
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text=f"Play anytime with /playlist play {matched_name}", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @playlist.command(name="play", description="Enqueue all tracks from a named playlist.")
    @app_commands.describe(name="Name of the playlist to play")
    async def pl_play(self, ctx: commands.Context, name: str):
        user_id = str(ctx.author.id)
        data = load_playlists()
        user_pls = data.get(user_id, {})

        matched_name = next((k for k in user_pls.keys() if k.lower() == name.strip().lower()), None)
        if not matched_name or not user_pls[matched_name]:
            return await ctx.send(f"❌ Playlist `{name}` not found or contains no songs.", ephemeral=True)

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
        tracks = user_pls[matched_name]
        for item in tracks:
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
                source_type="playlist"
            )
            player.queue.append(song)

        embed = discord.Embed(
            title=f"▶️ Enqueued Playlist • {matched_name}",
            description=f"Queued **{len(tracks)} tracks** from playlist **`{matched_name}`**!",
            color=config.COLOR_PRIMARY
        )
        if tracks[0].get("thumbnail"):
            embed.set_thumbnail(url=tracks[0]["thumbnail"])
        embed.set_footer(text="RAI VIBES 💗 • High Fidelity Playlists", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @playlist.command(name="list", description="View all your saved custom playlists.")
    async def pl_list(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        data = load_playlists()
        user_pls = data.get(user_id, {})

        if not user_pls:
            return await ctx.send("📂 You don't have any custom playlists yet. Create one with `/playlist create <name>`!", ephemeral=True)

        embed = discord.Embed(
            title=f"📂 {ctx.author.display_name}'s Custom Playlists",
            color=config.COLOR_PRIMARY
        )
        embed.set_author(name="RAI VIBES 💗 Playlists", icon_url=config.RAI_ICON_URL)

        lines = []
        for name, tracks in user_pls.items():
            lines.append(f"• **`{name}`** — `{len(tracks)} tracks` (Use `/playlist play {name}`)")

        embed.description = "\n".join(lines)
        embed.set_footer(text=f"Total Playlists: {len(user_pls)}", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @playlist.command(name="view", description="View tracks inside a specific playlist.")
    @app_commands.describe(name="Name of the playlist to view")
    async def pl_view(self, ctx: commands.Context, name: str):
        user_id = str(ctx.author.id)
        data = load_playlists()
        user_pls = data.get(user_id, {})

        matched_name = next((k for k in user_pls.keys() if k.lower() == name.strip().lower()), None)
        if not matched_name:
            return await ctx.send(f"❌ Playlist `{name}` not found.", ephemeral=True)

        tracks = user_pls[matched_name]
        if not tracks:
            return await ctx.send(f"📂 Playlist `{matched_name}` is empty. Add songs with `/playlist add {matched_name}`!", ephemeral=True)

        embed = discord.Embed(
            title=f"📂 Playlist: {matched_name} ({len(tracks)} tracks)",
            color=config.COLOR_PRIMARY
        )
        lines = []
        for i, t in enumerate(tracks[:20], 1):
            dur = time.strftime("%M:%S", time.gmtime(t.get("duration", 0))) if t.get("duration") else "Live"
            lines.append(f"`{i}.` [{t['title'][:40]}]({t['url']}) • `{dur}`")

        embed.description = "\n".join(lines)
        if len(tracks) > 20:
            embed.set_footer(text=f"Showing top 20 of {len(tracks)} tracks • Play with /playlist play {matched_name}", icon_url=config.RAI_ICON_URL)
        else:
            embed.set_footer(text=f"Play with /playlist play {matched_name}", icon_url=config.RAI_ICON_URL)

        await ctx.send(embed=embed)

    @playlist.command(name="delete", description="Delete a custom playlist.")
    @app_commands.describe(name="Name of the playlist to delete")
    async def pl_delete(self, ctx: commands.Context, name: str):
        user_id = str(ctx.author.id)
        data = load_playlists()
        user_pls = data.get(user_id, {})

        matched_name = next((k for k in user_pls.keys() if k.lower() == name.strip().lower()), None)
        if not matched_name:
            return await ctx.send(f"❌ Playlist `{name}` not found.", ephemeral=True)

        del user_pls[matched_name]
        save_playlists(data)

        await ctx.send(f"🗑️ Successfully deleted playlist **`{matched_name}`**.", ephemeral=True)

    @playlist.command(name="export", description="Export a playlist as a downloadable JSON backup file.")
    @app_commands.describe(name="Name of the playlist to export")
    async def pl_export(self, ctx: commands.Context, name: str):
        user_id = str(ctx.author.id)
        data = load_playlists()
        user_pls = data.get(user_id, {})

        matched_name = next((k for k in user_pls.keys() if k.lower() == name.strip().lower()), None)
        if not matched_name or not user_pls[matched_name]:
            return await ctx.send(f"❌ Playlist `{name}` not found or contains no songs.", ephemeral=True)

        tracks = user_pls[matched_name]
        export_payload = {
            "version": "1.0",
            "bot": "RAI VIBES 💗",
            "exported_by": ctx.author.display_name,
            "playlist_name": matched_name,
            "track_count": len(tracks),
            "tracks": tracks
        }
        json_bytes = json.dumps(export_payload, indent=2, ensure_ascii=False).encode("utf-8")
        safe_filename = "".join(c for c in matched_name if c.isalnum() or c in ("-", "_")).strip() or "playlist"
        discord_file = discord.File(io.BytesIO(json_bytes), filename=f"{safe_filename}_backup.json")

        embed = discord.Embed(
            title=f"📦 Exported Playlist • {matched_name}",
            description=(
                f"✅ Successfully exported **{len(tracks)} tracks** from **`{matched_name}`**!\n\n"
                f"📎 Download the `.json` file below. You can restore or share this playlist anytime using `/playlist import_file`."
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="RAI VIBES 💗 • Custom Playlists", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed, file=discord_file)

    @playlist.command(name="import_file", description="Import a playlist from a JSON backup file.")
    @app_commands.describe(name="New or existing playlist name", attachment="The .json backup file to import")
    async def pl_import_file(self, ctx: commands.Context, name: str, attachment: discord.Attachment):
        if not attachment.filename.lower().endswith(".json"):
            return await ctx.send("❌ Please attach a valid `.json` playlist backup file.", ephemeral=True)

        if attachment.size > 2 * 1024 * 1024:
            return await ctx.send("❌ File is too large. Maximum backup file size is 2 MB.", ephemeral=True)

        try:
            content = await attachment.read()
            payload = json.loads(content.decode("utf-8"))
        except Exception as e:
            return await ctx.send(f"❌ Failed to read backup file: `{e}`", ephemeral=True)

        tracks = payload.get("tracks") if isinstance(payload, dict) else payload
        if not isinstance(tracks, list) or not tracks:
            return await ctx.send("❌ Backup file does not contain any valid tracks.", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_playlists()
        if user_id not in data:
            data[user_id] = {}

        clean_name = name.strip()
        matched_name = next((k for k in data[user_id].keys() if k.lower() == clean_name.lower()), clean_name)
        if matched_name not in data[user_id]:
            data[user_id][matched_name] = []

        existing_titles = {item.get("title") for item in data[user_id][matched_name]}
        added_count = 0
        for t in tracks:
            if isinstance(t, dict) and t.get("title") and t.get("title") not in existing_titles:
                data[user_id][matched_name].append({
                    "title": t.get("title"),
                    "url": t.get("url") or "",
                    "duration": t.get("duration", 0),
                    "thumbnail": t.get("thumbnail"),
                    "uploader": t.get("uploader", "Unknown Artist")
                })
                existing_titles.add(t.get("title"))
                added_count += 1

        save_playlists(data)

        embed = discord.Embed(
            title=f"📥 Playlist Imported • {matched_name}",
            description=(
                f"✅ Successfully imported **{added_count} new tracks** into **`{matched_name}`**!\n"
                f"Total tracks in playlist: `{len(data[user_id][matched_name])}`\n\n"
                f"Play anytime with `/playlist play {matched_name}`"
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="RAI VIBES 💗 • Custom Playlists", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Favorites(bot))
