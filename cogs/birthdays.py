import json
import datetime
from pathlib import Path
import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Dict

import config

BIRTHDAY_FILE = Path(__file__).resolve().parent.parent / "data" / "birthdays.json"

def load_birthdays() -> Dict[str, dict]:
    if not BIRTHDAY_FILE.exists():
        BIRTHDAY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(BIRTHDAY_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    try:
        with open(BIRTHDAY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_birthdays(data: dict):
    BIRTHDAY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(BIRTHDAY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class Birthdays(commands.Cog):
    """Member Birthday & Celebration System."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.celebrated_today = set()
        self.check_birthdays.start()

    def cog_unload(self):
        self.check_birthdays.cancel()

    @tasks.loop(hours=1)
    async def check_birthdays(self):
        now = datetime.datetime.now()
        today_key = f"{now.month:02d}-{now.day:02d}"

        if now.hour == 0:
            self.celebrated_today.clear()

        data = load_birthdays()
        for user_id, info in data.items():
            if info.get("bday") == today_key and user_id not in self.celebrated_today:
                self.celebrated_today.add(user_id)
                # Post in Celebrations channel across guilds
                for guild in self.bot.guilds:
                    member = guild.get_member(int(user_id))
                    if member:
                        channel = discord.utils.get(guild.text_channels, name="🎉・celebrations") or discord.utils.get(guild.text_channels, name="💬・general-chat")
                        if channel:
                            embed = discord.Embed(
                                title="🎂 HAPPY BIRTHDAY! 🎉",
                                description=f"Wishing a fantastic birthday to {member.mention}! 🎈✨\nMay your day be filled with power, good vibes, and great music!",
                                color=config.COLOR_GOLD
                            )
                            embed.set_thumbnail(url=member.display_avatar.url)
                            embed.set_footer(text="RAI VIBES 💗 Celebrations", icon_url=config.RAI_ICON_URL)
                            try:
                                await channel.send(content=f"🎉 Everyone wish {member.mention} a Happy Birthday! 🎂", embed=embed)
                            except Exception:
                                pass

    @commands.hybrid_command(name="birthday_set", aliases=["setbday"], description="Set your birthday for server celebrations (Month and Day).")
    @app_commands.describe(month="Month (1-12)", day="Day (1-31)")
    async def set_birthday(self, ctx: commands.Context, month: int, day: int):
        if not (1 <= month <= 12 and 1 <= day <= 31):
            return await ctx.send("❌ Invalid date. Month must be 1-12 and day 1-31.", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_birthdays()
        data[user_id] = {
            "name": ctx.author.name,
            "bday": f"{month:02d}-{day:02d}"
        }
        save_birthdays(data)

        month_name = datetime.date(2000, month, 1).strftime("%B")
        await ctx.send(f"🎂 **Your birthday has been registered as {month_name} {day}!** We'll celebrate you when the day arrives! 🎉")


async def setup(bot: commands.Bot):
    await bot.add_cog(Birthdays(bot))
