import discord
from discord.ext import commands
from discord import app_commands
import random
import asyncio
from typing import Optional, List

import config

TRIVIA_QUESTIONS = [
    # Movies & Cinema
    {"cat": "🎬 Movies", "q": "In 'The Matrix', what color pill does Neo take to see the truth?", "options": ["Red", "Blue", "Green", "Yellow"], "answer": "Red"},
    {"cat": "🎬 Movies", "q": "Which movie features the iconic quote: 'May the Force be with you'?", "options": ["Star Wars", "Star Trek", "Guardians of the Galaxy", "Dune"], "answer": "Star Wars"},
    {"cat": "🎬 Movies", "q": "Who directed the sci-fi epic 'Interstellar' and 'Inception'?", "options": ["Christopher Nolan", "Steven Spielberg", "James Cameron", "Quentin Tarantino"], "answer": "Christopher Nolan"},
    {"cat": "🎬 Movies", "q": "What is the highest-grossing animated movie of all time?", "options": ["Inside Out 2", "Frozen II", "The Lion King (2019)", "Minions"], "answer": "Inside Out 2"},
    {"cat": "🎬 Movies", "q": "In Marvel's 'Avengers: Endgame', who sacrifices themselves on Vormir for the Soul Stone?", "options": ["Black Widow", "Hawkeye", "Gamora", "Iron Man"], "answer": "Black Widow"},
    
    # Music & Hits
    {"cat": "🎵 Music", "q": "Who is known as the 'King of Pop'?", "options": ["Michael Jackson", "Elvis Presley", "Prince", "Freddie Mercury"], "answer": "Michael Jackson"},
    {"cat": "🎵 Music", "q": "Which artist released the global hit album 'After Hours' featuring 'Blinding Lights'?", "options": ["The Weeknd", "Drake", "Bruno Mars", "Post Malone"], "answer": "The Weeknd"},
    {"cat": "🎵 Music", "q": "What legendary British rock band recorded 'Bohemian Rhapsody'?", "options": ["Queen", "The Beatles", "Led Zeppelin", "Pink Floyd"], "answer": "Queen"},
    {"cat": "🎵 Music", "q": "Which K-pop group released 'Dynamite' and 'Butter'?", "options": ["BTS", "BLACKPINK", "Stray Kids", "EXO"], "answer": "BTS"},
    
    # Gaming
    {"cat": "🎮 Gaming", "q": "In 'Minecraft', what material is required to craft Netherite gear?", "options": ["Netherite Ingot + Diamond Gear", "Obsidian", "Blaze Rods", "End Crystals"], "answer": "Netherite Ingot + Diamond Gear"},
    {"cat": "🎮 Gaming", "q": "Which battle royale game features the island named 'Kings Canyon'?", "options": ["Apex Legends", "Fortnite", "PUBG", "Warzone"], "answer": "Apex Legends"},
    {"cat": "🎮 Gaming", "q": "What is the name of the protagonist in 'The Legend of Zelda' series?", "options": ["Link", "Zelda", "Ganon", "Navi"], "answer": "Link"},
    
    # Anime & Pop Culture
    {"cat": "🌸 Anime", "q": "In 'Demon Slayer', what breathing style does Tanjiro Kamado originally learn?", "options": ["Water Breathing", "Sun Breathing", "Thunder Breathing", "Flame Breathing"], "answer": "Water Breathing"},
    {"cat": "🌸 Anime", "q": "What is the mythical treasure called in 'One Piece'?", "options": ["The One Piece", "The Holy Grail", "Dragon Balls", "Philosopher's Stone"], "answer": "The One Piece"},
    {"cat": "🌸 Anime", "q": "In 'Jujutsu Kaisen', who is known as the strongest Jujutsu sorcerer?", "options": ["Satoru Gojo", "Sukuna", "Megumi Fushiguro", "Yuji Itadori"], "answer": "Satoru Gojo"}
]

TRUTHS = [
    "What is the most embarrassing song or movie you secretly love?",
    "If you could trade lives with anyone in this Discord server for 24 hours, who would it be and why?",
    "What is your biggest fear that you rarely tell anyone?",
    "What is the longest gaming or movie binge session you have ever had without sleeping?",
    "Have you ever pretended to like a movie or song just to fit in?",
    "What is one dream vacation destination you will visit before you die?",
    "If you had to delete every app on your phone except 3, which 3 are you keeping?"
]

DARES = [
    "Send the 5th photo in your camera roll to `#├・「📸」media-gallery` without context!",
    "Sing or hum the chorus of your favorite song in voice channel for 10 seconds!",
    "Change your Discord nickname to '🍿 Movie Goblin' for the next 1 hour!",
    "Send a voice note or message saying 'I LOVE APEX VIBES' in the general chat!",
    "Drop your top 3 Spotify / YouTube songs in `#├・「🎵」music-commands` right now!",
    "Type your next 5 messages in ALL CAPS!",
    "Tell a funny joke in general chat. If nobody laughs, you owe the server 100 Vibe coins!"
]

class TriviaButtonView(discord.ui.View):
    def __init__(self, question_data: dict, author: discord.Member):
        super().__init__(timeout=25.0)
        self.question_data = question_data
        self.author = author
        self.answered = False
        
        # Shuffle options
        opts = list(question_data["options"])
        random.shuffle(opts)
        
        for opt in opts:
            btn = discord.ui.Button(label=opt, style=discord.ButtonStyle.secondary)
            btn.callback = self.make_callback(opt)
            self.add_item(btn)

    def make_callback(self, selected_option: str):
        async def callback(interaction: discord.Interaction):
            if self.answered:
                return await interaction.response.send_message("This trivia question has already ended!", ephemeral=True)
            
            self.answered = True
            is_correct = selected_option == self.question_data["answer"]
            
            # Disable buttons and highlight right/wrong
            for child in self.children:
                child.disabled = True
                if child.label == self.question_data["answer"]:
                    child.style = discord.ButtonStyle.success
                elif child.label == selected_option and not is_correct:
                    child.style = discord.ButtonStyle.danger

            if is_correct:
                res_embed = discord.Embed(
                    title="🎉 CORRECT ANSWER!",
                    description=f"{interaction.user.mention} nailed it! The answer was indeed **{self.question_data['answer']}**! 🧠⚡",
                    color=config.COLOR_SUCCESS
                )
            else:
                res_embed = discord.Embed(
                    title="❌ INCORRECT!",
                    description=f"{interaction.user.mention} chose `{selected_option}`.\nThe correct answer was **{self.question_data['answer']}**!",
                    color=config.COLOR_ERROR
                )
            
            await interaction.response.edit_message(embed=res_embed, view=self)
            self.stop()

        return callback


class TruthOrDareView(discord.ui.View):
    def __init__(self, author: discord.Member):
        super().__init__(timeout=60.0)
        self.author = author

    @discord.ui.button(label="🧠 TRUTH", style=discord.ButtonStyle.primary, emoji="💡")
    async def truth(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Only the person who rolled can choose!", ephemeral=True)
        q = random.choice(TRUTHS)
        embed = discord.Embed(
            title="💡 TRUTH CHALLENGE",
            description=f"{self.author.mention}, your question is:\n\n### *\"{q}\"*",
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="Answer honestly in chat!", icon_url=config.RAI_ICON_URL)
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()

    @discord.ui.button(label="🔥 DARE", style=discord.ButtonStyle.danger, emoji="⚡")
    async def dare(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.author.id:
            return await interaction.response.send_message("Only the person who rolled can choose!", ephemeral=True)
        d = random.choice(DARES)
        embed = discord.Embed(
            title="🔥 DARE CHALLENGE",
            description=f"{self.author.mention}, your dare is:\n\n### *\"{d}\"*",
            color=config.COLOR_ERROR
        )
        embed.set_footer(text="Complete the challenge or face the penalty!", icon_url=config.RAI_ICON_URL)
        for child in self.children:
            child.disabled = True
        await interaction.response.edit_message(embed=embed, view=self)
        self.stop()


class TicTacToeButton(discord.ui.Button["TicTacToeView"]):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        assert self.view is not None
        view: TicTacToeView = self.view
        state = view.board[self.y][self.x]
        if state in (view.X, view.O):
            return

        if interaction.user not in (view.player_x, view.player_o):
            return await interaction.response.send_message("You are not a player in this match!", ephemeral=True)

        if view.current_player == view.X and interaction.user != view.player_x:
            return await interaction.response.send_message("It's not your turn!", ephemeral=True)
        elif view.current_player == view.O and interaction.user != view.player_o:
            return await interaction.response.send_message("It's not your turn!", ephemeral=True)

        if view.current_player == view.X:
            self.style = discord.ButtonStyle.danger
            self.label = "X"
            self.disabled = True
            view.board[self.y][self.x] = view.X
            view.current_player = view.O
            content = f"🎮 It is now {view.player_o.mention}'s turn (O)!"
        else:
            self.style = discord.ButtonStyle.success
            self.label = "O"
            self.disabled = True
            view.board[self.y][self.x] = view.O
            view.current_player = view.X
            content = f"🎮 It is now {view.player_x.mention}'s turn (X)!"

        winner = view.check_board_winner()
        if winner is not None:
            if winner == view.X:
                content = f"🏆 **{view.player_x.mention} (X) WON THE MATCH!** 🎉"
            elif winner == view.O:
                content = f"🏆 **{view.player_o.mention} (O) WON THE MATCH!** 🎉"
            else:
                content = "🤝 **It's a Tie! Well played both!**"

            for child in view.children:
                child.disabled = True
            view.stop()

        await interaction.response.edit_message(content=content, view=view)


class TicTacToeView(discord.ui.View):
    X = -1
    O = 1
    Tie = 2

    def __init__(self, player_x: discord.Member, player_o: discord.Member):
        super().__init__(timeout=120.0)
        self.player_x = player_x
        self.player_o = player_o
        self.current_player = self.X
        self.board = [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]

        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_board_winner(self):
        # Check rows
        for y in range(3):
            val = sum(self.board[y])
            if val == 3: return self.O
            if val == -3: return self.X

        # Check columns
        for x in range(3):
            val = self.board[0][x] + self.board[1][x] + self.board[2][x]
            if val == 3: return self.O
            if val == -3: return self.X

        # Check diagonals
        diag1 = self.board[0][0] + self.board[1][1] + self.board[2][2]
        if diag1 == 3: return self.O
        if diag1 == -3: return self.X

        diag2 = self.board[0][2] + self.board[1][1] + self.board[2][0]
        if diag2 == 3: return self.O
        if diag2 == -3: return self.X

        # Check Tie
        if all(cell != 0 for row in self.board for cell in row):
            return self.Tie

        return None


class MiniGames(commands.Cog):
    """Interactive Discord Mini-Games (Trivia with Buttons, Truth or Dare, Tic Tac Toe)."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="trivia", description="Start an interactive multiple-choice trivia question!")
    async def trivia(self, ctx: commands.Context):
        q = random.choice(TRIVIA_QUESTIONS)
        embed = discord.Embed(
            title=f"🧠 {q['cat']} Trivia Challenge",
            description=f"**Question:**\n### {q['q']}\n\n*Click the button with your answer below! You have 25 seconds.*",
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="Apex Trivia Master", icon_url=config.RAI_ICON_URL)
        
        view = TriviaButtonView(question_data=q, author=ctx.author)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="truthordare", description="Play a game of Truth or Dare with friends!")
    async def truthordare(self, ctx: commands.Context):
        embed = discord.Embed(
            title="⚡ TRUTH OR DARE",
            description=f"{ctx.author.mention}, make your choice!\n\nChoose **💡 TRUTH** to answer a deep question, or **🔥 DARE** for a spicy challenge!",
            color=config.COLOR_GOLD
        )
        embed.set_footer(text="Apex Vibe Games", icon_url=config.RAI_ICON_URL)
        view = TruthOrDareView(author=ctx.author)
        await ctx.send(embed=embed, view=view)

    @commands.hybrid_command(name="tictactoe", description="Challenge a member to a game of Tic-Tac-Toe!")
    @app_commands.describe(opponent="The player you want to challenge")
    async def tictactoe(self, ctx: commands.Context, opponent: discord.Member):
        if opponent.id == ctx.author.id:
            return await ctx.send("❌ You can't play against yourself!", ephemeral=True)
        if opponent.bot:
            return await ctx.send("❌ You can't challenge bots to Tic-Tac-Toe!", ephemeral=True)

        view = TicTacToeView(player_x=ctx.author, player_o=opponent)
        await ctx.send(f"⚔️ **Tic-Tac-Toe Match:** {ctx.author.mention} (❌) vs {opponent.mention} (⭕)!\n{ctx.author.mention}'s turn first!", view=view)

    @commands.hybrid_command(name="8ball", description="Ask the Magic 8-Ball any question.")
    @app_commands.describe(question="Your question to the universe")
    async def eight_ball(self, ctx: commands.Context, question: str):
        responses = [
            "It is certain.", "Without a doubt.", "You may rely on it.",
            "Yes definitely.", "As I see it, yes.", "Most likely.",
            "Outlook good.", "Signs point to yes.", "Reply hazy, try again.",
            "Ask again later.", "Better not tell you now.", "Cannot predict now.",
            "Concentrate and ask again.", "Don't count on it.", "My reply is no.",
            "My sources say no.", "Outlook not so good.", "Very doubtful."
        ]
        embed = discord.Embed(
            title="🎱 Magic 8-Ball",
            description=f"**Question:** *{question}*\n**Answer:** `{random.choice(responses)}`",
            color=config.COLOR_SECONDARY
        )
        embed.set_footer(text="Apex Fortune Teller", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="activity", description="Launch interactive Discord games & YouTube in your voice channel!")
    @app_commands.describe(game="The activity you want to launch")
    @app_commands.choices(game=[
        app_commands.Choice(name="🎥 YouTube Watch Together", value="880218394199220274"),
        app_commands.Choice(name="🎨 Gartic Phone (Drawing)", value="1007373707583492166"),
        app_commands.Choice(name="🃏 Poker Night", value="755827207812677713"),
        app_commands.Choice(name="♟️ Chess in the Park", value="832012774040141894"),
        app_commands.Choice(name="✏️ Sketch Heads", value="902271654783815791"),
        app_commands.Choice(name="🍪 Word Snacks", value="879863976006127627"),
        app_commands.Choice(name="🔤 Letter League", value="879863686565621790"),
        app_commands.Choice(name="🎴 Ocho (Uno Party)", value="832025144389533716"),
    ])
    async def activity(self, ctx: commands.Context, game: app_commands.Choice[str]):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must be connected to a voice channel to launch an activity!", ephemeral=True)

        vc = ctx.author.voice.channel
        try:
            invite = await vc.create_invite(
                target_type=discord.InviteTarget.embedded_application,
                target_application_id=int(game.value),
                max_age=3600,
                reason=f"Discord Activity {game.name} started by {ctx.author.name}"
            )
            embed = discord.Embed(
                title=f"🚀 {game.name} Started!",
                description=(
                    f"**Host:** {ctx.author.mention}\n"
                    f"**Voice Channel:** {vc.mention}\n\n"
                    f"👉 **[Click Here to Join & Play {game.name}]({invite.url})**\n\n"
                    f"*Anyone inside {vc.mention} can click the link to play directly inside Discord!*"
                ),
                color=config.COLOR_PRIMARY
            )
            embed.set_thumbnail(url=ctx.author.display_avatar.url)
            embed.set_footer(text="RAI VIBES 💗 • VC Party Gaming", icon_url=config.RAI_ICON_URL)
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"❌ Could not launch activity: {e}\nMake sure the bot has permission to create invites in {vc.mention}.", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(MiniGames(bot))
