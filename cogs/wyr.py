import random
from typing import Dict, Set
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, button

import config

WYR_QUESTIONS = [
    ("Live in a high-tech cyberpunk metropolis", "Live in a peaceful, magical Studio Ghibli countryside"),
    ("Have free unlimited bubble tea & coffee forever", "Have free unlimited pizza & burgers forever"),
    ("Be able to pause time for 10 minutes a day", "Be able to teleport anywhere once a day"),
    ("Have 100 ping in every multiplayer game forever", "Have 10 FPS in every single-player game forever"),
    ("Be world-famous with zero privacy", "Be completely anonymous with $10,000,000 in your bank"),
    ("Speak every human language fluently", "Be able to speak with and understand all animals"),
    ("Only be able to listen to music while studying/gaming", "Only be able to watch movies with subtitles turned off"),
    ("Never have to sleep again with zero fatigue", "Never have to work again with guaranteed steady income"),
    ("Explore the depths of the uncharted ocean", "Explore deep space on a futuristic starship"),
    ("Win $1,000,000 right now", "Flip a coin for $50,000,000 (win 50M or $0)"),
    ("Have super-human speed like Flash", "Have super-human intelligence like Tony Stark"),
    ("Live in the Minecraft universe", "Live in the Pokemon universe"),
    ("Be forced to sing everything you say for a week", "Be forced to dance whenever you walk for a week"),
    ("Never be able to eat spicy food again", "Never be able to eat sweet desserts again"),
    ("Have your mind read by anyone you talk to", "Always blurt out whatever you are thinking"),
]


class WYRView(View):
    def __init__(self, option_a: str, option_b: str):
        super().__init__(timeout=300)
        self.option_a = option_a
        self.option_b = option_b
        self.votes_a: Set[int] = set()
        self.votes_b: Set[int] = set()

    def make_embed(self) -> discord.Embed:
        total = len(self.votes_a) + len(self.votes_b)
        pct_a = int((len(self.votes_a) / total) * 100) if total > 0 else 50
        pct_b = 100 - pct_a if total > 0 else 50

        bar_a = "█" * (pct_a // 10) + "░" * (10 - (pct_a // 10))
        bar_b = "█" * (pct_b // 10) + "░" * (10 - (pct_b // 10))

        embed = discord.Embed(
            title="🤔 ┊ 𝐖𝐎𝐔𝐋𝐃  𝐘𝐎𝐔  𝐑𝐀𝐓𝐇𝐄𝐑?",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"🅰️ **Option A:** {self.option_a}\n"
                f"`[{bar_a}] {pct_a}% ({len(self.votes_a)} votes)`\n\n"
                f"🅱️ **Option B:** {self.option_b}\n"
                f"`[{bar_b}] {pct_b}% ({len(self.votes_b)} votes)`\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"👉 *Cast your vote by clicking a button below!*"
            ),
            color=0x00F2FE
        )
        embed.set_footer(text=f"Total Votes: {total} • Voting open for 5 minutes", icon_url=config.RAI_ICON_URL)
        return embed

    @button(label="Option A 🅰️", style=discord.ButtonStyle.primary)
    async def vote_a(self, interaction: discord.Interaction, btn: Button):
        uid = interaction.user.id
        self.votes_b.discard(uid)
        self.votes_a.add(uid)
        await interaction.response.edit_message(embed=self.make_embed(), view=self)

    @button(label="Option B 🅱️", style=discord.ButtonStyle.secondary)
    async def vote_b(self, interaction: discord.Interaction, btn: Button):
        uid = interaction.user.id
        self.votes_a.discard(uid)
        self.votes_b.add(uid)
        await interaction.response.edit_message(embed=self.make_embed(), view=self)


class WouldYouRather(commands.Cog):
    """Interactive Dilemmas & Community Discussion Polls."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="wyr", description="Spark chat with an interactive Would You Rather dilemma!")
    async def wyr_command(self, interaction: discord.Interaction):
        opt_a, opt_b = random.choice(WYR_QUESTIONS)
        view = WYRView(opt_a, opt_b)
        embed = view.make_embed()
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(WouldYouRather(bot))
