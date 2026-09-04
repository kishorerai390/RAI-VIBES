import os
import sys
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
    VerifyButtonView,
    ColorRolesView,
    GamingRolesView,
    NotificationRolesView,
    IdentityRolesView,
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
{Fore.CYAN}  ████████╗██╗  ██╗ ██████╗ ██████╗     ██╗   ██╗██╗██████╗ ███████╗███████╗
  ╚══██╔══╝██║  ██║██╔═══██╗██╔══██╗    ██║   ██║██║██╔══██╗██╔════╝██╔════╝
     ██║   ███████║██║   ██║██████╔╝    ██║   ██║██║██████╔╝█████╗  ███████╗
     ██║   ██╔══██║██║   ██║██╔══██╗    ╚██╗ ██╔╝██║██╔══██╗██╔══╝  ╚════██║
     ██║   ██║  ██║╚██████╔╝██║  ██║     ╚████╔╝ ██║██████╔╝███████╗███████║
     ╚═╝   ╚═╝  ╚═╝ ╚═════╝ ╚═╝  ╚═╝      ╚═══╝  ╚═╝╚═════╝ ╚══════╝╚══════╝
{Fore.YELLOW}          ⚡ COMMAND THE POWER • HEAR THE RHYTHM • DISCORD MUSIC BOT ⚡
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

        logger.info(f"{config.BOT_NAME} is ONLINE & ready to play music in your server!")

    async def setup_hook():
        # Register Persistent Views before gateway connection so buttons work 100% of the time
        b.add_view(VerifyButtonView())
        b.add_view(ColorRolesView())
        b.add_view(GamingRolesView())
        b.add_view(NotificationRolesView())
        b.add_view(IdentityRolesView())
        b.add_view(TicketCreateView())
        b.add_view(TicketCloseView())
        logger.info("Registered all persistent interaction views in setup_hook.")

    b.setup_hook = setup_hook

    @b.event
    async def on_message(message: discord.Message):
        if message.author.bot or not message.guild:
            return

        content = message.content.strip()
        lower = content.lower()

        # 0. Dedicated Song Requests Channel Direct Queue (Zero-prefix)
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

        # 1. Direct Play triggers: /play, !play, play, /p, !p, p
        play_prefixes = ["/play ", "!play ", "play ", "/p ", "!p ", "p "]
        matched_prefix = next((p for p in play_prefixes if lower.startswith(p)), None)

        if matched_prefix:
            query = content[len(matched_prefix):].strip()
            if query:
                ctx = await b.get_context(message)
                music_cog = b.get_cog("Music")
                if music_cog:
                    return await music_cog.play(ctx, query=query)

        # 2. Direct Simple Commands: /skip, /pause, /resume, /stop, /queue, /np, /radio
        simple_cmds = {
            "/skip": "skip", "!skip": "skip", "skip": "skip",
            "/pause": "pause", "!pause": "pause", "pause": "pause",
            "/resume": "resume", "!resume": "resume", "resume": "resume",
            "/stop": "stop", "!stop": "stop", "stop": "stop",
            "/queue": "queue", "!queue": "queue", "queue": "queue",
            "/np": "nowplaying", "!np": "nowplaying", "np": "nowplaying",
            "/nowplaying": "nowplaying", "!nowplaying": "nowplaying",
            "/radio": "radio", "!radio": "radio"
        }
        if lower in simple_cmds:
            cmd_name = simple_cmds[lower]
            ctx = await b.get_context(message)
            cmd = b.get_command(cmd_name)
            if cmd:
                return await ctx.invoke(cmd)

        # 3. Mention Triggers (e.g. @RAI VIBES song)
        mention_clean = f"<@{b.user.id}>"
        mention_nick = f"<@!{b.user.id}>"

        if content.startswith(mention_clean) or content.startswith(mention_nick) or (b.user in message.mentions and not message.mention_everyone):
            raw_text = content.replace(mention_clean, "").replace(mention_nick, "").strip()
            if raw_text:
                query = raw_text
                if query.lower().startswith("play "):
                    query = query[5:].strip()
                elif query.lower().startswith("p "):
                    query = query[2:].strip()

                ctx = await b.get_context(message)
                music_cog = b.get_cog("Music")
                if music_cog:
                    return await music_cog.play(ctx, query=query)

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
    # Pure Music, Radio & Audio FX Engine for RAI VIBES 💗
    initial_extensions = [
        "cogs.music",
        "cogs.radio",
        "cogs.filters",
        "cogs.lyrics",
        "cogs.favorites",
        "cogs.general",
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
