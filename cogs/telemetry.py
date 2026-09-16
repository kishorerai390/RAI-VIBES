import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict

import discord
from discord import app_commands
from discord.ext import commands, tasks

import config

logger = logging.getLogger("Telemetry")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TELEMETRY_FILE = DATA_DIR / "telemetry.json"


def load_telemetry() -> Dict[str, dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if TELEMETRY_FILE.exists():
        try:
            with open(TELEMETRY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": {}, "songs": {}}
    return {"users": {}, "songs": {}}


def save_telemetry(data: Dict[str, dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(TELEMETRY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def record_song_play(song_title: str):
    """Utility hook called when a track plays."""
    data = load_telemetry()
    songs = data.setdefault("songs", {})
    clean_title = song_title.strip()
    songs[clean_title] = songs.get(clean_title, 0) + 1
    save_telemetry(data)


class Telemetry(commands.Cog):
    """Clean Voice Analytics, Time Tracking & Server Telemetry."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_tracker_task.start()

    def cog_unload(self):
        self.voice_tracker_task.cancel()

    @tasks.loop(minutes=2)
    async def voice_tracker_task(self):
        """Accrues voice participation telemetry in background."""
        await self.bot.wait_until_ready()
        data = load_telemetry()
        users = data.setdefault("users", {})

        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                if "afk" in vc.name.lower() or len(vc.members) < 1:
                    continue

                for m in vc.members:
                    if m.bot or m.voice.self_deaf:
                        continue
                    uid = str(m.id)
                    u_data = users.setdefault(uid, {
                        "total_minutes": 0,
                        "week_minutes": 0,
                        "vc_counts": {},
                        "last_seen": 0
                    })
                    u_data["total_minutes"] += 2
                    u_data["week_minutes"] += 2
                    u_data["last_seen"] = int(time.time())

                    vc_counts = u_data.setdefault("vc_counts", {})
                    vc_counts[vc.name] = vc_counts.get(vc.name, 0) + 2

        save_telemetry(data)

    @voice_tracker_task.before_loop
    async def before_tracker(self):
        import asyncio
        while not self.bot.is_ready():
            await asyncio.sleep(1)

    @app_commands.command(name="voicetime", description="Check your total voice lounge hours, rank, and listening stats.")
    @app_commands.describe(member="Member to inspect (defaults to you)")
    async def voicetime(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        data = load_telemetry()
        users = data.get("users", {})
        uid = str(target.id)

        u_data = users.get(uid, {"total_minutes": 0, "week_minutes": 0, "vc_counts": {}})
        total_mins = u_data.get("total_minutes", 0)
        week_mins = u_data.get("week_minutes", 0)

        total_hours = round(total_mins / 60, 1)
        week_hours = round(week_mins / 60, 1)

        # Favorite VC
        vc_counts = u_data.get("vc_counts", {})
        fav_vc = max(vc_counts, key=vc_counts.get) if vc_counts else "None yet"

        # Calculate rank
        sorted_users = sorted(users.items(), key=lambda x: x[1].get("total_minutes", 0), reverse=True)
        rank = next((i + 1 for i, (u, _) in enumerate(sorted_users) if u == uid), len(sorted_users) + 1)

        embed = discord.Embed(
            title=f"📊 VOICE TELEMETRY • {target.display_name}",
            color=0x00FFCC
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🎙️ Total Voice Time", value=f"**{total_hours} Hours** ({total_mins:,} min)", inline=True)
        embed.add_field(name="📅 Past 7 Days", value=f"**{week_hours} Hours**", inline=True)
        embed.add_field(name="🏆 Voice Rank", value=f"**#{rank}** in server", inline=True)
        embed.add_field(name="🎧 Favorite Lounge", value=f"`{fav_vc}`", inline=False)
        embed.set_footer(text="RAI VIBES Telemetry Engine • High Fidelity Voice Analytics", icon_url=config.RAI_ICON_URL)

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="servertop", description="View server audio telemetry and top played tracks.")
    async def servertop(self, interaction: discord.Interaction):
        data = load_telemetry()
        users = data.get("users", {})
        songs = data.get("songs", {})

        # Top 5 voice chatters
        sorted_users = sorted(users.items(), key=lambda x: x[1].get("total_minutes", 0), reverse=True)[:5]
        top_voice_text = []
        for i, (u_id, u_info) in enumerate(sorted_users):
            hrs = round(u_info.get("total_minutes", 0) / 60, 1)
            top_voice_text.append(f"`#{i+1}` <@{u_id}> — **{hrs} Hours**")

        # Top 5 songs
        sorted_songs = sorted(songs.items(), key=lambda x: x[1], reverse=True)[:5]
        top_songs_text = []
        for i, (title, count) in enumerate(sorted_songs):
            top_songs_text.append(f"`#{i+1}` **{title[:32]}** — `{count}` plays")

        embed = discord.Embed(
            title="📊 RAI VIBES • SERVER AUDIO TELEMETRY",
            description="High-fidelity listening trends and voice analytics across the community:\n",
            color=0xFF007F
        )
        embed.add_field(
            name="👑 Top Voice Loungers",
            value="\n".join(top_voice_text) if top_voice_text else "*No recorded telemetry yet.*",
            inline=False
        )
        embed.add_field(
            name="🎵 Most Streamed Tracks",
            value="\n".join(top_songs_text) if top_songs_text else "*Stream songs with `/play` or in song-requests!*",
            inline=False
        )
        embed.set_footer(text="RAI VIBES Community Telemetry", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Telemetry(bot))
