import os
import json
import asyncio
import datetime
from pathlib import Path
from typing import Optional, Literal

import discord
from discord.ext import commands, tasks
from discord import app_commands
from discord.ui import View, Button, button

import config

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BIRTHDAY_FILE = DATA_DIR / "birthdays.json"

MONTH_NAMES = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

class BirthdayWishButtonView(View):
    """Interactive Button allowing members to click and send an instant birthday wish!"""
    def __init__(self, target_id: int, target_name: str):
        super().__init__(timeout=86400) # Active for 24 hours
        self.target_id = target_id
        self.target_name = target_name

    @button(label="🎂 Wish Happy Birthday!", style=discord.ButtonStyle.primary, emoji="🎉", custom_id="wish_bday_btn")
    async def wish_button(self, interaction: discord.Interaction, btn: Button):
        if interaction.user.id == self.target_id:
            return await interaction.response.send_message("🎂 Happy Birthday to you! Enjoy your special day! 🌸💗", ephemeral=True)
        
        await interaction.response.send_message(
            f"🎉 {interaction.user.mention} wishes <@{self.target_id}>: **`Happy Birthday! May your year be filled with success, music & happiness! 🎂✨🎁`**",
            ephemeral=False
        )


class Birthday(commands.Cog):
    """Automated Birthday Announcement & Celebration Engine for RAI FAM 💗."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.birthdays = self.load_birthdays()
        self.wished_today = set() # (user_id, year)
        self.birthday_check_loop.start()

    def cog_unload(self):
        self.birthday_check_loop.cancel()
        self.save_birthdays()

    def load_birthdays(self) -> dict:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if BIRTHDAY_FILE.exists():
            try:
                with open(BIRTHDAY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_birthdays(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(BIRTHDAY_FILE, "w", encoding="utf-8") as f:
            json.dump(self.birthdays, f, indent=2)

    async def announce_birthday(self, guild: discord.Guild, member: discord.Member):
        """Sends the Grand Royal Birthday Announcement in Announcements & General."""
        target_channel = (
            discord.utils.get(guild.text_channels, name="📢・announcements") or
            discord.utils.get(guild.text_channels, name="announcements") or
            discord.utils.get(guild.text_channels, name="💬・general") or
            guild.text_channels[0]
        )

        if not target_channel:
            return

        embed = discord.Embed(
            title="🎂 ROYAL BIRTHDAY CELEBRATION • RAI FAM 💗",
            description=(
                f"# 🎉 **HAPPY BIRTHDAY, {member.mention}!** 🍰✨\n\n"
                f"Today is a very special day! The entire **{guild.name}** family is sending you our warmest, happiest, and most joyful birthday wishes! 🌸💖\n\n"
                f"🎁 **Birthday Perks & Wishes:**\n"
                f"• May all your gaming matches, edits, and dreams come true! 🎮⚡\n"
                f"• Enjoy non-stop vibe sessions in our 24/7 music lounges! 🎧\n"
                f"• Have a legendary day filled with cake, laughter, and great memories! 🥳🍿\n\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"👇 *Click the button below to wish {member.display_name} a Happy Birthday!*"
            ),
            color=0xFF69B4
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url="https://media.giphy.com/media/l4KhQo2MESJkc6HyM/giphy.gif")
        embed.set_footer(text=f"RAI FAM Birthday System • Celebrate Together 💗", icon_url=guild.icon.url if guild.icon else None)

        view = BirthdayWishButtonView(target_id=member.id, target_name=member.display_name)
        try:
            await target_channel.send(
                content=f"🎉 **TODAY IS A SPECIAL DAY! EVERYONE WISH HAPPY BIRTHDAY TO {member.mention}!** 🎂🎁✨",
                embed=embed,
                view=view
            )
        except Exception as e:
            pass

    @tasks.loop(hours=1)
    async def birthday_check_loop(self):
        """Checks daily at top of hour if today matches any member's birthday."""
        now = datetime.datetime.now()
        day = now.day
        month = now.month
        year = now.year

        for guild in self.bot.guilds:
            for uid_str, data in self.birthdays.items():
                if data.get("day") == day and data.get("month") == month:
                    user_id = int(uid_str)
                    wish_key = f"{user_id}_{year}_{month}_{day}"
                    if wish_key not in self.wished_today:
                        member = guild.get_member(user_id)
                        if member:
                            self.wished_today.add(wish_key)
                            await self.announce_birthday(guild, member)

    @birthday_check_loop.before_loop
    async def before_check(self):
        await self.bot.wait_until_ready()

    # ==========================================
    # BIRTHDAY SLASH COMMANDS
    # ==========================================

    @commands.hybrid_command(name="setbirthday", description="Set your birthday so RAI FAM can celebrate & announce your special day!")
    @app_commands.describe(
        day="Day of birth (1-31)",
        month="Month of birth (1-12)"
    )
    async def set_birthday(self, ctx: commands.Context, day: int, month: int):
        if not (1 <= month <= 12):
            return await ctx.send("❌ Invalid month! Please enter a month between 1 and 12 (e.g. 8 for August).", ephemeral=True)
        if not (1 <= day <= 31):
            return await ctx.send("❌ Invalid day! Please enter a day between 1 and 31.", ephemeral=True)

        uid = str(ctx.author.id)
        month_name = MONTH_NAMES[month - 1]

        self.birthdays[uid] = {
            "day": day,
            "month": month,
            "username": ctx.author.name
        }
        self.save_birthdays()

        embed = discord.Embed(
            title="🎂 Birthday Successfully Saved!",
            description=(
                f"✅ Hey {ctx.author.mention}, your birthday has been registered as **{month_name} {day}**! 🎉\n\n"
                f"When your special day arrives, **RAI FAM 💗** will automatically announce your birthday and celebrate with everyone in `#📢・announcements`! 🍰✨"
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="upcoming_birthdays", aliases=["birthdays", "bdaylist"], description="View upcoming server member birthdays.")
    async def upcoming_birthdays(self, ctx: commands.Context):
        if not self.birthdays:
            return await ctx.send("ℹ️ No birthdays registered yet! Use `/setbirthday` to register yours! 🎂", ephemeral=True)

        sorted_list = sorted(self.birthdays.items(), key=lambda x: (x[1]["month"], x[1]["day"]))
        
        lines = []
        for uid_str, data in sorted_list[:15]:
            member = ctx.guild.get_member(int(uid_str))
            name = member.mention if member else data.get("username", "Member")
            m_name = MONTH_NAMES[data["month"] - 1]
            lines.append(f"• **{m_name} {data['day']}** — {name}")

        embed = discord.Embed(
            title="🎂 UPCOMING BIRTHDAYS • RAI FAM 💗",
            description="\n".join(lines) if lines else "No birthdays found.",
            color=0xFF69B4
        )
        embed.set_footer(text="Use /setbirthday to add your birthday to the list!")
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="wish_birthday", description="[Staff / Fun] Trigger a live birthday celebration for a member right now!")
    @app_commands.describe(member="Member to celebrate birthday for")
    async def wish_birthday_cmd(self, ctx: commands.Context, member: discord.Member):
        await ctx.defer()
        await self.announce_birthday(ctx.guild, member)
        await ctx.send(f"✅ Birthday celebration announcement sent for {member.mention}!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Birthday(bot))
