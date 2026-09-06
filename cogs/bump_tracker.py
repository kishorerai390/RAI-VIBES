import os
import json
import time
import logging
import discord
from discord.ext import commands, tasks
from discord import app_commands
from pathlib import Path

import config

logger = logging.getLogger("BumpTracker")

BUMP_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "bump_data.json"
GENERAL_CHANNEL_ID = 1545502730699808768
DISBOARD_BOT_ID = 1546072104397443175
COOLDOWN_SECONDS = 7200  # 2 hours

def load_bump_data() -> dict:
    if not BUMP_DATA_FILE.exists():
        BUMP_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BUMP_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_bump": 0, "last_bumper": None, "reminded": True, "total_bumps": 0}, f, indent=2)
        return {"last_bump": 0, "last_bumper": None, "reminded": True, "total_bumps": 0}
    try:
        with open(BUMP_DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_bump": 0, "last_bumper": None, "reminded": True, "total_bumps": 0}

def save_bump_data(data: dict):
    BUMP_DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BUMP_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class BumpTracker(commands.Cog):
    """Automatic 2-Hour Disboard Bump Cooldown Tracker & Reward System."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bump_checker_loop.start()

    def cog_unload(self):
        self.bump_checker_loop.cancel()

    @tasks.loop(minutes=1)
    async def bump_checker_loop(self):
        """Checks every minute if 2 hours have passed since the last bump."""
        await self.bot.wait_until_ready()
        data = load_bump_data()
        last_bump = data.get("last_bump", 0)
        reminded = data.get("reminded", True)

        now = time.time()
        if last_bump > 0 and (now - last_bump >= COOLDOWN_SECONDS) and not reminded:
            # 2 hours elapsed -> Send reminder ping
            channel = self.bot.get_channel(GENERAL_CHANNEL_ID)
            if channel:
                embed = discord.Embed(
                    title="🚀 DISBOARD BUMP IS READY! 🌟",
                    description=(
                        "### 📢 Help RAI FAM Grow!\n"
                        "Our 2-hour Disboard cooldown has expired.\n\n"
                        "👉 **Type `/bump` in this channel right now!**\n"
                        "✨ *The first member to bump gets **+150 Sakura Coins 🪙**!*"
                    ),
                    color=config.COLOR_PRIMARY
                )
                embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3135/3135715.png")
                embed.set_footer(text="RAI FAM 💗 Disboard Growth Engine", icon_url=config.RAI_ICON_URL)

                try:
                    await channel.send(content="🔔 <@&1546088542885642324> **Disboard Bump is ready!**", embed=embed)
                    data["reminded"] = True
                    save_bump_data(data)
                    logger.info("Sent Disboard bump reminder to general chat.")
                except Exception as e:
                    logger.error(f"Failed to send bump reminder: {e}")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Listens for Disboard bump confirmation messages."""
        if not message.guild:
            return

        # Check if message is from DISBOARD bot or contains bump success
        is_disboard = (
            message.author.id == DISBOARD_BOT_ID
            or "disboard" in message.author.name.lower()
            or (message.interaction and "bump" in message.interaction.name.lower())
        )

        if is_disboard:
            # Check embeds for bump success
            is_success = False
            bumper = None

            if message.embeds:
                for emb in message.embeds:
                    desc = (emb.description or "").lower()
                    if "bump done" in desc or "check it on disboard" in desc or "👍" in desc:
                        is_success = True
                        break

            # Or interaction user
            if message.interaction and "bump" in message.interaction.name.lower():
                is_success = True
                bumper = message.interaction.user

            if is_success:
                now = time.time()
                data = load_bump_data()
                data["last_bump"] = now
                data["reminded"] = False
                data["total_bumps"] = data.get("total_bumps", 0) + 1
                if bumper:
                    data["last_bumper"] = bumper.id
                save_bump_data(data)

                # Reward bumper with coins in economy
                try:
                    economy_file = Path(__file__).resolve().parent.parent / "data" / "economy.json"
                    if economy_file.exists():
                        with open(economy_file, "r", encoding="utf-8") as f:
                            econ = json.load(f)
                    else:
                        econ = {}

                    target_id = str(bumper.id) if bumper else str(message.author.id)
                    if target_id not in econ:
                        econ[target_id] = {"coins": 200, "last_daily": 0, "wins": 0, "losses": 0}
                    econ[target_id]["coins"] += 150
                    with open(economy_file, "w", encoding="utf-8") as f:
                        json.dump(econ, f, indent=2)
                except Exception as e:
                    logger.warning(f"Could not credit bump reward: {e}")

                embed = discord.Embed(
                    title="🎉 THANK YOU FOR BUMPING RAI FAM! 🌸",
                    description=(
                        f"Awesome job {bumper.mention if bumper else 'buddy'}!\n"
                        f"• **Reward Added:** `+150 Sakura Coins 🪙`\n"
                        f"• **Next Bump:** <t:{int(now + COOLDOWN_SECONDS)}:R> (<t:{int(now + COOLDOWN_SECONDS)}:t>)\n\n"
                        f"I will remind the server automatically when it's time to bump again! 🚀"
                    ),
                    color=config.COLOR_SUCCESS
                )
                embed.set_footer(text="RAI VIBES 💗 Bump Watchdog", icon_url=config.RAI_ICON_URL)
                await message.channel.send(embed=embed)

    @commands.hybrid_command(name="bumptime", aliases=["nextbump", "bumpstatus"], description="Check when the next Disboard bump is ready.")
    async def bumptime(self, ctx: commands.Context):
        data = load_bump_data()
        last_bump = data.get("last_bump", 0)
        now = time.time()

        if last_bump == 0 or (now - last_bump >= COOLDOWN_SECONDS):
            embed = discord.Embed(
                title="🚀 Disboard Bump is READY NOW!",
                description="👉 Type `/bump` in this channel right now to boost **RAI FAM 💗** on Disboard!",
                color=config.COLOR_SUCCESS
            )
        else:
            remaining = int(COOLDOWN_SECONDS - (now - last_bump))
            embed = discord.Embed(
                title="⏳ Disboard Bump Cooldown",
                description=(
                    f"• **Next Bump Available:** <t:{int(last_bump + COOLDOWN_SECONDS)}:R> (<t:{int(last_bump + COOLDOWN_SECONDS)}:t>)\n"
                    f"• **Total Server Bumps:** `{data.get('total_bumps', 0)}`\n"
                    f"• **Bump Reward:** `+150 Sakura Coins 🪙`"
                ),
                color=config.COLOR_PRIMARY
            )
        embed.set_footer(text="RAI VIBES 💗 Disboard Tracker", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(BumpTracker(bot))
