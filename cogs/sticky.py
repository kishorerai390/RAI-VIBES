import os
import json
import logging
from pathlib import Path
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("StickyMessages")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STICKY_FILE = DATA_DIR / "sticky_messages.json"

def load_sticky() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if STICKY_FILE.exists():
        try:
            with open(STICKY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_sticky(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(STICKY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save sticky messages: {e}")

class StickyMessages(commands.Cog):
    """Dynamic bottom-pinned announcements and guidelines."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.sticky_data = load_sticky()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        ch_id = str(message.channel.id)
        if ch_id not in self.sticky_data:
            return

        config_item = self.sticky_data[ch_id]
        text = config_item.get("content")
        last_msg_id = config_item.get("last_msg_id")

        if not text:
            return

        # Delete previous sticky message if present
        if last_msg_id:
            try:
                old_msg = await message.channel.fetch_message(last_msg_id)
                await old_msg.delete()
            except Exception:
                pass

        # Repost sticky message at bottom
        embed = discord.Embed(
            description=f"📌 **PINNED NOTICE:**\n\n{text}",
            color=0xFF77A9
        )
        embed.set_footer(text="RAI SENTINEL • Channel Guideline")
        try:
            new_msg = await message.channel.send(embed=embed)
            self.sticky_data[ch_id]["last_msg_id"] = new_msg.id
            save_sticky(self.sticky_data)
        except Exception as e:
            logger.debug(f"Could not repost sticky: {e}")

    @app_commands.command(name="sticky_set", description="Stick an announcement dynamically to the bottom of this channel.")
    @app_commands.describe(message="The message text to keep pinned at the bottom")
    @commands.has_permissions(manage_messages=True)
    async def sticky_set(self, interaction: discord.Interaction, message: str):
        ch_id = str(interaction.channel.id)
        self.sticky_data[ch_id] = {
            "content": message,
            "last_msg_id": None
        }
        save_sticky(self.sticky_data)

        embed = discord.Embed(
            description=f"📌 **PINNED NOTICE:**\n\n{message}",
            color=0xFF77A9
        )
        embed.set_footer(text="RAI SENTINEL • Channel Guideline")
        new_msg = await interaction.channel.send(embed=embed)
        self.sticky_data[ch_id]["last_msg_id"] = new_msg.id
        save_sticky(self.sticky_data)

        await interaction.response.send_message("✅ Sticky message configured and pinned to the bottom of this channel!", ephemeral=True)

    @app_commands.command(name="sticky_clear", description="Remove the sticky message from this channel.")
    @commands.has_permissions(manage_messages=True)
    async def sticky_clear(self, interaction: discord.Interaction):
        ch_id = str(interaction.channel.id)
        if ch_id in self.sticky_data:
            last_id = self.sticky_data[ch_id].get("last_msg_id")
            if last_id:
                try:
                    old_msg = await interaction.channel.fetch_message(last_id)
                    await old_msg.delete()
                except Exception:
                    pass
            self.sticky_data.pop(ch_id, None)
            save_sticky(self.sticky_data)
            await interaction.response.send_message("🗑️ Sticky message removed from this channel.", ephemeral=True)
        else:
            await interaction.response.send_message("ℹ️ No sticky message active in this channel.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(StickyMessages(bot))
