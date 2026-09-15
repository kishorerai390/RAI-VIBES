import random
import discord
from discord import app_commands
from discord.ext import commands, tasks
import logging
from typing import Optional
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
    "What is the best piece of advice anyone has ever given you?"
]

class QOTD(commands.Cog):
    """Question of the Day Discussion Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="qotd", description="Post an interactive Question of the Day to spark chat discussion.")
    @app_commands.describe(question="Optional custom question (leave blank for a random curated topic)")
    async def qotd_command(self, interaction: discord.Interaction, question: Optional[str] = None):
        if not interaction.user.guild_permissions.manage_messages and interaction.user.id != 1457380609641938981:
            return await interaction.response.send_message("❌ You lack permissions to post QOTD.", ephemeral=True)

        chosen = question or random.choice(QOTD_POOL)

        embed = discord.Embed(
            title="💬 QUESTION OF THE DAY • RAI FAM 💗",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"### {chosen}\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Drop your answers in chat below! React with your thoughts!* 🌸"
            ),
            color=0xFF69B4
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1149363065603702834.webp?size=96&quality=lossless")
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
