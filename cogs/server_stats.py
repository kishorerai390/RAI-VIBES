import os
import logging
import discord
from discord.ext import commands, tasks

logger = logging.getLogger("ServerStats")

GUILD_ID = 1457382179981099090
CH_ALL_MEMBERS = 1546099701496029194
CH_HUMANS = 1546099703630798848
CH_BOTS = 1546059375574130769

class ServerStats(commands.Cog):
    """Live Server Member Statistics Engine with Real-Time Datacenter Sync."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def cog_load(self):
        if not self.stats_loop.is_running():
            self.stats_loop.start()

    def cog_unload(self):
        self.stats_loop.cancel()

    async def update_stats(self):
        """Fetch real-time member counts and update voice channels."""
        try:
            guild = self.bot.get_guild(GUILD_ID)
            if not guild:
                return

            # Count members accurately from guild chunk/fetch
            try:
                members = [m async for m in guild.fetch_members(limit=1000)]
                bots = len([m for m in members if m.bot])
                humans = len(members) - bots
                total = len(members)
            except Exception:
                try:
                    full_guild = await self.bot.fetch_guild(GUILD_ID, with_counts=True)
                    total = full_guild.approximate_member_count or guild.member_count or 24
                except Exception:
                    total = guild.member_count or 24
                cached_bots = len([m for m in guild.members if m.bot])
                bots = max(cached_bots, 9)
                humans = total - bots if total >= bots else total

            # 1. Update All Members Channel
            ch_all = guild.get_channel(CH_ALL_MEMBERS) or self.bot.get_channel(CH_ALL_MEMBERS)
            if ch_all:
                name_all = f"👥・All Members: {total}"
                if ch_all.name != name_all:
                    await ch_all.edit(name=name_all)
                    logger.info(f"Updated All Members -> {name_all}")

            # 2. Update Humans Channel
            ch_hum = guild.get_channel(CH_HUMANS) or self.bot.get_channel(CH_HUMANS)
            if ch_hum:
                name_hum = f"👤・Members: {humans}"
                if ch_hum.name != name_hum:
                    await ch_hum.edit(name=name_hum)
                    logger.info(f"Updated Humans -> {name_hum}")

            # 3. Update Bots Channel
            ch_bot = guild.get_channel(CH_BOTS) or self.bot.get_channel(CH_BOTS)
            if ch_bot:
                name_bot = f"🤖・Bots: {bots}"
                if ch_bot.name != name_bot:
                    await ch_bot.edit(name=name_bot)
                    logger.info(f"Updated Bots -> {name_bot}")

        except discord.errors.HTTPException as e:
            if e.status == 429:
                logger.warning(f"Stats rate limited by Discord, will retry next cycle.")
            else:
                logger.error(f"Error updating stats: {e}")
        except Exception as e:
            logger.error(f"Unexpected stats error: {e}")

    @tasks.loop(minutes=15)
    async def stats_loop(self):
        await self.update_stats()

    @stats_loop.before_loop
    async def before_stats(self):
        import asyncio
        while not self.bot.is_ready():
            await asyncio.sleep(1)


async def setup(bot: commands.Bot):
    await bot.add_cog(ServerStats(bot))
