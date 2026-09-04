import asyncio
import random
import time
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, button, Button

import config

class GiveawayView(View):
    def __init__(self, prize: str, end_time: float, winner_count: int):
        super().__init__(timeout=None)
        self.prize = prize
        self.end_time = end_time
        self.winner_count = winner_count
        self.entries = set()

    @button(label="Enter Giveaway", emoji="🎉", style=discord.ButtonStyle.success, custom_id="enter_giveaway_btn")
    async def enter_button(self, interaction: discord.Interaction, btn: Button):
        if interaction.user.id in self.entries:
            self.entries.remove(interaction.user.id)
            await interaction.response.send_message("❌ **You left the giveaway.**", ephemeral=True)
        else:
            self.entries.add(interaction.user.id)
            await interaction.response.send_message("🎉 **You entered the giveaway! Good luck!**", ephemeral=True)


class Giveaways(commands.Cog):
    """Automated Community Giveaways Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="giveaway", description="Host an automated giveaway with interactive entry button.")
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(
        duration_minutes="Duration in minutes (e.g. 60)",
        prize="The prize to give away (e.g. Discord Nitro)",
        winners="Number of winners (default 1)"
    )
    async def giveaway(self, ctx: commands.Context, duration_minutes: int, prize: str, winners: int = 1):
        if duration_minutes <= 0 or winners <= 0:
            return await ctx.send("❌ Duration and winners must be positive numbers.", ephemeral=True)

        end_time = time.time() + (duration_minutes * 60)
        end_timestamp = int(end_time)

        embed = discord.Embed(
            title="🎁 APEX COMMUNITY GIVEAWAY 🎁",
            description=(
                f"**Prize:** `{prize}`\n"
                f"**Hosted by:** {ctx.author.mention}\n"
                f"**Winners:** `{winners}`\n"
                f"**Ends:** <t:{end_timestamp}:R> (<t:{end_timestamp}:f>)\n\n"
                "👉 Click the **`[🎉 Enter Giveaway]`** button below to participate!"
            ),
            color=config.COLOR_GOLD
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="Good luck to everyone!", icon_url=config.RAI_ICON_URL)

        view = GiveawayView(prize, end_time, winners)
        msg = await ctx.send(embed=embed, view=view)

        # Wait for giveaway duration
        await asyncio.sleep(duration_minutes * 60)

        # Select Winners
        if not view.entries:
            end_embed = discord.Embed(
                title="🎁 Giveaway Ended (No Entries)",
                description=f"**Prize:** `{prize}`\nNo one participated in the giveaway.",
                color=config.COLOR_DARK
            )
            return await msg.edit(embed=end_embed, view=None)

        winner_ids = random.sample(list(view.entries), min(winners, len(view.entries)))
        winner_mentions = [f"<@{uid}>" for uid in winner_ids]

        win_embed = discord.Embed(
            title="🎉 GIVEAWAY WINNER(S) ANNOUNCED! 🎉",
            description=f"**Prize:** `{prize}`\n**Winner(s):** {', '.join(winner_mentions)}\n\nCongratulations! Please DM {ctx.author.mention} to claim your prize!",
            color=config.COLOR_SUCCESS
        )
        win_embed.set_footer(text="RAI VIBES 💗 Giveaways", icon_url=config.RAI_ICON_URL)

        await msg.edit(embed=win_embed, view=None)
        await ctx.channel.send(f"🎊 Congratulations {', '.join(winner_mentions)}! You won **{prize}**!")


async def setup(bot: commands.Bot):
    await bot.add_cog(Giveaways(bot))
