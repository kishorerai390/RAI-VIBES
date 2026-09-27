import os
import json
import time
import math
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

import config
from cogs.economy import update_user_coins, get_user_data

logger = logging.getLogger("BattlePass")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
BP_FILE = DATA_DIR / "battlepass.json"

SEASON_NAME = "Season 1: Apex Cyberpunk"
XP_PER_TIER = 500
MAX_TIER = 30

TIER_REWARDS = {
    1: {"coins": 200, "title": None, "badge": "🔰 Novice"},
    5: {"coins": 500, "title": "Neon Initiate", "badge": "⚡ Spark"},
    10: {"coins": 1000, "title": "Grid Phantom", "badge": "👾 Cyber Runner"},
    15: {"coins": 2000, "title": "Overclocked", "badge": "🚀 Pulse"},
    20: {"coins": 3500, "title": "Apex Vanguard", "badge": "🛡️ Vanguard"},
    25: {"coins": 5000, "title": "Night City Legend", "badge": "🔥 Legend"},
    30: {"coins": 10000, "title": "★ CYBER OVERLORD ★", "badge": "👑 Overlord"}
}

def load_bp() -> Dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if BP_FILE.exists():
        try:
            with open(BP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_bp(data: Dict[str, Any]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(BP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_user_bp(user_id: int) -> dict:
    data = load_bp()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "xp": 0,
            "claimed_tiers": [],
            "last_msg_time": 0,
            "titles": []
        }
        save_bp(data)
    return data[uid]

def add_bp_xp(user_id: int, amount: int) -> int:
    data = load_bp()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {
            "xp": 0,
            "claimed_tiers": [],
            "last_msg_time": 0,
            "titles": []
        }
    data[uid]["xp"] = data[uid].get("xp", 0) + amount
    save_bp(data)
    return data[uid]["xp"]

def render_progress_bar(current: int, total: int, length: int = 12) -> str:
    fraction = min(1.0, max(0.0, current / total if total > 0 else 0))
    filled = int(fraction * length)
    empty = length - filled
    return "▰" * filled + "▱" * empty


class BattlePassView(discord.ui.View):
    def __init__(self, cog, user_id: int):
        super().__init__(timeout=60)
        self.cog = cog
        self.user_id = user_id

    @discord.ui.button(label="Claim Rewards 🎁", style=discord.ButtonStyle.success, emoji="🎟️")
    async def claim_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This is not your Battle Pass deck.", ephemeral=True)

        user_data = get_user_bp(self.user_id)
        current_xp = user_data.get("xp", 0)
        current_tier = min(MAX_TIER, current_xp // XP_PER_TIER)
        claimed = set(user_data.get("claimed_tiers", []))

        unclaimed_tiers = [t for t in TIER_REWARDS if t <= current_tier and t not in claimed]
        if not unclaimed_tiers:
            return await interaction.response.send_message("ℹ️ You have no pending rewards to claim. Level up to unlock more!", ephemeral=True)

        total_coins = 0
        new_titles = []
        for t in unclaimed_tiers:
            reward = TIER_REWARDS[t]
            total_coins += reward.get("coins", 0)
            if reward.get("title"):
                new_titles.append(reward["title"])
            claimed.add(t)

        user_data["claimed_tiers"] = sorted(list(claimed))
        if new_titles:
            user_data["titles"] = list(set(user_data.get("titles", []) + new_titles))

        data = load_bp()
        data[str(self.user_id)] = user_data
        save_bp(data)

        if total_coins > 0:
            update_user_coins(self.user_id, total_coins)

        title_msg = f"\n🎖️ **New Titles Unlocked:** {', '.join(f'`[{t}]`' for t in new_titles)}" if new_titles else ""
        await interaction.response.send_message(
            f"🎉 **Battle Pass Rewards Claimed!**\n"
            f"• Claimed Tiers: {', '.join(f'`Tier {t}`' for t in unclaimed_tiers)}\n"
            f"• 🪙 **+{total_coins:,} Coins credited!**{title_msg}",
            ephemeral=True
        )


class BattlePass(commands.Cog):
    """Seasonal Battle Pass & Progression System for RAI ARCADE."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
        now = time.time()
        uid = str(message.author.id)
        data = load_bp()
        user_info = data.get(uid, {})
        last_time = user_info.get("last_msg_time", 0)

        # Grant 5 BP XP per message with 30s cooldown
        if now - last_time >= 30:
            user_info["last_msg_time"] = now
            user_info["xp"] = user_info.get("xp", 0) + 5
            data[uid] = user_info
            save_bp(data)

    @app_commands.command(name="battlepass", description="View your Seasonal Battle Pass progress and claim tier rewards.")
    async def battlepass_cmd(self, interaction: discord.Interaction):
        user_data = get_user_bp(interaction.user.id)
        xp = user_data.get("xp", 0)
        current_tier = min(MAX_TIER, xp // XP_PER_TIER)
        tier_xp = xp % XP_PER_TIER if current_tier < MAX_TIER else XP_PER_TIER
        bar = render_progress_bar(tier_xp, XP_PER_TIER, length=14)

        next_milestone = next((t for t in sorted(TIER_REWARDS.keys()) if t > current_tier), None)
        if next_milestone:
            next_reward = TIER_REWARDS[next_milestone]
            next_text = f"**Tier {next_milestone}:** `+{next_reward['coins']:,} Coins`"
            if next_reward.get("title"):
                next_text += f" + Title `[{next_reward['title']}]`"
        else:
            next_text = "🏆 **MAX TIER REACHED!**"

        claimed = set(user_data.get("claimed_tiers", []))
        unclaimed_count = len([t for t in TIER_REWARDS if t <= current_tier and t not in claimed])

        embed = discord.Embed(
            title=f"🎟️ ┊ {SEASON_NAME.upper()}",
            description=(
                f"### ⚡ **Operative:** {interaction.user.mention}\n\n"
                f"**Current Rank:** `Tier {current_tier} / {MAX_TIER}`\n"
                f"**XP Progress:** `[{tier_xp} / {XP_PER_TIER} XP]`\n"
                f"`{bar}`\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"🎯 **Next Milestone Reward:**\n{next_text}\n\n"
                f"🎁 **Unclaimed Rewards:** `{unclaimed_count} tier(s) ready to claim`\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"*Earn BP XP by chatting, spending time in voice lounges, and winning mini-games!*"
            ),
            color=0x00FFCC
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI ARCADE • Seasonal Battle Pass Engine", icon_url=getattr(config, "RAI_ICON_URL", None))

        view = BattlePassView(self, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="bpleaderboard", description="View the top Battle Pass rank leaders in the server.")
    async def bp_leaderboard_cmd(self, interaction: discord.Interaction):
        data = load_bp()
        sorted_users = sorted(data.items(), key=lambda x: x[1].get("xp", 0), reverse=True)[:10]

        if not sorted_users:
            return await interaction.response.send_message("ℹ️ No Battle Pass data recorded yet.", ephemeral=True)

        lines = []
        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        for idx, (uid, uinfo) in enumerate(sorted_users):
            m = medals[idx] if idx < len(medals) else f"`#{idx+1}`"
            xp = uinfo.get("xp", 0)
            tier = min(MAX_TIER, xp // XP_PER_TIER)
            lines.append(f"{m} <@{uid}> — **Tier {tier}** `({xp:,} XP)`")

        embed = discord.Embed(
            title=f"🏆 ┊ BATTLE PASS LEADERBOARD • {SEASON_NAME}",
            description="\n".join(lines),
            color=0xFFD700
        )
        embed.set_footer(text="RAI ARCADE • Battle Pass Top Grinders", icon_url=getattr(config, "RAI_ICON_URL", None))
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(BattlePass(bot))
