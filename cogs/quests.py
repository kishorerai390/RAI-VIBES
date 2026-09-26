import os
import json
import time
import math
import logging
import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import discord
from discord import app_commands
from discord.ext import commands, tasks

import config
from cogs.economy import update_user_coins, get_user_data

logger = logging.getLogger("Quests")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
QUESTS_FILE = DATA_DIR / "quests.json"
LEVELS_FILE = DATA_DIR / "levels.json"

# Quests template with target values and rewards
WEEKLY_QUESTS_DEF = [
    {
        "id": "chat_messages",
        "title": "💬 Apex Conversationalist",
        "desc": "Send 25 messages in community text channels",
        "target": 25,
        "reward_coins": 300,
        "reward_xp": 150,
        "emoji": "💬"
    },
    {
        "id": "voice_minutes",
        "title": "🎙️ Sanctuary Resident",
        "desc": "Spend 45 minutes chilling in any Voice Channel",
        "target": 45,
        "reward_coins": 450,
        "reward_xp": 250,
        "emoji": "🎙️"
    },
    {
        "id": "music_vibes",
        "title": "🎵 Rhythm Connoisseur",
        "desc": "Play or listen to 5 tracks in music voice rooms",
        "target": 5,
        "reward_coins": 250,
        "reward_xp": 120,
        "emoji": "🎵"
    },
    {
        "id": "casino_plays",
        "title": "🪙 Casino Challenger",
        "desc": "Play 3 rounds of coinflip, slots, or dice",
        "target": 3,
        "reward_coins": 350,
        "reward_xp": 180,
        "emoji": "🪙"
    },
    {
        "id": "daily_streak",
        "title": "🔥 Dedicated Vibe Keeper",
        "desc": "Claim your /daily reward at least 2 times this week",
        "target": 2,
        "reward_coins": 400,
        "reward_xp": 200,
        "emoji": "🔥"
    }
]

GRAND_BONUS_COINS = 1000
GRAND_BONUS_XP = 500


def get_current_week_id() -> str:
    """Returns ISO calendar string like '2026-W39'."""
    now = datetime.datetime.now(datetime.timezone.utc)
    year, week, _ = now.isocalendar()
    return f"{year}-W{week}"


def load_quests_data() -> Dict[str, Any]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if QUESTS_FILE.exists():
        try:
            with open(QUESTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_quests_data(data: Dict[str, Any]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(QUESTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_user_quest_progress(guild_id: int, user_id: int) -> dict:
    data = load_quests_data()
    week_id = get_current_week_id()
    gid = str(guild_id)
    uid = str(user_id)

    if gid not in data:
        data[gid] = {}
    if uid not in data[gid] or data[gid][uid].get("week_id") != week_id:
        # Initialize or reset for new week
        data[gid][uid] = {
            "week_id": week_id,
            "progress": {q["id"]: 0 for q in WEEKLY_QUESTS_DEF},
            "claimed": {q["id"]: False for q in WEEKLY_QUESTS_DEF},
            "grand_claimed": False,
            "total_quests_completed": data[gid].get(uid, {}).get("total_quests_completed", 0)
        }
        save_quests_data(data)
    return data[gid][uid]


def update_quest_progress(guild_id: int, user_id: int, quest_id: str, amount: int = 1):
    data = load_quests_data()
    week_id = get_current_week_id()
    gid = str(guild_id)
    uid = str(user_id)

    if gid not in data:
        data[gid] = {}
    if uid not in data[gid] or data[gid][uid].get("week_id") != week_id:
        data[gid][uid] = {
            "week_id": week_id,
            "progress": {q["id"]: 0 for q in WEEKLY_QUESTS_DEF},
            "claimed": {q["id"]: False for q in WEEKLY_QUESTS_DEF},
            "grand_claimed": False,
            "total_quests_completed": data[gid].get(uid, {}).get("total_quests_completed", 0)
        }

    user_data = data[gid][uid]
    curr = user_data["progress"].get(quest_id, 0)
    # Find max target
    q_def = next((q for q in WEEKLY_QUESTS_DEF if q["id"] == quest_id), None)
    if q_def:
        user_data["progress"][quest_id] = min(curr + amount, q_def["target"])
    else:
        user_data["progress"][quest_id] = curr + amount

    save_quests_data(data)


def add_user_xp(guild_id: int, user_id: int, xp_amount: int):
    """Directly awards leveling XP into data/levels.json."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        levels = {}
        if LEVELS_FILE.exists():
            with open(LEVELS_FILE, "r", encoding="utf-8") as f:
                levels = json.load(f)
        gid = str(guild_id)
        uid = str(user_id)
        if gid not in levels:
            levels[gid] = {}
        if uid not in levels[gid]:
            levels[gid][uid] = {"xp": 0, "level": 1, "messages": 0, "voice_minutes": 0}
        levels[gid][uid]["xp"] += xp_amount
        with open(LEVELS_FILE, "w", encoding="utf-8") as f:
            json.dump(levels, f, indent=2)
    except Exception as e:
        logger.debug(f"Could not add quest XP: {e}")


def render_progress_bar(current: int, target: int, length: int = 10) -> str:
    ratio = min(max(current / max(target, 1), 0.0), 1.0)
    filled = int(round(ratio * length))
    empty = length - filled
    percent = int(ratio * 100)
    bar = "▓" * filled + "░" * empty
    return f"`[{bar}]` **{percent}%** ({current}/{target})"


class QuestClaimView(discord.ui.View):
    """Interactive view allowing members to claim completed quests and the Grand Bounty."""
    def __init__(self, guild_id: int, user_id: int):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.user_id = user_id

    @discord.ui.button(label="Claim All Rewards", style=discord.ButtonStyle.success, emoji="🎁", custom_id="quest:claim_all")
    async def claim_all(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This is not your quest board.", ephemeral=True)

        user_data = get_user_quest_progress(self.guild_id, self.user_id)
        data = load_quests_data()
        gid = str(self.guild_id)
        uid = str(self.user_id)

        claimed_coins = 0
        claimed_xp = 0
        claimed_count = 0

        # Check standard quests
        for q in WEEKLY_QUESTS_DEF:
            qid = q["id"]
            progress = user_data["progress"].get(qid, 0)
            is_claimed = user_data["claimed"].get(qid, False)
            if progress >= q["target"] and not is_claimed:
                user_data["claimed"][qid] = True
                claimed_coins += q["reward_coins"]
                claimed_xp += q["reward_xp"]
                claimed_count += 1
                user_data["total_quests_completed"] = user_data.get("total_quests_completed", 0) + 1

        # Check grand bonus
        all_completed = all(user_data["progress"].get(q["id"], 0) >= q["target"] for q in WEEKLY_QUESTS_DEF)
        if all_completed and not user_data.get("grand_claimed", False):
            user_data["grand_claimed"] = True
            claimed_coins += GRAND_BONUS_COINS
            claimed_xp += GRAND_BONUS_XP
            claimed_count += 1

        if claimed_count == 0:
            return await interaction.response.send_message("⚠️ You have no completed, unclaimed quests right now. Keep chatting, listening, and gaming!", ephemeral=True)

        # Award rewards
        data[gid][uid] = user_data
        save_quests_data(data)

        new_balance = update_user_coins(self.user_id, claimed_coins)
        add_user_xp(self.guild_id, self.user_id, claimed_xp)

        embed = discord.Embed(
            title="🎉 QUEST REWARDS CLAIMED!",
            description=(
                f"**Awesome work, {interaction.user.mention}!**\n\n"
                f"• **Coins Earned:** `+{claimed_coins:,}` 🪙\n"
                f"• **XP Earned:** `+{claimed_xp:,}` ✨\n"
                f"• **New Balance:** `{new_balance:,}` Coins\n"
                f"• **Quests Redeemed:** `{claimed_count}`"
            ),
            color=0x00FF88
        )
        embed.set_footer(text="RAI VIBES 💗 Weekly Bounty Board", icon_url=interaction.user.display_avatar.url)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @discord.ui.button(label="Refresh Progress", style=discord.ButtonStyle.secondary, emoji="🔄", custom_id="quest:refresh")
    async def refresh_board(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user_id:
            return await interaction.response.send_message("❌ This is not your quest board.", ephemeral=True)

        user_data = get_user_quest_progress(self.guild_id, self.user_id)
        embed = build_quests_embed(interaction.user, user_data)
        await interaction.response.edit_message(embed=embed, view=self)


def build_quests_embed(user: discord.User, user_data: dict) -> discord.Embed:
    week_id = user_data.get("week_id", get_current_week_id())
    completed_count = 0

    embed = discord.Embed(
        title=f"⚔️ RAI FAM • WEEKLY BOUNTY BOARD ({week_id})",
        description=(
            f"**Welcome to your active weekly quest objectives, {user.mention}!**\n"
            "Complete quests across text, voice, music, and games to earn coins and level XP.\n"
            "Reset occurs every **Monday at 00:00 UTC**."
        ),
        color=0xFF69B4
    )

    for q in WEEKLY_QUESTS_DEF:
        qid = q["id"]
        progress = user_data["progress"].get(qid, 0)
        target = q["target"]
        is_claimed = user_data["claimed"].get(qid, False)
        is_done = progress >= target

        if is_done:
            completed_count += 1
            status_tag = "✅ **[CLAIMED]**" if is_claimed else "🎁 **[READY TO CLAIM]**"
        else:
            status_tag = "⏳ **[IN PROGRESS]**"

        bar = render_progress_bar(progress, target)
        embed.add_field(
            name=f"{q['emoji']} {q['title']} • {status_tag}",
            value=(
                f"{q['desc']}\n"
                f"{bar}\n"
                f"🏆 **Reward:** `{q['reward_coins']}` 🪙 Coins • `{q['reward_xp']}` ✨ XP"
            ),
            inline=False
        )

    # Grand Weekly Bounty
    all_done = completed_count == len(WEEKLY_QUESTS_DEF)
    grand_claimed = user_data.get("grand_claimed", False)
    if grand_claimed:
        grand_status = "👑 **[CLAIMED & MASTERED]**"
    elif all_done:
        grand_status = "🎉 **[UNLOCKED - READY TO CLAIM!]**"
    else:
        grand_status = f"🔒 **[{completed_count}/{len(WEEKLY_QUESTS_DEF)} Quests Completed]**"

    embed.add_field(
        name=f"🌟 GRAND COMPLETIONIST BOUNTY • {grand_status}",
        value=(
            f"Finish all {len(WEEKLY_QUESTS_DEF)} quests in a single week to unlock the motherlode bonus:\n"
            f"🎁 **Bonus Reward:** `+{GRAND_BONUS_COINS:,}` 🪙 Coins • `+{GRAND_BONUS_XP:,}` ✨ XP • Exclusive Profile Renown"
        ),
        inline=False
    )

    embed.set_thumbnail(url=user.display_avatar.url)
    embed.set_footer(text="RAI VIBES 💗 Weekly Quests & Bounties • Keep Vibe Alive", icon_url=getattr(config, "RAI_ICON_URL", ""))
    embed.timestamp = discord.utils.utcnow()
    return embed


class QuestsCog(commands.Cog, name="Quests"):
    """Weekly Bounty & Community Quests Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.msg_cooldowns: Dict[int, float] = {}
        self.vc_active_time: Dict[int, float] = {}
        self.voice_tracker.start()

    def cog_unload(self):
        self.voice_tracker.cancel()

    # Track Voice Channel minutes in background
    @tasks.loop(minutes=2)
    async def voice_tracker(self):
        """Monitors members in voice channels and updates their voice_minutes quest progress."""
        try:
            for guild in self.bot.guilds:
                for vc in guild.voice_channels:
                    # Only reward if at least 2 non-bot members are in voice or active
                    human_members = [m for m in vc.members if not m.bot and not m.voice.afk and not (m.voice.self_deaf or m.voice.deaf)]
                    for m in human_members:
                        update_quest_progress(guild.id, m.id, "voice_minutes", amount=2)
        except Exception as e:
            logger.debug(f"Voice tracker error: {e}")

    @voice_tracker.before_loop
    async def before_voice_tracker(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # 10-second spam throttle per user to prevent micro-spamming
        now = time.time()
        last = self.msg_cooldowns.get(message.author.id, 0)
        if now - last < 8.0:
            return

        self.msg_cooldowns[message.author.id] = now
        update_quest_progress(message.guild.id, message.author.id, "chat_messages", amount=1)

    quests_group = app_commands.Group(name="quests", description="View active weekly quests, progress, and claim rewards.")

    @quests_group.command(name="board", description="Open your personal Weekly Quest & Bounty Board.")
    async def quests_board(self, interaction: discord.Interaction):
        user_data = get_user_quest_progress(interaction.guild_id, interaction.user.id)
        embed = build_quests_embed(interaction.user, user_data)
        view = QuestClaimView(interaction.guild_id, interaction.user.id)
        await interaction.response.send_message(embed=embed, view=view)

    @quests_group.command(name="leaderboard", description="View the top quest completionists in the server.")
    async def quests_leaderboard(self, interaction: discord.Interaction):
        data = load_quests_data()
        gid = str(interaction.guild_id)
        guild_quests = data.get(gid, {})

        if not guild_quests:
            return await interaction.response.send_message("⚔️ No quest completions recorded yet for this server. Start questing with `/quests board`!", ephemeral=True)

        # Sort by total completed quests
        sorted_users = sorted(
            guild_quests.items(),
            key=lambda x: x[1].get("total_quests_completed", 0),
            reverse=True
        )[:10]

        embed = discord.Embed(
            title=f"🏆 Top Quest Champions • {interaction.guild.name}",
            description="**Members with the highest total completed community bounties:**",
            color=0xF1C40F
        )

        ranks = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        desc_lines = []
        for i, (uid_str, udata) in enumerate(sorted_users):
            badge = ranks[i] if i < len(ranks) else f"#{i+1}"
            total = udata.get("total_quests_completed", 0)
            desc_lines.append(f"{badge} <@{uid_str}> — **`{total}` Quests Completed**")

        embed.description = "\n".join(desc_lines) if desc_lines else "No records found."
        embed.set_footer(text="RAI VIBES 💗 Quest Master Hall of Fame", icon_url=getattr(config, "RAI_ICON_URL", ""))
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(QuestsCog(bot))
