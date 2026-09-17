import random
import datetime
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands, tasks

import config

logger = logging.getLogger("QOTD")

GENERAL_CHAT_ID = 1545502730699808768

QOTD_POOL = [
    "What is one video game you can replay forever without getting bored?",
    "If you could have dinner with any anime or movie character, who would it be?",
    "PC Gaming or Console Gaming — what is your ultimate preference and why?",
    "What is the single best song or music track you discovered this month?",
    "If you woke up tomorrow with $1,000,000 in your bank account, what is the first thing you buy?",
    "What is your all-time favorite midnight snack while chilling on Discord?",
    "What is one skill or hobby you have always wanted to master?",
    "Single-player story games or competitive multiplayer shooters — which one wins?",
    "What movie or anime made you feel the most emotional?",
    "If you could instantly travel anywhere in the world right now for free, where are you going?",
    "What is your favorite Discord emoji or server sticker right now?",
    "Who is your favorite musical artist or band of all time?",
    "What is your opinion on pineapple on pizza: culinary genius or crime?",
    "If you had to survive in a zombie apocalypse with 3 Discord members, who are you picking?",
    "What is the best piece of advice anyone has ever given you?",
    "What is your favorite comfort food when you've had a long exhausting day?",
    "If you had to listen to only one music genre for the rest of your life, what would it be?",
    "What superpower would you choose: Teleportation, Invisibility, or Time Travel?",
    "What was the very first video game you ever fell in love with?",
    "Do you prefer morning coffee/tea vibes or 2:00 AM midnight energy?",
    "If you could create your own dream anime or game, what would the plot be?",
    "What's one obscure movie or show that you think everyone needs to watch at least once?",
    "What's the funniest Discord or gaming moment you've experienced with friends?",
    "Introvert, Extrovert, or Ambivert — where do you fall and why?",
    "What is your favorite aesthetic: Cyberpunk Neon, Lo-Fi Cozy, Dark Fantasy, or Cottagecore?",
    "If you could instantly speak 3 languages fluently, which 3 would you choose?",
    "What's your proudest gaming achievement (a hard boss defeated, a clutch round, etc.)?",
    "Would you rather live in a futuristic cyberpunk metropolis or a peaceful anime countryside?",
    "What's your go-to song when you need an immediate boost of energy or motivation?"
]

class QOTD(commands.Cog):
    """Question of the Day Discussion Engine with Automated 8:00 PM Broadcast."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.last_posted_date: Optional[str] = None
        self.daily_qotd_loop.start()

    def cog_unload(self):
        self.daily_qotd_loop.cancel()

    @tasks.loop(minutes=15)
    async def daily_qotd_loop(self):
        # 8:00 PM IST corresponds to 14:30 UTC
        now_utc = datetime.datetime.now(datetime.timezone.utc)
        today_str = now_utc.strftime("%Y-%m-%d")

        # Check if 14:30 - 15:00 UTC and haven't posted today yet
        if now_utc.hour == 14 and now_utc.minute >= 30:
            if self.last_posted_date != today_str:
                self.last_posted_date = today_str
                await self._post_daily_qotd()

    @daily_qotd_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    async def _post_daily_qotd(self, channel_id: int = GENERAL_CHAT_ID):
        channel = self.bot.get_channel(channel_id)
        if not channel:
            return

        chosen = random.choice(QOTD_POOL)
        embed = discord.Embed(
            title="💬 ┊ 𝐐𝐔𝐄𝐒𝐓𝐈𝐎𝐍  𝐎𝐅  𝐓𝐇𝐄  𝐃𝐀𝐘",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"### ✨ {chosen}\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Drop your answers in chat below! React with your thoughts!* 🌸"
            ),
            color=0xFF69B4
        )
        embed.set_footer(text="RAI FAM 💗 • Daily Community Sparks • 8:00 PM Drop", icon_url=config.RAI_ICON_URL)
        msg = await channel.send(embed=embed)
        try:
            await msg.add_reaction("💬")
            await msg.add_reaction("🔥")
            await msg.add_reaction("💖")
        except Exception:
            pass
        logger.info(f"Auto-posted daily QOTD: {chosen}")

    @app_commands.command(name="qotd", description="Post an interactive Question of the Day to spark chat discussion.")
    @app_commands.describe(question="Optional custom question (leave blank for a random curated topic)")
    async def qotd_command(self, interaction: discord.Interaction, question: Optional[str] = None):
        if not interaction.user.guild_permissions.manage_messages and interaction.user.id != 1457380609641938981:
            return await interaction.response.send_message("❌ You lack permissions to post QOTD.", ephemeral=True)

        chosen = question or random.choice(QOTD_POOL)

        embed = discord.Embed(
            title="💬 ┊ 𝐐𝐔𝐄𝐒𝐓𝐈𝐎𝐍  𝐎𝐅  𝐓𝐇𝐄  𝐃𝐀𝐘",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"### ✨ {chosen}\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Drop your answers in chat below! React with your thoughts!* 🌸"
            ),
            color=0xFF69B4
        )
        embed.set_footer(text=f"Hosted by {interaction.user.display_name} • Daily Community Sparks", icon_url=interaction.user.display_avatar.url)

        await interaction.response.send_message("✅ QOTD posted!", ephemeral=True)
        msg = await interaction.channel.send(embed=embed)
        try:
            await msg.add_reaction("💬")
            await msg.add_reaction("🔥")
            await msg.add_reaction("💖")
        except Exception:
            pass

async def setup(bot: commands.Bot):
    await bot.add_cog(QOTD(bot))
