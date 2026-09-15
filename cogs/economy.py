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

OWNER_ID = 1457380609641938981

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
        "role_id": 1545834931165335673,
        "role_name": "💎 ┊ 𝐑𝐀𝐈 𝐄𝐋𝐈𝐓𝐄",
        "emoji": "💎"
    },
    "sakura_pink": {
        "name": "🌸 Sakura Pink Name Color",
        "description": "Shine in chat with the aesthetic Sakura Pink username color",
        "price": 800,
        "role_id": 1546088552293728268,
        "role_name": "Sakura Pink",
        "emoji": "🌸"
    },
    "neon_purple": {
        "name": "💜 Neon Purple Name Color",
        "description": "Vibrant glowing neon purple name in all server channels",
        "price": 800,
        "role_id": 1546088554747142174,
        "role_name": "Neon Purple",
        "emoji": "💜"
    },
    "cyber_cyan": {
        "name": "💎 Cyber Cyan Name Color",
        "description": "Futuristic neon cyan glow for your username",
        "price": 800,
        "role_id": 1546088557742129232,
        "role_name": "Cyber Cyan",
        "emoji": "💎"
    },
    "royal_gold": {
        "name": "💛 Royal Gold Name Color",
        "description": "Prestigious shimmering gold name in server chat",
        "price": 800,
        "role_id": 1546088559830634586,
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
    if int(user_id) == OWNER_ID:
        data[uid]["coins"] = 999_999_999_999
        data[uid]["streak"] = max(data[uid].get("streak", 0), 999)
        data[uid]["rep"] = max(data[uid].get("rep", 0), 999)
    return data[uid]


def update_user_coins(user_id: int, delta: int) -> int:
    if int(user_id) == OWNER_ID:
        return 999_999_999_999
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
class ShopSelect(discord.ui.Select):
    def __init__(self):
        options = []
        for key, item in SHOP_ITEMS.items():
            options.append(discord.SelectOption(
                label=f"{item['name']} ({item['price']:,} coins)",
                value=key,
                description=item['description'][:95],
                emoji=item['emoji']
            ))
        super().__init__(
            placeholder="🛒 Click here to select a role or color to buy...",
            min_values=1,
            max_values=1,
            options=options,
            row=0
        )

    async def callback(self, interaction: discord.Interaction):
        view: ShopBuyView = self.view
        await view.process_purchase(interaction, self.values[0])


class ShopBuyView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.add_item(ShopSelect())

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("❌ This shop menu belongs to someone else.", ephemeral=True)
            return False
        return True

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
                f"Your Wallet Balance: **`{user_coins:,}` Coins** 🪙\n\n"
                f"**Available Exclusive Roles & Perks:**\n"
                f"• 🎧 **DJ Pass Role** — `1,000 Coins`\n"
                f"  *Full audio control, skip priority, and sound filter access.*\n\n"
                f"• 💎 **VIP Elite Role** — `2,500 Coins`\n"
                f"  *Prestige badge, private VIP voice lounge, and cinema lounge access.*\n\n"
                f"• 🌸 **Sakura Pink Name Color** — `800 Coins`\n"
                f"• 💜 **Neon Purple Name Color** — `800 Coins`\n"
                f"• 💎 **Cyber Cyan Name Color** — `800 Coins`\n"
                f"• 💛 **Royal Gold Name Color** — `800 Coins`\n\n"
                f"👉 *Choose any item from the dropdown menu below to buy!*"
            ),
            color=0x9B5DE5
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else config.RAI_ICON_URL)
        embed.set_footer(text="Earn coins by chatting or relaxing in VC (+5 coins every 2 min)!", icon_url=config.RAI_ICON_URL)

        view = ShopBuyView(interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    # 7. BALANCE / WALLET
    @app_commands.command(name="balance", description="Check your current coin balance, daily streak, and reputation points.")
    @app_commands.describe(member="Optional member whose wallet you want to view")
    async def balance_command(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        if target.bot:
            return await interaction.response.send_message("❌ Bots do not have economy wallets.", ephemeral=True)

        user_data = get_user_data(target.id)
        coins = user_data.get("coins", 0)
        streak = user_data.get("streak", 0)
        rep = user_data.get("rep", 0)

        coin_display = "∞ *(Infinite Vault • Server Owner)*" if target.id == OWNER_ID else f"`{coins:,}` Coins"

        embed = discord.Embed(
            title=f"👛 {target.display_name.upper()}'S WALLET",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"🪙 **Coin Balance:** {coin_display}\n"
                f"🔥 **Daily Streak:** `{streak}` Days\n"
                f"⭐ **Community Rep:** `{rep}` Points\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"💡 *Use `/daily` to claim bonus coins or `/shop` to purchase VIP perks!*"
            ),
            color=0xFF69B4
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Vault & Economy System", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    # 8. GAMBLE / COIN TOSS BET
    @app_commands.command(name="gamble", description="Double or nothing! Bet coins on Heads or Tails.")
    @app_commands.describe(bet="Amount of coins to gamble (Min: 10)", choice="Your prediction")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads 👑", value="heads"),
        app_commands.Choice(name="Tails 🪙", value="tails")
    ])
    async def gamble_command(self, interaction: discord.Interaction, bet: int, choice: str):
        if bet < 10:
            return await interaction.response.send_message("❌ Minimum bet is `10` Coins.", ephemeral=True)

        user_data = get_user_data(interaction.user.id)
        coins = user_data.get("coins", 0)
        if coins < bet and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(
                f"❌ You don't have enough coins! Your balance: `{coins:,}` Coins.",
                ephemeral=True
            )

        outcome = random.choice(["heads", "tails"])
        won = (choice.lower() == outcome)

        if won:
            new_bal = update_user_coins(interaction.user.id, bet)
            bal_str = "∞ (Owner Vault)" if interaction.user.id == OWNER_ID else f"`{new_bal:,}` Coins"
            embed = discord.Embed(
                title="🎉 YOU WON THE COIN FLIP!",
                description=(
                    f"The coin spun through the air and landed on **{outcome.upper()}**!\n\n"
                    f"✨ **Prediction:** `{choice.capitalize()}` *(Correct!)*\n"
                    f"💰 **Profit:** `+{bet:,}` Coins\n"
                    f"👛 **New Balance:** {bal_str}"
                ),
                color=0x2ECC71
            )
        else:
            new_bal = update_user_coins(interaction.user.id, -bet)
            bal_str = "∞ (Owner Vault)" if interaction.user.id == OWNER_ID else f"`{new_bal:,}` Coins"
            embed = discord.Embed(
                title="💀 BETTER LUCK NEXT TIME!",
                description=(
                    f"The coin spun through the air and landed on **{outcome.upper()}**!\n\n"
                    f"❌ **Prediction:** `{choice.capitalize()}` *(Missed)*\n"
                    f"💸 **Loss:** `-{bet:,}` Coins\n"
                    f"👛 **New Balance:** {bal_str}"
                ),
                color=0xE74C3C
            )

        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • High Stakes Arena", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    # 9. RICHEST LEADERBOARD
    @app_commands.command(name="richest", description="View the top 10 richest members in the server.")
    async def richest_command(self, interaction: discord.Interaction):
        data = load_economy()
        if not data:
            return await interaction.response.send_message("ℹ️ No economy data recorded yet.", ephemeral=True)

        # Sort by coin balance descending, exclude owner from normal rank since owner has infinite
        sorted_users = [
            (uid, udata) for uid, udata in sorted(data.items(), key=lambda x: x[1].get("coins", 0), reverse=True)
            if int(uid) != OWNER_ID
        ]
        top_10 = sorted_users[:9]

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣"]
        lines = ["👑 **rf.rai_006** — `∞ Coins` *(🔥 999d • Server Owner)*"]

        for idx, (uid_str, udata) in enumerate(top_10):
            medal = medals[idx] if idx < len(medals) else f"`#{idx+1}`"
            try:
                member = interaction.guild.get_member(int(uid_str))
                name = member.display_name if member else f"User {uid_str}"
            except Exception:
                name = f"User {uid_str}"

            c = udata.get("coins", 0)
            streak = udata.get("streak", 0)
            lines.append(f"{medal} **{name}** — `{c:,}` Coins *(🔥 {streak}d)*")

        board_text = "\n".join(lines)

        user_coins = get_user_data(interaction.user.id).get("coins", 0)
        user_rank = "👑 Server Owner (#1)" if interaction.user.id == OWNER_ID else "Unranked"
        if interaction.user.id != OWNER_ID:
            for rank_idx, (uid_str, _) in enumerate(sorted_users):
                if uid_str == str(interaction.user.id):
                    user_rank = f"#{rank_idx + 2}"
                    break

        coin_str = "∞ Coins" if interaction.user.id == OWNER_ID else f"{user_coins:,} Coins"

        embed = discord.Embed(
            title="🏆 RAI FAM 💗 • RICHEST MEMBERS LEADERBOARD",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"{board_text}\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"👤 **Your Rank:** `{user_rank}` with **`{coin_str}`**"
            ),
            color=0xF1C40F
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else config.RAI_ICON_URL)
        embed.set_footer(text="Earn coins by chatting or relaxing in VC (+5 coins every 2 min)!", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
