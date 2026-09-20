import os
import time
import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional

import discord
from discord.ext import commands, tasks

logger = logging.getLogger("ServerStats")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATS_CONFIG_FILE = DATA_DIR / "server_stats.json"

DEFAULT_STATS_CONFIG: Dict[str, Dict[str, Any]] = {
    # ABIJITH 777
    "1428058914141900860": {
        "category_id": 1550235570700165221,
        "ch_all": 1550235757526917253,
        "ch_humans": 1550235577285214218,
        "ch_bots": 1550235585808171079,
        "format_all": "| • ALL MEMBERS: {total}",
        "format_humans": "| • MEMBERS: {humans}",
        "format_bots": "| • BOTS: {bots}",
    },
    # RAI FAM💗
    "1457382179981099090": {
        "category_id": 1546059369085534229,
        "ch_all": 1546099701496029194,
        "ch_humans": 1546099703630798848,
        "ch_bots": 1546059375574130769,
        "format_all": "👥・All Members: {total}",
        "format_humans": "👤・Members: {humans}",
        "format_bots": "🤖・Bots: {bots}",
    }
}

class ServerStats(commands.Cog):
    """Multi-Guild Live Server Member Statistics Engine with Real-Time Auto-Update."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._last_edit_time: Dict[int, float] = {}  # channel_id -> timestamp
        self._config_cache: Dict[str, Dict[str, Any]] = {}
        self.announced_milestones: Dict[int, set] = {}
        self.load_config()

    def load_config(self):
        """Load stats configuration from data/server_stats.json or initialize defaults."""
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if STATS_CONFIG_FILE.exists():
            try:
                with open(STATS_CONFIG_FILE, "r", encoding="utf-8") as f:
                    self._config_cache = json.load(f)
            except Exception as e:
                logger.warning(f"Could not read {STATS_CONFIG_FILE}: {e}")
                self._config_cache = DEFAULT_STATS_CONFIG.copy()
        else:
            self._config_cache = DEFAULT_STATS_CONFIG.copy()
            self.save_config()

    def save_config(self):
        """Save active stats configuration to disk."""
        try:
            with open(STATS_CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(self._config_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save {STATS_CONFIG_FILE}: {e}")

    async def cog_load(self):
        if not self.stats_loop.is_running():
            self.stats_loop.start()

    def cog_unload(self):
        self.stats_loop.cancel()

    async def update_all_stats(self):
        """Iterate through all configured guilds and update live stats."""
        self.load_config()
        for g_id_str, cfg in list(self._config_cache.items()):
            try:
                guild = self.bot.get_guild(int(g_id_str))
                if guild:
                    await self.update_stats_for_guild(guild, cfg)
            except Exception as e:
                logger.error(f"Error updating stats for guild {g_id_str}: {e}")

    async def update_stats_for_guild(self, guild: discord.Guild, cfg: Optional[Dict[str, Any]] = None):
        """Fetch member counts for a specific guild and update its stat channels."""
        g_id_str = str(guild.id)
        if not cfg:
            cfg = self._config_cache.get(g_id_str, DEFAULT_STATS_CONFIG.get(g_id_str))
        if not cfg:
            return

        try:
            # Count members accurately
            try:
                members = [m async for m in guild.fetch_members(limit=1000)]
                bots = len([m for m in members if m.bot])
                humans = len(members) - bots
                total = len(members)
            except Exception:
                try:
                    full_guild = await self.bot.fetch_guild(guild.id, with_counts=True)
                    total = full_guild.approximate_member_count or guild.member_count or 27
                except Exception:
                    total = guild.member_count or 27
                cached_bots = len([m for m in guild.members if m.bot])
                bots = cached_bots or 5
                humans = total - bots if total >= bots else total

            format_all = cfg.get("format_all", "| • ALL MEMBERS: {total}")
            format_humans = cfg.get("format_humans", "| • MEMBERS: {humans}")
            format_bots = cfg.get("format_bots", "| • BOTS: {bots}")

            target_all = format_all.format(total=total)
            target_humans = format_humans.format(humans=humans)
            target_bots = format_bots.format(bots=bots)

            # Update channels with per-channel rate limit guard (minimum 300s between edits per channel)
            channel_mappings = [
                (cfg.get("ch_all"), target_all, "All Members"),
                (cfg.get("ch_humans"), target_humans, "Humans"),
                (cfg.get("ch_bots"), target_bots, "Bots"),
            ]

            now = time.time()
            for ch_id, target_name, label in channel_mappings:
                if not ch_id:
                    continue
                ch = guild.get_channel(ch_id) or self.bot.get_channel(ch_id)
                if not ch:
                    continue

                if ch.name != target_name:
                    last_edit = self._last_edit_time.get(ch_id, 0)
                    if now - last_edit < 300:  # 5 min cooldown per channel
                        logger.debug(f"Skipping edit for {ch.name} (cooldown: {int(300 - (now - last_edit))}s)")
                        continue

                    try:
                        await ch.edit(name=target_name)
                        self._last_edit_time[ch_id] = now
                        logger.info(f"[{guild.name}] Updated {label} -> '{target_name}'")
                    except discord.errors.HTTPException as e:
                        if e.status == 429:
                            logger.warning(f"[{guild.name}] {ch.name} rate limited by Discord.")
                        else:
                            logger.error(f"[{guild.name}] Failed to update {ch.name}: {e}")

            # Check milestone for RAI FAM
            if guild.id == 1457382179981099090:
                await self.check_milestones(guild, total)

        except Exception as e:
            logger.error(f"Error in update_stats_for_guild ({guild.name}): {e}")

    async def check_milestones(self, guild: discord.Guild, total_members: int):
        milestones_file = DATA_DIR / "milestones.json"
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        MILESTONES = [30, 50, 75, 100, 150, 200, 250, 500]

        if guild.id not in self.announced_milestones:
            announced_set = set()
            if milestones_file.exists():
                try:
                    with open(milestones_file, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if isinstance(data, list):
                            announced_set = set(data)
                        elif isinstance(data, dict):
                            announced_set = set(data.get(str(guild.id), []))
                except Exception:
                    announced_set = set()
            # Seed with all milestones already achieved up to current member count so we NEVER announce past ones!
            for m in MILESTONES:
                if total_members >= m:
                    announced_set.add(m)
            self.announced_milestones[guild.id] = announced_set
            try:
                with open(milestones_file, "w", encoding="utf-8") as f:
                    json.dump({str(guild.id): list(announced_set)}, f, indent=2)
            except Exception:
                pass
            return  # On bot boot/init, seed and exit without spamming

        announced_set = self.announced_milestones[guild.id]
        for m in MILESTONES:
            if total_members >= m and m not in announced_set:
                announced_set.add(m)
                try:
                    with open(milestones_file, "w", encoding="utf-8") as f:
                        json.dump({str(guild.id): list(announced_set)}, f, indent=2)
                except Exception:
                    pass

                ch = guild.get_channel(1545502718792175646) or guild.get_channel(1545502730699808768)
                if ch:
                    embed = discord.Embed(
                        title="🎉 ✦ SERVER MILESTONE ACHIEVED! ✦ 🎉",
                        description=(
                            f"✨ **{guild.name} has officially crossed {m} Members!** ✨\n\n"
                            f"A massive thank you to everyone who made this community vibrant, welcoming, and fun!\n"
                            f"Here is to the next big milestone on our journey together! 🌸"
                        ),
                        color=0xFF69B4
                    )
                    icon_url = guild.icon.url if guild.icon else None
                    embed.set_footer(text=f"{guild.name} Milestone Tracker • {total_members} Members Strong", icon_url=icon_url)
                    try:
                        # SILENT CELEBRATION: Never ping @everyone
                        await ch.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
                    except Exception:
                        pass
                logger.info(f"Announced server milestone: {m} members in {guild.name}!")

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        """Auto-update server stats immediately when a new member joins."""
        await asyncio.sleep(2)  # Short delay to allow Discord member count to sync
        await self.update_stats_for_guild(member.guild)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        """Auto-update server stats immediately when a member leaves."""
        await asyncio.sleep(2)
        await self.update_stats_for_guild(member.guild)

    @tasks.loop(minutes=5)
    async def stats_loop(self):
        """Periodic auto-update loop every 5 minutes."""
        await self.update_all_stats()

    @stats_loop.before_loop
    async def before_stats(self):
        while not self.bot.is_ready():
            await asyncio.sleep(1)


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerStats(bot))
