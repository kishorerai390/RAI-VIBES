import os
import sys
import json
import random
import time
from pathlib import Path
from typing import Optional, Dict
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
            "wins": 0,
            "losses": 0
        }
        save_economy(data)
    return data[uid]


def update_user_coins(user_id: int, delta: int) -> int:
    data = load_economy()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"coins": 200, "last_daily": 0, "streak": 0, "wins": 0, "losses": 0}
    data[uid]["coins"] = max(0, data[uid].get("coins", 0) + delta)
    save_economy(data)
    return data[uid]["coins"]


class ShopBuyView(View):
    """Interactive Shop Purchase Buttons."""
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
                f"💡 *Earn more by listening in voice lounges (+5 coins every 2 min) or claiming `/daily`!*",
                ephemeral=True
            )

        # Grant role if applicable
        role = None
        if item["role_id"]:
            role = guild.get_role(item["role_id"])
        if not role:
            role = discord.utils.get(guild.roles, name=item["role_name"])

        if role:
            if role in user.roles:
                return await interaction.response.send_message(f"⚠️ You already possess the **{role.name}** perk!", ephemeral=True)
            try:
                await user.add_roles(role, reason=f"Purchased {item['name']} from Server Shop")
            except Exception as e:
                return await interaction.response.send_message(f"❌ Failed to grant role: {e}", ephemeral=True)

        # Deduct coins
        new_balance = update_user_coins(user.id, -item["price"])
        embed = discord.Embed(
            title="🎉 PURCHASE SUCCESSFUL!",
            description=(
                f"Congratulations {user.mention}! You purchased **{item['name']}**!\n\n"
                f"💸 **Amount Paid:** `{item['price']:,} Coins`\n"
                f"💰 **New Balance:** `{new_balance:,} Coins`\n"
                f"✨ Perk is now active on your server profile!"
            ),
            color=0x2ECC71
        )
        embed.set_thumbnail(url=user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Server Shop", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)


class Economy(commands.Cog):
    """Server Economy, Rewards, Gambling Mini-games & Perks Shop."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def add_balance(self, user_id: int, amount: int) -> int:
        return update_user_coins(user_id, amount)

    def get_balance(self, user_id: int) -> int:
        return get_user_data(user_id).get("coins", 0)

    # -------------------------------------------------------------
    # DAILY REWARD
    # -------------------------------------------------------------
    @app_commands.command(name="daily", description="Claim your daily coin reward and build your streak!")
    async def daily_command(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        data = load_economy()
        uid = str(user_id)
        if uid not in data:
            data[uid] = {"coins": 200, "last_daily": 0, "streak": 0, "wins": 0, "losses": 0}

        now = int(time.time())
        last_daily = data[uid].get("last_daily", 0)
        cooldown = 86400  # 24 hours
        diff = now - last_daily

        if diff < cooldown:
            rem = cooldown - diff
            hours, rem = divmod(rem, 3600)
            mins, secs = divmod(rem, 60)
            return await interaction.response.send_message(
                f"⏳ **Daily Cooldown!** You can claim your next daily reward in **{hours}h {mins}m {secs}s**.",
                ephemeral=True
            )

        # Check streak (streak keeps if within 48h)
        streak = data[uid].get("streak", 0)
        if diff < 172800:
            streak += 1
        else:
            streak = 1

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

    # -------------------------------------------------------------
    # COINFLIP
    # -------------------------------------------------------------
    @app_commands.command(name="coinflip", description="Bet your coins on a 50/50 heads or tails coin toss!")
    @app_commands.describe(amount="Amount of coins to bet", choice="Your guess (heads or tails)")
    async def coinflip_command(self, interaction: discord.Interaction, amount: int, choice: str):
        choice = choice.lower().strip()
        if choice not in ["heads", "tails", "h", "t"]:
            return await interaction.response.send_message("❌ Choice must be `heads` or `tails`.", ephemeral=True)
        if choice in ["h", "heads"]:
            choice = "heads"
        else:
            choice = "tails"

        if amount < 10:
            return await interaction.response.send_message("❌ Minimum bet is `10` Coins.", ephemeral=True)

        user_data = get_user_data(interaction.user.id)
        if user_data.get("coins", 0) < amount:
            return await interaction.response.send_message(f"❌ You only have `{user_data.get('coins', 0):,}` Coins.", ephemeral=True)

        outcome = random.choice(["heads", "tails"])
        won = outcome == choice

        delta = amount if won else -amount
        new_balance = update_user_coins(interaction.user.id, delta)

        color = 0x2ECC71 if won else 0xE74C3C
        result_title = "🎉 YOU WON!" if won else "💔 YOU LOST!"
        desc = (
            f"The golden coin landed on **`{outcome.upper()}`**! 🪙\n\n"
            f"• **Your Guess:** `{choice.capitalize()}`\n"
            f"• **Payout:** `+{amount:,}` Coins\n" if won else f"• **Loss:** `-{amount:,}` Coins\n"
        )
        desc += f"• **Wallet Balance:** `{new_balance:,}` Coins"

        embed = discord.Embed(title=result_title, description=desc, color=color)
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • High Stakes Coinflip", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    # -------------------------------------------------------------
    # SLOTS
    # -------------------------------------------------------------
    @app_commands.command(name="slots", description="Spin the Lucky 7 Casino Slots for up to a 10x jackpot!")
    @app_commands.describe(amount="Amount of coins to bet")
    async def slots_command(self, interaction: discord.Interaction, amount: int):
        if amount < 20:
            return await interaction.response.send_message("❌ Minimum slot bet is `20` Coins.", ephemeral=True)

        user_data = get_user_data(interaction.user.id)
        if user_data.get("coins", 0) < amount:
            return await interaction.response.send_message(f"❌ You only have `{user_data.get('coins', 0):,}` Coins.", ephemeral=True)

        emojis = ["🍒", "🍋", "🍇", "🔔", "💎", "7️⃣"]
        reel1 = random.choice(emojis)
        reel2 = random.choice(emojis)
        reel3 = random.choice(emojis)

        # Multipliers
        multiplier = 0
        if reel1 == reel2 == reel3:
            if reel1 == "7️⃣":
                multiplier = 10
            elif reel1 == "💎":
                multiplier = 7
            else:
                multiplier = 5
        elif reel1 == reel2 or reel2 == reel3 or reel1 == reel3:
            multiplier = 1.5

        won = multiplier > 0
        if won:
            profit = int(amount * multiplier) - amount
            new_balance = update_user_coins(interaction.user.id, profit)
        else:
            profit = -amount
            new_balance = update_user_coins(interaction.user.id, -amount)

        embed = discord.Embed(
            title="🎰 LUCKY CASINO SLOTS",
            description=(
                f"╭───────────────╮\n"
                f"│  {reel1}  ┆  {reel2}  ┆  {reel3}  │\n"
                f"╰───────────────╯\n\n"
                f"{'🎉 **JACKPOT WINNER!**' if won else '💔 **No match! Better luck next spin.**'}\n\n"
                f"• **Multiplier:** `{multiplier}x`\n"
                f"• **Profit/Loss:** `{'+' if won else ''}{profit:,} Coins`\n"
                f"• **New Balance:** `{new_balance:,}` Coins"
            ),
            color=0xF1C40F if won else 0x2B2D31
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Casino Royale", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    # -------------------------------------------------------------
    # PAY / TRANSFER
    # -------------------------------------------------------------
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

    # -------------------------------------------------------------
    # SERVER PERKS SHOP
    # -------------------------------------------------------------
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
