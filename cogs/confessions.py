import os
import json
import logging
from pathlib import Path
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput

import config

logger = logging.getLogger("Confessions")
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
CONFESSIONS_FILE = DATA_DIR / "confessions.json"
CONFESSIONS_CHANNEL_ID = 1550059973634039828
PETS_FOOD_CHANNEL_ID = 1550059976326651905


def load_confession_data() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if CONFESSIONS_FILE.exists():
        try:
            with open(CONFESSIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"count": 0}
    return {"count": 0}


def save_confession_data(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFESSIONS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class ConfessionModal(Modal, title="💌 Submit Anonymous Confession"):
    confession = TextInput(
        label="Your Anonymous Thought or Story",
        style=discord.TextStyle.paragraph,
        placeholder="Share a funny story, anonymous thought, or secret shoutout... (100% anonymous)",
        max_length=1500,
        required=True
    )

    def __init__(self, cog: "Confessions"):
        super().__init__()
        self.cog = cog

    async def on_submit(self, interaction: discord.Interaction):
        data = load_confession_data()
        data["count"] = data.get("count", 0) + 1
        confession_num = data["count"]
        save_confession_data(data)

        channel = interaction.guild.get_channel(CONFESSIONS_CHANNEL_ID)
        if not channel:
            # Fallback search by name
            channel = next((c for c in interaction.guild.text_channels if "confess" in c.name.lower() or "ᴄᴏɴꜰᴇꜱꜱɪᴏɴꜱ" in c.name), None)

        if not channel:
            return await interaction.response.send_message("❌ Confessions channel could not be found.", ephemeral=True)

        embed = discord.Embed(
            title=f"💌 ┊ 𝐀𝐍𝐎𝐍𝐘𝐌𝐎𝐔𝐒  𝐂𝐎𝐍𝐅𝐄𝐒𝐒𝐈𝐎𝐍  #{confession_num}",
            description=f">>> {self.confession.value}",
            color=0xFF69B4
        )
        embed.set_footer(text="RAI FAM 💗 • Anonymous Whispers • Send yours with /confess", icon_url=config.RAI_ICON_URL)
        embed.timestamp = discord.utils.utcnow()

        try:
            msg = await channel.send(embed=embed)
            # Add reaction triggers
            for emoji in ["💬", "😂", "💀", "👀", "🔥"]:
                try:
                    await msg.add_reaction(emoji)
                except Exception:
                    pass

            await interaction.response.send_message(
                f"✅ **Your confession has been anonymously posted as #{confession_num}!** Check {channel.mention}",
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(f"❌ Error submitting confession: {e}", ephemeral=True)


class Confessions(commands.Cog):
    """Anonymous Confession Box and Gallery Interactions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="confess", description="Submit a 100% anonymous confession to #💌・confessions.")
    async def confess(self, interaction: discord.Interaction):
        await interaction.response.send_modal(ConfessionModal(self))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Auto-heart & flame reactions for media uploads in #pets-and-food."""
        if message.author.bot or not message.guild:
            return

        if message.channel.id == PETS_FOOD_CHANNEL_ID or "pets" in message.channel.name.lower() or "ᴘᴇᴛꜱ" in message.channel.name:
            if message.attachments:
                has_image = any(att.content_type and "image" in att.content_type for att in message.attachments)
                if has_image or message.attachments:
                    for emoji in ["❤️", "🔥", "✨"]:
                        try:
                            await message.add_reaction(emoji)
                        except Exception:
                            pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Confessions(bot))
