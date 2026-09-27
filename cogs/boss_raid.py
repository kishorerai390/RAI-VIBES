import os
import json
import time
import math
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

import config
from cogs.economy import update_user_coins, get_user_data
from cogs.battlepass import add_bp_xp

logger = logging.getLogger("BossRaid")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
RAID_FILE = DATA_DIR / "boss_raid.json"

DEFAULT_BOSSES = [
    {"name": "Titan Voidreaver", "hp": 50000, "emoji": "🐉", "reward": 25000, "color": 0x9B59B6},
    {"name": "Mecha Behemoth X-9", "hp": 60000, "emoji": "🤖", "reward": 30000, "color": 0xE74C3C},
    {"name": "Abyssal Dreadnought", "hp": 45000, "emoji": "🦑", "reward": 20000, "color": 0x1ABC9C},
    {"name": "Infernal Dragon Lord", "hp": 75000, "emoji": "🔥", "reward": 40000, "color": 0xE67E22}
]

def load_raid() -> Dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if RAID_FILE.exists():
        try:
            with open(RAID_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_raid(data: Dict[str, Any]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(RAID_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def render_hp_bar(current: int, total: int, length: int = 15) -> str:
    fraction = min(1.0, max(0.0, current / total if total > 0 else 0))
    filled = int(fraction * length)
    empty = length - filled
    return "🟥" * filled + "⬛" * empty


class BossRaid(commands.Cog):
    """Community Co-Op Server Boss Raids for RAI ARCADE."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.user_cooldowns: Dict[int, float] = {}

    def get_or_create_raid(self) -> dict:
        data = load_raid()
        now = time.time()
        raid = data.get("current_raid")
        if not raid or raid.get("current_hp", 0) <= 0 or (now - raid.get("started_at", 0) > 86400):
            boss = random.choice(DEFAULT_BOSSES)
            raid = {
                "name": boss["name"],
                "max_hp": boss["hp"],
                "current_hp": boss["hp"],
                "emoji": boss["emoji"],
                "reward_pool": boss["reward"],
                "color": boss["color"],
                "started_at": now,
                "contributors": {}  # uid: total_dmg
            }
            data["current_raid"] = raid
            save_raid(data)
        return raid

    @app_commands.command(name="raid", description="View current server Co-Op Boss Raid status.")
    async def raid_status(self, interaction: discord.Interaction):
        raid = self.get_or_create_raid()
        curr_hp = raid["current_hp"]
        max_hp = raid["max_hp"]
        pct = (curr_hp / max_hp) * 100
        bar = render_hp_bar(curr_hp, max_hp, length=12)

        sorted_contrib = sorted(raid.get("contributors", {}).items(), key=lambda x: x[1], reverse=True)[:5]
        top_lines = []
        for idx, (uid, dmg) in enumerate(sorted_contrib, 1):
            top_lines.append(f"`#{idx}` <@{uid}> — **{dmg:,} DMG**")
        top_text = "\n".join(top_lines) if top_lines else "*No strikes recorded yet. Be the first to strike!*"

        embed = discord.Embed(
            title=f"⚔️ ┊ CO-OP BOSS RAID: {raid['emoji']} {raid['name'].upper()}",
            description=(
                f"### 🛡️ **Boss Health:** `{curr_hp:,} / {max_hp:,} HP` ({pct:.1f}%)\n"
                f"{bar}\n\n"
                f"💰 **Total Bounty Pool:** `🪙 {raid['reward_pool']:,} Coins`\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"**🏆 Top Damage Dealers:**\n{top_text}\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"⚔️ Use `/attack` to deal damage and `/heal` to support the raid!"
            ),
            color=raid.get("color", 0x9B59B6)
        )
        embed.set_footer(text="RAI ARCADE • Server Co-Op Raid Engine", icon_url=getattr(config, "RAI_ICON_URL", None))
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="attack", description="Strike the active Raid Boss to deal damage and earn coins & Battle Pass XP.")
    async def raid_attack(self, interaction: discord.Interaction):
        uid = interaction.user.id
        now = time.time()
        last_attack = self.user_cooldowns.get(uid, 0)
        cooldown = 25  # 25 seconds cooldown

        if now - last_attack < cooldown:
            rem = int(cooldown - (now - last_attack))
            return await interaction.response.send_message(f"⏳ **Weapon Cooldown:** Catch your breath! Ready to attack again in `{rem}s`.", ephemeral=True)

        self.user_cooldowns[uid] = now
        data = load_raid()
        raid = data.get("current_raid")
        if not raid or raid.get("current_hp", 0) <= 0:
            raid = self.get_or_create_raid()
            data["current_raid"] = raid

        # Calculate damage: Base 150-350 with 25% crit chance (2x)
        is_crit = random.random() < 0.25
        base_dmg = random.randint(150, 350)
        dmg = base_dmg * 2 if is_crit else base_dmg

        raid["current_hp"] = max(0, raid["current_hp"] - dmg)
        str_uid = str(uid)
        raid["contributors"][str_uid] = raid["contributors"].get(str_uid, 0) + dmg

        # Instant reward: 20-50 coins + 25 BP XP
        coin_earn = random.randint(20, 50)
        update_user_coins(uid, coin_earn)
        add_bp_xp(uid, 25)

        crit_text = "💥 **CRITICAL HIT!**" if is_crit else "⚔️ **Direct Strike!**"

        if raid["current_hp"] <= 0:
            # Boss defeated!
            save_raid(data)
            reward_pool = raid["reward_pool"]
            total_dmg = sum(raid["contributors"].values()) or 1

            payout_lines = []
            for contributor_id, dealt in sorted(raid["contributors"].items(), key=lambda x: x[1], reverse=True)[:5]:
                share_pct = dealt / total_dmg
                payout = int(reward_pool * share_pct)
                update_user_coins(int(contributor_id), payout)
                add_bp_xp(int(contributor_id), 250)
                payout_lines.append(f"• <@{contributor_id}> dealt **{dealt:,} DMG** ➔ `+{payout:,} Coins` + `250 BP XP`")

            # Reset raid
            data["current_raid"] = None
            save_raid(data)

            embed = discord.Embed(
                title=f"🎉 ┊ RAID BOSS SLAIN: {raid['name'].upper()} DEFEATED!",
                description=(
                    f"{crit_text} {interaction.user.mention} dealt the final death blow of **{dmg:,} DMG**!\n\n"
                    f"🏆 **Bounty Distribution:**\n" + "\n".join(payout_lines) + "\n\n"
                    f"✨ A new boss will awaken soon!"
                ),
                color=0x2ECC71
            )
            embed.set_footer(text="RAI ARCADE • Victory Achieved", icon_url=getattr(config, "RAI_ICON_URL", None))
            return await interaction.response.send_message(embed=embed)

        save_raid(data)
        rem_hp = raid["current_hp"]
        pct = (rem_hp / raid["max_hp"]) * 100

        await interaction.response.send_message(
            f"{crit_text} You struck **{raid['name']}** for **`{dmg:,} DMG`**!\n"
            f"• 🪙 Earned `+{coin_earn} Coins` & `+25 BP XP`\n"
            f"• 🩸 Boss HP: `{rem_hp:,} / {raid['max_hp']:,}` ({pct:.1f}%)"
        )

    @app_commands.command(name="heal", description="Support the raid party with shield reinforcement.")
    async def raid_heal(self, interaction: discord.Interaction):
        uid = interaction.user.id
        now = time.time()
        last_act = self.user_cooldowns.get(uid, 0)
        cooldown = 30

        if now - last_act < cooldown:
            rem = int(cooldown - (now - last_act))
            return await interaction.response.send_message(f"⏳ **Cooldown:** Spell ready in `{rem}s`.", ephemeral=True)

        self.user_cooldowns[uid] = now
        coins = random.randint(15, 35)
        update_user_coins(uid, coins)
        add_bp_xp(uid, 20)

        await interaction.response.send_message(
            f"🛡️ {interaction.user.mention} deployed a **Raid Defense Ward**!\n"
            f"• Party shields bolstered!\n"
            f"• 🪙 Earned `+{coins} Coins` & `+20 BP XP` support bonus."
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(BossRaid(bot))
