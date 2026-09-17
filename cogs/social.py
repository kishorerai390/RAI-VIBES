import os
import json
import time
import random
import logging
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

import config

logger = logging.getLogger("Social")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
REP_FILE = DATA_DIR / "reputation.json"

# Curated, verified friendship and anime expression GIFs
ACTION_GIFS = {
    "hug": [
        "https://media.giphy.com/media/od5H3PmEG5EVq/giphy.gif"
    ],
    "pat": [
        "https://media.giphy.com/media/5tmRHwTlHAA9WkV3NT/giphy.gif",
        "https://media.giphy.com/media/ARSp9T7wwxNcs/giphy.gif",
        "https://media.giphy.com/media/L2z7dnOduqEow/giphy.gif"
    ],
    "slap": [
        "https://media.tenor.com/Ws6Dm1ZW_vMAAAAC/anime-slap.gif",
        "https://media1.tenor.com/m/Ws6Dm1ZW_vMAAAAC/anime-slap.gif"
    ],
    "highfive": [
        "https://media.giphy.com/media/nx8GZtJKkgqVG/giphy.gif"
    ],
    "fistbump": [
        "https://media.giphy.com/media/pHb82xtBPfqEg/giphy.gif"
    ],
    "cheers": [
        "https://media.giphy.com/media/Zw3oBUuIg23EWvdvWK/giphy.gif",
        "https://media.giphy.com/media/8Iv5lqKwKsZ2g/giphy.gif",
        "https://media.giphy.com/media/BPJmthQ3YRwD6QqcVD/giphy.gif"
    ],
    "poke": [
        "https://media.giphy.com/media/pWd3OvOGq1Tx8S0WNP/giphy.gif",
        "https://media.giphy.com/media/44xXqOpSV01c4/giphy.gif"
    ]
}


def load_rep_data() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if REP_FILE.exists():
        try:
            with open(REP_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_rep_data(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(REP_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_rep_badge(points: int) -> str:
    if points >= 100:
        return "💎 **Server Legend**"
    elif points >= 50:
        return "🥇 **Community Pillar**"
    elif points >= 25:
        return "🥈 **Respected Peer**"
    elif points >= 10:
        return "🥉 **Helpful Member**"
    elif points >= 1:
        return "⭐ **Friendly Contributor**"
    return "🌱 **Newcomer**"


class Social(commands.Cog):
    """Wholesome Social Expressions, Friendship Actions & Community Reputation."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # -------------------------------------------------------------
    # 🌟 REPUTATION SYSTEM
    # -------------------------------------------------------------
    @app_commands.command(name="rep", description="Give +1 community reputation/respect to a helpful server member.")
    @app_commands.describe(member="The member who helped you or deserves respect")
    async def rep_command(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot give reputation to yourself!", ephemeral=True)
        if member.bot:
            return await interaction.response.send_message("🤖 Bots appreciate the gratitude, but cannot hold reputation!", ephemeral=True)

        data = load_rep_data()
        sender_id = str(interaction.user.id)
        target_id = str(member.id)

        # 12-hour cooldown per user
        cooldown_sec = 12 * 3600
        now = int(time.time())
        sender_info = data.get(sender_id, {})
        last_given = sender_info.get("last_given", 0)

        if now - last_given < cooldown_sec:
            rem = cooldown_sec - (now - last_given)
            hours = rem // 3600
            mins = (rem % 3600) // 60
            return await interaction.response.send_message(
                f"⏳ You have already awarded reputation recently! You can give rep again in **{hours}h {mins}m**.",
                ephemeral=True
            )

        # Update sender
        if sender_id not in data:
            data[sender_id] = {"points": 0, "last_given": now, "given_count": 1}
        else:
            data[sender_id]["last_given"] = now
            data[sender_id]["given_count"] = data[sender_id].get("given_count", 0) + 1

        # Update target
        if target_id not in data:
            data[target_id] = {"points": 1, "last_given": 0, "given_count": 0}
        else:
            data[target_id]["points"] = data[target_id].get("points", 0) + 1

        save_rep_data(data)

        target_points = data[target_id]["points"]
        badge = get_rep_badge(target_points)

        embed = discord.Embed(
            title="🌟 ┊ 𝐑𝐄𝐏𝐔𝐓𝐀𝐓𝐈𝐎𝐍  𝐀𝐖𝐀𝐑𝐃𝐄𝐃!",
            description=(
                f"🎉 {interaction.user.mention} gave **+1 Reputation** to {member.mention}!\n\n"
                f"📈 **Total Reputation:** `{target_points} pts`\n"
                f"🎖️ **Rank:** {badge}\n\n"
                f"*Thank you for making **RAI FAM 💗** a helpful and welcoming community!*"
            ),
            color=0xFFD700
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Community Recognition", icon_url=config.RAI_ICON_URL)
        embed.timestamp = discord.utils.utcnow()
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="reputation", description="Check your or another member's community reputation score.")
    @app_commands.describe(member="Optional member to inspect")
    async def reputation_check(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        data = load_rep_data()
        target_info = data.get(str(target.id), {})
        points = target_info.get("points", 0)
        given = target_info.get("given_count", 0)
        badge = get_rep_badge(points)

        embed = discord.Embed(
            title=f"⭐ ┊ 𝐑𝐄𝐏𝐔𝐓𝐀𝐓𝐈𝐎𝐍  𝐏𝐑𝐎𝐅𝐈𝐋𝐄: {target.display_name}",
            description=(
                f"🎖️ **Standing:** {badge}\n\n"
                f"✨ **Reputation Points Received:** `{points}`\n"
                f"🤝 **Reputation Points Given:** `{given}`"
            ),
            color=0x00F2FE
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Award rep to peers with /rep @member", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    # -------------------------------------------------------------
    # 🤝 FRIENDSHIP & EXPRESSIVE ACTIONS
    # -------------------------------------------------------------
    @app_commands.command(name="highfive", description="Give an epic high-five to celebrate a win or milestone!")
    @app_commands.describe(member="The member you want to high-five")
    async def highfive(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("👏 Self high-five! You're doing amazing!", ephemeral=True)

        embed = discord.Embed(
            title="✋ ┊ 𝐄𝐏𝐈𝐂  𝐇𝐈𝐆𝐇  𝐅𝐈𝐕𝐄!",
            description=f"**{interaction.user.display_name}** gave **{member.display_name}** a resounding high-five! 💥 Teamwork makes the dream work!",
            color=0x00FF88
        )
        embed.set_image(url=random.choice(ACTION_GIFS["highfive"]))
        embed.set_footer(text="RAI FAM 💗 • Good Vibes Only", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(content=f"{member.mention}", embed=embed)

    @app_commands.command(name="fistbump", description="Give a friendly gamer fist-bump!")
    @app_commands.describe(member="The member you want to fist-bump")
    async def fistbump(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("👊 You bump fists with your reflection in the monitor. Ready to game!", ephemeral=True)

        embed = discord.Embed(
            title="👊 ┊ 𝐅𝐈𝐒𝐓  𝐁𝐔𝐌𝐏!",
            description=f"**{interaction.user.display_name}** bumps fists with **{member.display_name}**! Locked in and ready to roll! 🎮🔥",
            color=0x70A1FF
        )
        embed.set_image(url=random.choice(ACTION_GIFS["fistbump"]))
        embed.set_footer(text="RAI FAM 💗 • Gaming Hub", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(content=f"{member.mention}", embed=embed)

    @app_commands.command(name="cheers", description="Raise a glass, coffee, or tea to celebrate together!")
    @app_commands.describe(member="The member you want to toast with")
    async def cheers(self, interaction: discord.Interaction, member: discord.Member):
        target_name = member.display_name if member.id != interaction.user.id else "the entire server"
        embed = discord.Embed(
            title="🥂 ┊ 𝐂𝐇𝐄𝐄𝐑𝐒  ＆  𝐓𝐎𝐀𝐒𝐓!",
            description=f"**{interaction.user.display_name}** raises a drink to **{target_name}**! Here's to great tunes, chill vibes, and good company! ☕✨",
            color=0xFFA502
        )
        embed.set_image(url=random.choice(ACTION_GIFS["cheers"]))
        embed.set_footer(text="RAI FAM 💗 • Chill Lounge", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(content=None if member.id == interaction.user.id else member.mention, embed=embed)

    @app_commands.command(name="pat", description="Give a comforting, encouraging headpat to a friend.")
    @app_commands.describe(member="The member who deserves a pat")
    async def pat(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("🌸 You gently pat your own head. Rest up and stay awesome!", ephemeral=True)

        embed = discord.Embed(
            title="🌸 ┊ 𝐂𝐎𝐌𝐅𝐎𝐑𝐓𝐈𝐍𝐆  𝐏𝐀𝐓",
            description=f"**{interaction.user.display_name}** gently pats **{member.display_name}** on the head! You're doing great, keep your head up! ✨",
            color=0xFFB8C6
        )
        embed.set_image(url=random.choice(ACTION_GIFS["pat"]))
        embed.set_footer(text="RAI FAM 💗 • Wholesome Corner", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(content=f"{member.mention}", embed=embed)

    @app_commands.command(name="slap", description="Playfully slap someone with an anime squeaky toy or giant fish!")
    @app_commands.describe(member="The member you want to playfully slap")
    async def slap(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("🛡️ Don't slap yourself! Be kind to yourself.", ephemeral=True)

        items = ["a squeaky rubber hammer", "a giant oversized tuna 🐟", "a plushie pillow 🧸", "a folded newspaper 🗞️"]
        chosen = random.choice(items)

        embed = discord.Embed(
            title="💥 ┊ 𝐂𝐎𝐌𝐈𝐂  𝐀𝐍𝐈𝐌𝐄  𝐒𝐋𝐀𝐏!",
            description=f"**{interaction.user.display_name}** playfully slapped **{member.display_name}** across the room with **{chosen}**! *BAM!* 💨",
            color=0xFF4757
        )
        embed.set_image(url=random.choice(ACTION_GIFS["slap"]))
        embed.set_footer(text="RAI FAM 💗 • 100% Comedic & Harmless Fun", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(content=f"{member.mention}", embed=embed)

    @app_commands.command(name="poke", description="Playfully poke a friend to get their attention!")
    @app_commands.describe(member="The member you want to poke")
    async def poke(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("👉 You poke yourself in the cheek. *Boop!*", ephemeral=True)

        embed = discord.Embed(
            title="👉 ┊ *𝐁𝐎𝐎𝐏!*  𝐏𝐎𝐊𝐄",
            description=f"**{interaction.user.display_name}** poked **{member.display_name}**! Hey, wake up or check chat! 👀",
            color=0x2ED573
        )
        embed.set_image(url=random.choice(ACTION_GIFS["poke"]))
        embed.set_footer(text="RAI FAM 💗 • Friendly Interactions", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(content=f"{member.mention}", embed=embed)

    @app_commands.command(name="hug", description="Give a warm, friendly buddy hug to a member.")
    @app_commands.describe(member="The member you want to hug")
    async def hug(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("🫂 You wrap your arms around yourself in a comforting self-hug! 🌸", ephemeral=True)

        embed = discord.Embed(
            title="🫂 ┊ 𝐅𝐑𝐈𝐄𝐍𝐃𝐋𝐘  𝐇𝐔𝐆",
            description=f"**{interaction.user.display_name}** gives **{member.display_name}** a warm, supportive hug! Everything is going to be alright! 🌸",
            color=0xFF69B4
        )
        embed.set_image(url=random.choice(ACTION_GIFS["hug"]))
        embed.set_footer(text="RAI FAM 💗 • Wholesome Community", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(content=f"{member.mention}", embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Social(bot))
