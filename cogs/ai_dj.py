import asyncio
import os
import random
import re
import tempfile
import time
from pathlib import Path
from typing import Optional, Dict, Any

import discord
from discord import app_commands
from discord.ext import commands
import edge_tts

import config
from utils.ffmpeg_setup import get_ffmpeg_executable

VOICES = {
    "christopher": {
        "id": "en-US-ChristopherNeural",
        "name": "🎙️ Christopher (Deep FM Radio Host)",
        "lang": "en"
    },
    "jenny": {
        "id": "en-US-JennyNeural",
        "name": "🎧 Jenny (Chill Radio Host)",
        "lang": "en"
    },
    "sonia": {
        "id": "en-GB-SoniaNeural",
        "name": "📻 Sonia (British BBC Style)",
        "lang": "en"
    },
    "valluvar": {
        "id": "ta-IN-ValluvarNeural",
        "name": "🪕 Valluvar (Tamil Radio Host)",
        "lang": "ta"
    }
}

RADIO_INTROS = {
    "en": [
        "You're locked into 24/7 RAI VIBES FM! Up next, {title}. Crank up the volume!",
        "Broadcasting live in RAI FAM. Coming up next is {title} for everyone chilling in voice. Let's ride!",
        "Back to back bangers on RAI VIBES! Here comes {title}. Enjoy the sound!",
        "This is RAI VIBES Radio! Requested in voice: {title}. Turn it up!"
    ],
    "ta": [
        "இது உங்கள் RAI VIBES FM! அடுத்த பாடல் {title}. கேட்டு மகிழுங்கள்!",
        "RAI FAM குடும்பத்திற்கு அடுத்த அசத்தலான பாடல் {title}. என்ஜாய் பண்ணுங்க!",
        "24 மணி நேரமும் இசை மழை! அடுத்த பாடல் {title}."
    ]
}


class AIDJ(commands.Cog):
    """Spotify DJ X style Neural AI Radio Host for live voice commentary and transitions."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings: Dict[int, Dict[str, Any]] = {}
        self.temp_dir = Path(__file__).resolve().parent.parent / "data" / "temp_dj"
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.last_shoutout_time: Dict[int, float] = {}

    def is_enabled(self, guild_id: int) -> bool:
        return self.settings.get(guild_id, {}).get("enabled", False)

    def get_voice(self, guild_id: int) -> str:
        v_key = self.settings.get(guild_id, {}).get("voice", "christopher")
        return VOICES.get(v_key, VOICES["christopher"])["id"]

    def clean_song_title(self, raw_title: str) -> str:
        # Strip brackets, featuring, official video etc.
        title = re.sub(r'[\(\[][^()]*?[\)\]]', '', raw_title)
        title = re.sub(r'(?i)(official|video|audio|lyrics|hd|4k|remix|full song)', '', title)
        title = ' '.join(title.split()).strip()
        return title[:60] if title else raw_title[:60]

    async def generate_speech_file(self, text: str, voice_id: str) -> Optional[str]:
        try:
            filename = f"dj_{int(time.time() * 1000)}_{random.randint(100, 999)}.mp3"
            filepath = self.temp_dir / filename
            communicate = edge_tts.Communicate(text, voice_id)
            await communicate.save(str(filepath))
            return str(filepath)
        except Exception as e:
            print(f"[AI DJ TTS Error] {e}")
            return None

    async def play_transition(self, voice_client: discord.VoiceClient, song) -> None:
        """Plays a smooth 3-4 second AI radio transition before the song starts."""
        if not voice_client or not voice_client.is_connected():
            return

        guild_id = voice_client.guild.id
        v_key = self.settings.get(guild_id, {}).get("voice", "christopher")
        voice_info = VOICES.get(v_key, VOICES["christopher"])
        voice_id = voice_info["id"]
        lang = voice_info["lang"]

        clean_title = self.clean_song_title(song.title)
        templates = RADIO_INTROS.get(lang, RADIO_INTROS["en"])
        script = random.choice(templates).format(title=clean_title)

        filepath = await self.generate_speech_file(script, voice_id)
        if not filepath or not os.path.exists(filepath):
            return

        ffmpeg_bin = get_ffmpeg_executable()
        done_event = asyncio.Event()

        def _after(err):
            done_event.set()
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass

        try:
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()
                await asyncio.sleep(0.1)

            source = discord.FFmpegPCMAudio(
                filepath,
                executable=ffmpeg_bin,
                options="-vn -bufsize 2048k"
            )
            # Normal volume for DJ voice
            transformed = discord.PCMVolumeTransformer(source, volume=1.1)
            voice_client.play(transformed, after=_after)

            # Wait up to 6 seconds for DJ transition to finish cleanly
            await asyncio.wait_for(done_event.wait(), timeout=6.5)
        except (asyncio.TimeoutError, Exception) as e:
            print(f"[AI DJ Playback Note] {e}")
            try:
                if os.path.exists(filepath):
                    os.remove(filepath)
            except Exception:
                pass

    @app_commands.command(name="aidj", description="🎙️ Spotify DJ X AI Radio Host: Toggle live transitions and custom shoutouts!")
    @app_commands.describe(
        action="Action to perform with AI DJ",
        voice="Voice personality to use",
        shoutout_msg="Custom shoutout message to announce live in voice (costs 100 coins)"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="🟢 Turn ON (Live FM commentary between songs)", value="on"),
            app_commands.Choice(name="🔴 Turn OFF (Direct track playback)", value="off"),
            app_commands.Choice(name="🎙️ Change Radio Host Voice", value="voice"),
            app_commands.Choice(name="📢 Broadcast Voice Shoutout (100 coins)", value="shoutout"),
            app_commands.Choice(name="ℹ️ Status & Settings", value="status")
        ],
        voice=[
            app_commands.Choice(name="🎙️ Christopher (Deep FM Radio Host)", value="christopher"),
            app_commands.Choice(name="🎧 Jenny (Chill US Host)", value="jenny"),
            app_commands.Choice(name="📻 Sonia (British BBC Style)", value="sonia"),
            app_commands.Choice(name="🪕 Valluvar (Tamil Radio Host)", value="valluvar")
        ]
    )
    async def aidj(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        voice: Optional[app_commands.Choice[str]] = None,
        shoutout_msg: Optional[str] = None
    ):
        guild_id = interaction.guild_id
        if not guild_id:
            return await interaction.response.send_message("❌ This command must be used in a server.", ephemeral=True)

        if guild_id not in self.settings:
            self.settings[guild_id] = {"enabled": False, "voice": "christopher"}

        cur = self.settings[guild_id]

        if action.value == "on":
            cur["enabled"] = True
            v_info = VOICES.get(cur.get("voice", "christopher"), VOICES["christopher"])
            embed = discord.Embed(
                title="🎙️ AI Radio DJ • Online & Active",
                description=(
                    f"**Spotify DJ X style live commentary is now ENABLED!**\n\n"
                    f"• **Current Host:** `{v_info['name']}`\n"
                    f"• The AI DJ will now introduce queued tracks and add live radio station polish between songs!"
                ),
                color=config.COLOR_PRIMARY
            )
            embed.set_footer(text="RAI VIBES 💗 • Neural Audio DJ", icon_url=config.RAI_ICON_URL)
            return await interaction.response.send_message(embed=embed)

        elif action.value == "off":
            cur["enabled"] = False
            embed = discord.Embed(
                title="🎙️ AI Radio DJ • Disabled",
                description="Live radio commentary turned off. Songs will play directly without voice transitions.",
                color=config.COLOR_DARK
            )
            return await interaction.response.send_message(embed=embed)

        elif action.value == "voice":
            if not voice:
                return await interaction.response.send_message("❌ Please select a voice from the `voice` dropdown option.", ephemeral=True)
            cur["voice"] = voice.value
            v_info = VOICES[voice.value]
            embed = discord.Embed(
                title="🎙️ Radio Host Voice Updated",
                description=f"AI DJ host voice switched to: **{v_info['name']}**!",
                color=config.COLOR_PRIMARY
            )
            return await interaction.response.send_message(embed=embed)

        elif action.value == "shoutout":
            if not shoutout_msg:
                return await interaction.response.send_message("❌ Please provide a `shoutout_msg` to announce!", ephemeral=True)

            if len(shoutout_msg) > 150:
                return await interaction.response.send_message("❌ Shoutouts are capped at 150 characters for clean broadcast.", ephemeral=True)

            # Check economy balance
            from cogs.economy import load_economy, save_economy
            eco = load_economy()
            u_id = str(interaction.user.id)
            user_eco = eco.get(u_id, {"balance": 0})

            if user_eco.get("balance", 0) < 100:
                return await interaction.response.send_message(
                    f"❌ **Insufficient Coins!** A live voice shoutout costs `100 Coins`. Your balance: `{user_eco.get('balance', 0)} 🪙`.\n"
                    f"Earn coins using `/daily` or playing minigames in `#💸｜ᴏᴡᴏ-ᴄʜᴀᴛ`!",
                    ephemeral=True
                )

            # Deduct coins
            user_eco["balance"] -= 100
            eco[u_id] = user_eco
            save_economy(eco)

            # Check VC connection
            vc = interaction.guild.voice_client
            if not vc or not vc.is_connected():
                return await interaction.response.send_message(
                    "❌ The bot is not connected to any voice channel right now. Use `/play` or `/join` first!",
                    ephemeral=True
                )

            await interaction.response.send_message(
                f"📢 **Broadcasting Live Shoutout!** `{interaction.user.display_name}` spent `100 🪙` to take over the airwaves:\n"
                f"> *\"{shoutout_msg}\"*",
                ephemeral=False
            )

            # Generate and broadcast shoutout
            v_id = self.get_voice(guild_id)
            script = f"Live shoutout from {interaction.user.display_name}! {shoutout_msg}"
            filepath = await self.generate_speech_file(script, v_id)
            if filepath and os.path.exists(filepath):
                ffmpeg_bin = get_ffmpeg_executable()
                
                # If song playing, wait for slight pause or overlay
                done = asyncio.Event()
                def _after_shout(e):
                    done.set()
                    try:
                        if os.path.exists(filepath):
                            os.remove(filepath)
                    except Exception:
                        pass

                was_playing = vc.is_playing()
                if was_playing:
                    vc.pause()

                src = discord.FFmpegPCMAudio(filepath, executable=ffmpeg_bin)
                vc.play(discord.PCMVolumeTransformer(src, volume=1.2), after=_after_shout)
                
                try:
                    await asyncio.wait_for(done.wait(), timeout=10.0)
                except Exception:
                    pass

                if was_playing and vc.is_paused():
                    vc.resume()

        elif action.value == "status":
            enabled = cur.get("enabled", False)
            v_info = VOICES.get(cur.get("voice", "christopher"), VOICES["christopher"])
            embed = discord.Embed(
                title="🎙️ AI Radio DJ • System Dashboard",
                color=config.COLOR_PRIMARY if enabled else config.COLOR_DARK
            )
            embed.add_field(name="📻 Radio Commentary", value="🟢 **ACTIVE**" if enabled else "🔴 **OFF**", inline=True)
            embed.add_field(name="🎙️ Active Host", value=f"`{v_info['name']}`", inline=True)
            embed.add_field(name="💡 Quick Tip", value="Use `/aidj shoutout` to broadcast custom announcements live in VC for `100 🪙`!", inline=False)
            embed.set_footer(text="RAI VIBES 💗 • Spotify DJ X Audio Engine", icon_url=config.RAI_ICON_URL)
            return await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(AIDJ(bot))
