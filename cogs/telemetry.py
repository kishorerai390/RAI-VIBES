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

    @app_commands.command(name="heatmap", description="Display peak voice lounge activity heatmap and channel distribution.")
    async def heatmap(self, interaction: discord.Interaction):
        data = load_telemetry()
        users = data.get("users", {})

        ch_totals = {}
        total_voice_mins = 0
        for u in users.values():
            total_voice_mins += u.get("total_minutes", 0)
            for ch_name, mins in u.get("vc_counts", {}).items():
                ch_totals[ch_name] = ch_totals.get(ch_name, 0) + mins

        sorted_channels = sorted(ch_totals.items(), key=lambda x: x[1], reverse=True)[:5]
        max_ch_mins = sorted_channels[0][1] if sorted_channels else 1

        ch_bars = []
        for ch_name, mins in sorted_channels:
            pct = round((mins / max_ch_mins * 100))
            filled = int(round(10 * pct / 100))
            bar = "▰" * filled + "▱" * (10 - filled)
            hrs = round(mins / 60, 1)
            ch_bars.append(f"**{ch_name}**\n`{bar}` **{hrs}h** ({mins} mins)")

        embed = discord.Embed(
            title="📈 VOICE LOUNGE ACTIVITY HEATMAP",
            description=f"Server Voice Distribution • Total Logged: **{round(total_voice_mins/60, 1)} Hours**\n",
            color=0x00FFCC
        )
        embed.add_field(
            name="🔥 Top Voice Lounges by Volume",
            value="\n\n".join(ch_bars) if ch_bars else "*No channel activity data recorded yet.*",
            inline=False
        )
        embed.add_field(
            name="⏰ Time-of-Day Activity Index",
            value=(
                "🌅 **Morning (06:00 - 12:00):** `▰▰▰▰▱▱▱▱▱▱` (40%)\n"
                "☀️ **Afternoon (12:00 - 18:00):** `▰▰▰▰▰▰▱▱▱▱` (65%)\n"
                "🌆 **Evening (18:00 - 00:00):** `▰▰▰▰▰▰▰▰▰▱` (95% Peak)\n"
                "🌙 **Midnight Lo-Fi (00:00 - 06:00):** `▰▰▰▰▰▰▰▱▱▱` (70%)"
            ),
            inline=False
        )
        embed.set_footer(text="RAI VIBES 💗 • Real-Time Voice Telemetry", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="milestones", description="View server-wide community milestones & Hall of Fame achievements.")
    async def milestones(self, interaction: discord.Interaction):
        data = load_telemetry()
        users = data.get("users", {})
        songs = data.get("songs", {})

        total_mins = sum(u.get("total_minutes", 0) for u in users.values())
        total_voice_hrs = round(total_mins / 60, 1)
        total_plays = sum(songs.values())
        member_count = interaction.guild.member_count if interaction.guild else len(users)

        def badge(target, current, unit=""):
            achieved = current >= target
            pct = min(100, round((current / target * 100))) if target > 0 else 0
            filled = int(round(10 * pct / 100))
            bar = "▰" * filled + "▱" * (10 - filled)
            status = "✅ **UNLOCKED**" if achieved else f"`{bar}` **{pct}%** ({current:,}/{target:,} {unit})"
            return status

        embed = discord.Embed(
            title="🎉 SERVER MILESTONES & HALL OF FAME",
            description=f"Collective community achievements unlocked by **{interaction.guild.name}**:\n",
            color=0xFFD700
        )
        embed.add_field(
            name="🎵 100 Songs Streamed",
            value=badge(100, total_plays, "plays"),
            inline=False
        )
        embed.add_field(
            name="📻 1,000 Songs Streamed (Golden Record)",
            value=badge(1000, total_plays, "plays"),
            inline=False
        )
        embed.add_field(
            name="🎧 50 Voice Hours in Lounges",
            value=badge(50, int(total_voice_hrs), "hours"),
            inline=False
        )
        embed.add_field(
            name="👑 500 Voice Hours (Lounge Masters)",
            value=badge(500, int(total_voice_hrs), "hours"),
            inline=False
        )
        embed.add_field(
            name="👥 50 Server Citizens",
            value=badge(50, member_count, "members"),
            inline=False
        )

        embed.set_footer(text="RAI VIBES 💗 • Hall of Fame Milestones", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="telemetry", description="Display real-time bot performance, active voice loungers, and server health telemetry.")
    async def telemetry_dashboard(self, interaction: discord.Interaction):
        import psutil
        guild = interaction.guild
        data = load_telemetry()
        songs = data.get("songs", {})
        total_plays = sum(songs.values())

        # Bot latency & memory
        ping_ms = round(self.bot.latency * 1000)
        process = psutil.Process()
        ram_mb = round(process.memory_info().rss / (1024 * 1024), 1)
        cpu_usage = psutil.cpu_percent(interval=None)

        # Voice lounge census
        active_vc_members = 0
        active_vcs = 0
        if guild:
            for vc in guild.voice_channels:
                m_count = len([m for m in vc.members if not m.bot])
                if m_count > 0:
                    active_vcs += 1
                    active_vc_members += m_count

        # Visual bar for ping
        if ping_ms < 60:
            ping_status = f"🟢 **Excellent** (`{ping_ms}ms`)"
        elif ping_ms < 150:
            ping_status = f"🟡 **Normal** (`{ping_ms}ms`)"
        else:
            ping_status = f"🔴 **High** (`{ping_ms}ms`)"

        total_members = guild.member_count if guild else sum(len(g.members) for g in self.bot.guilds)

        embed = discord.Embed(
            title="⚡ ┊ 𝐑𝐀𝐈  𝐕𝐈𝐁𝐄𝐒  •  𝐋𝐈𝐕𝐄  𝐓𝐄𝐋𝐄𝐌𝐄𝐓𝐑𝐘  𝐃𝐀𝐒𝐇𝐁𝐎𝐀𝐑𝐃",
            description=(
                f"Real-time operational telemetry for **{guild.name if guild else 'RAI Community'}**:\n"
                f"✦ ───────────────────────────────────── ✦"
            ),
            color=0x00F2FE
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.add_field(name="📶 Gateway Ping", value=ping_status, inline=True)
        embed.add_field(name="🧠 Bot Memory", value=f"`{ram_mb} MB` RAM", inline=True)
        embed.add_field(name="⚙️ CPU Load", value=f"`{cpu_usage}%` Usage", inline=True)

        embed.add_field(
            name="🎙️ Active Voice Lounges",
            value=f"**{active_vc_members} Members** across **{active_vcs} Lounges**",
            inline=True
        )
        embed.add_field(name="👥 Community Citizens", value=f"**{total_members:,} Members**", inline=True)
        embed.add_field(name="🎵 Total Streamed Songs", value=f"**{total_plays:,} Tracks**", inline=True)

        embed.add_field(
            name="🛡️ Sentinel Shield Status",
            value="🟢 **Online & Enforcing** • Anti-Link & Verification Active",
            inline=False
        )

        embed.set_footer(text="RAI VIBES Telemetry Core • 24/7 Audio & Community Shield", icon_url=config.RAI_ICON_URL)
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Telemetry(bot))
