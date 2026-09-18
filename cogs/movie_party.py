import os
import json
import time
import asyncio
import logging
import datetime
import urllib.request
import urllib.parse
from pathlib import Path
from typing import Optional, Dict, List

import requests
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, button

import config

logger = logging.getLogger("MovieParty")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EVENTS_FILE = DATA_DIR / "movie_events.json"
SUGGESTIONS_FILE = DATA_DIR / "movie_suggestions.json"

DEFAULT_ANNOUNCEMENT_CHANNEL_ID = 1545502718792175646  # 📢｜ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛꜱ
DEFAULT_VOICE_ROOM_ID = 1550196955660029964           # 🍿 | Movie Time 1
CINEMA_CHAT_CHANNEL_ID = 1550584226376720476          # 🍿｜ᴄɪɴᴇᴍᴀ-ᴄʜᴀᴛ
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


def load_suggestions() -> Dict[str, dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SUGGESTIONS_FILE.exists():
        try:
            with open(SUGGESTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_suggestions(data: Dict[str, dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(SUGGESTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save movie suggestions: {e}")


async def set_voice_channel_status(channel_id: int, status_text: str):
    """Sets Discord native voice channel status text displayed next to voice channels."""
    token = config.DISCORD_TOKEN
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    url = f"https://discord.com/api/v10/channels/{channel_id}/voice-status"

    def _put():
        return requests.put(url, headers=headers, json={"status": status_text[:500]})

    try:
        res = await asyncio.to_thread(_put)
        if res.status_code in [200, 204]:
            logger.info(f"✨ Set voice status on channel {channel_id} -> '{status_text}'")
    except Exception as e:
        logger.debug(f"Failed to update voice channel status: {e}")


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
            chat_url = f"https://discord.com/channels/1457382179981099090/{CINEMA_CHAT_CHANNEL_ID}"
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


class MovieVoteView(View):
    """Persistent voting view for community movie suggestions."""
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Upvote 👍 (0)", style=discord.ButtonStyle.success, custom_id="movie_vote_up_btn", row=0)
    async def upvote_btn(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        suggestions = load_suggestions()
        msg_id = str(interaction.message.id)

        if msg_id not in suggestions:
            suggestions[msg_id] = {"upvotes": [], "downvotes": []}

        s_data = suggestions[msg_id]
        uid = interaction.user.id

        if uid in s_data.get("upvotes", []):
            s_data["upvotes"].remove(uid)
            msg = "⚪ Removed your upvote."
        else:
            if uid not in s_data["upvotes"]:
                s_data["upvotes"].append(uid)
            if uid in s_data.get("downvotes", []):
                s_data["downvotes"].remove(uid)
            msg = "👍 **Upvoted!** You voted in favor of this movie."

        save_suggestions(suggestions)
        await self._update_message(interaction, s_data)
        await interaction.followup.send(msg, ephemeral=True)

    @button(label="Downvote 👎 (0)", style=discord.ButtonStyle.danger, custom_id="movie_vote_down_btn", row=0)
    async def downvote_btn(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        suggestions = load_suggestions()
        msg_id = str(interaction.message.id)

        if msg_id not in suggestions:
            suggestions[msg_id] = {"upvotes": [], "downvotes": []}

        s_data = suggestions[msg_id]
        uid = interaction.user.id

        if uid in s_data.get("downvotes", []):
            s_data["downvotes"].remove(uid)
            msg = "⚪ Removed your downvote."
        else:
            if uid not in s_data["downvotes"]:
                s_data["downvotes"].append(uid)
            if uid in s_data.get("upvotes", []):
                s_data["upvotes"].remove(uid)
            msg = "👎 **Downvoted.** You voted against this movie."

        save_suggestions(suggestions)
        await self._update_message(interaction, s_data)
        await interaction.followup.send(msg, ephemeral=True)

    async def _update_message(self, interaction: discord.Interaction, s_data: dict):
        up_count = len(s_data.get("upvotes", []))
        down_count = len(s_data.get("downvotes", []))

        for child in self.children:
            if getattr(child, "custom_id", None) == "movie_vote_up_btn":
                child.label = f"Upvote 👍 ({up_count})"
            elif getattr(child, "custom_id", None) == "movie_vote_down_btn":
                child.label = f"Downvote 👎 ({down_count})"

        try:
            if interaction.message.embeds:
                embed = interaction.message.embeds[0]
                for i, field in enumerate(embed.fields):
                    if "Community Votes" in field.name or "Votes" in field.name:
                        embed.set_field_at(
                            i,
                            name="📊 Community Votes",
                            value=f"👍 **Upvotes:** `{up_count}`  •  👎 **Downvotes:** `{down_count}`",
                            inline=False
                        )
                        break
                await interaction.message.edit(embed=embed, view=self)
        except Exception as e:
            logger.debug(f"Could not update suggestion embed: {e}")


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
        note="Optional custom note from host (e.g. Bring your popcorn and headsets!)",
        create_event="Whether to publish a native Discord Scheduled Event banner"
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
        note: Optional[str] = None,
        create_event: Optional[bool] = False
    ):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

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

        status_msg = await interaction.followup.send(
            f"⏳ Fetching theatrical data and poster for **\"{movie}\"**...",
            ephemeral=True
        )

        target_channel = channel or interaction.guild.get_channel(DEFAULT_ANNOUNCEMENT_CHANNEL_ID) or interaction.channel
        screening_room = room or interaction.guild.get_channel(DEFAULT_VOICE_ROOM_ID)
        room_name = screening_room.name if screening_room else "Movie Time 1"
        room_id = screening_room.id if screening_room else DEFAULT_VOICE_ROOM_ID

        movie_data = await asyncio.to_thread(fetch_movie_metadata_sync, movie)

        title_display = f"{movie_data['title']}"
        if movie_data.get("year"):
            title_display += f" ({movie_data['year']})"

        # 1. Update Voice Channel Status live
        voice_status_text = f"🎬 {title_display}"
        if movie_data.get("rating") and movie_data.get("rating") != "N/A":
            voice_status_text += f" • ⭐ {movie_data['rating']}"
        await set_voice_channel_status(room_id, voice_status_text)

        # 2. Build Announcement Embed
        embed = discord.Embed(
            title=f"🎬 RAI FAM CINEMA NIGHT: {title_display.upper()}",
            description=(
                f"Popcorn ready, volume up, and fasten your seatbelts! Tonight we are streaming **{title_display}** together in high definition!\n\n"
                f"*{note or movie_data.get('plot', 'Grab your snacks and join the cinema lounge for an epic community watch-party!')}*"
            ),
            color=0xFF007F
        )

        room_mention = screening_room.mention if screening_room else f"`🍿 | {room_name}`"
        details_lines = [
            f"• 📅 **Showtime:** `{showtime}`",
            f"• 🎙️ **Screening Room:** {room_mention}",
            f"• 💬 **Live Chat:** <#{CINEMA_CHAT_CHANNEL_ID}>",
            f"• 🎧 **Audio / Quality:** `1080p 60FPS Stereo Surround`",
            f"• 🍿 **Vibe:** Relaxed, high fidelity & open to all RAI FAM members!"
        ]
        embed.add_field(name="🎟️ Screening Details", value="\n".join(details_lines), inline=False)

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

        if note and movie_data.get("plot"):
            embed.add_field(name="📖 Synopsis", value=f"*{movie_data['plot'][:1000]}*", inline=False)

        if movie_data.get("poster") and movie_data["poster"].startswith("http"):
            embed.set_image(url=movie_data["poster"])
        else:
            embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/3172/3172555.png")

        embed.add_field(
            name="🍿 Attendees RSVP'd (0)",
            value="Be the first to RSVP! Click the button below to join the roster.",
            inline=False
        )

        embed.set_footer(
            text="RAI FAM Cinema Lounge • Streamed in 1080p 60FPS • Grab your snacks!",
            icon_url=config.RAI_ICON_URL
        )

        if ping == "everyone":
            content = "@everyone 🍿 **COMMUNITY MOVIE NIGHT ANNOUNCEMENT!**"
        elif ping == "here":
            content = "@here 🍿 **COMMUNITY MOVIE NIGHT ANNOUNCEMENT!**"
        else:
            content = "🍿 **COMMUNITY MOVIE NIGHT ANNOUNCEMENT!**"

        view = MovieRSVPView(room_id=room_id, room_name=room_name)

        try:
            posted_msg = await target_channel.send(content=content, embed=embed, view=view)
        except Exception as e:
            await interaction.followup.send(
                f"❌ Failed to post in {target_channel.mention}: `{e}`. Make sure the bot has 'Send Messages' permissions.",
                ephemeral=True
            )
            return

        # 3. Create Discord Scheduled Event if requested
        if create_event and interaction.guild:
            try:
                start_iso = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=10)).isoformat()
                event_payload = {
                    "channel_id": str(room_id),
                    "name": f"🎬 {title_display} Screening",
                    "privacy_level": 2,
                    "scheduled_start_time": start_iso,
                    "entity_type": 2,
                    "description": f"Community Watch-Party in {room_name}!\n\nSynopsis:\n{movie_data.get('plot', '')[:800]}"
                }
                headers = {"Authorization": f"Bot {config.DISCORD_TOKEN}", "Content-Type": "application/json"}
                await asyncio.to_thread(
                    requests.post,
                    f"https://discord.com/api/v10/guilds/{interaction.guild.id}/scheduled-events",
                    headers=headers,
                    json=event_payload
                )
            except Exception as e:
                logger.debug(f"Event creation notice: {e}")

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

        confirm_embed = discord.Embed(
            title="🍿 Cinema Announcement Published!",
            description=(
                f"✅ Official movie announcement for **{title_display}** is now published!\n\n"
                f"📢 **Channel:** {target_channel.mention}\n"
                f"🍿 **Voice Room:** {room_mention}\n"
                f"💬 **Live Discussion:** <#{CINEMA_CHAT_CHANNEL_ID}>\n"
                f"✨ **Voice Status:** Updated to `{voice_status_text}`\n"
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
            note=None,
            create_event=False
        )

    @app_commands.command(
        name="movieend",
        description="🎬 End the movie screening, reset voice channel status & unmute viewers"
    )
    @app_commands.describe(room="Voice screening room (default: 🍿 | Movie Time 1)")
    async def movieend(
        self,
        interaction: discord.Interaction,
        room: Optional[discord.VoiceChannel] = None
    ):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        is_founder = interaction.user.id in [FOUNDER_USER_ID, interaction.guild.owner_id]
        has_perm = interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_events
        if not (is_founder or has_perm):
            await interaction.followup.send("❌ Only the Founder and Event Hosts can end screenings.", ephemeral=True)
            return

        screening_room = room or interaction.guild.get_channel(DEFAULT_VOICE_ROOM_ID)
        room_id = screening_room.id if screening_room else DEFAULT_VOICE_ROOM_ID

        # Reset Voice Channel Status
        await set_voice_channel_status(room_id, "🍿 Grab your popcorn & relax")

        # Unmute everyone and restore speak permissions
        if screening_room:
            try:
                ow = screening_room.overwrites_for(interaction.guild.default_role)
                ow.speak = True
                await screening_room.set_permissions(interaction.guild.default_role, overwrite=ow)
                for member in screening_room.members:
                    if member.voice and member.voice.mute:
                        try:
                            await member.edit(mute=False, reason="Movie Screening Ended")
                        except Exception:
                            pass
            except Exception as e:
                logger.debug(f"Reset permissions error: {e}")

        embed = discord.Embed(
            title="🎬 Movie Screening Concluded",
            description=(
                f"✅ Voice status reset to `🍿 Grab your popcorn & relax` in {screening_room.mention if screening_room else 'screening room'}.\n"
                f"🎙️ Microphones unmuted for post-movie discussions.\n"
                f"💬 Head over to <#{CINEMA_CHAT_CHANNEL_ID}> to share your reviews and ratings!"
            ),
            color=0x2ECC71
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="cinemamute",
        description="🤫 Mute viewers in screening room so movie audio plays in crystal clarity"
    )
    @app_commands.describe(room="Voice screening room (default: 🍿 | Movie Time 1)")
    async def cinemamute(
        self,
        interaction: discord.Interaction,
        room: Optional[discord.VoiceChannel] = None
    ):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        is_founder = interaction.user.id in [FOUNDER_USER_ID, interaction.guild.owner_id]
        has_perm = interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_events
        if not (is_founder or has_perm):
            await interaction.followup.send("❌ Only the Founder and Event Hosts can activate Cinema Silence.", ephemeral=True)
            return

        screening_room = room or interaction.guild.get_channel(DEFAULT_VOICE_ROOM_ID)
        if not screening_room:
            await interaction.followup.send("❌ Voice channel not found.", ephemeral=True)
            return

        # 1. Disable speaking for @everyone
        ow = screening_room.overwrites_for(interaction.guild.default_role)
        ow.speak = False
        await screening_room.set_permissions(interaction.guild.default_role, overwrite=ow)

        # 2. Server mute non-admins currently connected
        muted_count = 0
        for member in screening_room.members:
            if not member.guild_permissions.administrator and member.id != FOUNDER_USER_ID:
                try:
                    await member.edit(mute=True, reason="Cinema Silence Mode")
                    muted_count += 1
                except Exception:
                    pass

        embed = discord.Embed(
            title="🤫 Cinema Silence Mode Activated",
            description=(
                f"🔒 Speaking permissions locked in {screening_room.mention} ({muted_count} viewers muted).\n"
                f"🎧 Movie audio will now play cleanly without mic echo or background noise.\n"
                f"💬 Members can react and chat live in <#{CINEMA_CHAT_CHANNEL_ID}>!"
            ),
            color=0xFF007F
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="cinemaunmute",
        description="🎙️ Restore voice permissions in screening room for post-movie chat"
    )
    @app_commands.describe(room="Voice screening room (default: 🍿 | Movie Time 1)")
    async def cinemaunmute(
        self,
        interaction: discord.Interaction,
        room: Optional[discord.VoiceChannel] = None
    ):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        is_founder = interaction.user.id in [FOUNDER_USER_ID, interaction.guild.owner_id]
        has_perm = interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_events
        if not (is_founder or has_perm):
            await interaction.followup.send("❌ Only the Founder and Event Hosts can deactivate Cinema Silence.", ephemeral=True)
            return

        screening_room = room or interaction.guild.get_channel(DEFAULT_VOICE_ROOM_ID)
        if not screening_room:
            await interaction.followup.send("❌ Voice channel not found.", ephemeral=True)
            return

        # 1. Restore speaking for @everyone
        ow = screening_room.overwrites_for(interaction.guild.default_role)
        ow.speak = True
        await screening_room.set_permissions(interaction.guild.default_role, overwrite=ow)

        # 2. Unmute members
        unmuted_count = 0
        for member in screening_room.members:
            if member.voice and member.voice.mute:
                try:
                    await member.edit(mute=False, reason="Cinema Silence Mode Deactivated")
                    unmuted_count += 1
                except Exception:
                    pass

        embed = discord.Embed(
            title="🎙️ Cinema Silence Mode Deactivated",
            description=(
                f"✅ Speaking permissions restored in {screening_room.mention} ({unmuted_count} unmuted).\n"
                f"🗣️ Mics are now open for post-movie discussions!"
            ),
            color=0x2ECC71
        )
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name="moviesuggest",
        description="💡 Suggest a movie to watch with IMDb rating & community voting!"
    )
    @app_commands.describe(movie="Title of the movie to suggest (e.g. Inception, Interstellar, Spirited Away)")
    async def moviesuggest(
        self,
        interaction: discord.Interaction,
        movie: str
    ):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        movie_data = await asyncio.to_thread(fetch_movie_metadata_sync, movie)
        title_display = f"{movie_data['title']}"
        if movie_data.get("year"):
            title_display += f" ({movie_data['year']})"

        cinema_chat = interaction.guild.get_channel(CINEMA_CHAT_CHANNEL_ID) or interaction.channel

        embed = discord.Embed(
            title=f"💡 MOVIE NIGHT SUGGESTION: {title_display.upper()}",
            description=(
                f"🎬 Suggested by {interaction.user.mention} for upcoming community cinema night!\n\n"
                f"*{movie_data.get('plot', 'Vote below if you want to watch this film together!')}*"
            ),
            color=0xFF007F
        )

        specs = []
        if movie_data.get("rating") and movie_data.get("rating") != "N/A":
            specs.append(f"• ⭐ **IMDb Rating:** `{movie_data['rating']}/10`")
        if movie_data.get("runtime") and movie_data.get("runtime") != "N/A":
            specs.append(f"• ⏱️ **Runtime:** `{movie_data['runtime']}`")
        if movie_data.get("rated") and movie_data.get("rated") != "N/A":
            specs.append(f"• 🏷️ **Rated:** `{movie_data['rated']}`")
        if movie_data.get("genre") and movie_data.get("genre") != "N/A":
            specs.append(f"• 🎭 **Genre:** `{movie_data['genre']}`")
        if specs:
            embed.add_field(name="🎟️ Film Overview", value="\n".join(specs), inline=False)

        crew = []
        if movie_data.get("director") and movie_data.get("director") != "N/A":
            crew.append(f"• 🎬 **Director:** `{movie_data['director']}`")
        if movie_data.get("actors") and movie_data.get("actors") != "N/A":
            crew.append(f"• 🌟 **Starring:** `{movie_data['actors']}`")
        if crew:
            embed.add_field(name="👥 Cast & Crew", value="\n".join(crew), inline=False)

        embed.add_field(
            name="📊 Community Votes",
            value="👍 **Upvotes:** `0`  •  👎 **Downvotes:** `0`",
            inline=False
        )

        if movie_data.get("poster") and movie_data["poster"].startswith("http"):
            embed.set_image(url=movie_data["poster"])

        embed.set_footer(
            text="RAI FAM Cinema Hub • Click buttons below to vote for this movie!",
            icon_url=config.RAI_ICON_URL
        )

        view = MovieVoteView()
        msg = await cinema_chat.send(embed=embed, view=view)

        suggestions = load_suggestions()
        suggestions[str(msg.id)] = {
            "title": title_display,
            "suggester_id": interaction.user.id,
            "upvotes": [],
            "downvotes": []
        }
        save_suggestions(suggestions)

        confirm_embed = discord.Embed(
            title="🍿 Movie Suggestion Submitted!",
            description=(
                f"✅ **{title_display}** has been posted to {cinema_chat.mention}!\n"
                f"Members can now vote on your suggestion.\n"
                f"🔗 [**Jump to Suggestion**]({msg.jump_url})"
            ),
            color=0x2ECC71
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(MovieParty(bot))
