import json
import time
from pathlib import Path
from typing import Optional, Dict

import discord
from discord.ext import commands, tasks
from discord import app_commands

import config

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATS_FILE = DATA_DIR / "voice_stats.json"

class VoiceStats(commands.Cog):
    """Voice Channel Activity Tracker & Top Voice Leaderboard for RAI VIBES 💗."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.stats = self.load_stats()
        self.voice_sessions: Dict[int, float] = {}  # user_id: join_timestamp
        self.track_voice_loop.start()

    def cog_unload(self):
        self.track_voice_loop.cancel()
        self.save_stats()

    def load_stats(self) -> dict:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if STATS_FILE.exists():
            try:
                with open(STATS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_stats(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(STATS_FILE, "w", encoding="utf-8") as f:
            json.dump(self.stats, f, indent=2)

    def format_duration(self, seconds: int) -> str:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    @tasks.loop(minutes=2)
    async def track_voice_loop(self):
        """Periodically increments active voice time & awards XP for active voice users."""
        now = time.time()
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                # Count non-bot members
                active_members = [m for m in vc.members if not m.bot and not m.voice.self_deaf and not m.voice.deaf]
                for m in active_members:
                    uid = str(m.id)
                    if uid not in self.stats:
                        self.stats[uid] = {"total_seconds": 0, "voice_xp": 0, "username": m.display_name}

                    # Add 120 seconds of voice time
                    self.stats[uid]["total_seconds"] += 120
                    self.stats[uid]["voice_xp"] += 10
                    self.stats[uid]["username"] = m.display_name

                    # Integrate with Levels cog
                    levels_cog = self.bot.get_cog("Levels")
                    if levels_cog:
                        try:
                            levels_cog.add_xp(m.id, 10)
                        except Exception:
                            pass

        self.save_stats()

    @track_voice_loop.before_loop
    async def before_track(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        now = time.time()
        uid = str(member.id)

        # Joined VC
        if not before.channel and after.channel:
            self.voice_sessions[member.id] = now
        # Left VC
        elif before.channel and not after.channel:
            join_time = self.voice_sessions.pop(member.id, None)
            if join_time:
                elapsed = int(now - join_time)
                if elapsed >= 30:
                    if uid not in self.stats:
                        self.stats[uid] = {"total_seconds": 0, "voice_xp": 0, "username": member.display_name}
                    self.stats[uid]["total_seconds"] += elapsed
                    self.stats[uid]["voice_xp"] += int(elapsed / 15)
                    self.stats[uid]["username"] = member.display_name
                    self.save_stats()

    @commands.hybrid_command(name="vtop", aliases=["voiceleaderboard", "vlb", "topvoice"], description="Display Top Voice Chatters & Music Listeners in the server.")
    async def voice_leaderboard(self, ctx: commands.Context):
        if not self.stats:
            return await ctx.send("📜 No voice activity recorded yet. Join a voice channel to start ranking!", ephemeral=True)

        # Sort by total_seconds
        sorted_users = sorted(self.stats.items(), key=lambda x: x[1].get("total_seconds", 0), reverse=True)[:10]

        lines = []
        for rank, (uid_str, data) in enumerate(sorted_users, 1):
            uid = int(uid_str)
            member = ctx.guild.get_member(uid)
            name = member.mention if member else data.get("username", f"User {uid}")
            dur = self.format_duration(data.get("total_seconds", 0))
            xp = data.get("voice_xp", 0)

            medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"`#{rank}`"))
            lines.append(f"{medal} **{name}** — ⏱️ `{dur}` • `⭐ {xp} Voice XP`")

        embed = discord.Embed(
            title=f"🏆 Top Voice Chatters • {ctx.guild.name}",
            description="\n".join(lines),
            color=config.COLOR_GOLD
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="RAI VIBES 💗 • Active Voice Gamification", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="vstats", aliases=["voicestats"], description="Check your or another member's total voice channel time and rank.")
    @app_commands.describe(member="Optional member to inspect voice stats for")
    async def voice_stats(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        target = member or ctx.author
        uid = str(target.id)
        data = self.stats.get(uid, {"total_seconds": 0, "voice_xp": 0})

        dur = self.format_duration(data.get("total_seconds", 0))
        xp = data.get("voice_xp", 0)

        # Calculate rank
        sorted_keys = [k for k, v in sorted(self.stats.items(), key=lambda x: x[1].get("total_seconds", 0), reverse=True)]
        rank = (sorted_keys.index(uid) + 1) if uid in sorted_keys else len(sorted_keys) + 1

        embed = discord.Embed(
            title=f"🎙️ Voice Activity Profile • {target.display_name}",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="⏱️ Total Time in Voice", value=f"`{dur}`", inline=True)
        embed.add_field(name="⭐ Voice XP", value=f"`{xp} XP`", inline=True)
        embed.add_field(name="🏆 Server Voice Rank", value=f"`#{rank}`", inline=True)
        embed.set_footer(text="RAI VIBES 💗 • High Fidelity Sound Engine", icon_url=config.RAI_ICON_URL)

        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(VoiceStats(bot))
