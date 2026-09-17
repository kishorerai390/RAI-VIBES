import os
import json
import time
import random
import hashlib
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, button

import config

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MARRIAGE_FILE = DATA_DIR / "marriages.json"

ANIME_GIFS = {
    "hug": [
        "https://media.tenor.com/kCZvsN305gkAAAAC/anime-hug.gif",
        "https://media.tenor.com/7oAptSmhHqAAAAAC/hug-warm.gif",
        "https://media.tenor.com/2lrDXrvIF modular.gif"
    ],
    "pat": [
        "https://media.tenor.com/Y7B549vX6W8AAAAC/anime-head-pat.gif",
        "https://media.tenor.com/DCM_J1ad24AAAAAC/pat-head.gif"
    ],
    "slap": [
        "https://media.tenor.com/Ws6Dm1ZW_vMAAAAC/anime-slap.gif",
        "https://media.tenor.com/CvBTA0GyrogAAAAC/anime-slap.gif"
    ],
    "kiss": [
        "https://media.tenor.com/Erw_wI9-r6EAAAAC/anime-kiss.gif",
        "https://media.tenor.com/I83WJ7-2CcwAAAAC/anime-kiss.gif"
    ]
}


def load_marriages() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if MARRIAGE_FILE.exists():
        try:
            with open(MARRIAGE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_marriages(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(MARRIAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class MarriageProposalView(View):
    def __init__(self, proposer: discord.Member, target: discord.Member):
        super().__init__(timeout=120)
        self.proposer = proposer
        self.target = target

    @button(label="Accept 💍", style=discord.ButtonStyle.success)
    async def accept(self, interaction: discord.Interaction, btn: Button):
        if interaction.user.id != self.target.id:
            return await interaction.response.send_message("❌ This marriage proposal was not meant for you!", ephemeral=True)

        data = load_marriages()
        t = int(time.time())
        data[str(self.proposer.id)] = {"partner": self.target.id, "date": t}
        data[str(self.target.id)] = {"partner": self.proposer.id, "date": t}
        save_marriages(data)

        self.stop()
        embed = discord.Embed(
            title="💍 ┊ 𝐇𝐎𝐋𝐘  𝐌𝐀𝐓𝐑𝐈𝐌𝐎𝐍Ｙ!",
            description=(
                f"🎉 {self.target.mention} accepted the proposal from {self.proposer.mention}!\n\n"
                f"🌸 **They are now officially married in RAI FAM 💗!**\n"
                f"May your love, lo-fi vibes, and coin wallets flourish together forever! 🥂"
            ),
            color=0xFF69B4
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1149363065603702834.webp?size=96&quality=lossless")
        embed.set_footer(text="RAI FAM 💗 • Wedding Chapel")
        await interaction.response.edit_message(content=None, embed=embed, view=None)

    @button(label="Decline 💔", style=discord.ButtonStyle.danger)
    async def decline(self, interaction: discord.Interaction, btn: Button):
        if interaction.user.id != self.target.id:
            return await interaction.response.send_message("❌ This proposal is not for you!", ephemeral=True)

        self.stop()
        embed = discord.Embed(
            title="💔 ┊ 𝐏𝐑𝐎𝐏𝐎𝐒𝐀𝐋  𝐑𝐄𝐉𝐄𝐂𝐓𝐄𝐃",
            description=f"Ouch... {self.target.mention} turned down {self.proposer.mention}'s proposal. There are plenty of fish in the cyber sea! 🐟",
            color=0x747D8C
        )
        await interaction.response.edit_message(content=None, embed=embed, view=None)


class Social(commands.Cog):
    """Social, Romance, Marriage and Expressive Interactions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="marry", description="Propose marriage to a server member!")
    @app_commands.describe(member="The lucky person you wish to propose to")
    async def marry(self, interaction: discord.Interaction, member: discord.Member):
        if member.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot marry yourself, as much as you love self-care!", ephemeral=True)
        if member.bot:
            return await interaction.response.send_message("🤖 You cannot marry bots! Their only true love is Python code.", ephemeral=True)

        data = load_marriages()
        uid = str(interaction.user.id)
        mid = str(member.id)

        if uid in data:
            partner = interaction.guild.get_member(data[uid]["partner"])
            pname = partner.mention if partner else f"User ID {data[uid]['partner']}"
            return await interaction.response.send_message(f"❌ You are already married to {pname}! Use `/divorce` first.", ephemeral=True)

        if mid in data:
            partner = interaction.guild.get_member(data[mid]["partner"])
            pname = partner.mention if partner else f"User ID {data[mid]['partner']}"
            return await interaction.response.send_message(f"❌ {member.display_name} is already married to {pname}!", ephemeral=True)

        embed = discord.Embed(
            title="💍 ┊ 𝐌𝐀𝐑𝐑𝐈𝐀𝐆𝐄  𝐏𝐑𝐎𝐏𝐎𝐒𝐀𝐋",
            description=(
                f"🌹 **{member.mention}**, you have received a marriage proposal from **{interaction.user.mention}**!\n\n"
                f"*Will you take their hand in virtual holy matrimony?*"
            ),
            color=0xFFB8C6
        )
        embed.set_footer(text="Proposal expires in 2 minutes")
        view = MarriageProposalView(interaction.user, member)
        await interaction.response.send_message(content=member.mention, embed=embed, view=view)

    @app_commands.command(name="divorce", description="Divorce your current partner.")
    async def divorce(self, interaction: discord.Interaction):
        data = load_marriages()
        uid = str(interaction.user.id)

        if uid not in data:
            return await interaction.response.send_message("❌ You are single! There is no one to divorce.", ephemeral=True)

        partner_id = data[uid]["partner"]
        pid = str(partner_id)
        partner = interaction.guild.get_member(partner_id)
        pname = partner.mention if partner else f"User ID {partner_id}"

        del data[uid]
        if pid in data:
            del data[pid]
        save_marriages(data)

        embed = discord.Embed(
            title="📜 ┊ 𝐃𝐈𝐕𝐎𝐑𝐂𝐄  𝐅𝐈𝐋𝐄𝐃",
            description=(
                f"💔 {interaction.user.mention} and {pname} are now officially divorced.\n\n"
                f"🏠 *You kept the lo-fi playlists; they kept the pet cat.* Both of you are back on the market!"
            ),
            color=0x747D8C
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="marriage", description="Check your or someone else's marriage status.")
    @app_commands.describe(member="Optional member to inspect")
    async def marriage_status(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        data = load_marriages()
        tid = str(target.id)

        if tid not in data:
            desc = f"💔 **{target.display_name}** is currently single and ready to mingle!"
            color = 0x747D8C
        else:
            partner_id = data[tid]["partner"]
            partner = interaction.guild.get_member(partner_id)
            pname = partner.mention if partner else f"User ID {partner_id}"
            wedding_time = data[tid]["date"]
            days = (int(time.time()) - wedding_time) // 86400

            desc = (
                f"💍 **Married To:** {pname}\n"
                f"📅 **Wedding Date:** <t:{wedding_time}:D>\n"
                f"⏳ **Together For:** `{days}` days of harmony! 🥂"
            )
            color = 0xFF69B4

        embed = discord.Embed(
            title=f"🌸 ┊ 𝐌𝐀𝐑𝐑𝐈𝐀𝐆𝐄  𝐒𝐓𝐀𝐓𝐔𝐒: {target.display_name}",
            description=desc,
            color=color
        )
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ship", description="Calculate romantic & friendship compatibility between two members!")
    @app_commands.describe(user1="First person", user2="Second person (defaults to you)")
    async def ship(self, interaction: discord.Interaction, user1: discord.Member, user2: Optional[discord.Member] = None):
        target2 = user2 or interaction.user
        if user1.id == target2.id:
            return await interaction.response.send_message("💖 100% Love! Self-love is the greatest romance of all.", ephemeral=True)

        # Consistent seed per day for the pair
        combined_ids = sorted([user1.id, target2.id])
        day_str = time.strftime("%Y-%m-%d")
        seed_str = f"{combined_ids[0]}-{combined_ids[1]}-{day_str}"
        score = int(hashlib.md5(seed_str.encode()).hexdigest(), 16) % 101

        filled = int(score / 10)
        bar = "█" * filled + "░" * (10 - filled)

        if score >= 90:
            verdict = "💍 **FATED SOULMATES!** Buy the wedding rings already!"
            color = 0xFF1493
        elif score >= 70:
            verdict = "✨ **CUTE DYNAMIC DUO!** Sparks are definitely flying."
            color = 0xFF69B4
        elif score >= 50:
            verdict = "💫 **SOLID COMPATIBILITY!** Great banter and friendship potential."
            color = 0x00FF88
        elif score >= 25:
            verdict = "😬 **AWKWARD ACQUAINTANCES!** Tread carefully."
            color = 0xFFD700
        else:
            verdict = "☠️ **TOXIC HAZARD!** Keep 100 meters distance at all times."
            color = 0xFF4757

        embed = discord.Embed(
            title="💘 ┊ 𝐋𝐎𝐕𝐄  ＆  𝐒𝐇𝐈𝐏  𝐌𝐄𝐓𝐄𝐑",
            description=(
                f"**Couple:** {user1.mention} 💞 {target2.mention}\n\n"
                f"**Match Rating:** `{score}%`\n"
                f"`[{bar}]`\n\n"
                f"{verdict}"
            ),
            color=color
        )
        embed.set_footer(text="RAI FAM 💗 • Cupid's Laboratory")
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Social(bot))
