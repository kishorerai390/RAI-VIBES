import os
import json
import time
import random
import asyncio
from pathlib import Path
from typing import Optional, List, Literal

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, button

import config

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ECONOMY_FILE = DATA_DIR / "economy.json"


def get_coins(user_id: int) -> int:
    if ECONOMY_FILE.exists():
        try:
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                eco = json.load(f)
                return eco.get(str(user_id), {}).get("coins", 0)
        except Exception:
            pass
    return 0


def add_coins(user_id: int, amount: int):
    try:
        eco = {}
        if ECONOMY_FILE.exists():
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                eco = json.load(f)
        uid = str(user_id)
        if uid not in eco:
            eco[uid] = {"coins": 200, "last_daily": 0, "wins": 0, "losses": 0}
        eco[uid]["coins"] = max(0, eco[uid].get("coins", 0) + amount)
        with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
            json.dump(eco, f, indent=2)
    except Exception:
        pass


def record_stats(user_id: int, won: bool):
    try:
        eco = {}
        if ECONOMY_FILE.exists():
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                eco = json.load(f)
        uid = str(user_id)
        if uid not in eco:
            eco[uid] = {"coins": 200, "last_daily": 0, "wins": 0, "losses": 0}
        if won:
            eco[uid]["wins"] = eco[uid].get("wins", 0) + 1
        else:
            eco[uid]["losses"] = eco[uid].get("losses", 0) + 1
        with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
            json.dump(eco, f, indent=2)
    except Exception:
        pass


# -------------------------------------------------------------
# BLACKJACK GAME ENGINE
# -------------------------------------------------------------
CARD_SUITS = ["♠️", "♥️", "♦️", "♣️"]
CARD_RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]


def draw_card() -> str:
    return f"{random.choice(CARD_RANKS)}{random.choice(CARD_SUITS)}"


def calculate_hand(hand: List[str]) -> int:
    value = 0
    aces = 0
    for card in hand:
        rank = card[:-2] if card.endswith(("♠️", "♥️", "♦️", "♣️")) else card[:-1]
        if rank in ["J", "Q", "K"]:
            value += 10
        elif rank == "A":
            aces += 1
            value += 11
        else:
            try:
                value += int(rank)
            except ValueError:
                value += 10
    while value > 21 and aces > 0:
        value -= 10
        aces -= 1
    return value


class BlackjackView(View):
    def __init__(self, user: discord.User, bet: int):
        super().__init__(timeout=60)
        self.user = user
        self.bet = bet
        self.player_hand: List[str] = [draw_card(), draw_card()]
        self.dealer_hand: List[str] = [draw_card(), draw_card()]
        self.game_over = False

    def build_embed(self, finished: bool = False, outcome: str = "") -> discord.Embed:
        p_val = calculate_hand(self.player_hand)
        p_cards = " ".join([f"`{c}`" for c in self.player_hand])

        if finished:
            d_val = calculate_hand(self.dealer_hand)
            d_cards = " ".join([f"`{c}`" for c in self.dealer_hand])
            dealer_title = f"🎰 Dealer's Hand ({d_val})"
        else:
            d_cards = f"`{self.dealer_hand[0]}` `🂠`"
            dealer_title = "🎰 Dealer's Hand (?)"

        embed = discord.Embed(
            title="♠️ CYBER BLACKJACK • HIGH-STAKES TABLE ♠️",
            description=f"Player: {self.user.mention} | Wager: **{self.bet:,} Coins**",
            color=0x00FFCC if finished and "Won" in outcome else (0xFF0055 if finished else 0xFF69B4)
        )
        embed.add_field(name=f"👤 Your Hand ({p_val})", value=p_cards, inline=False)
        embed.add_field(name=dealer_title, value=d_cards, inline=False)

        if outcome:
            embed.add_field(name="🏆 Game Result", value=outcome, inline=False)

        embed.set_footer(text="RAI VIBES Casino • Click Hit to draw or Stand to hold")
        return embed

    @button(label="Hit", emoji="🃏", style=discord.ButtonStyle.primary)
    async def hit(self, interaction: discord.Interaction, btn: Button):
        if interaction.user.id != self.user.id or self.game_over:
            return await interaction.response.send_message("❌ This is not your game!", ephemeral=True)

        self.player_hand.append(draw_card())
        p_val = calculate_hand(self.player_hand)

        if p_val > 21:
            self.game_over = True
            self.stop()
            record_stats(self.user.id, won=False)
            embed = self.build_embed(finished=True, outcome=f"💥 **BUST!** You scored `{p_val}` and lost **{self.bet:,} Coins**!")
            await interaction.response.edit_message(embed=embed, view=None)
        else:
            embed = self.build_embed()
            await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Stand", emoji="🛑", style=discord.ButtonStyle.secondary)
    async def stand(self, interaction: discord.Interaction, btn: Button):
        if interaction.user.id != self.user.id or self.game_over:
            return await interaction.response.send_message("❌ This is not your game!", ephemeral=True)

        self.game_over = True
        self.stop()

        # Dealer draws to 17
        while calculate_hand(self.dealer_hand) < 17:
            self.dealer_hand.append(draw_card())

        p_val = calculate_hand(self.player_hand)
        d_val = calculate_hand(self.dealer_hand)

        if d_val > 21:
            win_amt = self.bet * 2
            add_coins(self.user.id, win_amt)
            record_stats(self.user.id, won=True)
            outcome = f"🎉 **DEALER BUST!** Dealer scored `{d_val}`. You won **+{self.bet:,} Coins**!"
        elif p_val > d_val:
            win_amt = self.bet * 2
            add_coins(self.user.id, win_amt)
            record_stats(self.user.id, won=True)
            outcome = f"🎉 **YOU WON!** `{p_val}` beats `{d_val}`. You won **+{self.bet:,} Coins**!"
        elif p_val < d_val:
            record_stats(self.user.id, won=False)
            outcome = f"💔 **DEALER WINS!** `{d_val}` beats `{p_val}`. You lost **{self.bet:,} Coins**."
        else:
            add_coins(self.user.id, self.bet)  # Refund
            outcome = f"🤝 **PUSH!** Both scored `{p_val}`. Your **{self.bet:,} Coins** were refunded!"

        embed = self.build_embed(finished=True, outcome=outcome)
        await interaction.response.edit_message(embed=embed, view=None)

    @button(label="Double Down", emoji="⚡", style=discord.ButtonStyle.danger)
    async def double(self, interaction: discord.Interaction, btn: Button):
        if interaction.user.id != self.user.id or self.game_over:
            return await interaction.response.send_message("❌ This is not your game!", ephemeral=True)

        user_coins = get_coins(self.user.id)
        if user_coins < self.bet:
            return await interaction.response.send_message(f"❌ You need another **{self.bet:,} Coins** to double down!", ephemeral=True)

        add_coins(self.user.id, -self.bet)
        self.bet *= 2
        self.game_over = True
        self.stop()

        # One card only
        self.player_hand.append(draw_card())
        p_val = calculate_hand(self.player_hand)

        if p_val > 21:
            record_stats(self.user.id, won=False)
            embed = self.build_embed(finished=True, outcome=f"💥 **BUST!** You drew a card, scored `{p_val}`, and lost **{self.bet:,} Coins**!")
            return await interaction.response.edit_message(embed=embed, view=None)

        while calculate_hand(self.dealer_hand) < 17:
            self.dealer_hand.append(draw_card())

        d_val = calculate_hand(self.dealer_hand)

        if d_val > 21 or p_val > d_val:
            win_amt = self.bet * 2
            add_coins(self.user.id, win_amt)
            record_stats(self.user.id, won=True)
            outcome = f"⚡🔥 **DOUBLE DOWN VICTORY!** You won **+{self.bet:,} Coins**!"
        elif p_val < d_val:
            record_stats(self.user.id, won=False)
            outcome = f"💔 **DEALER WINS!** `{d_val}` beats `{p_val}`. You lost **{self.bet:,} Coins**."
        else:
            add_coins(self.user.id, self.bet)
            outcome = f"🤝 **PUSH!** Both scored `{p_val}`. Refunded **{self.bet:,} Coins**!"

        embed = self.build_embed(finished=True, outcome=outcome)
        await interaction.response.edit_message(embed=embed, view=None)


class Casino(commands.Cog):
    """Social Casino & High-Stakes Minigames Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    casino = app_commands.Group(name="casino", description="High-stakes cyber casino games")

    @casino.command(name="blackjack", description="Play high-stakes Blackjack against the dealer!")
    @app_commands.describe(bet="Amount of coins to wager (minimum 50)")
    async def blackjack(self, interaction: discord.Interaction, bet: int):
        if bet < 50:
            return await interaction.response.send_message("❌ Minimum bet is **50 Coins**!", ephemeral=True)

        user_coins = get_coins(interaction.user.id)
        if user_coins < bet:
            return await interaction.response.send_message(f"❌ You only have **{user_coins:,} Coins**! Claim `/daily` to get more.", ephemeral=True)

        # Deduct bet upfront
        add_coins(interaction.user.id, -bet)

        view = BlackjackView(interaction.user, bet)
        # Check natural blackjack
        p_val = calculate_hand(view.player_hand)
        d_val = calculate_hand(view.dealer_hand)

        if p_val == 21:
            view.game_over = True
            if d_val == 21:
                add_coins(interaction.user.id, bet)
                outcome = "🤝 **Both scored Natural Blackjack!** Push - coins refunded."
            else:
                payout = int(bet * 2.5)  # 3:2 payout
                add_coins(interaction.user.id, payout)
                record_stats(interaction.user.id, won=True)
                outcome = f"👑✨ **NATURAL BLACKJACK!** You won **+{payout - bet:,} Coins** (3:2 Payout)!"
            embed = view.build_embed(finished=True, outcome=outcome)
            return await interaction.response.send_message(embed=embed)

        embed = view.build_embed()
        await interaction.response.send_message(embed=embed, view=view)

    @casino.command(name="slots", description="Spin the Cyber-Pink slot machine for jackpot multipliers!")
    @app_commands.describe(bet="Amount of coins to spin (minimum 25)")
    async def slots(self, interaction: discord.Interaction, bet: int):
        if bet < 25:
            return await interaction.response.send_message("❌ Minimum spin is **25 Coins**!", ephemeral=True)

        user_coins = get_coins(interaction.user.id)
        if user_coins < bet:
            return await interaction.response.send_message(f"❌ You only have **{user_coins:,} Coins**!", ephemeral=True)

        add_coins(interaction.user.id, -bet)

        symbols = ["💎", "🌸", "👑", "⚡", "🍒", "7️⃣"]
        r1, r2, r3 = random.choice(symbols), random.choice(symbols), random.choice(symbols)

        # Payout logic
        multiplier = 0
        jackpot = False
        if r1 == r2 == r3:
            if r1 == "💎":
                multiplier = 10.0
                jackpot = True
            elif r1 == "7️⃣":
                multiplier = 7.0
            elif r1 == "👑":
                multiplier = 5.0
            elif r1 == "🌸":
                multiplier = 4.0
            elif r1 == "⚡":
                multiplier = 3.0
            elif r1 == "🍒":
                multiplier = 2.5
        elif r1 == r2 or r2 == r3 or r1 == r3:
            multiplier = 1.5

        winnings = int(bet * multiplier)
        if winnings > 0:
            add_coins(interaction.user.id, winnings)
            record_stats(interaction.user.id, won=True)
            if jackpot:
                result_text = f"💎🔥 **MEGA JACKPOT HIT!** You won **+{winnings:,} Coins** (10x Multiplier)!"
            else:
                result_text = f"🎉 **WINNER!** You won **+{winnings:,} Coins** ({multiplier}x Multiplier)!"
            color = 0x00FFCC
        else:
            record_stats(interaction.user.id, won=False)
            result_text = f"💔 No match! You lost **{bet:,} Coins**. Spin again to win!"
            color = 0xFF0055

        embed = discord.Embed(
            title="🎰 CYBER-PINK SLOTS 🎰",
            description=(
                f"Player: {interaction.user.mention} | Bet: **{bet:,} Coins**\n\n"
                f"╭─────────────╮\n"
                f"│  [ {r1} | {r2} | {r3} ]  │\n"
                f"╰─────────────╯\n\n"
                f"{result_text}"
            ),
            color=color
        )
        embed.set_footer(text="RAI PLAY 🎮 • Match 3 for massive jackpots!")

        # Animated multi-frame slot spin
        embed_spin1 = discord.Embed(
            title="🎰 CYBER-PINK SLOTS 🎰",
            description=(
                f"Player: {interaction.user.mention} | Bet: **{bet:,} Coins**\n\n"
                f"╭─────────────╮\n"
                f"│  [ 🌀 | 🌀 | 🌀 ]  │\n"
                f"╰─────────────╯\n\n"
                f"⚡ *Reels are spinning at hyper-speed...*"
            ),
            color=0x2B0938
        )
        embed_spin1.set_footer(text="RAI PLAY 🎮 • Cyber Casino")
        await interaction.response.send_message(embed=embed_spin1)
        await asyncio.sleep(0.8)

        embed_spin2 = discord.Embed(
            title="🎰 CYBER-PINK SLOTS 🎰",
            description=(
                f"Player: {interaction.user.mention} | Bet: **{bet:,} Coins**\n\n"
                f"╭─────────────╮\n"
                f"│  [ {r1} | 🌀 | 🌀 ]  │\n"
                f"╰─────────────╯\n\n"
                f"🔒 *Reel 1 locked in! Suspense builds...*"
            ),
            color=0x9B59B6
        )
        embed_spin2.set_footer(text="RAI PLAY 🎮 • Cyber Casino")
        try:
            await interaction.edit_original_response(embed=embed_spin2)
        except Exception:
            pass
        await asyncio.sleep(0.8)

        embed_spin3 = discord.Embed(
            title="🎰 CYBER-PINK SLOTS 🎰",
            description=(
                f"Player: {interaction.user.mention} | Bet: **{bet:,} Coins**\n\n"
                f"╭─────────────╮\n"
                f"│  [ {r1} | {r2} | 🌀 ]  │\n"
                f"╰─────────────╯\n\n"
                f"🔥 *Reel 2 locked! Here comes the final stop...*"
            ),
            color=0xFFA502
        )
        embed_spin3.set_footer(text="RAI PLAY 🎮 • Cyber Casino")
        try:
            await interaction.edit_original_response(embed=embed_spin3)
        except Exception:
            pass
        await asyncio.sleep(0.9)

        try:
            await interaction.edit_original_response(embed=embed)
        except Exception:
            pass

    @casino.command(name="coinflip", description="Flip a coin for double-or-nothing coin rewards!")
    @app_commands.describe(choice="Heads or Tails", bet="Amount of coins to bet")
    async def coinflip(self, interaction: discord.Interaction, choice: Literal["heads", "tails"], bet: int):
        if bet < 20:
            return await interaction.response.send_message("❌ Minimum bet is **20 Coins**!", ephemeral=True)

        user_coins = get_coins(interaction.user.id)
        if user_coins < bet:
            return await interaction.response.send_message(f"❌ You only have **{user_coins:,} Coins**!", ephemeral=True)

        add_coins(interaction.user.id, -bet)
        outcome = random.choice(["heads", "tails"])

        if choice.lower() == outcome:
            win_amt = bet * 2
            add_coins(interaction.user.id, win_amt)
            record_stats(interaction.user.id, won=True)
            res = f"🎉 **It's {outcome.upper()}!** You won **+{bet:,} Coins**!"
            color = 0x00FFCC
        else:
            record_stats(interaction.user.id, won=False)
            res = f"💔 **It's {outcome.upper()}!** You lost **{bet:,} Coins**."
            color = 0xFF0055

        embed = discord.Embed(
            title="🪙 CYBER COIN TOSS",
            description=(
                f"Your Pick: **{choice.upper()}** | Outcome: **{outcome.upper()}**\n\n"
                f"{res}"
            ),
            color=color
        )
        embed.set_footer(text="RAI VIBES Casino • Double or Nothing")
        await interaction.response.send_message(embed=embed)

    @casino.command(name="dice", description="Roll high-stakes cyber dice against the bot!")
    @app_commands.describe(bet="Amount of coins to bet")
    async def dice(self, interaction: discord.Interaction, bet: int):
        if bet < 20:
            return await interaction.response.send_message("❌ Minimum bet is **20 Coins**!", ephemeral=True)

        user_coins = get_coins(interaction.user.id)
        if user_coins < bet:
            return await interaction.response.send_message(f"❌ You only have **{user_coins:,} Coins**!", ephemeral=True)

        add_coins(interaction.user.id, -bet)
        user_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)

        DICE_EMOJIS = {1: "⚀", 2: "⚁", 3: "⚂", 4: "⚃", 5: "⚄", 6: "⚅"}

        if user_roll > bot_roll:
            multiplier = 3.0 if user_roll == 6 else 2.0
            winnings = int(bet * multiplier)
            add_coins(interaction.user.id, winnings)
            record_stats(interaction.user.id, won=True)
            res = f"🎉 **VICTORY!** You won **+{winnings:,} Coins** ({multiplier}x multiplier)!"
            color = 0x00FF88
        elif user_roll == bot_roll:
            add_coins(interaction.user.id, bet)  # refund
            res = f"⚖️ **TIE!** Both rolled **{user_roll}**. Your bet of **{bet:,} Coins** was refunded!"
            color = 0xFFD700
        else:
            record_stats(interaction.user.id, won=False)
            res = f"💔 **DEFEAT!** The house wins. You lost **{bet:,} Coins**."
            color = 0xFF4757

        embed = discord.Embed(
            title="🎲 ┊ 𝐂𝐘𝐁𝐄𝐑  𝐃𝐈𝐂Ｅ  𝐃𝐔𝐄𝐋",
            description=(
                f"**Your Roll:** {DICE_EMOJIS[user_roll]} `({user_roll})`\n"
                f"**Bot Roll:**  {DICE_EMOJIS[bot_roll]} `({bot_roll})`\n\n"
                f"{res}"
            ),
            color=color
        )
        embed.set_footer(text="RAI VIBES Casino • High Rollers Arena")
        await interaction.response.send_message(embed=embed)

    @casino.command(name="spin", description="Spin the Daily Lucky Wheel of Fortune for bonus coins and jackpots!")
    async def spin_wheel(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        spins_file = DATA_DIR / "spins.json"
        now = int(time.time())
        cooldown = 64800  # 18 hours

        spins_data = {}
        if spins_file.exists():
            try:
                with open(spins_file, "r", encoding="utf-8") as f:
                    spins_data = json.load(f)
            except Exception:
                pass

        last_spin = spins_data.get(str(user_id), 0)
        if now - last_spin < cooldown:
            next_spin_ts = last_spin + cooldown
            return await interaction.response.send_message(
                f"⏳ You have already spun the wheel today! Your next spin is available <t:{next_spin_ts}:R> (<t:{next_spin_ts}:t>).",
                ephemeral=True
            )

        # Record spin time
        spins_data[str(user_id)] = now
        try:
            with open(spins_file, "w", encoding="utf-8") as f:
                json.dump(spins_data, f, indent=2)
        except Exception:
            pass

        # Defer and show spinning animation
        await interaction.response.defer()

        # Spin outcome selection
        TIERS = [
            ("🍒", 150, "Cherry Nibble", 0xFF6B81, 35),
            ("🍋", 300, "Lemon Zest", 0xFFA502, 25),
            ("🍇", 600, "Grape Rush", 0x9B59B6, 20),
            ("🔔", 1200, "Golden Bell", 0x00FFCC, 12),
            ("⭐", 2500, "Starlight Bonanza", 0xFFD700, 6),
            ("💎", 5000, "GRAND CYBER JACKPOT", 0xFF1493, 2),
        ]

        weights = [t[4] for t in TIERS]
        chosen_tier = random.choices(TIERS, weights=weights, k=1)[0]
        symbol, reward, tier_name, color, _ = chosen_tier

        # Reel animation
        reel1 = symbol
        reel2 = symbol if random.random() < 0.75 else random.choice(["🍒", "🍋", "🍇", "🔔"])
        reel3 = symbol if reel2 == symbol and random.random() < 0.65 else random.choice(["🍒", "🍋", "🍇", "🔔", "⭐"])

        embed_spinning = discord.Embed(
            title="🎰 ┊ 𝐋𝐔𝐂𝐊𝐘  𝐖𝐇𝐄𝐄𝐋  𝐎𝐅  𝐅𝐎𝐑𝐓𝐔𝐍𝐄",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"### `[ 🌀 ┊ 🌀 ┊ 🌀 ]`\n"
                f"*The wheel is spinning through the neon reels...*\n\n"
                f"✦ ───────────────────────────────────── ✦"
            ),
            color=0x2B0938
        )
        msg = await interaction.followup.send(embed=embed_spinning)
        await asyncio.sleep(1.8)

        add_coins(user_id, reward)
        record_stats(user_id, won=True)

        embed_result = discord.Embed(
            title="🎰 ┊ 𝐋𝐔𝐂𝐊𝐘  𝐖𝐇𝐄𝐄𝐋  𝐎𝐅  𝐅𝐎𝐑𝐓𝐔𝐍𝐄",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"### `[ {reel1} ┊ {reel2} ┊ {reel3} ]`\n\n"
                f"✨ **Tier Reached:** `{tier_name}`\n"
                f"💰 **Payout Awarded:** `+{reward:,} Rai Coins`!\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"Come back <t:{now + cooldown}:R> for your next free spin! 🌸"
            ),
            color=color
        )
        embed_result.set_footer(text=f"Spun by {interaction.user.display_name} • Daily Wheel", icon_url=interaction.user.display_avatar.url)
        await msg.edit(embed=embed_result)

    @app_commands.command(name="heist", description="💼 Cooperative Bank Heist: Assemble a crew, breach security, and crack the vault!")
    @app_commands.describe(vault="Target security vault to infiltrate")
    @app_commands.choices(
        vault=[
            app_commands.Choice(name="🏦 Downtown National Vault (Easy • 10,000 Coin Vault)", value="easy"),
            app_commands.Choice(name="🎰 Cyber-City Neon Casino Vault (Medium • 25,000 Coin Vault)", value="medium"),
            app_commands.Choice(name="💎 Federal Reserve Titanium Stash (Extreme • 50,000 Coin Vault)", value="hard")
        ]
    )
    async def heist(self, interaction: discord.Interaction, vault: Optional[app_commands.Choice[str]] = None):
        user_id = interaction.user.id
        entry_fee = 200
        user_coins = get_coins(user_id)
        if user_coins < entry_fee:
            return await interaction.response.send_message(f"❌ You need at least **{entry_fee} Coins** to buy into heist equipment!", ephemeral=True)

        add_coins(user_id, -entry_fee)

        v_type = vault.value if vault else "medium"
        vault_data = {
            "easy": {"name": "Downtown National Vault", "base_jackpot": 10000, "color": 0x00FFCC},
            "medium": {"name": "Cyber-City Neon Casino Vault", "base_jackpot": 25000, "color": 0xFFA502},
            "hard": {"name": "Federal Reserve Titanium Stash", "base_jackpot": 50000, "color": 0xFF0055}
        }[v_type]

        lobby_view = HeistLobbyView(interaction.user, entry_fee)
        embed_lobby = discord.Embed(
            title=f"💼 CO-OP HEIST: {vault_data['name'].upper()}",
            description=(
                f"**Mastermind:** {interaction.user.mention}\n"
                f"**Target Stash:** `{vault_data['base_jackpot']:,} Coins` minimum!\n"
                f"**Crew Buy-in:** `{entry_fee} Coins` per operative.\n\n"
                f"⚡ **Operatives needed!** Click **`[💼 Join Heist Crew]`** within **25 seconds** to gear up!\n"
                f"*(The larger the crew, the bigger the bonus jackpot split!)*"
            ),
            color=vault_data["color"]
        )
        embed_lobby.set_footer(text="RAI PLAY 🎮 • Co-op Bank Heist")
        await interaction.response.send_message(embed=embed_lobby, view=lobby_view)

        await asyncio.sleep(25.0)
        lobby_view.stop()

        crew = lobby_view.crew
        crew_mentions = ", ".join(m.mention for m in crew)
        total_vault_pot = vault_data["base_jackpot"] + (len(crew) * 2500)

        # Stage 1: Laser Grid
        s1_opts = ["🔴 Cut Red Frequency Wire", "🔵 Cut Blue Optical Wire", "🟢 Cut Green Earth Wire"]
        s1_view = HeistStageView(crew, "🔵 Cut Blue Optical Wire", s1_opts)
        embed_s1 = discord.Embed(
            title="🚨 HEIST STAGE 1: LASER OPTICAL GRID",
            description=(
                f"**Operatives:** {crew_mentions}\n\n"
                f"⚠️ *Corridor laced with blue scanning lasers!*\n"
                f"**Directive:** An operative must **Cut the BLUE Optical Wire** within **12 seconds**!"
            ),
            color=0x3498DB
        )
        await interaction.followup.send(embed=embed_s1, view=s1_view)
        await asyncio.sleep(12.0)
        s1_view.stop()

        if not s1_view.cleared:
            embed_fail = discord.Embed(
                title="🚨 HEIST FAILED: ALARMS TRIGGERED!",
                description="The optical tripwire was breached! Police sirens wailed and the crew escaped empty handed!",
                color=0xFF0055
            )
            return await interaction.followup.send(embed=embed_fail)

        # Stage 2: Mainframe Firewall
        s2_opts = ["💾 Inject IP Bypass Code", "⚡ Overload Generator", "🛠️ Smash Terminal"]
        s2_view = HeistStageView(crew, "💾 Inject IP Bypass Code", s2_opts)
        embed_s2 = discord.Embed(
            title="💻 HEIST STAGE 2: MAINFRAME FIREWALL",
            description=(
                f"**Lasers Bypassed by {s1_view.success_by.mention}!**\n\n"
                f"⚠️ *Security door locked with 256-bit cryptographic cipher!*\n"
                f"**Directive:** An operative must **Inject IP Bypass Code** within **12 seconds**!"
            ),
            color=0x9B59B6
        )
        await interaction.followup.send(embed=embed_s2, view=s2_view)
        await asyncio.sleep(12.0)
        s2_view.stop()

        if not s2_view.cleared:
            embed_fail = discord.Embed(
                title="🚨 HEIST FAILED: LOCKDOWN TRIGGERED!",
                description="Cybersecurity countermeasures locked down the facility! Mission aborted.",
                color=0xFF0055
            )
            return await interaction.followup.send(embed=embed_fail)

        # Stage 3: Titanium Vault Core
        s3_opts = ["💣 Detonate Shaped C4", "🪛 Pick Pin Mechanism", "🔋 Battery Short-Circuit"]
        s3_view = HeistStageView(crew, "💣 Detonate Shaped C4", s3_opts)
        embed_s3 = discord.Embed(
            title="💥 HEIST STAGE 3: TITANIUM VAULT DOOR",
            description=(
                f"**Firewall Breached by {s2_view.success_by.mention}!**\n\n"
                f"⚠️ *6-inch reinforced vault door standing between the crew and the gold!*\n"
                f"**Directive:** An operative must **Detonate Shaped C4** within **12 seconds**!"
            ),
            color=0xE67E22
        )
        await interaction.followup.send(embed=embed_s3, view=s3_view)
        await asyncio.sleep(12.0)
        s3_view.stop()

        if not s3_view.cleared:
            embed_fail = discord.Embed(
                title="🚨 HEIST FAILED: C4 MISFIRE!",
                description="The explosive charge failed! Emergency security forces surrounded the vault.",
                color=0xFF0055
            )
            return await interaction.followup.send(embed=embed_fail)

        # VICTORY!
        payout_per_member = total_vault_pot // len(crew)
        for member in crew:
            add_coins(member.id, payout_per_member)
            record_stats(member.id, won=True)

        embed_win = discord.Embed(
            title="💎🔥 HEIST SUCCESS: VAULT EMPTIED! 🔥💎",
            description=(
                f"### 🏆 **Total Vault Stash Cracked:** `+{total_vault_pot:,} Coins`\n\n"
                f"**Operative Crew Payouts:**\n"
                + "\n".join(f"• {m.mention} ➔ **`+{payout_per_member:,} Coins`** 💰" for m in crew)
                + f"\n\n✨ *Loot deposited directly into everyone's Arcade Account! Incredible teamwork!*"
            ),
            color=0x00FFCC
        )
        embed_win.set_footer(text="RAI PLAY 🎮 • Legendary Co-op Heist Masters")
        await interaction.followup.send(embed=embed_win)


class HeistStageButton(Button):
    def __init__(self, label: str, is_correct: bool, stage_view: 'HeistStageView'):
        super().__init__(label=label, style=discord.ButtonStyle.secondary)
        self.is_correct = is_correct
        self.stage_view = stage_view

    async def callback(self, interaction: discord.Interaction):
        if not any(m.id == interaction.user.id for m in self.stage_view.crew):
            return await interaction.response.send_message("❌ Only official Heist Crew members can execute tactical tasks!", ephemeral=True)

        if self.stage_view.cleared:
            return await interaction.response.send_message("⚡ This obstacle has already been breached!", ephemeral=True)

        if self.is_correct:
            self.stage_view.cleared = True
            self.stage_view.success_by = interaction.user
            self.style = discord.ButtonStyle.success
            await interaction.response.send_message(f"💥 **CRITICAL BREACH!** {interaction.user.mention} executed the task successfully!", ephemeral=False)
            self.stage_view.stop()
        else:
            self.style = discord.ButtonStyle.danger
            self.disabled = True
            await interaction.response.send_message("🚨 **WRONG MOVE!** Security alarms detected an error!", ephemeral=True)
            try:
                await interaction.message.edit(view=self.stage_view)
            except Exception:
                pass


class HeistStageView(View):
    def __init__(self, crew: list, correct_label: str, options: list):
        super().__init__(timeout=15.0)
        self.crew = crew
        self.cleared = False
        self.success_by = None
        for opt in options:
            self.add_item(HeistStageButton(opt, opt == correct_label, self))


class HeistLobbyView(View):
    def __init__(self, mastermind: discord.Member, entry_fee: int):
        super().__init__(timeout=30.0)
        self.mastermind = mastermind
        self.entry_fee = entry_fee
        self.crew = [mastermind]
        self.launched = False

    @button(label="💼 Join Heist Crew (200 Coins)", style=discord.ButtonStyle.success, custom_id="heist_crew_join")
    async def join_crew(self, interaction: discord.Interaction, btn: Button):
        if self.launched:
            return await interaction.response.send_message("❌ The heist team is already in the vault!", ephemeral=True)
        if any(m.id == interaction.user.id for m in self.crew):
            return await interaction.response.send_message("⚠️ You are already equipped in the crew roster!", ephemeral=True)

        user_coins = get_coins(interaction.user.id)
        if user_coins < self.entry_fee:
            return await interaction.response.send_message(f"❌ You need at least **{self.entry_fee} Coins** to buy into the heist gear!", ephemeral=True)

        add_coins(interaction.user.id, -self.entry_fee)
        self.crew.append(interaction.user)
        await interaction.response.send_message(f"💼 **{interaction.user.mention}** joined the heist crew! Entry `{self.entry_fee} 🪙` staked.", ephemeral=False)

    @button(label="🚨 Infiltrate Now (Leader)", style=discord.ButtonStyle.primary, custom_id="heist_crew_launch")
    async def launch_early(self, interaction: discord.Interaction, btn: Button):
        if interaction.user.id != self.mastermind.id:
            return await interaction.response.send_message("❌ Only the heist mastermind can initiate early infiltration!", ephemeral=True)
        self.launched = True
        self.stop()
        await interaction.response.send_message("🚨 **ALARM SILENCED • INFILTRATION COMMENCING NOW!**", ephemeral=False)


async def setup(bot: commands.Bot):
    await bot.add_cog(Casino(bot))
