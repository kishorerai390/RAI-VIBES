import os
import json
import time
import random
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, button

import config
from cogs.economy import get_user_data, update_user_coins, save_economy, load_economy
from cogs.casino import get_coins, add_coins

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SPINS_FILE = DATA_DIR / "spins.json"


class ArcadeStationView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Claim Daily", emoji="🪙", style=discord.ButtonStyle.success, custom_id="arcade_station_daily")
    async def claim_daily(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        u_data = get_user_data(user_id)

        now = int(time.time())
        last_daily = u_data.get("last_daily", 0)
        cooldown = 72000  # 20 hours

        if now - last_daily < cooldown:
            ready_ts = last_daily + cooldown
            return await interaction.followup.send(
                f"⏳ You have already claimed your daily bonus!\nNext claim available <t:{ready_ts}:R> (<t:{ready_ts}:t>).",
                ephemeral=True
            )

        # Calculate streak
        streak = u_data.get("streak", 0)
        if now - last_daily > (36 * 3600):
            streak = 1
        else:
            streak += 1

        base_reward = 500
        streak_bonus = min(streak * 25, 500)
        total = base_reward + streak_bonus

        # Update economy
        data = load_economy()
        uid = str(user_id)
        if uid not in data:
            data[uid] = {"coins": 200, "last_daily": 0, "streak": 0}
        data[uid]["coins"] = data[uid].get("coins", 0) + total
        data[uid]["last_daily"] = now
        data[uid]["streak"] = streak
        save_economy(data)

        embed = discord.Embed(
            title="🪙 ✦ DAILY BONUS CLAIMED! ✦",
            description=(
                f"🎉 **+{total:,} Coins** added to your wallet!\n\n"
                f"🔥 **Daily Streak:** `{streak} Day(s)` *(+{streak_bonus} bonus)*\n"
                f"💰 **Total Balance:** `{data[uid]['coins']:,} Coins`"
            ),
            color=0x2ECC71
        )
        embed.set_footer(text="RAI VIBES Arcade • Come back in 20h for your next streak bonus!")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @button(label="Lucky Wheel Spin", emoji="🎰", style=discord.ButtonStyle.primary, custom_id="arcade_station_spin")
    async def spin_wheel(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        now = int(time.time())
        cooldown = 64800  # 18 hours

        spins_data = {}
        if SPINS_FILE.exists():
            try:
                with open(SPINS_FILE, "r", encoding="utf-8") as f:
                    spins_data = json.load(f)
            except Exception:
                pass

        last_spin = spins_data.get(str(user_id), 0)
        if now - last_spin < cooldown:
            next_ts = last_spin + cooldown
            return await interaction.followup.send(
                f"⏳ Lucky Wheel is on cooldown! Next free spin available <t:{next_ts}:R>.",
                ephemeral=True
            )

        spins_data[str(user_id)] = now
        try:
            with open(SPINS_FILE, "w", encoding="utf-8") as f:
                json.dump(spins_data, f, indent=2)
        except Exception:
            pass

        TIERS = [
            ("🍒", 150, "Cherry Nibble", 0xFF6B81, 35),
            ("🍋", 300, "Lemon Zest", 0xFFA502, 25),
            ("🍇", 600, "Grape Rush", 0x9B59B6, 20),
            ("🔔", 1200, "Golden Bell", 0x00FFCC, 12),
            ("💎", 3000, "Diamond Rush", 0x00D2D3, 6),
            ("👑", 10000, "ROYAL JACKPOT", 0xFFD700, 2),
        ]
        weights = [t[4] for t in TIERS]
        chosen = random.choices(TIERS, weights=weights, k=1)[0]
        emoji, payout, name, color, _ = chosen

        add_coins(user_id, payout)
        new_balance = get_coins(user_id)

        embed = discord.Embed(
            title="🎰 ✦ LUCKY WHEEL RESULT ✦",
            description=(
                f"🎯 The wheel landed on: **{emoji} {name}**!\n\n"
                f"🎁 **Payout:** `+{payout:,} Coins`\n"
                f"💳 **New Balance:** `{new_balance:,} Coins`\n\n"
                f"{'🔥 **LEGENDARY HIT!**' if payout >= 3000 else '✨ Nice spin!'}"
            ),
            color=color
        )
        embed.set_footer(text="RAI VIBES Casino • Next spin in 18 hours")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @button(label="My Wallet & Stats", emoji="💳", style=discord.ButtonStyle.secondary, custom_id="arcade_station_wallet")
    async def my_wallet(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        user_id = interaction.user.id
        eco_data = get_user_data(user_id)
        coins = get_coins(user_id)
        streak = eco_data.get("streak", 0)

        embed = discord.Embed(
            title=f"💳 {interaction.user.display_name}'s Financial Profile",
            description=(
                f"💰 **Total Coins:** `{coins:,} Coins`\n"
                f"🔥 **Daily Streak:** `{streak} Day(s)`\n\n"
                f"💡 *Play casino games (/slots, /coinflip, /dice) or claim daily bonuses to grow your wallet!*"
            ),
            color=0x00FFCC
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Economy", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @button(label="Match Squad (LFG)", emoji="🎮", style=discord.ButtonStyle.secondary, custom_id="arcade_station_lfg")
    async def match_squad(self, interaction: discord.Interaction, btn: Button):
        lfg_chan = discord.utils.get(interaction.guild.text_channels, name="🎮｜ʟꜰɢ-ᴍᴀᴛᴄʜᴍᴀᴋɪɴɢ")
        dest = lfg_chan.mention if lfg_chan else "the gaming area"
        await interaction.response.send_message(
            f"🎯 Ready to play? Jump into {dest} to launch 1-click squad alerts for **Free Fire**, **BGMI**, and **GTA RP**!",
            ephemeral=True
        )


class ArcadePanelCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="postarcadepanel", description="Post the persistent 1-Click Arcade & Economy station.")
    @commands.has_permissions(administrator=True)
    async def post_arcade_panel(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 ✦ RAI VIBES ARCADE & ECONOMY STATION ✦ 🪙",
            description=(
                "Welcome to the **1-Click Quick Arcade**! Tap below to manage coins, claim streak rewards, and test your luck instantly with zero typing needed:\n\n"
                "> 🪙 **Claim Daily Bonus:** Collect your daily stipend & maintain your multiplier streak.\n"
                "> 🎰 **Lucky Wheel Spin:** Spin the free 18h Wheel of Fortune for jackpots up to 10,000 coins!\n"
                "> 💳 **My Wallet & Stats:** Check your liquid coin balance and gaming statistics.\n"
                "> 🎮 **Match Squad (LFG):** Find active teammates for Free Fire, BGMI, and GTA RP."
            ),
            color=0x9B5DE5
        )
        embed.set_image(url="https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=1000&auto=format&fit=crop")
        embed.set_footer(text="RAI FAM 💗 • 24/7 Autonomous Arcade Engine", icon_url=config.RAI_ICON_URL)
        await interaction.channel.send(embed=embed, view=ArcadeStationView())
        await interaction.response.send_message("✅ Arcade Station panel posted!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(ArcadePanelCog(bot))
