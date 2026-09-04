import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

import config

class Movies(commands.Cog):
    """Cinema & Movie Night Management for Chill Communities."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="movie_schedule", description="Announce and schedule an upcoming Movie Night / Cinema Stream.")
    @commands.has_permissions(manage_events=True)
    @app_commands.describe(
        title="Movie or Anime title to watch",
        time="Time/date for movie night (e.g. Tonight @ 8:00 PM)",
        genre="Genre (e.g. Horror, Comedy, Anime)",
        description="Short synopsis or description"
    )
    async def movie_schedule(self, ctx: commands.Context, title: str, time: str, genre: str = "Movie", description: Optional[str] = None):
        movie_role = discord.utils.get(ctx.guild.roles, name="🍿 Movie Night Ping")
        mention_text = movie_role.mention if movie_role else "@everyone"

        embed = discord.Embed(
            title=f"🎬 UPCOMING MOVIE NIGHT: {title.upper()}",
            description=(
                f"**Genre:** `{genre}`\n"
                f"**Scheduled Time:** ⏰ `{time}`\n"
                f"**Hosted by:** {ctx.author.mention}\n\n"
                f"**Synopsis:**\n{description or 'Grab your popcorn and drinks! We are streaming this in the Cinema Theater voice channel.'}\n\n"
                "👉 Join **`🎥・Cinema Theater 1 [Screen Share]`** when the event starts!"
            ),
            color=config.COLOR_GOLD
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2809/2809590.png")
        embed.set_footer(text="Apex Cinema & Watch Party", icon_url=config.RAI_ICON_URL)

        sched_chan = discord.utils.get(ctx.guild.text_channels, name="╭・「🎬」movie-schedule") or discord.utils.get(ctx.guild.text_channels, name="🎬・movie-schedule") or ctx.channel
        await sched_chan.send(content=f"🍿 {mention_text} **New Movie Night Scheduled!**", embed=embed)
        if sched_chan != ctx.channel:
            await ctx.send(f"✅ Movie Night scheduled in {sched_chan.mention}!", ephemeral=True)

    @commands.hybrid_command(name="movie_suggest", description="Suggest a movie or show for the next community watch party.")
    @app_commands.describe(title="Name of the movie or show")
    async def movie_suggest(self, ctx: commands.Context, title: str):
        suggest_chan = discord.utils.get(ctx.guild.text_channels, name="╰・「📺」movie-suggestions") or discord.utils.get(ctx.guild.text_channels, name="📺・movie-suggestions") or ctx.channel

        embed = discord.Embed(
            title="📺 New Movie Suggestion",
            description=f"**Title:** `{title}`\n**Suggested By:** {ctx.author.mention}\n\nReact with 👍 or 👎 to vote for this movie!",
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="Apex Movie Suggestions", icon_url=config.RAI_ICON_URL)

        msg = await suggest_chan.send(embed=embed)
        await msg.add_reaction("👍")
        await msg.add_reaction("👎")
        if suggest_chan != ctx.channel:
            await ctx.send("✅ Movie suggestion submitted!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Movies(bot))
