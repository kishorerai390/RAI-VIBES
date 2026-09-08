import os
import sys
import json
import random
import time
from pathlib import Path
from typing import Optional, Dict, List
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, button

import config

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ECONOMY_FILE = DATA_DIR / "economy.json"

SHOP_ITEMS = {
    "dj_pass": {
        "name": "🎧 DJ Pass Role",
        "description": "Unlock DJ controls, skip bypass, and audio filter privileges",
        "price": 1000,
        "role_id": 1545834928221069522,  # 🎧 ✧ 𝐃𝐉
        "role_name": "🎧 ✧ 𝐃𝐉",
        "emoji": "🎧"
    },
    "vip_elite": {
        "name": "💎 VIP Elite Prestige",
        "description": "Gain the prestigious VIP role with exclusive lounge & VC access",
        "price": 2500,
        "role_id": None,
        "role_name": "💎 ┊ 𝐑𝐀𝐈 𝐄𝐋𝐈𝐓𝐄",
        "emoji": "💎"
    },
    "custom_color": {
        "name": "🎨 Royal Gold Name Color",
        "description": "Shine in server chat with the exclusive Royal Gold name color",
        "price": 800,
        "role_id": 1546088559830634586,  # Royal Gold
        "role_name": "Royal Gold",
        "emoji": "💛"
    }
}


def load_economy() -> Dict[str, dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if ECONOMY_FILE.exists():
        try:
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_economy(data: Dict[str, dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_user_data(user_id: int) -> dict:
    data = load_economy()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "coins": 200,
            "last_daily": 0,
            "streak": 0,
            "rep": 0,
            "last_rep": 0
        }
        save_economy(data)
    return data[uid]


def update_user_coins(user_id: int, delta: int) -> int:
    data = load_economy()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"coins": 200, "last_daily": 0, "streak": 0, "rep": 0, "last_rep": 0}
    data[uid]["coins"] = max(0, data[uid].get("coins", 0) + delta)
    save_economy(data)
    return data[uid]["coins"]


# =====================================================================
# TIC-TAC-TOE INTERACTIVE VIEW
# =====================================================================
class TicTacToeButton(Button):
    def __init__(self, x: int, y: int):
        super().__init__(style=discord.ButtonStyle.secondary, label="\u200b", row=y)
        self.x = x
        self.y = y

    async def callback(self, interaction: discord.Interaction):
        view: TicTacToeView = self.view
        if interaction.user.id != view.current_player.id:
            if interaction.user.id in (view.p1.id, view.p2.id):
                return await interaction.response.send_message("⏳ It's not your turn!", ephemeral=True)
            return await interaction.response.send_message("❌ You are not a player in this match.", ephemeral=True)

        if view.board[self.y][self.x] != 0:
            return await interaction.response.send_message("⚠️ That square is already taken!", ephemeral=True)

        symbol = "X" if view.current_player == view.p1 else "O"
        self.style = discord.ButtonStyle.danger if symbol == "X" else discord.ButtonStyle.primary
        self.label = symbol
        self.disabled = True
        view.board[self.y][self.x] = 1 if symbol == "X" else 2

        winner = view.check_winner()
        if winner:
            for child in view.children:
                child.disabled = True
            view.stop()
            winner_user = view.p1 if winner == 1 else view.p2
            update_user_coins(winner_user.id, 50)  # +50 winner bonus!
            embed = discord.Embed(
                title="🏆 TIC-TAC-TOE • VICTORY!",
                description=(
                    f"🎉 **{winner_user.mention} ({symbol}) has WON the match!** 🌸\n\n"
                    f"🎁 **Reward:** `+50 Coins` awarded to the winner!"
                ),
                color=0x2ECC71
            )
            embed.set_thumbnail(url=winner_user.display_avatar.url)
            embed.set_footer(text="RAI FAM 💗 • Mini-Games", icon_url=config.RAI_ICON_URL)
            return await interaction.response.edit_message(content=None, embed=embed, view=view)

        if view.is_board_full():
            for child in view.children:
                child.disabled = True
            view.stop()
            embed = discord.Embed(
                title="🤝 TIC-TAC-TOE • STALEMATE DRAW!",
                description=f"Great battle between {view.p1.mention} and {view.p2.mention}! It's a draw.",
                color=0xF1C40F
            )
            embed.set_footer(text="RAI FAM 💗 • Mini-Games", icon_url=config.RAI_ICON_URL)
            return await interaction.response.edit_message(content=None, embed=embed, view=view)

        # Switch Turn
        view.current_player = view.p2 if view.current_player == view.p1 else view.p1
        next_symbol = "X" if view.current_player == view.p1 else "O"
        embed = discord.Embed(
            title="🎮 TIC-TAC-TOE MATCH",
            description=(
                f"**Current Turn:** {view.current_player.mention} (`{next_symbol}`)\n\n"
                f"❌ **Player 1:** {view.p1.mention}\n"
                f"⭕ **Player 2:** {view.p2.mention}"
            ),
            color=0x9B5DE5
        )
        await interaction.response.edit_message(content=None, embed=embed, view=view)


class TicTacToeView(View):
    def __init__(self, p1: discord.Member, p2: discord.Member):
        super().__init__(timeout=120)
        self.p1 = p1
        self.p2 = p2
        self.current_player = p1
        self.board = [[0, 0, 0], [0, 0, 0], [0, 0, 0]]
        for y in range(3):
            for x in range(3):
                self.add_item(TicTacToeButton(x, y))

    def check_winner(self) -> Optional[int]:
        for i in range(3):
            # Rows
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != 0:
                return self.board[i][0]
            # Columns
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != 0:
                return self.board[0][i]
        # Diagonals
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != 0:
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != 0:
            return self.board[0][2]
        return None

    def is_board_full(self) -> bool:
        return all(self.board[y][x] != 0 for y in range(3) for x in range(3))


# =====================================================================
# TRIVIA INTERACTIVE VIEW
# =====================================================================
TRIVIA_QUESTIONS = [
    {"q": "Which planet in our solar system is known as the Red Planet?", "options": ["Mars", "Venus", "Jupiter", "Saturn"], "answer": "Mars", "category": "General"},
    {"q": "What is the highest-grossing film of all time worldwide?", "options": ["Avatar", "Avengers: Endgame", "Titanic", "Star Wars: The Force Awakens"], "answer": "Avatar", "category": "Movies"},
    {"q": "Which battle royale mobile game features characters like Chrono, Alok, and Kelly?", "options": ["Free Fire", "BGMI", "Call of Duty", "Roblox"], "answer": "Free Fire", "category": "Gaming"},
    {"q": "In the anime 'Demon Slayer', what color is Tanjiro Kamado's Nichirin blade?", "options": ["Black", "Red", "Blue", "Yellow"], "answer": "Black", "category": "Anime"},
    {"q": "What does CPU stand for in computer hardware?", "options": ["Central Processing Unit", "Computer Power Utility", "Core Program Unit", "Control Processor Utility"], "answer": "Central Processing Unit", "category": "Tech"},
    {"q": "Who directed the sci-fi masterpiece 'Interstellar'?", "options": ["Christopher Nolan", "Steven Spielberg", "James Cameron", "Quentin Tarantino"], "answer": "Christopher Nolan", "category": "Movies"},
    {"q": "In 'Dragon Ball Z', what is the name of Goku's signature energy beam?", "options": ["Kamehameha", "Rasengan", "Bankai", "Chidori"], "answer": "Kamehameha", "category": "Anime"},
    {"q": "What is the fastest land animal in the world?", "options": ["Cheetah", "Lion", "Peregrine Falcon", "Greyhound"], "answer": "Cheetah", "category": "General"},
    {"q": "In 'Minecraft', which material is required to create a Nether Portal?", "options": ["Obsidian", "Bedrock", "Diamond Block", "Ancient Debris"], "answer": "Obsidian", "category": "Gaming"},
    {"q": "Which programming language was developed by Guido van Rossum in 1991?", "options": ["Python", "Java", "C++", "JavaScript"], "answer": "Python", "category": "Tech"}
]

class TriviaChoiceButton(Button):
    def __init__(self, label: str, is_correct: bool, parent_view: 'TriviaView'):
        super().__init__(style=discord.ButtonStyle.secondary, label=label[:80])
        self.is_correct = is_correct
        self.parent_view = parent_view

    async def callback(self, interaction: discord.Interaction):
        if self.parent_view.answered:
            return await interaction.response.send_message("⌛ This trivia question has already been answered!", ephemeral=True)

        self.parent_view.answered = True
        for child in self.parent_view.children:
            child.disabled = True
            if getattr(child, "is_correct", False):
                child.style = discord.ButtonStyle.success
            elif child == self:
                child.style = discord.ButtonStyle.danger

        if self.is_correct:
            update_user_coins(interaction.user.id, 50)
            embed = discord.Embed(
                title="🎉 CORRECT ANSWER!",
                description=(
                    f"Bravo {interaction.user.mention}! **`{self.label}`** is correct!\n\n"
                    f"🎁 **Reward:** `+50 Coins` credited to your profile! 🪙"
                ),
                color=0x2ECC71
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
        else:
            embed = discord.Embed(
                title="💔 INCORRECT ANSWER",
                description=(
                    f"Nice try {interaction.user.mention}! The correct answer was **`{self.parent_view.correct_answer}`**.\n"
                    f"Try another question anytime with `/trivia`!"
                ),
                color=0xE74C3C
            )

        embed.set_footer(text="RAI FAM 💗 • Brain Arena", icon_url=config.RAI_ICON_URL)
        await interaction.response.edit_message(embed=embed, view=self.parent_view)


class TriviaView(View):
    def __init__(self, question_data: dict):
        super().__init__(timeout=45)
        self.answered = False
        self.correct_answer = question_data["answer"]
        opts = list(question_data["options"])
        random.shuffle(opts)
        for opt in opts:
            self.add_item(TriviaChoiceButton(opt, opt == self.correct_answer, self))


# =====================================================================
# SHOP VIEW
# =====================================================================
class ShopBuyView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=90)
        self.user_id = user_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This shop menu belongs to someone else.", ephemeral=True)
            return False
        return True

    @button(label="Buy DJ Pass (1,000)", style=discord.ButtonStyle.primary, emoji="🎧")
    async def buy_dj(self, interaction: discord.Interaction, button: Button):
        await self.process_purchase(interaction, "dj_pass")

    @button(label="Buy VIP Elite (2,500)", style=discord.ButtonStyle.success, emoji="💎")
    async def buy_vip(self, interaction: discord.Interaction, button: Button):
        await self.process_purchase(interaction, "vip_elite")

    @button(label="Buy Royal Gold (800)", style=discord.ButtonStyle.secondary, emoji="💛")
    async def buy_color(self, interaction: discord.Interaction, button: Button):
        await self.process_purchase(interaction, "custom_color")

    async def process_purchase(self, interaction: discord.Interaction, item_key: str):
        item = SHOP_ITEMS.get(item_key)
        if not item:
            return await interaction.response.send_message("❌ Unknown item.", ephemeral=True)

        user = interaction.user
        guild = interaction.guild
        data = get_user_data(user.id)
        current_coins = data.get("coins", 0)

        if current_coins < item["price"]:
            return await interaction.response.send_message(
                f"❌ **Insufficient Coins!** You have `{current_coins:,}` Coins, but **{item['name']}** costs `{item['price']:,}` Coins.\n"
                f"💡 *Earn more by chatting, participating in voice lounges (+5 coins every 2 min), or claiming `/daily`!*",
                ephemeral=True
            )

        role = None
        if item["role_id"]:
            role = guild.get_role(item["role_id"])
        if not role:
            role = discord.utils.get(guild.roles, name=item["role_name"])

        if role:
            if role in user.roles:
                return await interaction.response.send_message(f"⚠️ You already have the **{role.name}** perk!", ephemeral=True)
            try:
                await user.add_roles(role, reason=f"Purchased {item['name']} from Server Shop")
            except Exception as e:
                return await interaction.response.send_message(f"❌ Failed to grant role: {e}", ephemeral=True)

        new_balance = update_user_coins(user.id, -item["price"])
        embed = discord.Embed(
            title="🎉 PURCHASE SUCCESSFUL!",
            description=(
                f"Congratulations {user.mention}! You acquired **{item['name']}**!\n\n"
                f"💸 **Amount Paid:** `{item['price']:,} Coins`\n"
                f"💰 **New Balance:** `{new_balance:,}` Coins\n"
                f"✨ Perk is now active on your server profile!"
            ),
            color=0x2ECC71
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Server Shop", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)


# =====================================================================
# MAIN ECONOMY & COMMUNITY COG
# =====================================================================
class Economy(commands.Cog):
    """Server Economy, Reputation, Daily Rewards, Trivia & Social Mini-games."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def add_balance(self, user_id: int, amount: int) -> int:
        return update_user_coins(user_id, amount)

    def get_balance(self, user_id: int) -> int:
        return get_user_data(user_id).get("coins", 0)

    # 1. DAILY REWARD
    @app_commands.command(name="daily", description="Claim your daily coin allowance and build your streak!")
    async def daily_command(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        data = load_economy()
        uid = str(user_id)
        if uid not in data:
            data[uid] = {"coins": 200, "last_daily": 0, "streak": 0, "rep": 0, "last_rep": 0}

        now = int(time.time())
        last_daily = data[uid].get("last_daily", 0)
        cooldown = 86400
        diff = now - last_daily

        if diff < cooldown:
            rem = cooldown - diff
            hours, rem = divmod(rem, 3600)
            mins, secs = divmod(rem, 60)
            return await interaction.response.send_message(
                f"⏳ **Daily Cooldown!** You can claim your next daily reward in **{hours}h {mins}m {secs}s**.",
                ephemeral=True
            )

        streak = data[uid].get("streak", 0)
        streak = streak + 1 if diff < 172800 else 1

        base_reward = 250
        streak_bonus = min(250, streak * 25)
        total_reward = base_reward + streak_bonus

        data[uid]["coins"] = data[uid].get("coins", 0) + total_reward
        data[uid]["last_daily"] = now
        data[uid]["streak"] = streak
        save_economy(data)

        embed = discord.Embed(
            title="🎁 DAILY REWARD CLAIMED!",
            description=(
                f"Welcome back, {interaction.user.mention}! Here is your daily reward:\n\n"
                f"🪙 **Base Reward:** `+{base_reward}` Coins\n"
                f"🔥 **Streak Bonus:** `+{streak_bonus}` Coins *(Day {streak})*\n"
                f"💰 **Total Earned:** `+{total_reward:,}` Coins\n"
                f"👛 **New Balance:** `{data[uid]['coins']:,}` Coins"
            ),
            color=0xF1C40F
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="Come back in 24 hours to keep your streak alive!", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    # 2. COMMUNITY REPUTATION
    @app_commands.command(name="rep", description="Award a reputation point (+1 Rep) to a helpful member once every 24h.")
    @app_commands.describe(member="Member to give reputation to")
    async def rep_command(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot give reputation to yourself!", ephemeral=True)
        if member.bot:
            return await interaction.response.send_message("❌ Bots cannot receive reputation points.", ephemeral=True)

        user_data = get_user_data(interaction.user.id)
        last_rep = user_data.get("last_rep", 0)
        now = int(time.time())
        cooldown = 86400

        if now - last_rep < cooldown:
            rem = cooldown - (now - last_rep)
            hours, rem = divmod(rem, 3600)
            mins, secs = divmod(rem, 60)
            return await interaction.response.send_message(
                f"⏳ **Rep Cooldown!** You can award another reputation point in **{hours}h {mins}m {secs}s**.",
                ephemeral=True
            )

        data = load_economy()
        g_uid = str(interaction.user.id)
        if g_uid not in data:
            data[g_uid] = {"coins": 200, "last_daily": 0, "streak": 0, "rep": 0, "last_rep": 0}
        data[g_uid]["last_rep"] = now

        r_uid = str(member.id)
        if r_uid not in data:
            data[r_uid] = {"coins": 200, "last_daily": 0, "streak": 0, "rep": 0, "last_rep": 0}
        data[r_uid]["rep"] = data[r_uid].get("rep", 0) + 1
        new_rep = data[r_uid]["rep"]
        save_economy(data)

        embed = discord.Embed(
            title="⭐ REPUTATION AWARDED!",
            description=(
                f"{interaction.user.mention} gave **+1 Reputation** to {member.mention}! 🌸\n\n"
                f"💖 **{member.display_name}** now has **`{new_rep}` Reputation Points**!\n"
                f"Reputation displays proudly on your `/rank` card."
            ),
            color=0xFF69B4
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Community Karma & Respect", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    # 3. INTERACTIVE TIC-TAC-TOE
    @app_commands.command(name="tictactoe", description="Challenge another server member to an interactive Tic-Tac-Toe match!")
    @app_commands.describe(opponent="Member you want to challenge")
    async def tictactoe_command(self, interaction: discord.Interaction, opponent: discord.Member):
        if opponent.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot play Tic-Tac-Toe against yourself!", ephemeral=True)
        if opponent.bot:
            return await interaction.response.send_message("❌ You cannot challenge bots.", ephemeral=True)

        embed = discord.Embed(
            title="🎮 TIC-TAC-TOE MATCH STARTED",
            description=(
                f"**Match:** {interaction.user.mention} (`X`) vs {opponent.mention} (`O`)\n\n"
                f"👉 **First Turn:** {interaction.user.mention} (`X`)\n"
                f"Click any button on the 3x3 grid below to make your move!"
            ),
            color=0x9B5DE5
        )
        embed.set_footer(text="Winner receives +50 Coins bonus!", icon_url=config.RAI_ICON_URL)

        view = TicTacToeView(interaction.user, opponent)
        await interaction.response.send_message(embed=embed, view=view)

    # 4. INTERACTIVE TRIVIA
    @app_commands.command(name="trivia", description="Answer a fun multiple-choice trivia question for +50 Coins!")
    @app_commands.describe(category="Optional category filter")
    @app_commands.choices(category=[
        app_commands.Choice(name="All Categories", value="all"),
        app_commands.Choice(name="Gaming", value="gaming"),
        app_commands.Choice(name="Anime", value="anime"),
        app_commands.Choice(name="Movies", value="movies"),
        app_commands.Choice(name="Tech", value="tech")
    ])
    async def trivia_command(self, interaction: discord.Interaction, category: Optional[str] = "all"):
        pool = TRIVIA_QUESTIONS
        if category and category != "all":
            filtered = [q for q in TRIVIA_QUESTIONS if q["category"].lower() == category.lower()]
            if filtered:
                pool = filtered

        question_data = random.choice(pool)
        embed = discord.Embed(
            title=f"🧠 TRIVIA TIME • {question_data['category'].upper()}",
            description=(
                f"### {question_data['q']}\n\n"
                f"👉 *Click the button with the correct answer below within 45s!*\n"
                f"🎁 **Correct Answer:** `+50 Coins` reward"
            ),
            color=0x3498DB
        )
        embed.set_footer(text="RAI FAM 💗 • Brain Arena", icon_url=config.RAI_ICON_URL)

        view = TriviaView(question_data)
        await interaction.response.send_message(embed=embed, view=view)

    # 5. PAY / TRANSFER
    @app_commands.command(name="pay", description="Send coins directly to another server member.")
    @app_commands.describe(member="Member to pay", amount="Amount of coins to send")
    async def pay_command(self, interaction: discord.Interaction, member: discord.Member, amount: int):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot send coins to yourself.", ephemeral=True)
        if member.bot:
            return await interaction.response.send_message("❌ Bots cannot hold coins.", ephemeral=True)
        if amount < 10:
            return await interaction.response.send_message("❌ Minimum transfer is `10` Coins.", ephemeral=True)

        sender_data = get_user_data(interaction.user.id)
        if sender_data.get("coins", 0) < amount:
            return await interaction.response.send_message(f"❌ You only have `{sender_data.get('coins', 0):,}` Coins.", ephemeral=True)

        new_sender = update_user_coins(interaction.user.id, -amount)
        new_receiver = update_user_coins(member.id, amount)

        embed = discord.Embed(
            title="💸 COIN TRANSFER SUCCESSFUL",
            description=(
                f"{interaction.user.mention} sent **`{amount:,} Coins`** to {member.mention}! 💗\n\n"
                f"• **Your New Balance:** `{new_sender:,}` Coins\n"
                f"• **Recipient Balance:** `{new_receiver:,}` Coins"
            ),
            color=0x2ECC71
        )
        embed.set_footer(text="RAI FAM 💗 • Secure Coin Transfer", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    # 6. PERKS SHOP
    @app_commands.command(name="shop", description="Open the Server Perks Store to buy roles, VIP, and badges.")
    async def shop_command(self, interaction: discord.Interaction):
        user_coins = get_user_data(interaction.user.id).get("coins", 0)
        embed = discord.Embed(
            title="🛒 RAI FAM • OFFICIAL PERKS STORE",
            description=(
                f"Welcome to the Server Store, {interaction.user.mention}! 🌸\n"
                f"Your Wallet Balance: **`{user_coins:,} Coins`** 🪙\n\n"
                f"**Available Exclusive Items:**\n"
                f"• 🎧 **DJ Pass Role** — `1,000 Coins`\n"
                f"  *Full audio control, skip priority, and sound filter access.*\n\n"
                f"• 💎 **VIP Elite Role** — `2,500 Coins`\n"
                f"  *Prestige badge, private VIP voice lounge, and cinema lounge access.*\n\n"
                f"• 💛 **Royal Gold Name Color** — `800 Coins`\n"
                f"  *Stand out in text channels with a brilliant royal gold name.*\n\n"
                f"👉 *Click the buttons below to purchase instantly!*"
            ),
            color=0x9B5DE5
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else config.RAI_ICON_URL)
        embed.set_footer(text="Earn coins by chatting or relaxing in VC (+5 coins every 2 min)!", icon_url=config.RAI_ICON_URL)

        view = ShopBuyView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
