import os
import json
import time
import datetime
from pathlib import Path
from typing import Optional, Dict

import discord
from discord.ext import commands
from discord import app_commands

import config
import database
from cogs.economy import get_user_data, OWNER_ID
from cogs.entry_sound import get_user_entry_profile, ENTRY_SOUNDS

DATA_DIR = Path("data")
PROFILES_FILE = DATA_DIR / "profiles.json"

def load_profiles_data() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if PROFILES_FILE.exists():
        try:
            with open(PROFILES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_profiles_data(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PROFILES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_user_bio(user_id: int) -> str:
    data = load_profiles_data()
    return data.get(str(user_id), {}).get("bio", "Vibing in RAI FAM 💗")

def set_user_bio(user_id: int, bio: str):
    data = load_profiles_data()
    data.setdefault(str(user_id), {})["bio"] = bio[:120]
    save_profiles_data(data)

class Profile(commands.Cog):
    """Aesthetic Member Profiles, Showcase Badges & Personal Bio Catchphrases."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="setbio", description="Set your personal bio catchphrase displayed on your profile card.")
    @app_commands.describe(quote="Your personal quote / catchphrase (Max 100 characters)")
    async def setbio_command(self, interaction: discord.Interaction, quote: str):
        clean_quote = quote.strip()[:100]
        set_user_bio(interaction.user.id, clean_quote)

        embed = discord.Embed(
            title="✨ PROFILE BIO UPDATED!",
            description=(
                f"Your new personal bio has been saved:\n\n"
                f"💬 *\"{clean_quote}\"*\n\n"
                f"View your updated status anytime with `/profile`!"
            ),
            color=0x9B5DE5
        )
        embed.set_footer(text="RAI FAM 💗 • Aesthetic Profiles", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="badges", description="Inspect member showcase badges, wallet standing, and audio presence.")
    @app_commands.describe(member="Member whose badges you want to view (Defaults to you)")
    async def badges_command(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        if isinstance(target, discord.User):
            target = interaction.guild.get_member(target.id) or target

        # 1. Economy & Streaks
        user_eco = get_user_data(target.id)
        coins = user_eco.get("coins", 0)
        streak = user_eco.get("streak", 0)
        rep = user_eco.get("rep", 0)
        coin_str = "∞ *(Infinite Vault)*" if target.id == OWNER_ID else f"`{coins:,}` Coins"

        # 2. Level & Chat Activity
        lvl_data = await database.get_user_level_data(interaction.guild.id, target.id)
        xp = lvl_data.get("xp", 0)
        level = lvl_data.get("level", 0)
        rank = lvl_data.get("rank", 1)

        # 3. Audio & Voice Presence
        entry_prof = get_user_entry_profile(target.id)
        eq_in = entry_prof.get("equipped")
        eq_out = entry_prof.get("exit_sound")
        in_sfx = ENTRY_SOUNDS.get(eq_in) if eq_in else None
        out_sfx = ENTRY_SOUNDS.get(eq_out) if eq_out else None
        in_name = f"{in_sfx.get('emoji', '🎵')} {in_sfx.get('name')}" if in_sfx else "🚫 None (Not Set)"
        out_name = f"{out_sfx.get('emoji', '👋')} {out_sfx.get('name')}" if out_sfx else "🚫 None (Not Set)"

        # 4. Badges Calculation
        badges = []
        if target.id == OWNER_ID:
            badges.append("👑 **Server Founder & Owner**")
        if target.guild_permissions.administrator:
            badges.append("🛡️ **Executive Administrator**")
        if target.premium_since:
            badges.append("🚀 **Server Booster**")
        if discord.utils.get(target.roles, name="💎 ┊ 𝐑𝐀𝐈 𝐄𝐋𝐈𝐓𝐄"):
            badges.append("💎 **VIP Elite Prestige**")
        if discord.utils.get(target.roles, name="🎧 ✧ 𝐃𝐉"):
            badges.append("🎧 **Master DJ**")
        if streak >= 7:
            badges.append(f"🔥 **{streak}-Day Streak Champion**")
        if level >= 20:
            badges.append(f"⭐ **Level {level} Veteran**")
        if coins >= 10000 or target.id == OWNER_ID:
            badges.append("🪙 **High Roller**")
        if not badges:
            badges.append("🌸 **RAI Family Member**")

        # 5. Join Date & Bio
        bio = get_user_bio(target.id)
        join_str = target.joined_at.strftime("%B %d, %Y") if hasattr(target, "joined_at") and target.joined_at else "Recently"

        embed = discord.Embed(
            title=f"🌸 ✦ {target.display_name.upper()}'S PROFILE ✦ 🌸",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"💬 *\"{bio}\"*\n\n"
                f"### 📊 Community Stats:\n"
                f"> • ⭐ **Chat Standing:** Level `{level}` • Rank `#{rank}` • `{xp:,} XP`\n"
                f"> • 🪙 **Economy Vault:** {coin_str}\n"
                f"> • 🔥 **Daily Streak:** `{streak}` Days • ⭐ **Reputation:** `{rep}` Points\n"
                f"> • 📅 **Joined Server:** `{join_str}`\n\n"
                f"### 🔊 Voice Audio Presence:\n"
                f"> • 🎵 **Entrance Theme:** {in_name}\n"
                f"> • 🚪 **Exit Goodbye:** {out_name}\n\n"
                f"### 🏅 Showcase Badges:\n"
                f"> " + "\n> ".join(badges) + "\n\n"
                f"✦ ───────────────────────────────────── ✦"
            ),
            color=0xFF69B4
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        if hasattr(target, "banner") and target.banner:
            embed.set_image(url=target.banner.url)
        embed.set_footer(text="RAI FAM 💗 • Use /setbio to personalize your profile", icon_url=config.RAI_ICON_URL)

        await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(Profile(bot))
