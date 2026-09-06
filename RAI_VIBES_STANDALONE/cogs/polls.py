import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button
from typing import List, Dict

import config

class PollVoteButton(Button):
    def __init__(self, option_index: int, label: str):
        super().__init__(label=label, style=discord.ButtonStyle.primary, row=option_index // 5)
        self.option_index = option_index

    async def callback(self, interaction: discord.Interaction):
        view: PollView = self.view
        user_id = interaction.user.id

        # Update votes (one vote per user)
        for opt_idx, voters in view.votes.items():
            if user_id in voters:
                voters.remove(user_id)

        view.votes[self.option_index].add(user_id)
        embed = view.generate_embed()
        await interaction.response.edit_message(embed=embed, view=view)


class PollView(View):
    def __init__(self, question: str, options: List[str], author: discord.Member):
        super().__init__(timeout=None)
        self.question = question
        self.options = options
        self.author = author
        self.votes: Dict[int, set] = {i: set() for i in range(len(options))}

        for i, opt in enumerate(options):
            self.add_item(PollVoteButton(i, f"{i+1}. {opt[:40]}"))

    def generate_embed(self) -> discord.Embed:
        total_votes = sum(len(voters) for voters in self.votes.values())
        embed = discord.Embed(
            title=f"📊 Community Poll: {self.question}",
            color=config.COLOR_PRIMARY
        )
        embed.set_author(name=f"Poll by {self.author.display_name}", icon_url=self.author.display_avatar.url)

        lines = []
        for i, opt in enumerate(self.options):
            count = len(self.votes[i])
            pct = (count / total_votes * 100) if total_votes > 0 else 0
            filled = int(pct / 10)
            bar = "█" * filled + "░" * (10 - filled)
            lines.append(f"**{i+1}. {opt}**\n`{bar}` **{count} votes** ({pct:.1f}%)")

        embed.description = "\n\n".join(lines)
        embed.set_footer(text=f"Total Votes: {total_votes} • Click buttons to cast your vote!", icon_url=config.RAI_ICON_URL)
        return embed


class Polls(commands.Cog):
    """Interactive Community Polls System."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="poll", description="Create an interactive poll with button voting.")
    @app_commands.describe(
        question="The poll question",
        options="Comma-separated options (e.g. Valorant, GTA V, Minecraft)"
    )
    async def poll(self, ctx: commands.Context, question: str, options: str):
        opt_list = [o.strip() for o in options.split(",") if o.strip()]
        if len(opt_list) < 2:
            return await ctx.send("❌ Please provide at least 2 comma-separated options. Example: `/poll question: Best color? options: Red, Blue, Gold`", ephemeral=True)
        if len(opt_list) > 10:
            return await ctx.send("❌ Maximum 10 options allowed per poll.", ephemeral=True)

        view = PollView(question, opt_list, ctx.author)
        embed = view.generate_embed()
        await ctx.send(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Polls(bot))
