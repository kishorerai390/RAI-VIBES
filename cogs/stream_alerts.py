import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, List, Literal

import discord
from discord import app_commands
from discord.ext import commands, tasks

import config

logger = logging.getLogger("StreamAlerts")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ALERTS_FILE = DATA_DIR / "stream_alerts.json"


def load_alerts() -> Dict[str, list]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if ALERTS_FILE.exists():
        try:
            with open(ALERTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"streamers": []}
    return {"streamers": []}


def save_alerts(data: Dict[str, list]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(ALERTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class StreamAlerts(commands.Cog):
    """Creator & Streamer Live Notifications."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="streamer", description="Manage creator stream announcements for the server.")
    @app_commands.describe(
        action="Choose action (add, list, remove, announce)",
        platform="Streaming platform (Twitch, YouTube, Kick)",
        handle="Channel username or link",
        custom_title="Stream title or message"
    )
    async def streamer_cmd(
        self,
        interaction: discord.Interaction,
        action: Literal["add", "list", "remove", "announce"],
        platform: Optional[Literal["twitch", "youtube", "kick"]] = None,
        handle: Optional[str] = None,
        custom_title: Optional[str] = None
    ):
        data = load_alerts()
        streamers: List[dict] = data.setdefault("streamers", [])

        # 1. LIST
        if action == "list":
            if not streamers:
                return await interaction.response.send_message("ℹ️ No creators configured yet. Add one with `/streamer action:add`.", ephemeral=True)
            embed = discord.Embed(
                title="📡 MONITORED CREATORS & STREAMERS",
                color=0x9146FF
            )
            for s in streamers:
                embed.add_field(
                    name=f"🎮 {s['handle']} ({s['platform'].upper()})",
                    value=f"Link: {s['url']}",
                    inline=False
                )
            embed.set_footer(text="RAI VIBES Creator Alerts", icon_url=config.RAI_ICON_URL)
            return await interaction.response.send_message(embed=embed)

        # 2. ADD
        if action == "add":
            if not interaction.user.guild_permissions.manage_guild:
                return await interaction.response.send_message("❌ You need Manage Server permissions to add creators.", ephemeral=True)

            if not platform or not handle:
                return await interaction.response.send_message("❌ Please specify both platform and handle! Example: `/streamer action:add platform:twitch handle:kishore`", ephemeral=True)

            clean_handle = handle.replace("https://", "").replace("www.", "").split("/")[-1].strip()
            if platform == "twitch":
                url = f"https://twitch.tv/{clean_handle}"
            elif platform == "kick":
                url = f"https://kick.com/{clean_handle}"
            else:
                url = f"https://youtube.com/@{clean_handle}"

            # Check if exists
            if any(s["handle"].lower() == clean_handle.lower() for s in streamers):
                return await interaction.response.send_message(f"⚠️ `{clean_handle}` is already in the streamer alert list!", ephemeral=True)

            streamers.append({
                "handle": clean_handle,
                "platform": platform,
                "url": url,
                "added_by": interaction.user.id
            })
            save_alerts(data)
            return await interaction.response.send_message(f"✅ Added **{clean_handle}** ({platform.upper()}) to creator alerts! URL: {url}")

        # 3. REMOVE
        if action == "remove":
            if not interaction.user.guild_permissions.manage_guild:
                return await interaction.response.send_message("❌ You need Manage Server permissions to remove creators.", ephemeral=True)
            if not handle:
                return await interaction.response.send_message("❌ Please specify the handle to remove.", ephemeral=True)

            clean_handle = handle.split("/")[-1].strip().lower()
            initial_len = len(streamers)
            streamers = [s for s in streamers if s["handle"].lower() != clean_handle]
            data["streamers"] = streamers
            save_alerts(data)

            if len(streamers) < initial_len:
                return await interaction.response.send_message(f"🗑️ Removed `{clean_handle}` from creator alerts.")
            else:
                return await interaction.response.send_message(f"❌ `{clean_handle}` was not found in the list.", ephemeral=True)

        # 4. INSTANT LIVE ANNOUNCEMENT
        if action == "announce":
            if not interaction.user.guild_permissions.mention_everyone and not interaction.user.guild_permissions.manage_messages:
                return await interaction.response.send_message("❌ Only staff or creators can broadcast live announcements.", ephemeral=True)

            target_handle = handle or interaction.user.display_name
            target_plat = platform or "twitch"
            stream_url = f"https://{target_plat}.tv/{target_handle.lower().replace(' ', '')}" if target_plat == "twitch" else f"https://{target_plat}.com/{target_handle.lower().replace(' ', '')}"
            title_text = custom_title or f"Live Stream with {interaction.user.display_name}!"

            embed = discord.Embed(
                title=f"🔴 LIVE NOW • {target_handle} is streaming!",
                description=(
                    f"### [{title_text}]({stream_url})\n\n"
                    f"🎮 **Platform:** `{target_plat.upper()}`\n"
                    f"🔗 **Watch Here:** [Click to Join Stream]({stream_url})\n\n"
                    f"Hop into stream and show some RAI VIBES love in chat! 🔥"
                ),
                color=0xFF0055 if target_plat == "youtube" else 0x9146FF
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text="RAI VIBES Creator Network", icon_url=config.RAI_ICON_URL)

            # Target announcement channel: #📢・ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛꜱ (1546062590910926951)
            ann_channel = (
                interaction.guild.get_channel(1546062590910926951)
                or discord.utils.get(interaction.guild.text_channels, name="announcements")
                or interaction.channel
            )

            await ann_channel.send(content=f"@everyone 🔴 **{target_handle} is LIVE NOW!**", embed=embed)
            if ann_channel.id != interaction.channel.id:
                return await interaction.response.send_message(f"✅ Live broadcast sent to {ann_channel.mention}!", ephemeral=True)
            else:
                return await interaction.response.send_message("✅ Live broadcast posted!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(StreamAlerts(bot))
