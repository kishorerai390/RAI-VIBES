import os
import sys
import json
import time
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

XP_TO_COIN_RATE = 2.0  # 1 XP = 2 Coins
COIN_TO_XP_RATE = 0.4  # 1 Coin = 0.4 XP (e.g. 500 Coins = 200 XP)

LEVEL_MILESTONES = {
    5: 500,
    10: 1500,
    20: 3500,
    50: 10000
}


def load_exchange_data() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if EXCHANGE_FILE.exists():
        try:
            with open(EXCHANGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"promocodes": {}, "milestones": {}}
    return {"promocodes": {}, "milestones": {}}


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
        placeholder="e.g., 100, 250, 500",
        min_length=1,
        max_length=6,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.amount.value.strip())
            if val < 50:
                return await interaction.response.send_message("❌ Minimum exchange is `50 XP`.", ephemeral=True)
        except ValueError:
            return await interaction.response.send_message("❌ Please enter a valid whole number.", ephemeral=True)

        user_lvl = await database.get_user_level_data(interaction.guild.id, interaction.user.id)
        current_xp = user_lvl.get("xp", 0)

        if current_xp < val:
            return await interaction.response.send_message(
                f"❌ **Insufficient XP!** You only have `{current_xp:,} XP`, cannot exchange `{val:,} XP`.",
                ephemeral=True
            )

        coins_awarded = int(val * XP_TO_COIN_RATE)
        # Deduct XP
        await database.add_user_xp(interaction.guild.id, interaction.user.id, -val)
        # Credit Coins
        new_coins = update_user_coins(interaction.user.id, coins_awarded)

        embed = discord.Embed(
            title="💱 REWARD EXCHANGE SUCCESSFUL",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"Successfully exchanged **`{val:,} XP`** ➜ **`+{coins_awarded:,} Coins`**! 🪙\n\n"
                f"• **Remaining XP:** `{current_xp - val:,} XP`\n"
                f"• **New Coin Wallet:** `{new_coins:,}` Coins\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"💡 *Spend your coins in `#🛒・server-shop` for VIP roles & custom colors!*"
            ),
            color=0x2ECC71
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Currency Exchange Booth", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class ConvertCoinsToXPModal(Modal, title="Exchange Coins ➜ Chat XP"):
    amount = TextInput(
        label="Amount of Coins to Exchange (Min: 100)",
        placeholder="e.g., 250, 500, 1000",
        min_length=1,
        max_length=8,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.amount.value.strip())
            if val < 100:
                return await interaction.response.send_message("❌ Minimum exchange is `100 Coins`.", ephemeral=True)
        except ValueError:
            return await interaction.response.send_message("❌ Please enter a valid whole number.", ephemeral=True)

        user_data = get_user_data(interaction.user.id)
        current_coins = user_data.get("coins", 0)

        if current_coins < val and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(
                f"❌ **Insufficient Coins!** You only have `{current_coins:,}` Coins.",
                ephemeral=True
            )

        xp_awarded = int(val * COIN_TO_XP_RATE)
        # Deduct coins (if not owner)
        new_coins = update_user_coins(interaction.user.id, -val)
        # Add XP
        new_xp, new_lvl, leveled = await database.add_user_xp(interaction.guild.id, interaction.user.id, xp_awarded)

        embed = discord.Embed(
            title="✨ XP CONVERSION SUCCESSFUL",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"Successfully converted **`{val:,} Coins`** ➜ **`+{xp_awarded:,} Chat XP`**! ⚡\n\n"
                f"• **Current Chat XP:** `{new_xp:,} XP` *(Level {new_lvl})*\n"
                f"• **Remaining Coins:** `{new_coins:,}` Coins\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"💡 *Use `/rank` to inspect your updated level card!*"
            ),
            color=0x3498DB
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Level Acceleration Booth", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)


class RedeemPromoModal(Modal, title="Redeem Gift / Voucher Code"):
    code = TextInput(
        label="Enter Promo Code",
        placeholder="e.g., RAIFAM2026, VIPGIFT",
        min_length=3,
        max_length=30,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        code_str = self.code.value.strip().upper()
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
            desc = f"🎉 You received **`+{reward_value:,} Coins`**! Your new balance: `{new_bal:,}` Coins 🪙"
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
        await interaction.response.send_message(embed=embed, ephemeral=True)


# =====================================================================
# INTERACTIVE EXCHANGE BOOTH VIEW
# =====================================================================
class ExchangeBoothView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Exchange XP ➜ Coins", style=discord.ButtonStyle.success, emoji="💱", custom_id="booth_xp_to_coins", row=0)
    async def xp_to_coins_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ConvertXPToCoinsModal())

    @button(label="Exchange Coins ➜ XP", style=discord.ButtonStyle.primary, emoji="🪙", custom_id="booth_coins_to_xp", row=0)
    async def coins_to_xp_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(ConvertCoinsToXPModal())

    @button(label="Claim Milestones", style=discord.ButtonStyle.secondary, emoji="🏆", custom_id="booth_claim_milestones", row=1)
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

        embed = discord.Embed(
            title="🏆 MILESTONES CLAIMED!",
            description=(
                f"Congratulations {interaction.user.mention}! You claimed bonuses for reaching **Levels {', '.join(map(str, claimable))}**!\n\n"
                f"💰 **Total Bonus Awarded:** `+{total_coins:,}` Coins\n"
                f"👛 **New Wallet Balance:** `{new_bal:,}` Coins"
            ),
            color=0xF1C40F
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Milestone Achievements", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @button(label="Redeem Code", style=discord.ButtonStyle.secondary, emoji="🎁", custom_id="booth_redeem_code", row=1)
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

        coin_str = "∞ (Owner Vault)" if interaction.user.id == OWNER_ID else f"{coins:,} Coins"

        embed = discord.Embed(
            title="🎁 RAI FAM 💗 • OFFICIAL REWARD EXCHANGE BOOTH",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"Welcome to the Exchange Booth, {interaction.user.mention}! 🌸\n"
                f"Convert your activity into currency or redeem special gift vouchers.\n\n"
                f"📊 **Your Standing:**\n"
                f"• 🪙 **Coin Wallet:** `{coin_str}`\n"
                f"• ⚡ **Chat Activity:** `{xp:,} XP` *(Level {lvl})*\n\n"
                f"💱 **Current Exchange Rates:**\n"
                f"• **XP ➜ Coins:** `100 XP = 200 Coins` (2.0x Rate)\n"
                f"• **Coins ➜ XP:** `500 Coins = 200 XP` (Boost your Level!)\n\n"
                f"🏆 **Milestone Rewards:**\n"
                f"• Level 5: `+500 Coins` • Level 10: `+1,500 Coins`\n"
                f"• Level 20: `+3,500 Coins` • Level 50: `+10,000 Coins`\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Click the buttons below to convert currency or enter a promo code!*"
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
            desc = f"🎉 You received **`+{reward_value:,} Coins`**! Your new balance: `{new_bal:,}` Coins 🪙"
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
