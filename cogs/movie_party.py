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
from discord.ext import commands, tasks
from discord.ui import View, Button, button

import config
from utils.ffmpeg_setup import get_ffmpeg_executable

logger = logging.getLogger("MovieParty")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
EVENTS_FILE = DATA_DIR / "movie_events.json"
SUGGESTIONS_FILE = DATA_DIR / "movie_suggestions.json"

DEFAULT_ANNOUNCEMENT_CHANNEL_ID = 1545502718792175646  # 📢｜ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛꜱ
DEFAULT_VOICE_ROOM_ID = 1550196955660029964           # 🍿 | Movie Time 1
OVERFLOW_VOICE_ROOM_ID = 1550198444021514331          # 🍿 | Movie Time 2
CINEMA_CHAT_CHANNEL_ID = 1550584226376720476          # 🍿｜ᴄɪɴᴇᴍᴀ-ᴄʜᴀᴛ
CINEMA_HOST_ROLE_ID = 1550588116077645914             # 🎙️ Cinema Host
FOUNDER_USER_ID = 1457380609641938981

LOFI_STREAM_URL = "https://stream.zeno.fm/f3wvbbqmdg8uv"

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin",
    "options": "-vn -b:a 96k"
}


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


def get_content_advisory_badge(rated: str) -> str:
    """Returns color-coded MPAA maturity advisory badges."""
    clean_r = (rated or "PG-13").strip().upper()
    advisories = {
        "G": "🟢 **Rated G** • General Audiences (All Ages Admitted)",
        "PG": "🟢 **Rated PG** • Parental Guidance Suggested",
        "PG-13": "🟡 **Rated PG-13** • Parents Strongly Cautioned (May be inappropriate for pre-teens)",
        "R": "🔴 **Rated R** • Mature Audiences Only (Age 17+ / Intense Action, Language & Themes)",
        "NC-17": "⛔ **Rated NC-17** • Adults Only (Strictly 18+)",
        "TV-MA": "🔴 **Rated TV-MA** • Mature Audience Only",
        "TV-14": "🟡 **Rated TV-14** • Parents Strongly Cautioned",
        "NOT RATED": "⚪ **Unrated** • Viewer Discretion Advised",
    }
    return advisories.get(clean_r, f"🟡 **Rated {clean_r}** • Viewer Discretion Advised")


def fetch_movie_metadata_sync(query: str) -> dict:
    """Fetch movie metadata, rating, synopsis, and HD theatrical poster from OMDb and Wikipedia."""
    import re
    clean_q = query.strip()
    data = {}

    year_match = re.search(r"\(?\b(19\d\d|20\d\d)\b\)?", clean_q)
    extracted_year = year_match.group(1) if year_match else None
    search_title = re.sub(r"\(?\b(19\d\d|20\d\d)\b\)?", "", clean_q).strip()
    search_title = re.sub(r"[\(\)]", "", search_title).strip() or clean_q

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
            msg = "🍿 **RSVP Confirmed!** You'll receive a showtime alert before screening begins!"

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
            if uid not in s_data.get("upvotes", []):
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
            if uid not in s_data.get("downvotes", []):
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
        self._last_overflow_alert = 0

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Monitors capacity in Movie Time 1 and alerts overflow to Movie Time 2 (Item 16)."""
        if after.channel and after.channel.id == DEFAULT_VOICE_ROOM_ID:
            count = len(after.channel.members)
            limit = after.channel.user_limit or 25
            now = time.time()
            if count >= limit and (now - self._last_overflow_alert) > 300:
                self._last_overflow_alert = now
                cinema_chat = member.guild.get_channel(CINEMA_CHAT_CHANNEL_ID)
                if cinema_chat:
                    overflow_vc = member.guild.get_channel(OVERFLOW_VOICE_ROOM_ID)
                    embed = discord.Embed(
                        title="⚠️ 🍿 Main Cinema Hall Reached Full Capacity!",
                        description=(
                            f"<#{DEFAULT_VOICE_ROOM_ID}> has reached **{count}/{limit} viewers**!\n\n"
                            f"🛋️ Please join the cozy overflow room in {overflow_vc.mention if overflow_vc else 'Movie Time 2'} "
                            f"to enjoy the synchronized stream without lag!"
                        ),
                        color=0xF1C40F
                    )
                    view = View()
                    if overflow_vc:
                        join_url = f"https://discord.com/channels/{member.guild.id}/{overflow_vc.id}"
                        view.add_item(Button(label="🍿 Join Movie Time 2", url=join_url, style=discord.ButtonStyle.link))
                    try:
                        await cinema_chat.send(embed=embed, view=view)
                    except Exception as e:
                        logger.debug(f"Overflow alert note: {e}")

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

        # Item 15: Cinema Auto-Bitrate Boost
        if screening_room and screening_room.bitrate < 96000:
            try:
                await screening_room.edit(bitrate=96000)
            except Exception:
                pass

        # Item 17: Dynamic Room Renaming
        if screening_room:
            try:
                clean_short_title = movie_data["title"][:18].strip()
                await screening_room.edit(name=f"🎬 | Screening: {clean_short_title}")
            except Exception as e:
                logger.debug(f"Dynamic room rename notice: {e}")

        # Item 14: Host Priority Speaker Role
        host_role = interaction.guild.get_role(CINEMA_HOST_ROLE_ID)
        if host_role and host_role not in interaction.user.roles:
            try:
                await interaction.user.add_roles(host_role, reason="Cinema Screening Host")
            except Exception:
                pass

        # Live Voice Channel Status
        voice_status_text = f"🎬 {title_display}"
        if movie_data.get("rating") and movie_data.get("rating") != "N/A":
            voice_status_text += f" • ⭐ {movie_data['rating']}"
        await set_voice_channel_status(room_id, voice_status_text)

        # Item 11: Content & Age Advisory Badge
        advisory_badge = get_content_advisory_badge(movie_data.get("rated", "PG-13"))

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
            f"• 🏷️ **Advisory:** {advisory_badge}",
            f"• 🎧 **Audio / Quality:** `96 kbps 1080p 60FPS Stereo Surround`",
            f"• 🍿 **Vibe:** Relaxed, high fidelity & open to all RAI FAM members!"
        ]
        embed.add_field(name="🎟️ Screening Details", value="\n".join(details_lines), inline=False)

        info_lines = []
        if movie_data.get("rating") and movie_data.get("rating") != "N/A":
            info_lines.append(f"• ⭐ **Rating:** `{movie_data['rating']}/10 IMDb`")
        if movie_data.get("runtime") and movie_data.get("runtime") != "N/A":
            info_lines.append(f"• ⏱️ **Runtime:** `{movie_data['runtime']}`")
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
                f"❌ Failed to post in {target_channel.mention}: `{e}`.",
                ephemeral=True
            )
            return

        # Discord Scheduled Event if requested
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
                f"🏷️ **Advisory:** {advisory_badge}\n"
                f"🔗 [**Jump to Announcement**]({posted_msg.jump_url})"
            ),
            color=0x2ECC71
        )
        await interaction.followup.send(embed=confirm_embed, ephemeral=True)

    @app_commands.command(
        name="moviecountdown",
        description="⏳ Launch a live showtime countdown timer in Cinema Chat (Item 1)"
    )
    @app_commands.describe(
        minutes="Minutes remaining until movie starts (e.g. 10, 15, 30)",
        movie="Optional movie title"
    )
    async def moviecountdown(
        self,
        interaction: discord.Interaction,
        minutes: int,
        movie: Optional[str] = None
    ):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        is_founder = interaction.user.id in [FOUNDER_USER_ID, interaction.guild.owner_id]
        has_perm = interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_events
        if not (is_founder or has_perm):
            return await interaction.followup.send("❌ Only Event Hosts can launch count downs.", ephemeral=True)

        cinema_chat = interaction.guild.get_channel(CINEMA_CHAT_CHANNEL_ID) or interaction.channel
        target_ts = int(time.time() + (minutes * 60))
        movie_name = movie or "Cinema Night Feature Film"

        embed = discord.Embed(
            title=f"⏳ SHOWTIME COUNTDOWN: {movie_name.upper()}",
            description=(
                f"🍿 Grab your snacks, refill your drinks, and take your seats!\n\n"
                f"🕒 **Starts:** <t:{target_ts}:R> (<t:{target_ts}:t>)\n"
                f"🎙️ **Screening Hall:** <#{DEFAULT_VOICE_ROOM_ID}>\n"
                f"💬 **Live Chat:** <#{CINEMA_CHAT_CHANNEL_ID}>"
            ),
            color=0xF1C40F
        )
        embed.set_footer(text="RAI FAM Cinema Lounge • Fasten your seatbelts!", icon_url=config.RAI_ICON_URL)

        view = View()
        join_url = f"https://discord.com/channels/{interaction.guild.id}/{DEFAULT_VOICE_ROOM_ID}"
        view.add_item(Button(label="🍿 Join Screening Hall", url=join_url, style=discord.ButtonStyle.link))

        msg = await cinema_chat.send(content="@here 🍿 **SHOWTIME COUNTDOWN INITIATED!**", embed=embed, view=view)
        await interaction.followup.send(f"✅ Showtime countdown posted to {cinema_chat.mention}! [Jump]({msg.jump_url})", ephemeral=True)

    @app_commands.command(
        name="moviealert",
        description="📢 Send automated showtime mention alerts to all RSVP'd guests (Item 3)"
    )
    async def moviealert(self, interaction: discord.Interaction):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        is_founder = interaction.user.id in [FOUNDER_USER_ID, interaction.guild.owner_id]
        has_perm = interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_events
        if not (is_founder or has_perm):
            return await interaction.followup.send("❌ Only Event Hosts can broadcast alerts.", ephemeral=True)

        events = load_events()
        all_rsvps = set()
        for ev in events.values():
            for uid in ev.get("rsvps", []):
                all_rsvps.add(uid)

        cinema_chat = interaction.guild.get_channel(CINEMA_CHAT_CHANNEL_ID) or interaction.channel
        if not all_rsvps:
            return await interaction.followup.send("ℹ️ No RSVP'd members found in the cinema roster yet.", ephemeral=True)

        mentions = " ".join(f"<@{uid}>" for uid in list(all_rsvps)[:25])
        alert_text = (
            f"🍿 **LAST CALL FOR SHOWTIME!** {mentions}\n\n"
            f"The lights are dimming and screening is starting now in <#{DEFAULT_VOICE_ROOM_ID}>! "
            f"Fasten your seatbelts and grab your popcorn!"
        )
        await cinema_chat.send(alert_text)
        await interaction.followup.send(f"✅ Broadcasted showtime call to {len(all_rsvps)} RSVP'd guests in {cinema_chat.mention}!", ephemeral=True)

    @app_commands.command(
        name="cinemaintro",
        description="🔊 Play the official THX / Dolby style cinematic intro chime in voice! (Item 4)"
    )
    @app_commands.describe(room="Voice screening room (default: 🍿 | Movie Time 1)")
    async def cinemaintro(
        self,
        interaction: discord.Interaction,
        room: Optional[discord.VoiceChannel] = None
    ):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        is_founder = interaction.user.id in [FOUNDER_USER_ID, interaction.guild.owner_id]
        has_perm = interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_events
        if not (is_founder or has_perm):
            return await interaction.followup.send("❌ Only Event Hosts can play cinema intro sound.", ephemeral=True)

        screening_room = room or interaction.guild.get_channel(DEFAULT_VOICE_ROOM_ID)
        if not screening_room:
            return await interaction.followup.send("❌ Voice channel not found.", ephemeral=True)

        sound_path = Path(__file__).resolve().parent.parent / "assets" / "cinema_intro.wav"
        if not sound_path.exists():
            return await interaction.followup.send("❌ Cinema intro audio file not found.", ephemeral=True)

        try:
            vc = interaction.guild.voice_client
            if not vc:
                vc = await screening_room.connect()
            elif vc.channel.id != screening_room.id:
                await vc.move_to(screening_room)

            if vc.is_playing():
                vc.stop()

            ffmpeg_bin = get_ffmpeg_executable()
            source = discord.FFmpegPCMAudio(str(sound_path), executable=ffmpeg_bin)
            vc.play(source)

            await interaction.followup.send(
                f"🔊 **Playing Cinematic Intro Chime** in {screening_room.mention}! *Fasten your seatbelts!*",
                ephemeral=True
            )
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to play intro sound: `{e}`", ephemeral=True)

    @app_commands.command(
        name="cinemastage",
        description="🎙️ Toggle Stage Broadcast Mode: host presents, audience listens (Item 18)"
    )
    @app_commands.describe(
        enabled="Enable or disable Stage Broadcast Mode",
        room="Voice screening room (default: 🍿 | Movie Time 1)"
    )
    async def cinemastage(
        self,
        interaction: discord.Interaction,
        enabled: bool,
        room: Optional[discord.VoiceChannel] = None
    ):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        is_founder = interaction.user.id in [FOUNDER_USER_ID, interaction.guild.owner_id]
        has_perm = interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_events
        if not (is_founder or has_perm):
            return await interaction.followup.send("❌ Only Event Hosts can toggle Stage Mode.", ephemeral=True)

        screening_room = room or interaction.guild.get_channel(DEFAULT_VOICE_ROOM_ID)
        if not screening_room:
            return await interaction.followup.send("❌ Voice channel not found.", ephemeral=True)

        ow = screening_room.overwrites_for(interaction.guild.default_role)
        ow.speak = not enabled
        await screening_room.set_permissions(interaction.guild.default_role, overwrite=ow)

        host_role = interaction.guild.get_role(CINEMA_HOST_ROLE_ID)
        if enabled:
            if host_role and host_role not in interaction.user.roles:
                try:
                    await interaction.user.add_roles(host_role, reason="Stage Host")
                except Exception:
                    pass
            await set_voice_channel_status(screening_room.id, "🎙️ Stage Broadcast Mode • Host Presenting")
            for m in screening_room.members:
                if not m.guild_permissions.administrator and m.id != FOUNDER_USER_ID:
                    try:
                        await m.edit(mute=True, reason="Stage Mode Enabled")
                    except Exception:
                        pass
            msg = f"🎙️ **Stage Mode ENABLED** in {screening_room.mention}. Only hosts can speak; audience is listening."
        else:
            await set_voice_channel_status(screening_room.id, "🍿 Grab your popcorn & relax")
            for m in screening_room.members:
                if m.voice and m.voice.mute:
                    try:
                        await m.edit(mute=False, reason="Stage Mode Disabled")
                    except Exception:
                        pass
            msg = f"🎙️ **Stage Mode DISABLED** in {screening_room.mention}. Microphones restored for everyone."

        await interaction.followup.send(msg, ephemeral=True)

    @app_commands.command(
        name="cinemaambience",
        description="🌧️ Stream 24/7 Midnight Cinema Lo-Fi & Rain Ambience (Item 27)"
    )
    @app_commands.describe(
        action="Start or stop ambient stream",
        room="Voice room (default: 🍿 | Movie Time 2)"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="Start Midnight Ambience", value="start"),
        app_commands.Choice(name="Stop Ambience", value="stop")
    ])
    async def cinemaambience(
        self,
        interaction: discord.Interaction,
        action: str,
        room: Optional[discord.VoiceChannel] = None
    ):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        target_room = room or interaction.guild.get_channel(OVERFLOW_VOICE_ROOM_ID)
        if not target_room:
            return await interaction.followup.send("❌ Room not found.", ephemeral=True)

        if action == "start":
            try:
                vc = interaction.guild.voice_client
                if not vc:
                    vc = await target_room.connect()
                elif vc.channel.id != target_room.id:
                    await vc.move_to(target_room)

                if vc.is_playing():
                    vc.stop()

                ffmpeg_bin = get_ffmpeg_executable()
                source = discord.FFmpegPCMAudio(LOFI_STREAM_URL, executable=ffmpeg_bin, **FFMPEG_OPTIONS)
                vc.play(source)

                await set_voice_channel_status(target_room.id, "🌧️ Midnight Cinema Ambience • Relax & Chill")
                await interaction.followup.send(
                    f"🌧️ **Midnight Cinema Ambience Started** in {target_room.mention}! Streaming 24/7 lo-fi chill audio.",
                    ephemeral=True
                )
            except Exception as e:
                await interaction.followup.send(f"❌ Ambience error: `{e}`", ephemeral=True)
        else:
            vc = interaction.guild.voice_client
            if vc and vc.is_playing():
                vc.stop()
            if vc:
                await vc.disconnect()
            await set_voice_channel_status(target_room.id, "🍿 Grab your popcorn & relax")
            await interaction.followup.send(f"⏹️ Midnight Cinema Ambience stopped in {target_room.mention}.", ephemeral=True)

    @app_commands.command(
        name="movierename",
        description="🏷️ Temporarily rename screening room to the movie title (Item 17)"
    )
    @app_commands.describe(
        title="Title of the movie",
        room="Voice room (default: 🍿 | Movie Time 1)"
    )
    async def movierename(
        self,
        interaction: discord.Interaction,
        title: str,
        room: Optional[discord.VoiceChannel] = None
    ):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        is_founder = interaction.user.id in [FOUNDER_USER_ID, interaction.guild.owner_id]
        has_perm = interaction.user.guild_permissions.administrator or interaction.user.guild_permissions.manage_events
        if not (is_founder or has_perm):
            return await interaction.followup.send("❌ Only Event Hosts can rename rooms.", ephemeral=True)

        screening_room = room or interaction.guild.get_channel(DEFAULT_VOICE_ROOM_ID)
        if not screening_room:
            return await interaction.followup.send("❌ Room not found.", ephemeral=True)

        new_name = f"🎬 | Screening: {title[:18].strip()}"
        try:
            await screening_room.edit(name=new_name)
            await interaction.followup.send(f"✅ Renamed {screening_room.mention} to `{new_name}`!", ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Failed to rename: `{e}`", ephemeral=True)

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

        await set_voice_channel_status(room_id, "🍿 Grab your popcorn & relax")

        # Revert room name
        if screening_room:
            try:
                await screening_room.edit(name="🍿 | Movie Time 1")
            except Exception:
                pass

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

        ow = screening_room.overwrites_for(interaction.guild.default_role)
        ow.speak = False
        await screening_room.set_permissions(interaction.guild.default_role, overwrite=ow)

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

        ow = screening_room.overwrites_for(interaction.guild.default_role)
        ow.speak = True
        await screening_room.set_permissions(interaction.guild.default_role, overwrite=ow)

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

        advisory_badge = get_content_advisory_badge(movie_data.get("rated", "PG-13"))

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
        specs.append(f"• 🏷️ **Advisory:** {advisory_badge}")
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
