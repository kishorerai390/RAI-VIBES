import asyncio
import random
import time
import re
import urllib.parse
from typing import Optional, List, Dict, Any

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button

import config
from utils.ffmpeg_setup import get_ffmpeg_executable

QUIZ_TRACKS = {
    "tamil": [
        {"title": "Arabic Kuthu", "artist": "Anirudh Ravichander", "search": "Arabic Kuthu Beast Anirudh", "start": 30},
        {"title": "Naa Ready", "artist": "Thalapathy Vijay & Anirudh", "search": "Naa Ready Leo song", "start": 25},
        {"title": "Hukum", "artist": "Anirudh Ravichander", "search": "Hukum Jailer Rajinikanth Anirudh", "start": 35},
        {"title": "Vaathi Coming", "artist": "Anirudh Ravichander", "search": "Vaathi Coming Master", "start": 20},
        {"title": "Enjoy Enjaami", "artist": "Dhee ft. Arivu", "search": "Enjoy Enjaami Dhee Arivu", "start": 30},
        {"title": "Rowdy Baby", "artist": "Dhanush & Dhee", "search": "Rowdy Baby Maari 2 Dhanush", "start": 40},
        {"title": "Illuminati", "artist": "Sushin Shyam & Dabzee", "search": "Illuminati Aavesham Fahadh", "start": 30},
        {"title": "Radhimaa", "artist": "Sai Abhyankkar", "search": "Radhimaa Sai Abhyankkar", "start": 30},
        {"title": "Katchi Sera", "artist": "Sai Abhyankkar", "search": "Katchi Sera Sai Abhyankkar", "start": 25},
        {"title": "Aalaporaan Thamizhan", "artist": "A.R. Rahman", "search": "Aalaporaan Thamizhan Mersal", "start": 45},
        {"title": "Marana Mass", "artist": "Anirudh Ravichander", "search": "Marana Mass Petta Anirudh", "start": 30},
        {"title": "Why This Kolaveri Di", "artist": "Dhanush", "search": "Why This Kolaveri Di Dhanush", "start": 30},
        {"title": "Chilla Chilla", "artist": "Anirudh & Ghibran", "search": "Chilla Chilla Thunivu Ajith", "start": 30},
        {"title": "Jimikki Ponnu", "artist": "Anirudh Ravichander", "search": "Jimikki Ponnu Varisu", "start": 20}
    ],
    "global": [
        {"title": "Blinding Lights", "artist": "The Weeknd", "search": "The Weeknd Blinding Lights", "start": 30},
        {"title": "Shape of You", "artist": "Ed Sheeran", "search": "Ed Sheeran Shape of You", "start": 25},
        {"title": "Stay", "artist": "The Kid LAROI & Justin Bieber", "search": "The Kid LAROI Stay Justin Bieber", "start": 20},
        {"title": "Levitating", "artist": "Dua Lipa", "search": "Dua Lipa Levitating", "start": 30},
        {"title": "Believer", "artist": "Imagine Dragons", "search": "Imagine Dragons Believer", "start": 35},
        {"title": "Starboy", "artist": "The Weeknd ft. Daft Punk", "search": "The Weeknd Starboy Daft Punk", "start": 30},
        {"title": "Bad Guy", "artist": "Billie Eilish", "search": "Billie Eilish Bad Guy", "start": 25},
        {"title": "Counting Stars", "artist": "OneRepublic", "search": "OneRepublic Counting Stars", "start": 35}
    ],
    "bollywood": [
        {"title": "Kesariya", "artist": "Arijit Singh", "search": "Kesariya Brahmastra Arijit Singh", "start": 30},
        {"title": "Tum Hi Ho", "artist": "Arijit Singh", "search": "Tum Hi Ho Aashiqui 2", "start": 30},
        {"title": "Chaleya", "artist": "Arijit Singh & Shilpa Rao", "search": "Chaleya Jawan Shah Rukh Khan", "start": 25},
        {"title": "Jhoome Jo Pathaan", "artist": "Arijit Singh & Vishal-Shekhar", "search": "Jhoome Jo Pathaan Shah Rukh Khan", "start": 30},
        {"title": "Apna Bana Le", "artist": "Arijit Singh", "search": "Apna Bana Le Bhediya", "start": 35},
        {"title": "Raataan Lambiyan", "artist": "Jubin Nautiyal & Asees Kaur", "search": "Raataan Lambiyan Shershaah", "start": 30}
    ],
    "anime": [
        {"title": "Gurenge", "artist": "LiSA (Demon Slayer)", "search": "LiSA Gurenge Demon Slayer Opening", "start": 30},
        {"title": "Unravel", "artist": "TK from Ling Tosite Sigure (Tokyo Ghoul)", "search": "Tokyo Ghoul Unravel Opening", "start": 30},
        {"title": "Silhouette", "artist": "KANA-BOON (Naruto Shippuden)", "search": "Silhouette KANA-BOON Naruto Opening 16", "start": 25},
        {"title": "Blue Bird", "artist": "Ikimonogakari (Naruto)", "search": "Naruto Shippuden Blue Bird Opening", "start": 20},
        {"title": "Kick Back", "artist": "Kenshi Yonezu (Chainsaw Man)", "search": "Chainsaw Man Kick Back Kenshi Yonezu", "start": 25},
        {"title": "Shinzo wo Sasageyo", "artist": "Linked Horizon (Attack on Titan)", "search": "Attack on Titan Season 2 Opening Sasageyo", "start": 30}
    ]
}

class QuizChoiceButton(Button):
    def __init__(self, label: str, is_correct: bool, quiz_view: 'MusicQuizView'):
        super().__init__(label=label[:80], style=discord.ButtonStyle.secondary)
        self.is_correct = is_correct
        self.quiz_view = quiz_view

    async def callback(self, interaction: discord.Interaction):
        if self.quiz_view.answered:
            return await interaction.response.send_message("⌛ This round has already ended!", ephemeral=True)

        if self.is_correct:
            self.quiz_view.answered = True
            self.quiz_view.winner = interaction.user
            self.style = discord.ButtonStyle.success

            # Award XP and coins
            levels_cog = interaction.client.get_cog("Levels")
            economy_cog = interaction.client.get_cog("Economy")
            if levels_cog:
                try:
                    levels_cog.add_xp(interaction.user.id, 100)
                except Exception:
                    pass
            if economy_cog:
                try:
                    economy_cog.add_balance(interaction.user.id, 150)
                except Exception:
                    pass

            await interaction.response.send_message(
                f"🎉 **BINGO!** {interaction.user.mention} correctly guessed **`{self.quiz_view.correct_track['title']}`**!\n"
                f"🏆 **Rewards:** `+100 XP` & `+150 Coins` 💰",
                ephemeral=False
            )
            self.quiz_view.stop()
        else:
            self.style = discord.ButtonStyle.danger
            self.disabled = True
            await interaction.response.send_message(f"❌ **Incorrect!** `{self.label}` is not the right track. Try another!", ephemeral=True)
            try:
                await interaction.message.edit(view=self.quiz_view)
            except Exception:
                pass


class MusicQuizView(View):
    def __init__(self, correct_track: dict, options: List[dict]):
        super().__init__(timeout=20)
        self.correct_track = correct_track
        self.options = options
        self.answered = False
        self.winner: Optional[discord.Member] = None

        for opt in options:
            is_correct = (opt["title"] == correct_track["title"])
            btn_label = f"🎵 {opt['title']} - {opt['artist'][:25]}"
            self.add_item(QuizChoiceButton(label=btn_label, is_correct=is_correct, quiz_view=self))


class MusicQuiz(commands.Cog):
    """Interactive 'Name That Tune' Voice Channel Quiz Minigame for RAI VIBES 💗."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_quizzes = set()  # guild_id

    @commands.hybrid_command(name="musicquiz", aliases=["guess-song", "songquiz", "quiz"], description="Start an interactive 'Name That Tune' audio quiz in voice channel!")
    @app_commands.describe(
        category="Select music genre/category",
        rounds="Number of quiz rounds (1 to 5)"
    )
    @app_commands.choices(category=[
        app_commands.Choice(name="🌸 Tamil Cinema Hits & Melody", value="tamil"),
        app_commands.Choice(name="🌍 Global Pop & Dance Hits", value="global"),
        app_commands.Choice(name="🎬 Bollywood & Indie Hits", value="bollywood"),
        app_commands.Choice(name="⚔️ Anime & Gaming OSTs", value="anime"),
    ])
    async def music_quiz_cmd(self, ctx: commands.Context, category: Optional[app_commands.Choice[str]] = None, rounds: int = 3):
        cat_key = category.value if category else "tamil"
        author = ctx.author

        if not author.voice or not author.voice.channel:
            return await ctx.send("⚡ **You must join a voice channel first to start the Music Quiz!**", ephemeral=True)

        if ctx.guild.id in self.active_quizzes:
            return await ctx.send("⚠️ A Music Quiz is already running in this server! Please finish it first.", ephemeral=True)

        music_cog = self.bot.get_cog("Music")
        if not music_cog:
            return await ctx.send("❌ Music engine is currently unavailable.", ephemeral=True)

        await ctx.defer()
        vc = await music_cog.ensure_voice(ctx)
        if not vc:
            return await ctx.send("❌ Could not connect to your voice channel.", ephemeral=True)

        self.active_quizzes.add(ctx.guild.id)
        player = music_cog.get_or_create_player(ctx.guild)
        rounds = max(1, min(5, rounds))

        # Announce Quiz Start
        category_names = {
            "tamil": "🌸 Tamil Cinema Superhits",
            "global": "🌍 Global Chartbusters",
            "bollywood": "🎬 Bollywood Superhits",
            "anime": "⚔️ Anime & Gaming OSTs"
        }
        start_embed = discord.Embed(
            title="🎮 🎶 MUSIC QUIZ: NAME THAT TUNE! 🎶",
            description=(
                f"### Category: **{category_names.get(cat_key, 'Music')}**\n"
                f"• **Rounds:** `{rounds}`\n"
                f"• **Snippet Length:** `15 Seconds`\n"
                f"• **Prize per round:** `100 XP` + `150 Coins` 💰\n\n"
                f"⚡ **Get Ready! Round 1 starts in 5 seconds...**"
            ),
            color=config.COLOR_PRIMARY
        )
        start_embed.set_footer(text="RAI VIBES 💗 • Interactive Quiz Engine", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=start_embed)
        await asyncio.sleep(5)

        track_pool = list(QUIZ_TRACKS.get(cat_key, QUIZ_TRACKS["tamil"]))
        random.shuffle(track_pool)

        scores: Dict[int, int] = {}
        ffmpeg_bin = get_ffmpeg_executable()

        from cogs.music import Song

        for round_num in range(1, rounds + 1):
            if not track_pool or not vc.is_connected():
                break

            correct_track = track_pool.pop(0)
            
            # Select 3 distractors
            other_tracks = [t for t in QUIZ_TRACKS[cat_key] if t["title"] != correct_track["title"]]
            distractors = random.sample(other_tracks, min(3, len(other_tracks)))
            options = [correct_track] + distractors
            random.shuffle(options)

            # Resolve streaming URL
            try:
                resolved_song = await Song.create_source(correct_track["search"], author, self.bot.loop)
                if not resolved_song or not resolved_song.url:
                    continue
            except Exception:
                continue

            # Play 15-second snippet in voice
            start_sec = correct_track.get("start", 25)
            before_opt = f"-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -ss {start_sec} -t 16 -nostdin"
            ffmpeg_opt = "-vn -bufsize 2048k"

            def after_playing(err):
                pass

            if vc.is_playing() or vc.is_paused():
                vc.stop()
                await asyncio.sleep(0.2)

            raw_source = discord.FFmpegPCMAudio(
                resolved_song.url,
                executable=ffmpeg_bin,
                before_options=before_opt,
                options=ffmpeg_opt
            )
            transformed = discord.PCMVolumeTransformer(raw_source, volume=player.get_volume_factor())
            vc.play(transformed, after=after_playing)

            # Post Quiz View in text channel
            view = MusicQuizView(correct_track, options)
            round_embed = discord.Embed(
                title=f"🎵 Round {round_num}/{rounds} • Guess The Song!",
                description=(
                    f"🔊 **Audio is playing in {vc.channel.mention}!**\n\n"
                    f"Click the correct song title below within **15 seconds**:\n"
                    f"*(First correct click wins the bounty!)*"
                ),
                color=config.COLOR_GOLD
            )
            round_embed.set_thumbnail(url=config.RAI_ICON_URL)
            round_embed.set_footer(text=f"Round {round_num}/{rounds} • Fast fingers win!", icon_url=config.RAI_ICON_URL)
            
            msg = await ctx.send(embed=round_embed, view=view)

            # Wait 15 seconds for answer
            await asyncio.sleep(15)

            if vc.is_playing():
                vc.stop()

            # Round conclusion
            if not view.answered:
                timeout_embed = discord.Embed(
                    title=f"⏰ Time's Up for Round {round_num}!",
                    description=f"Nobody guessed in time! The correct track was:\n### **🎵 {correct_track['title']}** - `{correct_track['artist']}`",
                    color=config.COLOR_DARK
                )
                try:
                    await msg.edit(view=None)
                except Exception:
                    pass
                await ctx.send(embed=timeout_embed)
            else:
                if view.winner:
                    scores[view.winner.id] = scores.get(view.winner.id, 0) + 1

            if round_num < rounds:
                await asyncio.sleep(3)

        self.active_quizzes.discard(ctx.guild.id)

        # Final Scoreboard
        if scores:
            leaderboard_lines = []
            sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
            for rank, (uid, pts) in enumerate(sorted_scores, 1):
                member = ctx.guild.get_member(uid)
                name = member.mention if member else f"User {uid}"
                medal = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else "🎖️"))
                leaderboard_lines.append(f"{medal} **{name}** — `{pts} Points`")

            final_embed = discord.Embed(
                title="🏆 MUSIC QUIZ FINAL RESULTS! 🏆",
                description="\n".join(leaderboard_lines),
                color=config.COLOR_GOLD
            )
            final_embed.set_footer(text="RAI VIBES 💗 • Music Champion Crowned!", icon_url=config.RAI_ICON_URL)
            await ctx.send(embed=final_embed)
        else:
            await ctx.send("✨ **Quiz completed!** Use `/musicquiz` anytime to challenge your friends again!")


async def setup(bot: commands.Bot):
    await bot.add_cog(MusicQuiz(bot))
