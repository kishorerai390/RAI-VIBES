import discord
from discord.ext import commands
from discord import app_commands
import aiohttp
import urllib.parse
from typing import Optional
import random

import config

GENRE_MOVIES = {
    "Sci-Fi / Space": [
        {"title": "Interstellar", "year": "2014", "desc": "A team of explorers travel through a wormhole in space in an attempt to ensure humanity's survival.", "imdb": "8.7/10"},
        {"title": "Inception", "year": "2010", "desc": "A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea.", "imdb": "8.8/10"},
        {"title": "Blade Runner 2049", "year": "2017", "desc": "Young Blade Runner K's discovery of a long-buried secret leads him to track down former Blade Runner Rick Deckard.", "imdb": "8.0/10"},
        {"title": "The Matrix", "year": "1999", "desc": "When a beautiful stranger leads computer hacker Neo to a forbidding underworld, he discovers the shocking truth.", "imdb": "8.7/10"}
    ],
    "Action / Thriller": [
        {"title": "The Dark Knight", "year": "2008", "desc": "When the menace known as the Joker wreaks havoc and chaos on Gotham, Batman must accept one of the greatest psychological tests.", "imdb": "9.0/10"},
        {"title": "John Wick: Chapter 4", "year": "2023", "desc": "John Wick uncovers a path to defeating The High Table, but before he can earn his freedom, he must face a new enemy.", "imdb": "7.7/10"},
        {"title": "Mad Max: Fury Road", "year": "2015", "desc": "In a post-apocalyptic wasteland, a woman rebels against a tyrannical ruler in search for her homeland with the aid of Max.", "imdb": "8.1/10"},
        {"title": "Fight Club", "year": "1999", "desc": "An insomniac office worker and a devil-may-care soap maker form an underground fight club that evolves into something much more.", "imdb": "8.8/10"}
    ],
    "Anime / Animation": [
        {"title": "Spirited Away", "year": "2001", "desc": "During her family's move to the suburbs, a 10-year-old girl wanders into a world ruled by gods, witches and spirits.", "imdb": "8.6/10"},
        {"title": "Your Name (Kimi no Na wa)", "year": "2016", "desc": "Two strangers find themselves linked in a bizarre way. When a connection forms, will distance be the only thing to keep them apart?", "imdb": "8.4/10"},
        {"title": "Spider-Man: Across the Spider-Verse", "year": "2023", "desc": "Miles Morales catapults across the Multiverse, where he encounters a team of Spider-People charged with protecting its very existence.", "imdb": "8.6/10"},
        {"title": "Suzume", "year": "2022", "desc": "A modern action adventure road story where a 17-year-old girl named Suzume helps a mysterious young man close doors from the other side.", "imdb": "7.6/10"}
    ],
    "Comedy / Chill": [
        {"title": "Superbad", "year": "2007", "desc": "Two co-dependent high school seniors are forced to deal with separation anxiety after their plan to stage a booze-soaked party goes awry.", "imdb": "7.6/10"},
        {"title": "The Grand Budapest Hotel", "year": "2014", "desc": "A writer encounters the owner of an aging high-class hotel, who tells him of his early years serving as a lobby boy.", "imdb": "8.1/10"},
        {"title": "Knives Out", "year": "2019", "desc": "A detective investigates the death of a patriarch of an eccentric, combative family.", "imdb": "7.9/10"},
        {"title": "Free Guy", "year": "2021", "desc": "A bank teller discovers that he's actually an NPC inside a brutal, open world video game.", "imdb": "7.1/10"}
    ],
    "Horror / Mystery": [
        {"title": "Get Out", "year": "2017", "desc": "A young African-American visits his white girlfriend's parents for the weekend, where his simmering uneasiness reaches a boiling point.", "imdb": "7.8/10"},
        {"title": "Shutter Island", "year": "2010", "desc": "In 1954, a U.S. Marshal investigates the disappearance of a murderer who escaped from a hospital for the criminally insane.", "imdb": "8.2/10"},
        {"title": "A Quiet Place", "year": "2018", "desc": "In a post-apocalyptic world, a family is forced to live in silence while hiding from monsters with ultra-sensitive hearing.", "imdb": "7.5/10"},
        {"title": "Se7en", "year": "1995", "desc": "Two detectives hunt a serial killer who uses the seven deadly sins as his motives.", "imdb": "8.6/10"}
    ]
}

class MovieRSVPView(discord.ui.View):
    def __init__(self, movie_title: str):
        super().__init__(timeout=None)
        self.movie_title = movie_title
        self.attending = set()
        self.maybe = set()

    @discord.ui.button(label="🍿 Going (0)", style=discord.ButtonStyle.success, custom_id="rsvp_going")
    async def going(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.maybe:
            self.maybe.remove(user_id)
        if user_id in self.attending:
            self.attending.remove(user_id)
            await interaction.response.send_message(f"Removed your RSVP for **{self.movie_title}**.", ephemeral=True)
        else:
            self.attending.add(user_id)
            await interaction.response.send_message(f"🎉 You're attending the watch party for **{self.movie_title}**!", ephemeral=True)
        
        button.label = f"🍿 Going ({len(self.attending)})"
        for child in self.children:
            if getattr(child, "custom_id", "") == "rsvp_maybe":
                child.label = f"🤔 Maybe ({len(self.maybe)})"
        await interaction.message.edit(view=self)

    @discord.ui.button(label="🤔 Maybe (0)", style=discord.ButtonStyle.secondary, custom_id="rsvp_maybe")
    async def maybe_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user_id = interaction.user.id
        if user_id in self.attending:
            self.attending.remove(user_id)
        if user_id in self.maybe:
            self.maybe.remove(user_id)
            await interaction.response.send_message(f"Removed your RSVP for **{self.movie_title}**.", ephemeral=True)
        else:
            self.maybe.add(user_id)
            await interaction.response.send_message(f"👍 Marked you as Maybe for **{self.movie_title}**.", ephemeral=True)

        button.label = f"🤔 Maybe ({len(self.maybe)})"
        for child in self.children:
            if getattr(child, "custom_id", "") == "rsvp_going":
                child.label = f"🍿 Going ({len(self.attending)})"
        await interaction.message.edit(view=self)


class CinemaHub(commands.Cog):
    """IMDb Search, Trailer Fetcher, Watch Party RSVP, and Movie Recommendation Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="imdb", description="Search IMDb database for movie/series ratings, plot, and details.")
    @app_commands.describe(title="Name of the movie or show")
    async def imdb(self, ctx: commands.Context, title: str):
        await ctx.defer()
        encoded = urllib.parse.quote(title)
        
        # Query public OMDb API / open movie mirror
        url = f"https://www.omdbapi.com/?t={encoded}&apikey=trilogy"
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=6)) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data.get("Response") == "True":
                            m_title = data.get("Title", title)
                            year = data.get("Year", "N/A")
                            rated = data.get("Rated", "N/A")
                            runtime = data.get("Runtime", "N/A")
                            genre = data.get("Genre", "N/A")
                            director = data.get("Director", "N/A")
                            actors = data.get("Actors", "N/A")
                            plot = data.get("Plot", "No synopsis available.")
                            imdb_rating = data.get("imdbRating", "N/A")
                            poster = data.get("Poster")

                            embed = discord.Embed(
                                title=f"🎬 {m_title} ({year})",
                                description=f"*{plot}*\n\n"
                                            f"⭐ **IMDb Rating:** `{imdb_rating}/10`\n"
                                            f"🎭 **Genre:** `{genre}`\n"
                                            f"⏳ **Runtime:** `{runtime}` | **Rated:** `{rated}`\n"
                                            f"🎬 **Director:** `{director}`\n"
                                            f"🌟 **Cast:** `{actors}`\n\n"
                                            f"🔗 [View on IMDb](https://www.imdb.com/title/{data.get('imdbID', '')})",
                                color=config.COLOR_GOLD
                            )
                            if poster and poster != "N/A":
                                embed.set_thumbnail(url=poster)
                            embed.set_footer(text="Apex Cinema Database", icon_url=config.RAI_ICON_URL)
                            return await ctx.send(embed=embed)
        except Exception:
            pass

        # Fallback Embed if external API limit reached
        embed = discord.Embed(
            title=f"🎬 Search Result: {title.title()}",
            description=f"Could not retrieve live OMDb stream. You can view the full record directly:\n\n"
                        f"👉 [Search '{title}' on IMDb](https://www.imdb.com/find?q={encoded})\n"
                        f"👉 [Search '{title}' on Rotten Tomatoes](https://www.rottentomatoes.com/search?search={encoded})",
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="Apex Cinema Database", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="trailer", description="Find and watch the official YouTube trailer for a movie.")
    @app_commands.describe(movie="Movie title")
    async def trailer(self, ctx: commands.Context, movie: str):
        encoded = urllib.parse.quote(f"{movie} official trailer")
        yt_search_url = f"https://www.youtube.com/results?search_query={encoded}"
        
        embed = discord.Embed(
            title=f"🍿 Official Trailer: {movie.title()}",
            description=f"Click the link below to stream the official trailer:\n\n"
                        f"▶️ **[Watch '{movie.title()}' Trailer on YouTube]({yt_search_url})**\n\n"
                        f"*(Ready to watch together? Hop into `🎥・Cinema Theater 1` and share screen!)*",
            color=config.COLOR_SECONDARY
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1384/1384060.png")
        embed.set_footer(text="Apex Cinema Theater", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="pick_movie", description="Roll a random top-rated movie recommendation by genre.")
    @app_commands.describe(genre="Choose a genre category")
    @app_commands.choices(genre=[
        app_commands.Choice(name="🌌 Sci-Fi / Space", value="Sci-Fi / Space"),
        app_commands.Choice(name="💥 Action / Thriller", value="Action / Thriller"),
        app_commands.Choice(name="🌸 Anime / Animation", value="Anime / Animation"),
        app_commands.Choice(name="😂 Comedy / Chill", value="Comedy / Chill"),
        app_commands.Choice(name="👻 Horror / Mystery", value="Horror / Mystery"),
    ])
    async def pick_movie(self, ctx: commands.Context, genre: Optional[app_commands.Choice[str]] = None):
        selected_genre = genre.value if genre else random.choice(list(GENRE_MOVIES.keys()))
        movies_list = GENRE_MOVIES.get(selected_genre, GENRE_MOVIES["Sci-Fi / Space"])
        pick = random.choice(movies_list)

        embed = discord.Embed(
            title=f"🎲 Squad Pick: {pick['title']} ({pick['year']})",
            description=f"**Category:** `{selected_genre}`\n"
                        f"⭐ **IMDb Score:** `{pick['imdb']}`\n\n"
                        f"**Plot Synopsis:**\n{pick['desc']}\n\n"
                        f"👉 [Watch Trailer](https://www.youtube.com/results?search_query={urllib.parse.quote(pick['title'] + ' trailer')})",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3172/3172555.png")
        embed.set_footer(text="Roll again with /pick_movie", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="movie_party", description="Create an interactive Watch Party invitation with RSVP buttons.")
    @app_commands.describe(
        title="Movie or Show title",
        time="Scheduled watch time (e.g. Tonight at 9:00 PM)",
        theater="Voice channel theater to host in"
    )
    async def movie_party(self, ctx: commands.Context, title: str, time: str, theater: str = "🎥・Cinema Theater 1"):
        movie_role = discord.utils.get(ctx.guild.roles, name="🍿 Movie Night Ping")
        mention_text = movie_role.mention if movie_role else "@everyone"

        embed = discord.Embed(
            title=f"🍿 LIVE CINEMA WATCH PARTY: {title.upper()}",
            description=(
                f"**🎬 Feature:** `{title}`\n"
                f"**⏰ Showtime:** `{time}`\n"
                f"**📍 Location:** `{theater}`\n"
                f"**👑 Host:** {ctx.author.mention}\n\n"
                f"Click **🍿 Going** below to RSVP and get a ping when the movie starts!"
            ),
            color=config.COLOR_GOLD
        )
        embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/2809/2809590.png")
        embed.set_footer(text="Apex Interactive Cinema", icon_url=config.RAI_ICON_URL)

        view = MovieRSVPView(movie_title=title)
        sched_chan = discord.utils.get(ctx.guild.text_channels, name="╭・「🎬」movie-schedule") or ctx.channel
        await sched_chan.send(content=f"🍿 {mention_text} **New Watch Party Announced!**", embed=embed, view=view)
        if sched_chan != ctx.channel:
            await ctx.send(f"✅ Watch party RSVP posted in {sched_chan.mention}!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(CinemaHub(bot))
