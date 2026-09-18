import os
import sys
import re
import socket
import asyncio
import logging

# Ensure single instance of RAI VIBES using OS-level local socket mutex
_instance_lock_socket = None

def acquire_instance_lock(port: int = 59124) -> bool:
    global _instance_lock_socket
    if _instance_lock_socket is not None:
        return True
    _instance_lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _instance_lock_socket.bind(("127.0.0.1", port))
        return True
    except OSError:
        print(f"[CRITICAL] Another instance of bot is already running (Port {port} in use)!")
        print("[CRITICAL] Exiting immediately to prevent duplicate responses and message spam.")
        sys.exit(0)

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import discord
from discord.ext import commands, tasks
import colorama
from colorama import Fore, Style

import config
from utils.ffmpeg_setup import get_ffmpeg_executable
from utils.persistent_views import (
    ColorRolesView,
    GamingRolesView,
    NotificationRolesView,
    IdentityRolesView,
    ServerGuideView,
    GamingHubStationView,
    TicketCreateView,
    TicketCloseView
)

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("RaiVibes")

BANNER = f"""
{Fore.MAGENTA}  ██████╗  █████╗ ██╗    ██╗   ██╗██╗██████╗ ███████╗███████╗
{Fore.MAGENTA}  ██╔══██╗██╔══██╗██║    ██║   ██║██║██╔══██╗██╔════╝██╔════╝
{Fore.CYAN}  ██████╔╝███████║██║    ██║   ██║██║██████╔╝█████╗  ███████╗
{Fore.CYAN}  ██╔══██╗██╔══██║██║    ╚██╗ ██╔╝██║██╔══██╗██╔══╝  ╚════██║
{Fore.MAGENTA}  ██║  ██║██║  ██║██║     ╚████╔╝ ██║██████╔╝███████╗███████║
{Fore.MAGENTA}  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝      ╚═══╝  ╚═╝╚═════╝ ╚══════╝╚══════╝
{Fore.LIGHTMAGENTA_EX}          💗 COMMAND THE VIBE • HEAR THE RHYTHM • DISCORD MUSIC BOT 💗
"""

def create_bot(use_members: bool = True, use_message_content: bool = True) -> commands.Bot:
    intents = discord.Intents.default()
    intents.voice_states = True
    intents.guilds = True
    if use_members:
        intents.members = True
    if use_message_content:
        intents.message_content = True

    b = commands.Bot(
        command_prefix=commands.when_mentioned_or(config.BOT_PREFIX),
        intents=intents,
        help_command=None
    )

    @b.event
    async def on_ready():
        print(BANNER)
        logger.info(f"Logged in as: {b.user.name}#{b.user.discriminator} (ID: {b.user.id})")
        logger.info(f"Connected to {len(b.guilds)} Discord server(s)")
        
        # Dynamic Presence Rotator (Item 48)
        presences = [
            discord.Streaming(name="🌸 24/7 Lo-Fi Chill Hop • /play", url="https://twitch.tv/lofigirl"),
            discord.Activity(type=discord.ActivityType.watching, name="🎮 Gaming Hub & Tourneys • /lfg"),
            discord.Activity(type=discord.ActivityType.listening, name="🍅 Focus Lounges • /pomodoro"),
            discord.Activity(type=discord.ActivityType.playing, name="🪙 High Rollers Casino • /spin"),
            discord.Activity(type=discord.ActivityType.watching, name="🛡️ Guarding RAI FAM 💗 • /telemetry")
        ]

        @tasks.loop(minutes=3)
        async def status_rotator():
            idx = getattr(status_rotator, "idx", 0)
            try:
                await b.change_presence(activity=presences[idx % len(presences)])
                status_rotator.idx = idx + 1
            except Exception:
                pass

        if not hasattr(b, "_status_rotator_started"):
            b._status_rotator_started = True
            status_rotator.start()

        # Automatically update server nickname to match RAI VIBES
        for guild in b.guilds:
            try:
                me = guild.me or await guild.fetch_member(b.user.id)
                if me and me.guild_permissions.change_nickname:
                    await me.edit(nick=config.BOT_NAME)
                    logger.info(f"Updated bot nickname to '{config.BOT_NAME}' in '{guild.name}'")
            except Exception as e:
                logger.debug(f"Could not change nickname in {guild.name}: {e}")

        # Register Persistent Views for instant interaction without timeout
        from cogs.voicehub import VoiceControlView
        from utils.views import MusicPlayerView
        from cogs.entry_sound import PublicEntrySoundLaunchView
        b.add_view(ColorRolesView())
        b.add_view(GamingRolesView())
        b.add_view(NotificationRolesView())
        b.add_view(IdentityRolesView())
        b.add_view(VoiceControlView())
        b.add_view(MusicPlayerView())
        b.add_view(PublicEntrySoundLaunchView())
        b.add_view(ServerGuideView())

        # Update bot profile banner to animated GIF
        banner_path = os.path.join("assets", "rai_vibes_banner.gif")
        if os.path.exists(banner_path):
            try:
                if not b.user.banner or not str(b.user.banner).startswith("a_"):
                    with open(banner_path, "rb") as f:
                        await b.user.edit(banner=f.read())
                    logger.info("✨ [RAI VIBES] Successfully applied animated GIF profile banner!")
            except Exception as e:
                logger.debug(f"[RAI VIBES] Banner update notice: {e}")

        # Attempt to set server banner (succeeds if server has Boost Level 2)
        fam_banner_path = os.path.join("assets", "rai_fam_server_banner.gif")
        if os.path.exists(fam_banner_path):
            target_guild = b.get_guild(1457382179981099090)
            if target_guild:
                try:
                    with open(fam_banner_path, "rb") as f:
                        await target_guild.edit(banner=f.read())
                    logger.info("✨ Successfully set animated GIF server banner for RAI FAM!")
                except Exception as e:
                    logger.info(f"Server banner note (requires Server Boost Level 2): {e}")

        # Synchronize slash commands directly to each guild for instant sub-second response
        try:
            for guild in b.guilds:
                b.tree.copy_global_to(guild=guild)
                synced_guild = await b.tree.sync(guild=guild)
                logger.info(f"✨ Instant-synced {len(synced_guild)} slash commands to '{guild.name}'")
            synced = await b.tree.sync()
            logger.info(f"✨ Synchronized {len(synced)} global Music slash commands.")
        except Exception as e:
            logger.error(f"Failed to synchronize slash commands: {e}")

        logger.info(f"{config.BOT_NAME} is ONLINE & ready to play music in your server!")

    @b.before_invoke
    async def auto_defer_commands(ctx: commands.Context):
        """Immediately defers slash command interactions to prevent 'didn't respond in time' timeouts."""
        if ctx.interaction and not ctx.interaction.response.is_done():
            try:
                await ctx.defer()
            except Exception:
                pass

    @b.command(name="sync")
    @commands.is_owner()
    async def sync_cmd(ctx: commands.Context):
        """Owner command to sync slash commands with Discord."""
        synced = await b.tree.sync()
        await ctx.send(f"✅ Successfully synchronized {len(synced)} slash commands!")

    @b.event
    async def on_message(message: discord.Message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip()
        lower = content.lower()

        # 0. Suggestions Auto-Reactions & Voting
        if "suggestion" in message.channel.name.lower():
            if not content.startswith("/"):
                try:
                    await message.add_reaction("👍")
                    await message.add_reaction("👎")
                except Exception:
                    pass

        # Media & Showcase Channels Automated Aesthetic Reactions
        ch_name = message.channel.name.lower()
        if any(k in ch_name for k in ["ꜱᴇᴛᴜᴘ", "setup", "desk"]):
            if message.attachments or "http" in content:
                try:
                    await message.add_reaction("💻")
                    await message.add_reaction("🔥")
                except Exception:
                    pass
        elif any(k in ch_name for k in ["ᴄʀᴇᴀᴛɪᴠᴇ", "art", "creative"]):
            if message.attachments or "http" in content:
                try:
                    await message.add_reaction("🎨")
                    await message.add_reaction("⭐")
                except Exception:
                    pass
        elif any(k in ch_name for k in ["ᴍᴜꜱɪᴄ-ꜱʜᴀʀɪɴɢ", "music-sharing"]):
            if "http" in content or "spotify" in lower or "youtu" in lower or "soundcloud" in lower:
                try:
                    await message.add_reaction("🎧")
                    await message.add_reaction("💜")
                except Exception:
                    pass
        elif any(k in ch_name for k in ["ᴏᴜᴛ-ᴏꜰ-ᴄᴏɴᴛᴇxᴛ", "context"]):
            try:
                await message.add_reaction("💀")
                await message.add_reaction("📸")
            except Exception:
                pass

        # 1. Dedicated Song Requests Channel Direct Queue (Zero-prefix)
        if message.channel.id == 1545534637122527332 or "song-request" in message.channel.name.lower() or "requests" in message.channel.name.lower() or "ꜱᴏɴɢ" in message.channel.name:
            if content and not content.startswith("/"):
                ctx = await b.get_context(message)
                try:
                    await message.delete()
                except Exception:
                    pass
                music_cog = b.get_cog("Music")
                if music_cog:
                    return await music_cog.play(ctx, song=content)

        # 2. Check if bot is mentioned (e.g. @RAI VIBES /play song, @RAI VIBES 💗/play song, @RAI VIBES song)
        if b.user in message.mentions and not message.mention_everyone:
            raw_text = re.sub(rf"<@!?{b.user.id}>", "", content).strip()
            # Strip bot nickname trailing emojis/text like 💗, 💖, 🌸
            raw_text = re.sub(r'^[💗💖🌸✨\s]+', '', raw_text).strip()
            ctx = await b.get_context(message)
            music_cog = b.get_cog("Music")

            if not raw_text:
                embed = discord.Embed(
                    title="🌸 RAI VIBES 💗 • Music Bot",
                    description="Need music? Type `@RAI VIBES <song name>` or `!play <song>` or `/play <song>`!",
                    color=config.COLOR_PRIMARY
                )
                embed.set_footer(text="RAI VIBES 💗 • Rythm Sound Engine", icon_url=config.RAI_ICON_URL)
                return await message.channel.send(embed=embed)

            # Check if mention is a simple command
            mention_lower = raw_text.lower().strip()
            simple_mention_cmds = {
                "skip": "skip", "/skip": "skip", "!skip": "skip", "s": "skip",
                "pause": "pause", "/pause": "pause", "!pause": "pause",
                "resume": "resume", "/resume": "resume", "!resume": "resume", "unpause": "resume",
                "stop": "stop", "/stop": "stop", "!stop": "stop", "dc": "stop", "leave": "stop",
                "queue": "queue", "/queue": "queue", "!queue": "queue", "q": "queue",
                "np": "nowplaying", "/np": "nowplaying", "!np": "nowplaying", "nowplaying": "nowplaying",
                "loop": "loop", "/loop": "loop", "!loop": "loop", "repeat": "loop",
                "shuffle": "shuffle", "/shuffle": "shuffle", "!shuffle": "shuffle",
                "clear": "clearqueue", "cq": "clearqueue", "/clearqueue": "clearqueue",
                "replay": "replay", "restart": "replay"
            }
            if mention_lower in simple_mention_cmds:
                cmd = b.get_command(simple_mention_cmds[mention_lower])
                if cmd:
                    return await ctx.invoke(cmd)

            # Extract clean song query or direct URL
            url_match = re.search(r"https?://\S+", raw_text)
            if url_match:
                query = url_match.group(0).strip()
            else:
                query = raw_text
                prefixes_to_strip = [
                    "/play ", "!play ", "play ", "/p ", "!p ", "p ", "/search ", "!search ", "search ",
                    "/play", "!play", "play", "/p", "!p"
                ]
                for prefix in prefixes_to_strip:
                    if query.lower().startswith(prefix):
                        query = query[len(prefix):].strip()
                        break

            if query and music_cog:
                return await music_cog.play(ctx, song=query)

        # 3. Direct Prefix Triggers: !play, !p
        play_prefixes = ["!play ", "!p "]
        matched_prefix = next((p for p in play_prefixes if lower.startswith(p)), None)

        if matched_prefix:
            query = content[len(matched_prefix):].strip()
            if query:
                ctx = await b.get_context(message)
                music_cog = b.get_cog("Music")
                if music_cog:
                    return await music_cog.play(ctx, song=query)

        # 4. Direct Simple Commands: !skip, !pause, !resume, !stop, !queue, !np
        simple_cmds = {
            "!skip": "skip",
            "!pause": "pause",
            "!resume": "resume",
            "!stop": "stop",
            "!queue": "queue",
            "!np": "nowplaying"
        }
        if lower in simple_cmds:
            cmd_name = simple_cmds[lower]
            ctx = await b.get_context(message)
            cmd = b.get_command(cmd_name)
            if cmd:
                return await ctx.invoke(cmd)

        await b.process_commands(message)

    @b.event
    async def on_command_error(ctx: commands.Context, error: Exception):
        if isinstance(error, commands.CommandNotFound):
            return
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(f"Missing argument: `{error.param.name}`. Example: `/play <song name>`")
        elif isinstance(error, commands.CheckFailure):
            await ctx.send("You don't have permission to execute this command.")
        else:
            logger.error(f"Error executing command '{ctx.command}': {error}")
            try:
                if ctx.interaction and ctx.interaction.response.is_done():
                    await ctx.interaction.followup.send(f"An error occurred: `{error}`", ephemeral=True)
                else:
                    await ctx.send(f"An error occurred: `{error}`")
            except Exception:
                pass

    @b.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        cmd_name = interaction.command.name if interaction.command else "Unknown"
        logger.error(f"Slash command error ({cmd_name}): {error}")
        if isinstance(error, discord.app_commands.CommandOnCooldown):
            msg = f"⏳ Command `{cmd_name}` is on cooldown. Try again in `{error.retry_after:.1f}s`."
        elif isinstance(error, discord.app_commands.MissingPermissions):
            msg = "❌ You lack the required permissions to execute this command."
        elif "voice" in str(error).lower() and cmd_name in ["play", "radio", "join", "stop", "pause", "resume", "skip", "equalizer", "eq"]:
            msg = "❌ Make sure you are connected to an active voice channel!"
        else:
            msg = f"❌ An error occurred while executing `/{cmd_name}`: `{error}`"

        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            pass

    return b

async def load_cogs(bot_instance: commands.Bot):
    # 100% Pure Music, Radio, Audio FX & Autonomous Auto-Updater for RAI VIBES 💗
    initial_extensions = [
        "cogs.music",
        "cogs.filters",
        "cogs.lyrics",
        "cogs.favorites",
        "cogs.voicehub",
        "cogs.soundboard",
        "cogs.dj",
        "cogs.music_quiz",
        "cogs.radio",
        "cogs.entry_sound",
        "cogs.auto_updater",
    ]

    for extension in initial_extensions:
        try:
            await bot_instance.load_extension(extension)
            logger.info(f"Loaded audio extension: {extension}")
        except Exception as e:
            logger.error(f"Failed to load extension {extension}: {e}")

async def start_bot(use_members: bool = True, use_message_content: bool = True):
    bot_instance = create_bot(use_members=use_members, use_message_content=use_message_content)
    async with bot_instance:
        await load_cogs(bot_instance)
        await bot_instance.start(config.DISCORD_TOKEN)

async def main():
    if not config.DISCORD_TOKEN or config.DISCORD_TOKEN == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print(BANNER)
        print("=" * 70)
        print("[CONFIGURATION ERROR] Discord Bot Token is missing!")
        print("Please open the '.env' file in this directory and paste your token:")
        print("DISCORD_BOT_TOKEN=your_actual_token_here")
        print("Get your token from: https://discord.com/developers/applications")
        print("=" * 70)
        return

    # Verify or setup FFmpeg
    ffmpeg_path = get_ffmpeg_executable()
    logger.info(f"FFmpeg ready at: {ffmpeg_path}")

    try:
        await start_bot(use_members=True, use_message_content=True)
    except discord.errors.PrivilegedIntentsRequired:
        logger.warning(
            "[NOTICE] Privileged Intents (Server Members or Message Content) not enabled in Developer Portal.\n"
            "[NOTICE] To enable automatic Welcome Cards on join, enable 'SERVER MEMBERS INTENT' at:\n"
            "[NOTICE] https://discord.com/developers/applications -> Bot -> Privileged Gateway Intents."
        )
        try:
            await start_bot(use_members=False, use_message_content=True)
        except discord.errors.PrivilegedIntentsRequired:
            await start_bot(use_members=False, use_message_content=False)

if __name__ == "__main__":
    acquire_instance_lock(59124)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[RAI VIBES 💗] Shutting down cleanly. Good bye!")
