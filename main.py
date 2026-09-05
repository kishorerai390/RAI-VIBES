import os
import sys
import re
import asyncio
import logging

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import discord
from discord.ext import commands
import colorama
from colorama import Fore, Style

import config
from utils.ffmpeg_setup import get_ffmpeg_executable
from utils.persistent_views import (
    ColorRolesView,
    GamingRolesView,
    NotificationRolesView,
    IdentityRolesView
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

def create_bot(use_message_content: bool = True) -> commands.Bot:
    intents = discord.Intents.default()
    intents.voice_states = True
    intents.guilds = True
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
        
        activity = discord.Activity(
            type=discord.ActivityType.listening,
            name=f"{config.BOT_NAME} | /play & /help"
        )
        await b.change_presence(status=discord.Status.online, activity=activity)

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
        b.add_view(ColorRolesView())
        b.add_view(GamingRolesView())
        b.add_view(NotificationRolesView())
        b.add_view(IdentityRolesView())
        b.add_view(VoiceControlView())
        b.add_view(MusicPlayerView())

        # Synchronize slash commands directly to each guild for instant updates
        try:
            for guild in b.guilds:
                b.tree.copy_global_to(guild=guild)
                synced_guild = await b.tree.sync(guild=guild)
                logger.info(f"✨ Successfully synchronized {len(synced_guild)} dedicated Music & Vibe slash commands to '{guild.name}'!")
            synced = await b.tree.sync()
            logger.info(f"✨ Global slash commands tree synchronized ({len(synced)} commands).")
        except Exception as e:
            logger.error(f"Failed to synchronize slash commands: {e}")

        # Clean RF tags from all members on startup
        for guild in b.guilds:
            for member in guild.members:
                if member.bot or member.id == guild.owner_id:
                    continue
                nick = member.nick
                if not nick:
                    continue
                clean_nick = re.sub(r'^(?:RF\s*\|\s*|RF\s*・\s*|RF\s*\|\s*|RF\s+)', '', nick, flags=re.IGNORECASE).strip()
                global_name = member.global_name or member.name
                if clean_nick != nick:
                    try:
                        target_nick = clean_nick if clean_nick != global_name else None
                        await member.edit(nick=target_nick, reason="Remove RF clan tag prefix")
                        logger.info(f"✅ Cleaned RF tag: '{nick}' -> '{clean_nick}' (Reset: {target_nick is None})")
                    except Exception as e:
                        logger.debug(f"Could not clean nick for {member.name}: {e}")

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

        # 1. Dedicated Song Requests Channel Direct Queue (Zero-prefix)
        if "song-request" in message.channel.name.lower() or "requests" in message.channel.name.lower():
            if content and not content.startswith("/"):
                ctx = await b.get_context(message)
                try:
                    await message.delete()
                except Exception:
                    pass
                music_cog = b.get_cog("Music")
                if music_cog:
                    return await music_cog.play(ctx, query=content)

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
                return await music_cog.play(ctx, query=query)

        # 3. Direct Prefix Triggers: !play, !p
        play_prefixes = ["!play ", "!p "]
        matched_prefix = next((p for p in play_prefixes if lower.startswith(p)), None)

        if matched_prefix:
            query = content[len(matched_prefix):].strip()
            if query:
                ctx = await b.get_context(message)
                music_cog = b.get_cog("Music")
                if music_cog:
                    return await music_cog.play(ctx, query=query)

        # 4. Direct Simple Commands: !skip, !pause, !resume, !stop, !queue, !np, !radio
        simple_cmds = {
            "!skip": "skip",
            "!pause": "pause",
            "!resume": "resume",
            "!stop": "stop",
            "!queue": "queue",
            "!np": "nowplaying",
            "!radio": "radio"
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

    return b

async def load_cogs(bot_instance: commands.Bot):
    # Pure Music, Karaoke, Radio, Audio FX & Community Engine for RAI VIBES 💗
    initial_extensions = [
        "cogs.music",
        "cogs.radio",
        "cogs.filters",
        "cogs.lyrics",
        "cogs.favorites",
        "cogs.general",
        "cogs.voicehub",
        "cogs.levels",
        "cogs.minigames",
        "cogs.giveaways",
        "cogs.polls",
        "cogs.welcome",
        "cogs.qotd",
        "cogs.counting",
        "cogs.starboard",
    ]
    for extension in initial_extensions:
        try:
            await bot_instance.load_extension(extension)
            logger.info(f"Loaded audio extension: {extension}")
        except Exception as e:
            logger.error(f"Failed to load extension {extension}: {e}")

async def start_bot(use_message_content: bool = True):
    bot_instance = create_bot(use_message_content=use_message_content)
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
        await start_bot(use_message_content=True)
    except discord.errors.PrivilegedIntentsRequired:
        logger.warning(
            "[NOTICE] Message Content Intent is not enabled in Discord Developer Portal.\n"
            "[NOTICE] Slash commands (/play) work 100%, but to enable @APEX DJ play <song> text mentions,\n"
            "[NOTICE] go to https://discord.com/developers/applications -> APEX VIBES -> Bot -> Enable 'Message Content Intent'."
        )
        await start_bot(use_message_content=False)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}[RAI VIBES 💗] Shutting down cleanly. Good bye!")
