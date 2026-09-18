import os
import json
import time
import asyncio
import logging
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, List

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, button

import config

logger = logging.getLogger("MovieParty")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EVENTS_FILE = DATA_DIR / "movie_events.json"

DEFAULT_ANNOUNCEMENT_CHANNEL_ID = 1545502718792175646  # 📢｜ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛꜱ
DEFAULT_VOICE_ROOM_ID = 1550196955660029964           # 🍿 | Movie Time 1
FOUNDER_USER_ID = 1457380609641938981


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
    try:
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save movie events: {e}")


def fetch_movie_metadata_sync(query: str) -> dict:
    """Fetch movie metadata, rating, synopsis, and HD theatrical poster from OMDb and Wikipedia."""
    import re
    clean_q = query.strip()
    data = {}

    # Extract 4-digit release year if provided (e.g. "Rush (2013)" or "Rush 2013")
    year_match = re.search(r"\(?\b(19\d\d|20\d\d)\b\)?", clean_q)
    extracted_year = year_match.group(1) if year_match else None
    search_title = re.sub(r"\(?\b(19\d\d|20\d\d)\b\)?", "", clean_q).strip()
    search_title = re.sub(r"[\(\)]", "", search_title).strip() or clean_q

    # 1. Primary: OMDb API
    try:
        url = f"http://www.omdbapi.com/?t={urllib.parse.quote(search_title)}"
        if extracted_year:
            url += f"&y={extracted_year}"
        url += "&apikey=trilogy"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=5) as res:
            res_json = json.loads(res.read().decode())
        if res_json.get("Response") == "True":
            poster = res_json.get("Poster")
            if poster == "N/A" or not poster:
                poster = None
            data = {
                "title": res_json.get("Title", search_title.title()),
                "year": res_json.get("Year", extracted_year or ""),
                "rated": res_json.get("Rated", "PG-13"),
                "runtime": res_json.get("Runtime", "N/A"),
                "genre": res_json.get("Genre", "Cinema / Feature"),
                "director": res_json.get("Director", "N/A"),
                "actors": res_json.get("Actors", "N/A"),
                "plot": res_json.get("Plot", "Grab your snacks and join the cinema room for an epic community watch-party!"),
                "rating": res_json.get("imdbRating", "N/A"),
                "poster": poster,
            }
    except Exception as e:
        logger.debug(f"OMDb lookup failed: {e}")

    # 2. Wikipedia fallback for poster / plot if needed
    if not data or not data.get("poster"):
        try:
            wiki_search = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(clean_q)}&limit=3&namespace=0&format=json"
            req_w = urllib.request.Request(wiki_search, headers={"User-Agent": "RaiVibesBot/1.0"})
            with urllib.request.urlopen(req_w, timeout=5) as res_w:
                w_res = json.loads(res_w.read().decode())
            if len(w_res) > 1 and w_res[1]:
                wiki_title = w_res[1][0]
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(wiki_title)}"
                req_sum = urllib.request.Request(summary_url, headers={"User-Agent": "RaiVibesBot/1.0"})
                with urllib.request.urlopen(req_sum, timeout=5) as res_sum:
                    w_data = json.loads(res_sum.read().decode())
                poster = (w_data.get("originalimage") or {}).get("source") or (w_data.get("thumbnail") or {}).get("source")
                if not data:
                    data = {
                        "title": w_data.get("title", clean_q.title()),
                        "year": "",
                        "rated": "PG-13",
                        "runtime": "Feature Length",
                        "genre": "Movie / Watch-Party",
                        "director": "N/A",
                        "actors": "Community Squad",
                        "plot": w_data.get("extract", "Watch together with RAI FAM!"),
                        "rating": "N/A",
                        "poster": poster,
                    }
                elif not data.get("poster") and poster:
                    data["poster"] = poster
        except Exception as e:
            logger.debug(f"Wikipedia fallback failed: {e}")

    if not data:
        data = {
            "title": clean_q.title(),
            "year": "",
            "rated": "PG-13",
            "runtime": "Feature Length",
            "genre": "Movie / Watch-Party",
            "director": "N/A",
            "actors": "Community Squad",
            "plot": "Grab your snacks and join the cinema room for an epic watch-along!",
            "rating": "N/A",
            "poster": None,
        }
    return data


class MovieRSVPView(View):
    """Persistent RSVP & Voice Channel Join View for Cinema Announcements."""
    def __init__(self, room_id: Optional[int] = None, room_name: Optional[str] = None):
        super().__init__(timeout=None)
        if room_id:
            join_url = f"https://discord.com/channels/1457382179981099090/{room_id}"
            btn_label = f"🍿 Join {room_name or 'Screening Room'}"
            self.add_item(Button(label=btn_label, url=join_url, style=discord.ButtonStyle.link, row=0))
            chat_url = "https://discord.com/channels/1457382179981099090/1550584226376720476"
            self.add_item(Button(label="💬 Cinema Chat", url=chat_url, style=discord.ButtonStyle.link, row=0))

    @button(label="Count Me In! 🍿", style=discord.ButtonStyle.primary, custom_id="movie_rsvp_toggle_btn", row=0)
    async def rsvp_button(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        events = load_events()
        msg_id = str(interaction.message.id)

        if msg_id not in events:
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
            msg = "🍿 **RSVP Confirmed!** You're on the cinema roster. Enjoy the screening!"

        events[msg_id]["rsvps"] = rsvps
        save_events(events)

        # Update button label count
        btn.label = f"Count Me In! 🍿 ({len(rsvps)})"
        try:
            if interaction.message.embeds:
                embed = interaction.message.embeds[0]
                for i, field in enumerate(embed.fields):
                    if "Attendees" in field.name or "RSVP" in field.name:
                        embed.set_field_at(
                            i,
                            name=f"🍿 Attendees RSVP'd ({len(rsvps)})",
                            value=f"{len(rsvps)} members joining! Click the button below to RSVP.",
                            inline=False
                        )
                        break
                await interaction.message.edit(embed=embed, view=self)
        except Exception as e:
            logger.debug(f"Could not update event message: {e}")

        await interaction.followup.send(msg, ephemeral=True)


class MovieParty(commands.Cog):
    """Automated Movie Night, Anime Watch-Party & Cinema Announcement Hub."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="movienight",
        description="🎬 Automatically fetch movie details & post a Cinema Night announcement!"
    )
    @app_commands.describe(
        movie="Name of the movie (e.g., Rush, Interstellar, Spirited Away, Inception)",
        showtime="Showtime status (e.g. LIVE NOW, Tonight @ 9:00 PM IST, Friday 8 PM)",
        room="Voice screening room (default: 🍿 | Movie Time 1)",
        channel="Text announcement channel (default: 📢｜ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛꜱ)",
        ping="Choose who to ping with the announcement",
        note="Optional custom note from host (e.g. Bring your popcorn and headsets!)"
    )
    @app_commands.choices(ping=[
        app_commands.Choice(name="@everyone (All Members)", value="everyone"),
        app_commands.Choice(name="@here (Active Online Members)", value="here"),
        app_commands.Choice(name="No Ping", value="none")
    ])
    async def movienight(
        self,
        interaction: discord.Interaction,
        movie: str,
        showtime: Optional[str] = "LIVE NOW 🔴",
        room: Optional[discord.VoiceChannel] = None,
        channel: Optional[discord.TextChannel] = None,
        ping: Optional[str] = "everyone",
        note: Optional[str] = None
    ):
        # Always defer ephemerally so the caller's interaction never times out
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        # Check permissions: Founder or Admin or Manage Events
        is_founder = interaction.user.id in [FOUNDER_USER_ID, interaction.guild.owner_id]
        has_perm = (
            interaction.user.guild_permissions.administrator
            or interaction.user.guild_permissions.manage_events
            or interaction.user.guild_permissions.manage_guild
        )
        if not (is_founder or has_perm):
            await interaction.followup.send(
                "❌ **Restricted Access**: Only the Founder and Server Managers can broadcast movie announcements.",
                ephemeral=True
            )
            return

        # Inform the user that data is being fetched
        status_msg = await interaction.followup.send(
            f"⏳ Fetching theatrical data and poster for **\"{movie}\"**...",
            ephemeral=True
        )

        # Resolve channels
        target_channel = channel or interaction.guild.get_channel(DEFAULT_ANNOUNCEMENT_CHANNEL_ID) or interaction.channel
        screening_room = room or interaction.guild.get_channel(DEFAULT_VOICE_ROOM_ID)
        room_name = screening_room.name if screening_room else "Movie Time 1"
        room_id = screening_room.id if screening_room else DEFAULT_VOICE_ROOM_ID

        # Fetch metadata in background thread to keep bot responsive
        movie_data = await asyncio.to_thread(fetch_movie_metadata_sync, movie)

        title_display = f"{movie_data['title']}"
        if movie_data.get("year"):
            title_display += f" ({movie_data['year']})"

        embed = discord.Embed(
            title=f"🎬 RAI FAM CINEMA NIGHT: {title_display.upper()}",
            description=(
                f"Popcorn ready, volume up, and fasten your seatbelts! Tonight we are streaming **{title_display}** together in high definition!\n\n"
                f"*{note or movie_data.get('plot', 'Grab your snacks and join the cinema lounge for an epic community watch-party!')}*"
            ),
            color=0xFF007F
        )

        # 1. Screening Details Field
        room_mention = screening_room.mention if screening_room else f"`🍿 | {room_name}`"
        details_lines = [
            f"• 📅 **Showtime:** `{showtime}`",
            f"• 🎙️ **Screening Room:** {room_mention}",
            f"• 💬 **Live Chat:** <#1550584226376720476>",
            f"• 🎧 **Audio / Quality:** `1080p 60FPS Stereo Surround`",
            f"• 🍿 **Vibe:** Relaxed, high fidelity & open to all RAI FAM members!"
        ]
        embed.add_field(name="🎟️ Screening Details", value="\n".join(details_lines), inline=False)

        # 2. Film Overview Field
        info_lines = []
        if movie_data.get("rating") and movie_data.get("rating") != "N/A":
            info_lines.append(f"• ⭐ **Rating:** `{movie_data['rating']}/10 IMDb`")
        if movie_data.get("runtime") and movie_data.get("runtime") != "N/A":
            info_lines.append(f"• ⏱️ **Runtime:** `{movie_data['runtime']}`")
        if movie_data.get("rated") and movie_data.get("rated") != "N/A":
            info_lines.append(f"• 🏷️ **Rated:** `{movie_data['rated']}`")
        if movie_data.get("genre") and movie_data.get("genre") != "N/A":
            info_lines.append(f"• 🎭 **Genre:** `{movie_data['genre']}`")
        if movie_data.get("director") and movie_data.get("director") != "N/A":
            info_lines.append(f"• 🎬 **Director:** `{movie_data['director']}`")
        if movie_data.get("actors") and movie_data.get("actors") != "N/A":
            info_lines.append(f"• 🌟 **Starring:** `{movie_data['actors']}`")

        if info_lines:
            embed.add_field(name="🏁 Film Overview", value="\n".join(info_lines), inline=False)

        # 3. Synopsis Field (if a custom note was provided, we preserve the official plot here)
        if note and movie_data.get("plot"):
            embed.add_field(name="📖 Synopsis", value=f"*{movie_data['plot'][:1000]}*", inline=False)

        # 4. Poster Image
        if movie_data.get("poster") and movie_data["poster"].startswith("http"):
            embed.set_image(url=movie_data["poster"])
        else:
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3172/3172555.png")

        # 5. Attendees Field
        embed.add_field(
            name="🍿 Attendees RSVP'd (0)",
            value="Be the first to RSVP! Click the button below to join the roster.",
            inline=False
        )

        embed.set_footer(
            text="RAI FAM Cinema Lounge • Streamed in 1080p 60FPS • Grab your snacks!",
            icon_url=config.RAI_ICON_URL
        )

        # Ping content
        if ping == "everyone":
            content = "@everyone 🍿 **COMMUNITY MOVIE NIGHT ANNOUNCEMENT!**"
        elif ping == "here":
            content = "@here 🍿 **COMMUNITY MOVIE NIGHT ANNOUNCEMENT!**"
        else:
            content = "🍿 **COMMUNITY MOVIE NIGHT ANNOUNCEMENT!**"

        # Interactive view with Jump to Voice Channel button & RSVP counter
        view = MovieRSVPView(room_id=room_id, room_name=room_name)

        try:
            posted_msg = await target_channel.send(content=content, embed=embed, view=view)
        except Exception as e:
            await interaction.followup.send(
                f"❌ Failed to post in {target_channel.mention}: `{e}`. Make sure the bot has 'Send Messages' permissions.",
                ephemeral=True
            )
            return

        # Record in events file
        events = load_events()
        events[str(posted_msg.id)] = {
            "title": title_display,
            "showtime": showtime,
            "room_id": room_id,
            "channel_id": target_channel.id,
            "host_id": interaction.user.id,
            "rsvps": []
        }
        save_events(events)

        # Ephemeral confirmation to executor with jump link
        confirm_embed = discord.Embed(
            title="🍿 Cinema Announcement Published!",
            description=(
                f"✅ Official movie announcement for **{title_display}** is now published!\n\n"
                f"📢 **Channel:** {target_channel.mention}\n"
                f"🍿 **Voice Room:** {room_mention}\n"
                f"🔗 [**Jump to Announcement**]({posted_msg.jump_url})"
            ),
            color=0x2ECC71
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)

    @app_commands.command(
        name="movie",
        description="🎬 Quick shortcut to announce a Cinema Night / Watch-Party"
    )
    @app_commands.describe(
        movie="Name of the movie (e.g., Rush, Inception, Interstellar)",
        showtime="Showtime status (default: LIVE NOW 🔴)",
        ping="Choose who to ping with the announcement"
    )
    async def movie_shortcut(
        self,
        interaction: discord.Interaction,
        movie: str,
        showtime: Optional[str] = "LIVE NOW 🔴",
        ping: Optional[str] = "everyone"
    ):
        """Shortcut forwarding directly to movienight."""
        await self.movienight.callback(
            self,
            interaction=interaction,
            movie=movie,
            showtime=showtime,
            room=None,
            channel=None,
            ping=ping,
            note=None
        )


async def setup(bot: commands.Bot):
    await bot.add_cog(MovieParty(bot))
