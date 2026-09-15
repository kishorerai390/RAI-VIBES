import os
import sys
import json
import time
import random
import asyncio
import logging
from pathlib import Path
from typing import Optional, List, Dict
import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import View, Button, button

import config

logger = logging.getLogger("Giveaway")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
GIVEAWAY_FILE = DATA_DIR / "giveaways.json"


def load_giveaways() -> Dict[str, dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if GIVEAWAY_FILE.exists():
        try:
            with open(GIVEAWAY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_giveaways(data: Dict[str, dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(GIVEAWAY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class EnterGiveawayButton(Button):
    def __init__(self, count: int = 0):
        super().__init__(
            label=f"🎉 Enter Giveaway ({count})",
            style=discord.ButtonStyle.success,
            custom_id="giveaway_enter_btn"
        )

    async def callback(self, interaction: discord.Interaction):
        msg_id = str(interaction.message.id)
        data = load_giveaways()

        if msg_id not in data or data[msg_id].get("ended", False):
            return await interaction.response.send_message("❌ This giveaway has ended.", ephemeral=True)

        entries: List[int] = data[msg_id].setdefault("entries", [])
        user_id = interaction.user.id

        if user_id in entries:
            entries.remove(user_id)
            save_giveaways(data)
            self.label = f"🎉 Enter Giveaway ({len(entries)})"
            await interaction.message.edit(view=self.view)
            return await interaction.response.send_message("👋 You left the giveaway.", ephemeral=True)
        else:
            entries.append(user_id)
            save_giveaways(data)
            self.label = f"🎉 Enter Giveaway ({len(entries)})"
            await interaction.message.edit(view=self.view)
            return await interaction.response.send_message("🎉 **You entered the giveaway!** Best of luck! 🌸", ephemeral=True)


class GiveawayView(View):
    def __init__(self, count: int = 0):
        super().__init__(timeout=None)
        self.btn = EnterGiveawayButton(count)
        self.add_item(self.btn)


class Giveaway(commands.Cog):
    """Interactive Server Giveaway Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.check_loop.start()

    def cog_unload(self):
        self.check_loop.cancel()

    @tasks.loop(seconds=15)
    async def check_loop(self):
        await self.bot.wait_until_ready()
        data = load_giveaways()
        now = int(time.time())
        updated = False

        for msg_id, g in list(data.items()):
            if g.get("ended", False):
                continue
            if now >= g.get("end_time", 0):
                g["ended"] = True
                updated = True
                await self.end_giveaway(msg_id, g)

        if updated:
            save_giveaways(data)

    async def end_giveaway(self, msg_id: str, g: dict):
        channel_id = g.get("channel_id")
        channel = self.bot.get_channel(channel_id)
        if not channel:
            try:
                channel = await self.bot.fetch_channel(channel_id)
            except Exception:
                return

        try:
            msg = await channel.fetch_message(int(msg_id))
        except Exception:
            return

        entries = g.get("entries", [])
        winner_count = max(1, g.get("winners", 1))
        prize = g.get("prize", "Secret Prize")

        if not entries:
            embed = discord.Embed(
                title=f"🎉 GIVEAWAY ENDED: {prize}",
                description="❌ No entries were recorded. No winner could be selected!",
                color=0xE74C3C
            )
            embed.set_footer(text="RAI FAM 💗 • Giveaway System", icon_url=config.RAI_ICON_URL)
            await msg.edit(embed=embed, view=None)
            return

        winner_ids = random.sample(entries, min(winner_count, len(entries)))
        winner_mentions = [f"<@{uid}>" for uid in winner_ids]
        winners_str = ", ".join(winner_mentions)

        embed = discord.Embed(
            title="🎉 GIVEAWAY ENDED • WINNER SELECTED!",
            description=(
                f"### 🎁 **Prize:** {prize}\n\n"
                f"🏆 **Winner(s):** {winners_str}\n"
                f"👥 **Total Entries:** `{len(entries)}`\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"Congratulations! Contact staff or check your inventory to claim! 🌸"
            ),
            color=0x2ECC71
        )
        embed.set_footer(text="RAI FAM 💗 • Fair Selection Engine", icon_url=config.RAI_ICON_URL)
        await msg.edit(embed=embed, view=None)
        await channel.send(f"🎊 Congratulations {winners_str}! You won the **{prize}**! 🥳", allowed_mentions=discord.AllowedMentions(users=True))

    giveaway_group = app_commands.Group(name="giveaway", description="Create and manage server giveaways")

    @giveaway_group.command(name="create", description="Start an interactive giveaway with live buttons.")
    @app_commands.describe(
        prize="What is being given away?",
        minutes="Duration of the giveaway in minutes",
        winners="Number of winners (default: 1)",
        channel="Channel to post giveaway in (default: current channel)"
    )
    async def create_cmd(
        self,
        interaction: discord.Interaction,
        prize: str,
        minutes: int,
        winners: Optional[int] = 1,
        channel: Optional[discord.TextChannel] = None
    ):
        if not interaction.user.guild_permissions.manage_guild and interaction.user.id != 1457380609641938981:
            return await interaction.response.send_message("❌ You lack permissions to start giveaways.", ephemeral=True)

        if minutes < 1:
            return await interaction.response.send_message("❌ Minimum duration is 1 minute.", ephemeral=True)

        target_ch = channel or interaction.channel
        end_timestamp = int(time.time()) + (minutes * 60)

        embed = discord.Embed(
            title="🎁 RAI FAM 💗 • OFFICIAL SERVER GIVEAWAY",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"### 🏆 **Prize:** {prize}\n\n"
                f"• 👥 **Winners:** `{winners}`\n"
                f"• ⏳ **Ends In:** <t:{end_timestamp}:R> (<t:{end_timestamp}:f>)\n"
                f"• 👑 **Hosted By:** {interaction.user.mention}\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"👉 *Click the **🎉 Enter Giveaway** button below to participate!*"
            ),
            color=0xFF69B4
        )
        embed.set_thumbnail(url=interaction.guild.icon.url if interaction.guild.icon else config.RAI_ICON_URL)
        embed.set_footer(text="Good luck everyone • Powered by RAI VIBES 💗", icon_url=config.RAI_ICON_URL)

        view = GiveawayView(count=0)
        await interaction.response.send_message(f"✅ Giveaway created in {target_ch.mention}!", ephemeral=True)
        msg = await target_ch.send(embed=embed, view=view)

        data = load_giveaways()
        data[str(msg.id)] = {
            "channel_id": target_ch.id,
            "prize": prize,
            "winners": winners,
            "end_time": end_timestamp,
            "host_id": interaction.user.id,
            "entries": [],
            "ended": False
        }
        save_giveaways(data)

    @giveaway_group.command(name="reroll", description="Reroll a new winner for an ended giveaway.")
    @app_commands.describe(message_id="Message ID of the ended giveaway")
    async def reroll_cmd(self, interaction: discord.Interaction, message_id: str):
        if not interaction.user.guild_permissions.manage_guild and interaction.user.id != 1457380609641938981:
            return await interaction.response.send_message("❌ You lack permissions to reroll giveaways.", ephemeral=True)

        data = load_giveaways()
        if message_id not in data:
            return await interaction.response.send_message("❌ Giveaway message not found.", ephemeral=True)

        g = data[message_id]
        entries = g.get("entries", [])
        if not entries:
            return await interaction.response.send_message("❌ No entries found to reroll from.", ephemeral=True)

        new_winner = random.choice(entries)
        channel = self.bot.get_channel(g.get("channel_id"))
        if channel:
            await channel.send(f"🎉 **REROLL!** New winner for **{g.get('prize')}** is <@{new_winner}>! Congratulations! 🥳")
        await interaction.response.send_message(f"✅ Rerolled! New winner: <@{new_winner}>", ephemeral=True)


async def setup(bot: commands.Bot):
    bot.add_view(GiveawayView())
    await bot.add_cog(Giveaway(bot))
