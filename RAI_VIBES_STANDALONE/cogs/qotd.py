import random
import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands
from typing import Optional

import config

QUESTIONS_CATALOG = [
    "🎧 What is that one song you can listen to on repeat without ever getting tired of it?",
    "🍿 If you could only watch one movie or anime for the rest of your life, which one is it?",
    "🎮 Which game has your highest playtime of all time?",
    "☕ Morning person or midnight night-owl?",
    "✈️ If you could instantly travel anywhere in the world right now for free, where would you go?",
    "🍕 What is your ultimate comfort food after a long, tiring day?",
    "💡 If you could meet any musical artist (living or legend) in person, who would you choose?",
    "🔥 What is your favorite gaming memory with friends?",
    "📱 Which mobile app or game do you use the most every single day?",
    "🌟 If you could have one superpower, what would you pick and why?",
    "🎵 What was the last song you listened to today?",
    "🎬 What is the best movie you've watched recently that you'd recommend to everyone?",
    "🏆 Android or iPhone? What's your daily driver?",
    "🌈 What is your favorite hobby when you're not gaming or listening to music?",
    "💬 What's a life advice or quote that has stuck with you?"
]

class QOTD(commands.Cog):
    """Question of the Day (QOTD) Automated Engagement Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.daily_qotd_loop.start()

    def cog_unload(self):
        self.daily_qotd_loop.cancel()

    async def post_daily_question(self, guild: discord.Guild, question: Optional[str] = None) -> Optional[discord.Message]:
        channel = (
            discord.utils.get(guild.text_channels, name="qotd") or
            discord.utils.get(guild.text_channels, name="question-of-the-day") or
            next((c for c in guild.text_channels if "qotd" in c.name), None)
        )
        if not channel:
            return None

        chosen_question = question or random.choice(QUESTIONS_CATALOG)

        embed = discord.Embed(
            title="🌸 QUESTION OF THE DAY • RAI FAM 💗",
            description=f"### 💡 **{chosen_question}**\n\n*Share your thoughts below! A discussion thread has been opened for everyone to chat!*",
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="Daily QOTD • Join the Conversation!", icon_url=config.RAI_ICON_URL)

        msg = await channel.send(embed=embed)
        try:
            thread = await msg.create_thread(name="💬 Today's Discussion", auto_archive_duration=1440)
            await thread.send(f"Welcome to today's QOTD discussion! Drop your answers here 👇")
        except Exception:
            pass

        return msg

    @tasks.loop(hours=24.0)
    async def daily_qotd_loop(self):
        """Automatically posts a daily question across all servers every 24 hours."""
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            try:
                await self.post_daily_question(guild)
            except Exception as e:
                print(f"[QOTD Loop Error] {e}")

    @daily_qotd_loop.before_loop
    async def before_qotd(self):
        await self.bot.wait_until_ready()

    @commands.hybrid_command(name="qotd", description="Post a new Question of the Day in #qotd.")
    @app_commands.describe(question="Optional custom question to post")
    async def qotd(self, ctx: commands.Context, question: Optional[str] = None):
        if not ctx.author.guild_permissions.manage_messages and not ctx.author.guild_permissions.administrator:
            return await ctx.send("❌ You need Manage Messages permission to trigger a new QOTD.", ephemeral=True)

        await ctx.defer(ephemeral=True)
        msg = await self.post_daily_question(ctx.guild, question=question)
        if msg:
            await ctx.send("✅ **Question of the Day posted successfully!**", ephemeral=True)
        else:
            await ctx.send("❌ Could not find `#qotd` channel in this server.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(QOTD(bot))
