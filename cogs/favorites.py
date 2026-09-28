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
SHARED_FILE = Path(__file__).resolve().parent.parent / "data" / "shared_playlists.json"

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


# =========================================================================
# INTERACTIVE PLAYLIST UI VIEW
# =========================================================================
class PlaylistSelectDropdown(discord.ui.Select):
    def __init__(self, user_id: int, playlists: Dict[str, List[dict]]):
        options = []
        for name, tracks in list(playlists.items())[:25]:
            options.append(discord.SelectOption(
                label=name[:25],
                value=name,
                description=f"{len(tracks)} track(s) saved",
                emoji="📁"
            ))
        super().__init__(
            placeholder="📂 Select a custom playlist to manage or play...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"pl_select_{user_id}"
        )
        self.user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This playlist panel belongs to someone else.", ephemeral=True)

        chosen = self.values[0]
        data = load_playlists()
        user_pls = data.get(str(self.user_id), {})
        tracks = user_pls.get(chosen, [])

        embed = discord.Embed(
            title=f"📁 Playlist: {chosen}",
            description=f"Contains **{len(tracks)} tracks**. Use the buttons below to control playback.",
            color=config.COLOR_PRIMARY
        )
        lines = []
        for i, t in enumerate(tracks[:10], 1):
            dur = time.strftime("%M:%S", time.gmtime(t.get("duration", 0))) if t.get("duration") else "Live"
            lines.append(f"`{i}.` [{t.get('title', 'Unknown')[:35]}]({t.get('url', '#')}) • `{dur}`")
        if lines:
            embed.add_field(name="Tracks Preview", value="\n".join(lines), inline=False)
        if len(tracks) > 10:
            embed.set_footer(text=f"Showing 10 of {len(tracks)} tracks • RAI VIBES 💗", icon_url=config.RAI_ICON_URL)
        else:
            embed.set_footer(text="RAI VIBES 💗 • Custom Playlists", icon_url=config.RAI_ICON_URL)

        self.view.selected_playlist = chosen
        await interaction.response.edit_message(embed=embed, view=self.view)


class PlaylistDashboardView(discord.ui.View):
    def __init__(self, cog: 'Favorites', user_id: int, playlists: Dict[str, List[dict]]):
        super().__init__(timeout=180)
        self.cog = cog
        self.user_id = user_id
        self.selected_playlist = list(playlists.keys())[0] if playlists else None

        if playlists:
            self.add_item(PlaylistSelectDropdown(user_id, playlists))

    @discord.ui.button(label="Play Selected", emoji="▶️", style=discord.ButtonStyle.success, row=1)
    async def play_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ You are not the owner of this menu.", ephemeral=True)
        if not self.selected_playlist:
            return await interaction.response.send_message("❌ Please select a playlist from the dropdown first.", ephemeral=True)

        await interaction.response.defer()
        await self.cog.enqueue_playlist(interaction, self.selected_playlist)

    @discord.ui.button(label="Save Current Queue", emoji="💾", style=discord.ButtonStyle.primary, row=1)
    async def save_queue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ You are not the owner of this menu.", ephemeral=True)

        modal = SaveQueueModal(self.cog)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Create Playlist", emoji="➕", style=discord.ButtonStyle.secondary, row=1)
    async def create_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ You are not the owner of this menu.", ephemeral=True)

        modal = CreatePlaylistModal(self.cog)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Delete Selected", emoji="🗑️", style=discord.ButtonStyle.danger, row=1)
    async def delete_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ You are not the owner of this menu.", ephemeral=True)
        if not self.selected_playlist:
            return await interaction.response.send_message("❌ Please select a playlist to delete.", ephemeral=True)

        data = load_playlists()
        user_pls = data.get(str(self.user_id), {})
        if self.selected_playlist in user_pls:
            del user_pls[self.selected_playlist]
            save_playlists(data)
            await interaction.response.send_message(f"🗑️ Deleted playlist **`{self.selected_playlist}`**.", ephemeral=True)
        else:
            await interaction.response.send_message("❌ Playlist not found.", ephemeral=True)


class SaveQueueModal(discord.ui.Modal, title="Save Current Queue"):
    name_input = discord.ui.TextInput(
        label="Playlist Name",
        placeholder="e.g. Chill Beats, Gym Pump, Night Drive",
        max_length=40,
        required=True
    )

    def __init__(self, cog: 'Favorites'):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name_input.value.strip()
        music_cog = self.cog.bot.get_cog("Music")
        player = music_cog.get_player(interaction.guild_id) if music_cog else None
        if not player or (not player.current and not player.queue):
            return await interaction.response.send_message("❌ No songs currently in queue to save.", ephemeral=True)

        user_id = str(interaction.user.id)
        data = load_playlists()
        user_pls = data.setdefault(user_id, {})
        user_pls[name] = []

        if player.current:
            user_pls[name].append({
                "title": player.current.title,
                "url": player.current.webpage_url,
                "duration": player.current.duration,
                "thumbnail": player.current.thumbnail,
                "uploader": player.current.uploader
            })
        for s in player.queue:
            user_pls[name].append({
                "title": s.title,
                "url": s.webpage_url,
                "duration": s.duration,
                "thumbnail": s.thumbnail,
                "uploader": s.uploader
            })

        save_playlists(data)
        await interaction.response.send_message(
            f"💾 Successfully saved **{len(user_pls[name])} tracks** into playlist **`{name}`**!",
            ephemeral=True
        )


class CreatePlaylistModal(discord.ui.Modal, title="Create Custom Playlist"):
    name_input = discord.ui.TextInput(
        label="Playlist Name",
        placeholder="e.g. Favorites 2026, Lo-Fi Chill",
        max_length=40,
        required=True
    )

    def __init__(self, cog: 'Favorites'):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        name = self.name_input.value.strip()
        user_id = str(interaction.user.id)
        data = load_playlists()
        user_pls = data.setdefault(user_id, {})

        if name.lower() in [k.lower() for k in user_pls.keys()]:
            return await interaction.response.send_message(f"⚠️ Playlist `{name}` already exists!", ephemeral=True)

        user_pls[name] = []
        save_playlists(data)
        await interaction.response.send_message(
            f"✨ Created playlist **`{name}`**! Add tracks using `/playlist action:add name:{name}`.",
            ephemeral=True
        )


# =========================================================================
# FAVORITES & PLAYLISTS COG
# =========================================================================
class Favorites(commands.Cog):
    """Clean, high-performance playlist and favorite music manager for RAI VIBES 💗."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # --- Autocomplete for Playlist Names ---
    async def playlist_name_autocomplete(self, interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
        user_id = str(interaction.user.id)
        data = load_playlists()
        user_pls = data.get(user_id, {})
        choices = []
        for name in user_pls.keys():
            if current.lower() in name.lower():
                choices.append(app_commands.Choice(name=name[:100], value=name[:100]))
        return choices[:25]

    async def enqueue_playlist(self, target, playlist_name: str):
        """Helper to enqueue a playlist from either a command Context or an Interaction."""
        guild = target.guild
        user = target.user if isinstance(target, discord.Interaction) else target.author
        send_fn = target.followup.send if isinstance(target, discord.Interaction) else target.send

        data = load_playlists()
        user_pls = data.get(str(user.id), {})
        matched_name = next((k for k in user_pls.keys() if k.lower() == playlist_name.lower().strip()), None)

        if not matched_name:
            return await send_fn(f"❌ Playlist `{playlist_name}` not found in your library.", ephemeral=True)

        tracks = user_pls[matched_name]
        if not tracks:
            return await send_fn(f"📂 Playlist `{matched_name}` is empty.", ephemeral=True)

        music_cog = self.bot.get_cog("Music")
        if not music_cog:
            return await send_fn("❌ Audio engine is currently unavailable.", ephemeral=True)

        voice_client = await music_cog.ensure_voice(target)
        if not voice_client:
            return

        player = music_cog.get_or_create_player(guild)
        player.voice_client = voice_client
        player.text_channel = target.channel

        from cogs.music import Song
        for item in tracks:
            song = Song(
                data={
                    "title": item.get("title", "Unknown"),
                    "search_query": item.get("title", ""),
                    "url": None,
                    "webpage_url": item.get("url", ""),
                    "duration": item.get("duration", 0),
                    "thumbnail": item.get("thumbnail"),
                    "uploader": item.get("uploader", "Unknown Artist")
                },
                requester=user,
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
        await send_fn(embed=embed)

    # =========================================================================
    # SINGLE UNIFIED /playlist COMMAND
    # =========================================================================
    @commands.hybrid_command(name="playlist", aliases=["pl"], description="Manage, browse, and stream your custom personal music playlists.")
    @app_commands.describe(
        action="Action: play, list, add, create, save_queue, view, or delete",
        name="Name of the playlist",
        query="Song title or link to add (when using add)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="▶️ Play Playlist", value="play"),
        app_commands.Choice(name="📂 List My Playlists", value="list"),
        app_commands.Choice(name="➕ Add Track to Playlist", value="add"),
        app_commands.Choice(name="✨ Create Empty Playlist", value="create"),
        app_commands.Choice(name="💾 Save Active Queue", value="save_queue"),
        app_commands.Choice(name="👁️ View Tracks", value="view"),
        app_commands.Choice(name="🗑️ Delete Playlist", value="delete"),
    ])
    @app_commands.autocomplete(name=playlist_name_autocomplete)
    async def playlist_cmd(
        self,
        ctx: commands.Context,
        action: Optional[app_commands.Choice[str]] = None,
        name: Optional[str] = None,
        query: Optional[str] = None
    ):
        act = action.value if action else None
        user_id = str(ctx.author.id)
        data = load_playlists()
        user_pls = data.get(user_id, {})

        # 1. Default to Interactive Dashboard if no action specified
        if not act:
            embed = discord.Embed(
                title=f"📂 {ctx.author.display_name}'s Playlist Hub",
                description=(
                    f"You have **{len(user_pls)} custom playlist(s)** saved.\n"
                    "Select a playlist from the dropdown below or use the quick buttons!"
                ),
                color=config.COLOR_PRIMARY
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            embed.set_footer(text="RAI VIBES 💗 • Custom Playlists", icon_url=config.RAI_ICON_URL)
            view = PlaylistDashboardView(self, ctx.author.id, user_pls)
            return await ctx.send(embed=embed, view=view, ephemeral=True)

        # 2. Action: List Playlists
        if act == "list":
            if not user_pls:
                return await ctx.send("📂 You don't have any custom playlists yet. Use `/playlist action:create name:<name>` to start one!", ephemeral=True)
            embed = discord.Embed(title=f"📂 {ctx.author.display_name}'s Custom Playlists", color=config.COLOR_PRIMARY)
            lines = [f"• **`{pname}`** — `{len(tracks)} track(s)`" for pname, tracks in user_pls.items()]
            embed.description = "\n".join(lines)
            embed.set_footer(text=f"Total: {len(user_pls)} playlists • Play with /playlist action:play name:<name>", icon_url=config.RAI_ICON_URL)
            return await ctx.send(embed=embed, ephemeral=True)

        # 3. Action: Play
        if act == "play":
            if not name:
                return await ctx.send("❌ Please provide the playlist `name` to play, e.g. `/playlist action:play name:Chill`", ephemeral=True)
            return await self.enqueue_playlist(ctx, name)

        # 4. Action: Create
        if act == "create":
            if not name:
                return await ctx.send("❌ Please provide a `name` for your new playlist.", ephemeral=True)
            clean_name = name.strip()
            if clean_name.lower() in [k.lower() for k in user_pls.keys()]:
                return await ctx.send(f"⚠️ Playlist `{clean_name}` already exists!", ephemeral=True)
            user_pls[clean_name] = []
            data[user_id] = user_pls
            save_playlists(data)
            return await ctx.send(f"✨ Successfully created playlist **`{clean_name}`**! Add tracks with `/playlist action:add name:{clean_name}`.", ephemeral=True)

        # 5. Action: Save Queue
        if act == "save_queue":
            target_name = (name or "Queue Backup").strip()
            music_cog = self.bot.get_cog("Music")
            player = music_cog.get_player(ctx.guild.id) if music_cog else None
            if not player or (not player.current and not player.queue):
                return await ctx.send("❌ No active queue or playing songs to save.", ephemeral=True)

            user_pls[target_name] = []
            if player.current:
                user_pls[target_name].append({
                    "title": player.current.title,
                    "url": player.current.webpage_url,
                    "duration": player.current.duration,
                    "thumbnail": player.current.thumbnail,
                    "uploader": player.current.uploader
                })
            for s in player.queue:
                user_pls[target_name].append({
                    "title": s.title,
                    "url": s.webpage_url,
                    "duration": s.duration,
                    "thumbnail": s.thumbnail,
                    "uploader": s.uploader
                })
            data[user_id] = user_pls
            save_playlists(data)
            return await ctx.send(f"💾 Saved **{len(user_pls[target_name])} songs** from queue into playlist **`{target_name}`**!", ephemeral=True)

        # 6. Action: Add Track
        if act == "add":
            if not name:
                return await ctx.send("❌ Please specify which playlist `name` to add to.", ephemeral=True)
            matched_name = next((k for k in user_pls.keys() if k.lower() == name.strip().lower()), None)
            if not matched_name:
                return await ctx.send(f"❌ Playlist `{name}` not found. Create it first with `/playlist action:create name:{name}`.", ephemeral=True)

            track_to_add = None
            if query:
                from cogs.music import Song
                resolved = await Song.create_source(query, ctx.author, self.bot.loop)
                if not resolved:
                    return await ctx.send(f"❌ Could not resolve track for `{query}`.", ephemeral=True)
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
                    return await ctx.send("❌ No track currently playing. Specify a `query` or start playing music first.", ephemeral=True)
                track_to_add = {
                    "title": player.current.title,
                    "url": player.current.webpage_url,
                    "duration": player.current.duration,
                    "thumbnail": player.current.thumbnail,
                    "uploader": player.current.uploader
                }

            user_pls[matched_name].append(track_to_add)
            save_playlists(data)
            return await ctx.send(f"🎵 Added **[{track_to_add['title']}]({track_to_add['url']})** to playlist **`{matched_name}`**! Total tracks: `{len(user_pls[matched_name])}`")

        # 7. Action: View Tracks
        if act == "view":
            if not name:
                return await ctx.send("❌ Please specify the playlist `name` to view.", ephemeral=True)
            matched_name = next((k for k in user_pls.keys() if k.lower() == name.strip().lower()), None)
            if not matched_name:
                return await ctx.send(f"❌ Playlist `{name}` not found.", ephemeral=True)
            tracks = user_pls[matched_name]
            embed = discord.Embed(title=f"📂 Playlist: {matched_name} ({len(tracks)} tracks)", color=config.COLOR_PRIMARY)
            lines = [f"`{i}.` [{t['title'][:40]}]({t['url']})" for i, t in enumerate(tracks[:20], 1)]
            embed.description = "\n".join(lines) if lines else "*This playlist is currently empty.*"
            return await ctx.send(embed=embed, ephemeral=True)

        # 8. Action: Delete
        if act == "delete":
            if not name:
                return await ctx.send("❌ Please specify which playlist `name` to delete.", ephemeral=True)
            matched_name = next((k for k in user_pls.keys() if k.lower() == name.strip().lower()), None)
            if not matched_name:
                return await ctx.send(f"❌ Playlist `{name}` not found.", ephemeral=True)
            del user_pls[matched_name]
            save_playlists(data)
            return await ctx.send(f"🗑️ Successfully deleted playlist **`{matched_name}`**.", ephemeral=True)

    # =========================================================================
    # SINGLE UNIFIED /favorite COMMAND
    # =========================================================================
    @commands.hybrid_command(name="favorite", aliases=["fav"], description="Manage and stream your personal favorite songs.")
    @app_commands.describe(
        action="Action: play, list, or add",
        query="Optional song title or link to add (defaults to currently playing track)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="▶️ Play Favorites", value="play"),
        app_commands.Choice(name="⭐ View Favorites", value="list"),
        app_commands.Choice(name="➕ Add Track to Favorites", value="add"),
    ])
    async def favorite_cmd(
        self,
        ctx: commands.Context,
        action: Optional[app_commands.Choice[str]] = None,
        query: Optional[str] = None
    ):
        act = action.value if action else "list"
        user_id = str(ctx.author.id)
        data = load_favorites()
        favs = data.get(user_id, [])

        # 1. View Favorites
        if act == "list":
            if not favs:
                return await ctx.send("⭐ You have not added any favorite tracks yet. Use `/favorite action:add` while playing a song!", ephemeral=True)
            embed = discord.Embed(title=f"⭐ {ctx.author.display_name}'s Favorites", color=config.COLOR_GOLD)
            lines = [f"`{i}.` [{item['title'][:40]}]({item['url']})" for i, item in enumerate(favs[:20], 1)]
            embed.description = "\n".join(lines)
            embed.set_footer(text=f"Total: {len(favs)} track(s) • Play with /favorite action:play", icon_url=config.RAI_ICON_URL)
            return await ctx.send(embed=embed, ephemeral=True)

        # 2. Add to Favorites
        if act == "add":
            track_to_add = None
            if query:
                from cogs.music import Song
                resolved = await Song.create_source(query, ctx.author, self.bot.loop)
                if not resolved:
                    return await ctx.send(f"❌ Could not resolve song for `{query}`.", ephemeral=True)
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
                    return await ctx.send("❌ No track currently playing. Provide a `query` or start playing music first.", ephemeral=True)
                track_to_add = {
                    "title": player.current.title,
                    "url": player.current.webpage_url,
                    "duration": player.current.duration,
                    "thumbnail": player.current.thumbnail,
                    "uploader": player.current.uploader
                }

            if user_id not in data:
                data[user_id] = []
            if any(item["title"] == track_to_add["title"] for item in data[user_id]):
                return await ctx.send(f"⚠️ `{track_to_add['title']}` is already in your favorites!", ephemeral=True)

            data[user_id].append(track_to_add)
            save_favorites(data)
            embed = discord.Embed(
                title="⭐ Added to Favorites",
                description=f"Saved **[{track_to_add['title']}]({track_to_add['url']})** to your personal library!",
                color=config.COLOR_GOLD
            )
            if track_to_add.get("thumbnail"):
                embed.set_thumbnail(url=track_to_add["thumbnail"])
            embed.set_footer(text=f"Total Favorites: {len(data[user_id])}", icon_url=config.RAI_ICON_URL)
            return await ctx.send(embed=embed)

        # 3. Play Favorites
        if act == "play":
            if not favs:
                return await ctx.send("⭐ Your favorites list is empty.", ephemeral=True)
            music_cog = self.bot.get_cog("Music")
            if not music_cog:
                return await ctx.send("❌ Audio engine unavailable.", ephemeral=True)
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
                description=f"Added **{len(favs)} favorite track(s)** to the queue!",
                color=config.COLOR_PRIMARY
            )
            if favs[0].get("thumbnail"):
                embed.set_thumbnail(url=favs[0]["thumbnail"])
            embed.set_footer(text="RAI VIBES 💗 • Premium Audio", icon_url=config.RAI_ICON_URL)
            return await ctx.send(embed=embed)

    # =========================================================================
    # ADVANCED PREFIX UTILITIES (Non-slash, so they don't pollute the slash picker)
    # =========================================================================
    @commands.command(name="plexport", description="Export a playlist as downloadable JSON backup.")
    async def pl_export_prefix(self, ctx: commands.Context, *, name: str):
        user_id = str(ctx.author.id)
        data = load_playlists()
        user_pls = data.get(user_id, {})
        matched_name = next((k for k in user_pls.keys() if k.lower() == name.strip().lower()), None)
        if not matched_name or not user_pls[matched_name]:
            return await ctx.send(f"❌ Playlist `{name}` not found or empty.")

        tracks = user_pls[matched_name]
        payload = {
            "version": "2.0",
            "bot": "RAI VIBES 💗",
            "playlist_name": matched_name,
            "tracks": tracks
        }
        json_bytes = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
        safe_name = "".join(c for c in matched_name if c.isalnum() or c in ("-", "_")).strip() or "playlist"
        file = discord.File(io.BytesIO(json_bytes), filename=f"{safe_name}_backup.json")
        await ctx.send(f"📦 Exported **{len(tracks)} tracks** from `{matched_name}`:", file=file)

    @commands.command(name="plimport", description="Import a playlist from a JSON backup file.")
    async def pl_import_prefix(self, ctx: commands.Context, *, name: str):
        if not ctx.message.attachments:
            return await ctx.send("❌ Please attach a `.json` playlist backup file.")
        att = ctx.message.attachments[0]
        content = await att.read()
        try:
            payload = json.loads(content.decode("utf-8"))
        except Exception as e:
            return await ctx.send(f"❌ Invalid JSON file: `{e}`")

        tracks = payload.get("tracks") if isinstance(payload, dict) else payload
        if not isinstance(tracks, list) or not tracks:
            return await ctx.send("❌ No valid tracks found in file.")

        user_id = str(ctx.author.id)
        data = load_playlists()
        user_pls = data.setdefault(user_id, {})
        user_pls[name.strip()] = tracks
        save_playlists(data)
        await ctx.send(f"📥 Successfully imported **{len(tracks)} tracks** into playlist **`{name.strip()}`**!")


async def setup(bot: commands.Bot):
    await bot.add_cog(Favorites(bot))
