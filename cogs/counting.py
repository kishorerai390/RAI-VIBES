import os
import json
import logging
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands

import config
from cogs.economy import update_user_coins

logger = logging.getLogger("Counting")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
COUNTING_FILE = DATA_DIR / "counting.json"
COUNTING_CHANNEL_ID = 1550052961445486633


def load_counting_data() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if COUNTING_FILE.exists():
        try:
            with open(COUNTING_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"current": 0, "last_user_id": 0, "high_score": 0}
    return {"current": 0, "last_user_id": 0, "high_score": 0}


def save_counting_data(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(COUNTING_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class Counting(commands.Cog):
    """Interactive Counting Game Engine with Rai Coins Rewards."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = load_counting_data()

    def is_counting_channel(self, channel: discord.TextChannel) -> bool:
        if channel.id == COUNTING_CHANNEL_ID:
            return True
        return "counting" in channel.name.lower() or "ᴄᴏᴜɴᴛɪɴɢ" in channel.name

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        if not self.is_counting_channel(message.channel):
            return

        content = message.content.strip()
        # Only process if message starts with digits
        if not content.isdigit():
            return

        try:
            number = int(content)
        except ValueError:
            return

        current = self.data.get("current", 0)
        last_user = self.data.get("last_user_id", 0)
        expected = current + 1

        # Anti double-count rule (cannot count twice consecutively)
        if message.author.id == last_user and current > 0:
            try:
                await message.add_reaction("❌")
            except Exception:
                pass

            old_high = self.data.get("high_score", 0)
            self.data["current"] = 0
            self.data["last_user_id"] = 0
            save_counting_data(self.data)

            embed = discord.Embed(
                title="❌ ┊ 𝐃𝐎𝐔𝐁𝐋𝐄  𝐂𝐎Ｕ𝐍𝐓  𝐕𝐈𝐎𝐋𝐀𝐓𝐈𝐎𝐍",
                description=(
                    f"{message.author.mention} you cannot count two numbers in a row!\n"
                    f"The count has been **reset to 0**.\n\n"
                    f"🏆 **Previous Peak:** `{current}`\n"
                    f"⭐ **All-Time Record:** `{old_high}`\n\n"
                    f"Start the comeback with `1`!"
                ),
                color=0xFF4757
            )
            embed.set_footer(text="RAI FAM 💗 • Teamwork Mini-Games", icon_url=config.RAI_ICON_URL)
            await message.channel.send(embed=embed)
            return

        # Incorrect number sequence rule
        if number != expected:
            try:
                await message.add_reaction("❌")
            except Exception:
                pass

            old_high = self.data.get("high_score", 0)
            self.data["current"] = 0
            self.data["last_user_id"] = 0
            save_counting_data(self.data)

            embed = discord.Embed(
                title="💥 ┊ 𝐂𝐎Ｕ𝐍𝐓  𝐑𝐔𝐈𝐍𝐄𝐃!",
                description=(
                    f"{message.author.mention} entered **`{number}`**, but the next number was **`{expected}`**!\n"
                    f"The streak was broken and count **resets to 0**.\n\n"
                    f"🏆 **Streak Ended At:** `{current}`\n"
                    f"⭐ **All-Time Record:** `{old_high}`\n\n"
                    f"Begin anew by typing `1`!"
                ),
                color=0xFF4757
            )
            embed.set_footer(text="RAI FAM 💗 • Counting Challenge", icon_url=config.RAI_ICON_URL)
            await message.channel.send(embed=embed)
            return

        # Correct number!
        self.data["current"] = number
        self.data["last_user_id"] = message.author.id
        if number > self.data.get("high_score", 0):
            self.data["high_score"] = number
        save_counting_data(self.data)

        # React with celebration or green check
        if number % 100 == 0:
            try:
                await message.add_reaction("💯")
            except Exception:
                pass
            bonus = 2500
            update_user_coins(message.author.id, bonus)
            embed = discord.Embed(
                title=f"🎉 ┊ 𝐌𝐈𝐋𝐄𝐒𝐓𝐎𝐍𝐄  𝐑𝐄𝐀𝐂𝐇𝐄𝐃: {number}!",
                description=(
                    f"👑 Incredible teamwork! {message.author.mention} hit **{number}**!\n\n"
                    f"🎁 **Reward:** `+{bonus:,} 🪙 Rai Coins` granted!\n"
                    f"⭐ **Current High Score:** `{self.data['high_score']}`"
                ),
                color=0xFFD700
            )
            embed.set_footer(text="RAI FAM 💗 • Century Milestone", icon_url=config.RAI_ICON_URL)
            await message.channel.send(embed=embed)
        elif number % 25 == 0:
            try:
                await message.add_reaction("⭐")
            except Exception:
                pass
            bonus = 500
            update_user_coins(message.author.id, bonus)
            embed = discord.Embed(
                title=f"✨ ┊ 𝐂𝐎Ｕ𝐍𝐓  𝐌𝐈𝐋𝐄𝐒𝐓𝐎𝐍𝐄: {number}",
                description=(
                    f"🔥 Great momentum! {message.author.mention} hit **{number}**!\n"
                    f"🎁 **Reward:** `+{bonus:,} 🪙 Rai Coins` added to wallet!"
                ),
                color=0x00FF88
            )
            embed.set_footer(text="RAI FAM 💗 • Mini-Game Matrix", icon_url=config.RAI_ICON_URL)
            await message.channel.send(embed=embed)
        else:
            try:
                await message.add_reaction("✅")
            except Exception:
                pass

    @app_commands.command(name="countstatus", description="Check current counting game streak and high score record.")
    async def countstatus(self, interaction: discord.Interaction):
        current = self.data.get("current", 0)
        high = self.data.get("high_score", 0)
        last_uid = self.data.get("last_user_id", 0)
        last_member = interaction.guild.get_member(last_uid)
        last_name = last_member.display_name if last_member else f"User ID {last_uid}" if last_uid else "None"

        embed = discord.Embed(
            title="🔢 ┊ 𝐂𝐎Ｕ𝐍𝐓𝐈𝐍Ｇ  𝐒𝐓𝐀𝐓𝐔𝐒",
            description=(
                f"**Current Number:** `{current}`\n"
                f"**Next Required:** `{current + 1}`\n"
                f"**Last Counter:** `{last_name}`\n"
                f"**All-Time High Score:** `{high}` 🏆\n\n"
                f"Jump into <#{COUNTING_CHANNEL_ID}> to join the streak!"
            ),
            color=0x00F2FE
        )
        embed.set_footer(text="RAI FAM 💗 • Counting Matrix", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Counting(bot))
