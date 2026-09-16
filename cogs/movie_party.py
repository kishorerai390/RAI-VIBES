import os
import json
import time
import logging
from pathlib import Path
from typing import Optional, Dict, List

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import View, Button, button

import config

logger = logging.getLogger("MovieParty")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EVENTS_FILE = DATA_DIR / "movie_events.json"


def load_events() -> Dict[str, dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if EVENTS_FILE.exists():
        try:
            with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_events(data: Dict[str, dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(EVENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class MovieRSVPView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Count Me In! 🍿", style=discord.ButtonStyle.primary, custom_id="movie_rsvp_toggle_btn")
    async def rsvp_button(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        events = load_events()
        msg_id = str(interaction.message.id)

        if msg_id not in events:
            # Initialize event tracking
            events[msg_id] = {
                "title": interaction.message.embeds[0].title if interaction.message.embeds else "Movie Night",
                "rsvps": []
            }

        rsvps: List[int] = events[msg_id].get("rsvps", [])
        uid = interaction.user.id

        if uid in rsvps:
            rsvps.remove(uid)
            msg = "⚪ You cancelled your RSVP."
        else:
            rsvps.append(uid)
            msg = "🍿 **RSVP Confirmed!** You'll be notified before showtime!"

        events[msg_id]["rsvps"] = rsvps
        save_events(events)

        # Update button label count
        btn.label = f"Count Me In! 🍿 ({len(rsvps)})"
        try:
            # Update embed field with RSVP list preview
            embed = interaction.message.embeds[0]
            for i, field in enumerate(embed.fields):
                if "Attendees" in field.name or "RSVP" in field.name:
                    embed.set_field_at(
                        i,
                        name=f"🍿 Attendees RSVP'd ({len(rsvps)})",
                        value=f"{len(rsvps)} members joining! Click button below to RSVP.",
                        inline=False
                    )
                    break
            await interaction.message.edit(embed=embed, view=self)
        except Exception as e:
            logger.debug(f"Could not update event message: {e}")

        await interaction.followup.send(msg, ephemeral=True)


class MovieParty(commands.Cog):
    """Automated Movie Night, Anime Watch-Party & Event RSVP Hub."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="movie", description="Schedule a community Movie Night or Anime Watch-Along!")
    @app_commands.describe(
        title="Title of the movie, anime episode, or stream",
        time_info="When is the watch-party (e.g. Tonight @ 9 PM IST, Saturday 8 PM)",
        description="Brief synopsis or stream details",
        banner_url="Optional image URL for the movie poster/banner"
    )
    async def host_movie(
        self,
        interaction: discord.Interaction,
        title: str,
        time_info: str,
        description: Optional[str] = None,
        banner_url: Optional[str] = None
    ):
        embed = discord.Embed(
            title=f"🎬 WATCH-PARTY: {title}",
            description=(
                f"Hosted by {interaction.user.mention}!\n\n"
                f"🕒 **Showtime:** `{time_info}`\n"
                f"📍 **Location:** Voice Suite / Screen Share Lounge\n\n"
                f"📝 **Overview:**\n*{description or 'Grab your snacks and popcorn for an epic watch-along with the squad!'}*"
            ),
            color=0xFF007F
        )

        if banner_url and banner_url.startswith("http"):
            embed.set_image(url=banner_url)
        else:
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3172/3172555.png")

        embed.add_field(
            name="🍿 Attendees RSVP'd (0)",
            value="Be the first to RSVP! Click the button below.",
            inline=False
        )
        embed.set_footer(text="RAI VIBES Cinema Lounge • Watch together in high fidelity", icon_url=config.RAI_ICON_URL)

        view = MovieRSVPView()
        # Post in movie channel or current channel
        movie_channel = (
            discord.utils.get(interaction.guild.text_channels, name="🍿・ᴍᴏᴠɪᴇ-ɴɪɢʜᴛꜱ")
            or discord.utils.get(interaction.guild.text_channels, name="movie-nights")
            or interaction.channel
        )

        msg = await movie_channel.send(content="@everyone 🍿 **New Watch-Party Announced!**", embed=embed, view=view)

        # Store in events
        events = load_events()
        events[str(msg.id)] = {
            "title": title,
            "time": time_info,
            "host_id": interaction.user.id,
            "rsvps": []
        }
        save_events(events)

        if movie_channel.id != interaction.channel.id:
            await interaction.response.send_message(f"✅ Watch-Party scheduled in {movie_channel.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message("✅ Watch-Party announced!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(MovieParty(bot))
