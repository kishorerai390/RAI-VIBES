import os
import sys
import json
import time
import random
import logging
from pathlib import Path
from typing import Optional, Dict, List
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, button

import config
import database
from cogs.economy import get_user_data, update_user_coins, OWNER_ID

logger = logging.getLogger("Exchange")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EXCHANGE_FILE = DATA_DIR / "exchange.json"

# Exchange Rates & Tiered Bonuses
XP_PACKAGES = {
    "starter": {"xp": 100, "coins": 250, "rate": "2.5x"},
    "pro": {"xp": 500, "coins": 1350, "rate": "2.7x"},
    "elite": {"xp": 1000, "coins": 3000, "rate": "3.0x (Mega Bonus!)"}
}

COIN_PACKAGES = {
    "boost": {"coins": 500, "xp": 200, "desc": "Quick Boost"},
    "surge": {"coins": 1000, "xp": 500, "desc": "Level Surge (+100 XP Bonus)"},
    "skip": {"coins": 2500, "xp": 1500, "desc": "Mega Level Skip (+250 XP Bonus)"}
}

LEVEL_MILESTONES = {
    5: 500,
    10: 1500,
    20: 3500,
    50: 10000
}

STREAK_MILESTONES = {
    3: 300,
    7: 1000,
    14: 2500,
    30: 6000
}


def load_exchange_data() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if EXCHANGE_FILE.exists():
        try:
            with open(EXCHANGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"promocodes": {}, "milestones": {}, "streak_claims": {}, "rep_claims": {}}
    return {"promocodes": {}, "milestones": {}, "streak_claims": {}, "rep_claims": {}}


def save_exchange_data(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(EXCHANGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


# =====================================================================
# MODALS FOR INTERACTIVE CONVERSION & REDEEM
# =====================================================================
class ConvertXPToCoinsModal(Modal, title="Exchange Chat XP ➜ Coins"):
    amount = TextInput(
        label="Amount of XP to Exchange (Min: 50 XP)",
        placeholder="e.g., 100 (250c), 500 (1,350c), 1000 (3,000c)",
        min_length=1,
        max_length=6,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            val = int(self.amount.value.strip())
            if val < 50:
                return await interaction.followup.send("❌ Minimum exchange is `50 XP`.", ephemeral=True)
        except ValueError:
            return await interaction.followup.send("❌ Please enter a valid whole number.", ephemeral=True)

        user_lvl = await database.get_user_level_data(interaction.guild.id, interaction.user.id)
        current_xp = user_lvl.get("xp", 0)

        if current_xp < val:
            return await interaction.followup.send(
                f"❌ **Insufficient XP!** You have `{current_xp:,} XP`, cannot exchange `{val:,} XP`.",
                ephemeral=True
            )

        # Dynamic tiered rate: 1000+ -> 3.0x, 500+ -> 2.7x, below -> 2.5x
        if val >= 1000:
            coins_awarded = int(val * 3.0)
            tier_msg = "💎 **Elite Tier Applied (3.0x Multiplier!)**"
        elif val >= 500:
            coins_awarded = int(val * 2.7)
            tier_msg = "💼 **Pro Tier Applied (2.7x Multiplier!)**"
        else:
            coins_awarded = int(val * 2.5)
            tier_msg = "📦 **Standard Tier Applied (2.5x Multiplier)**"

        # Deduct XP
        await database.add_user_xp(interaction.guild.id, interaction.user.id, -val)
        # Credit Coins
        new_coins = update_user_coins(interaction.user.id, coins_awarded)
        bal_str = "∞ (Owner Vault)" if interaction.user.id == OWNER_ID else f"{new_coins:,} Coins"

        embed = discord.Embed(
            title="💱 XP EXCHANGE SUCCESSFUL",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"Exchanged **`{val:,} XP`** ➜ **`+{coins_awarded:,} Coins`**! 🪙\n"
                f"{tier_msg}\n\n"
                f"• **Remaining XP:** `{current_xp - val:,} XP`\n"
                f"• **New Coin Wallet:** `{bal_str}`\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"💡 *Spend coins in `#🛒・server-shop` for VIP roles & custom colors!*"
            ),
            color=0x2ECC71
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Currency Exchange Booth", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)


class ConvertCoinsToXPModal(Modal, title="Exchange Coins ➜ Chat XP"):
    amount = TextInput(
        label="Amount of Coins to Exchange (Min: 100)",
        placeholder="e.g., 500 (200 XP), 1000 (500 XP), 2500 (1,500 XP)",
        min_length=1,
        max_length=8,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        try:
            val = int(self.amount.value.strip())
            if val < 100:
                return await interaction.followup.send("❌ Minimum exchange is `100 Coins`.", ephemeral=True)
        except ValueError:
            return await interaction.followup.send("❌ Please enter a valid whole number.", ephemeral=True)

        user_data = get_user_data(interaction.user.id)
        current_coins = user_data.get("coins", 0)

        if current_coins < val and interaction.user.id != OWNER_ID:
            return await interaction.followup.send(
                f"❌ **Insufficient Coins!** You only have `{current_coins:,}` Coins.",
                ephemeral=True
            )

        # Dynamic Tiered Surge: 2500+ -> 0.6x, 1000+ -> 0.5x, below -> 0.4x
        if val >= 2500:
            xp_awarded = int(val * 0.6)
            surge_msg = "🚀 **Mega Level Skip Applied (+250 Bonus XP!)**"
        elif val >= 1000:
            xp_awarded = int(val * 0.5)
            surge_msg = "⚡ **Level Surge Applied (+100 Bonus XP!)**"
        else:
            xp_awarded = int(val * 0.4)
            surge_msg = "✨ **Standard Boost Applied**"

        # Deduct coins (if not owner)
        new_coins = update_user_coins(interaction.user.id, -val)
        bal_str = "∞ (Owner Vault)" if interaction.user.id == OWNER_ID else f"{new_coins:,} Coins"
        # Add XP
        new_xp, new_lvl, _ = await database.add_user_xp(interaction.guild.id, interaction.user.id, xp_awarded)

        embed = discord.Embed(
            title="✨ LEVEL SURGE CONVERSION SUCCESSFUL",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"Converted **`{val:,} Coins`** ➜ **`+{xp_awarded:,} Chat XP`**! ⚡\n"
                f"{surge_msg}\n\n"
                f"• **Current Chat XP:** `{new_xp:,} XP` *(Level {new_lvl})*\n"
                f"• **Remaining Coins:** `{bal_str}`\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"💡 *Use `/rank` to view your updated level card & progress!*"
            ),
            color=0x3498DB
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Level Acceleration Booth", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)


class RedeemPromoModal(Modal, title="Redeem Gift / Voucher Code"):
    code = TextInput(
        label="Enter Promo Code",
        placeholder="e.g., RAIFAM2026, VIPGIFT",
        min_length=3,
        max_length=30,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        code_str = self.code.value.strip().upper()
        data = load_exchange_data()
        codes = data.get("promocodes", {})

        if code_str not in codes:
            return await interaction.followup.send("❌ Invalid or expired promo code.", ephemeral=True)

        promo = codes[code_str]
        claimed_by = promo.setdefault("claimed_by", [])
        uid = interaction.user.id

        if uid in claimed_by and uid != OWNER_ID:
            return await interaction.followup.send("⚠️ You have already redeemed this promo code.", ephemeral=True)

        max_uses = promo.get("max_uses", 0)
        if max_uses > 0 and len(claimed_by) >= max_uses and uid != OWNER_ID:
            return await interaction.followup.send("❌ This promo code has reached its maximum claim limit.", ephemeral=True)

        claimed_by.append(uid)
        save_exchange_data(data)

        reward_type = promo.get("type", "coins")
        reward_value = promo.get("value", 500)

        if reward_type == "coins":
            new_bal = update_user_coins(uid, reward_value)
            bal_str = "∞ (Owner Vault)" if uid == OWNER_ID else f"{new_bal:,} Coins"
            desc = f"🎉 You received **`+{reward_value:,} Coins`**! Your new balance: `{bal_str}` 🪙"
        elif reward_type == "xp":
            new_xp, new_lvl, _ = await database.add_user_xp(interaction.guild.id, uid, reward_value)
            desc = f"⚡ You received **`+{reward_value:,} Chat XP`**! Your XP: `{new_xp:,}` *(Level {new_lvl})*"
        elif reward_type == "role":
            role = interaction.guild.get_role(int(reward_value))
            if role:
                await interaction.user.add_roles(role, reason=f"Redeemed promo code {code_str}")
                desc = f"👑 You unlocked the **{role.name}** exclusive role!"
            else:
                desc = "Perk unlocked!"
        else:
            desc = "Reward claimed!"

        embed = discord.Embed(
            title="🎁 PROMO CODE REDEEMED!",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"Code: **`{code_str}`**\n\n"
                f"{desc}\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"Thank you for being an active part of RAI FAM 💗!"
            ),
            color=0x2ECC71
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Reward Vault", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)


# =====================================================================
# INTERACTIVE EXCHANGE BOOTH VIEW
# =====================================================================
class ExchangeBoothView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="XP ➜ Coins", style=discord.ButtonStyle.success, emoji="💱", custom_id="booth_xp_to_coins", row=0)
    async def xp_to_coins_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ConvertXPToCoinsModal())

    @button(label="Coins ➜ XP", style=discord.ButtonStyle.primary, emoji="⚡", custom_id="booth_coins_to_xp", row=0)
    async def coins_to_xp_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ConvertCoinsToXPModal())

    @button(label="Level Milestones", style=discord.ButtonStyle.secondary, emoji="🏆", custom_id="booth_claim_milestones", row=1)
    async def claim_milestones_btn(self, interaction: discord.Interaction, button: Button):
        user_lvl = await database.get_user_level_data(interaction.guild.id, interaction.user.id)
        level = user_lvl.get("level", 0)

        data = load_exchange_data()
        milestones = data.setdefault("milestones", {})
        claimed = milestones.setdefault(str(interaction.user.id), [])

        claimable = []
        total_coins = 0
        for lvl, bonus in LEVEL_MILESTONES.items():
            if level >= lvl and lvl not in claimed:
                claimable.append(lvl)
                total_coins += bonus

        if not claimable:
            next_lvl = next((lvl for lvl in LEVEL_MILESTONES.keys() if lvl > level), None)
            nxt_str = f"Reach Level {next_lvl} for your next bonus!" if next_lvl else "You have claimed all level milestone rewards!"
            return await interaction.response.send_message(
                f"ℹ️ **No Unclaimed Milestones!** Current Level: **`Level {level}`**.\n{nxt_str}",
                ephemeral=True
            )

        for lvl in claimable:
            claimed.append(lvl)
        save_exchange_data(data)

        new_bal = update_user_coins(interaction.user.id, total_coins)
        bal_str = "∞ (Owner Vault)" if interaction.user.id == OWNER_ID else f"{new_bal:,} Coins"

        embed = discord.Embed(
            title="🏆 LEVEL MILESTONES CLAIMED!",
            description=(
                f"Congratulations {interaction.user.mention}! You claimed bonuses for reaching **Levels {', '.join(map(str, claimable))}**!\n\n"
                f"💰 **Total Bonus Awarded:** `+{total_coins:,}` Coins\n"
                f"👛 **New Wallet Balance:** `{bal_str}`"
            ),
            color=0xF1C40F
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Milestone Achievements", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @button(label="Streak Rewards", style=discord.ButtonStyle.secondary, emoji="🔥", custom_id="booth_claim_streaks", row=1)
    async def claim_streaks_btn(self, interaction: discord.Interaction, button: Button):
        user_data = get_user_data(interaction.user.id)
        streak = user_data.get("streak", 0)

        data = load_exchange_data()
        streak_claims = data.setdefault("streak_claims", {})
        claimed = streak_claims.setdefault(str(interaction.user.id), [])

        claimable = []
        total_coins = 0
        for days, bonus in STREAK_MILESTONES.items():
            if streak >= days and days not in claimed:
                claimable.append(days)
                total_coins += bonus

        if not claimable:
            next_days = next((d for d in STREAK_MILESTONES.keys() if d > streak), None)
            nxt_str = f"Reach a {next_days}-day streak with `/daily` for your next bonus!" if next_days else "You have claimed all streak rewards!"
            return await interaction.response.send_message(
                f"ℹ️ **Current Streak:** `{streak} Days`.\n{nxt_str}",
                ephemeral=True
            )

        for d in claimable:
            claimed.append(d)
        save_exchange_data(data)

        new_bal = update_user_coins(interaction.user.id, total_coins)
        bal_str = "∞ (Owner Vault)" if interaction.user.id == OWNER_ID else f"{new_bal:,} Coins"

        embed = discord.Embed(
            title="🔥 STREAK MILESTONES CLAIMED!",
            description=(
                f"Incredible dedication, {interaction.user.mention}! Claimed bonus for **{', '.join(map(str, claimable))} Days Streak**!\n\n"
                f"💰 **Total Bonus Awarded:** `+{total_coins:,}` Coins\n"
                f"👛 **New Wallet Balance:** `{bal_str}`"
            ),
            color=0xE67E22
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Keep your /daily streak alive!", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @button(label="Lucky Mystery Box (350)", style=discord.ButtonStyle.success, emoji="🎁", custom_id="booth_mystery_box", row=2)
    async def mystery_box_btn(self, interaction: discord.Interaction, button: Button):
        user_data = get_user_data(interaction.user.id)
        current_coins = user_data.get("coins", 0)

        cost = 350
        if current_coins < cost and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(
                f"❌ **Insufficient Coins!** Lucky Mystery Box costs `350 Coins`. You have `{current_coins:,}` Coins.",
                ephemeral=True
            )

        # Deduct cost
        update_user_coins(interaction.user.id, -cost)

        # Random Mystery Roll
        roll = random.randint(1, 100)
        if roll <= 45:
            # Common Coin payout
            payout = random.choice([200, 250, 300, 400, 500])
            update_user_coins(interaction.user.id, payout)
            desc = f"🪙 You opened the box and discovered **`+{payout:,} Coins`**!"
            box_color = 0x3498DB
        elif roll <= 80:
            # XP Surge payout
            xp_payout = random.choice([100, 150, 200, 300])
            await database.add_user_xp(interaction.guild.id, interaction.user.id, xp_payout)
            desc = f"⚡ You opened the box and absorbed an **XP Surge of `+{xp_payout:,} Chat XP`**!"
            box_color = 0x9B5DE5
        elif roll <= 95:
            # Jackpot Coin payout
            jackpot = random.choice([750, 1000, 1500])
            update_user_coins(interaction.user.id, jackpot)
            desc = f"💎 **JACKPOT!** You found a glowing treasure chest with **`+{jackpot:,} Coins`**!"
            box_color = 0xF1C40F
        else:
            # Mega Win: 2,500 Coins or VIP Role Voucher
            mega = 2500
            update_user_coins(interaction.user.id, mega)
            desc = f"🌟 **LEGENDARY DROP!** You unlocked the Golden Vault with **`+{mega:,} Mega Coins`**!"
            box_color = 0xFF69B4

        new_bal = get_user_data(interaction.user.id).get("coins", 0)
        bal_str = "∞ (Owner Vault)" if interaction.user.id == OWNER_ID else f"{new_bal:,} Coins"

        embed = discord.Embed(
            title="🎁 LUCKY MYSTERY BOX UNBOXED!",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"{desc}\n\n"
                f"👛 **Updated Coin Balance:** `{bal_str}`\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"Feeling lucky? Open another box anytime!"
            ),
            color=box_color
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Mystery Fortune Booth", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)


    @button(label="Redeem Promo Code", style=discord.ButtonStyle.secondary, emoji="🎟️", custom_id="booth_redeem_code", row=2)
    async def redeem_code_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(RedeemPromoModal())


# =====================================================================
# MAIN REWARD EXCHANGE COG
# =====================================================================
class RewardExchange(commands.Cog):
    """Dedicated Reward Exchange & Currency Conversion Hub."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="exchange", description="Open the Reward Exchange Booth to convert XP/Coins and claim prizes.")
    async def exchange_command(self, interaction: discord.Interaction):
        user_lvl = await database.get_user_level_data(interaction.guild.id, interaction.user.id)
        user_data = get_user_data(interaction.user.id)

        coins = user_data.get("coins", 0)
        xp = user_lvl.get("xp", 0)
        lvl = user_lvl.get("level", 0)
        streak = user_data.get("streak", 0)

        coin_str = "∞ (Owner Vault)" if interaction.user.id == OWNER_ID else f"{coins:,} Coins"

        embed = discord.Embed(
            title="🎁 RAI FAM 💗 • OFFICIAL REWARD EXCHANGE BOOTH",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"Welcome to the Exchange Booth, {interaction.user.mention}! 🌸\n"
                f"Convert your activity into currency or claim special rewards.\n\n"
                f"📊 **Your Standing:**\n"
                f"• 🪙 **Coin Wallet:** `{coin_str}`\n"
                f"• ⚡ **Chat Activity:** `{xp:,} XP` *(Level {lvl})*\n"
                f"• 🔥 **Daily Streak:** `{streak} Days`\n\n"
                f"### 💱 XP ➜ Coins Tiered Rates:\n"
                f"> • 📦 **Starter:** `100 XP` ➜ `250 Coins` *(2.5x Rate)*\n"
                f"> • 💼 **Pro Trader:** `500 XP` ➜ `1,350 Coins` *(2.7x Rate +100 Bonus)*\n"
                f"> • 💎 **Elite Master:** `1,000 XP` ➜ `3,000 Coins` *(3.0x Mega Rate!)*\n\n"
                f"### ⚡ Coins ➜ XP Level Acceleration:\n"
                f"> • ⚡ **Quick Boost:** `500 Coins` ➜ `200 XP`\n"
                f"> • 🚀 **Level Surge:** `1,000 Coins` ➜ `500 XP` *(+100 Bonus XP)*\n"
                f"> • 👑 **Mega Skip:** `2,500 Coins` ➜ `1,500 XP` *(+250 Bonus XP)*\n\n"
                f"### 🏆 Level & Streak Milestone Payouts:\n"
                f"> • Level 5: `+500c` • Level 10: `+1,500c` • Level 20: `+3,500c` • Level 50: `+10,000c`\n"
                f"> • 3-Day Streak: `+300c` • 7-Day: `+1,000c` • 14-Day: `+2,500c` • 30-Day: `+6,000c`\n\n"
                f"### 🎁 Lucky Mystery Box (`350 Coins`):\n"
                f"> • Win between `200 - 2,500 Coins` or `100 - 300 XP` per roll!\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Click any button below to convert, claim, or test your luck!*"
            ),
            color=0x00F5D4
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else config.RAI_ICON_URL)
        embed.set_footer(text="RAI FAM 💗 • Pure Value & Fair Rewards", icon_url=config.RAI_ICON_URL)

        view = ExchangeBoothView()
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="redeem", description="Directly redeem a server gift code or promo voucher.")
    @app_commands.describe(code="Promo code (e.g., RAIFAM2026)")
    async def redeem_command(self, interaction: discord.Interaction, code: str):
        code_str = code.strip().upper()
        data = load_exchange_data()
        codes = data.get("promocodes", {})

        if code_str not in codes:
            return await interaction.response.send_message("❌ Invalid or expired promo code.", ephemeral=True)

        promo = codes[code_str]
        claimed_by = promo.setdefault("claimed_by", [])
        uid = interaction.user.id

        if uid in claimed_by and uid != OWNER_ID:
            return await interaction.response.send_message("⚠️ You have already redeemed this promo code.", ephemeral=True)

        max_uses = promo.get("max_uses", 0)
        if max_uses > 0 and len(claimed_by) >= max_uses and uid != OWNER_ID:
            return await interaction.response.send_message("❌ This promo code has reached its maximum claim limit.", ephemeral=True)

        claimed_by.append(uid)
        save_exchange_data(data)

        reward_type = promo.get("type", "coins")
        reward_value = promo.get("value", 500)

        if reward_type == "coins":
            new_bal = update_user_coins(uid, reward_value)
            bal_str = "∞ (Owner Vault)" if uid == OWNER_ID else f"{new_bal:,} Coins"
            desc = f"🎉 You received **`+{reward_value:,} Coins`**! Your new balance: `{bal_str}` 🪙"
        elif reward_type == "xp":
            new_xp, new_lvl, _ = await database.add_user_xp(interaction.guild.id, uid, reward_value)
            desc = f"⚡ You received **`+{reward_value:,} Chat XP`**! Your XP: `{new_xp:,}` *(Level {new_lvl})*"
        else:
            desc = "Reward claimed!"

        embed = discord.Embed(
            title="🎁 PROMO CODE REDEEMED!",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"Code: **`{code_str}`**\n\n"
                f"{desc}\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"Thank you for supporting RAI FAM 💗!"
            ),
            color=0x2ECC71
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Reward Vault", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    promocode_group = app_commands.Group(name="promocode", description="Create and manage server promo codes (Admin only)")

    @promocode_group.command(name="create", description="Create a new redeemable promo code.")
    @app_commands.describe(
        code="Unique promo code name",
        reward_type="Type of reward (coins or xp)",
        value="Amount of coins or XP awarded",
        max_uses="Max total claims (0 for unlimited)"
    )
    @app_commands.choices(reward_type=[
        app_commands.Choice(name="Coins 🪙", value="coins"),
        app_commands.Choice(name="Chat XP ⚡", value="xp")
    ])
    async def create_code(
        self,
        interaction: discord.Interaction,
        code: str,
        reward_type: str,
        value: int,
        max_uses: Optional[int] = 0
    ):
        if not interaction.user.guild_permissions.manage_guild and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message("❌ You lack permissions to create promo codes.", ephemeral=True)

        code_clean = code.strip().upper()
        data = load_exchange_data()
        codes = data.setdefault("promocodes", {})

        codes[code_clean] = {
            "type": reward_type,
            "value": value,
            "max_uses": max_uses,
            "created_by": interaction.user.id,
            "created_at": int(time.time()),
            "claimed_by": []
        }
        save_exchange_data(data)

        limit_str = f"{max_uses} claims" if max_uses > 0 else "Unlimited"
        await interaction.response.send_message(
            f"✅ Created promo code **`{code_clean}`**!\n"
            f"• **Reward:** `+{value:,} {reward_type.upper()}`\n"
            f"• **Limit:** `{limit_str}`\n"
            f"Members can redeem it using `/redeem {code_clean}` or in the Exchange Booth!",
            ephemeral=True
        )


async def setup(bot: commands.Bot):
    bot.add_view(ExchangeBoothView())
    await bot.add_cog(RewardExchange(bot))
