import os
import sys
import socket
import asyncio
import logging

# Ensure single instance of RAI SENTINEL using OS-level local socket mutex
_instance_lock_socket = None

def acquire_instance_lock(port: int = 59125) -> bool:
    global _instance_lock_socket
    if _instance_lock_socket is not None:
        return True
    _instance_lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        _instance_lock_socket.bind(("127.0.0.1", port))
        return True
    except OSError:
        print(f"[CRITICAL] Another instance of RAI SENTINEL is already running (Port {port} in use)!")
        print("[CRITICAL] Exiting immediately to prevent duplicate responses and message spam.")
        sys.exit(0)

import discord
from discord.ext import commands
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("RaiSentinel")

BOT_NAME = "AEGIS 🛡️"

BANNER = """
  █████╗ ███████╗ ██████╗ ██╗███████╗
 ██╔══██╗██╔════╝██╔════╝ ██║██╔════╝
 ███████║█████╗  ██║  ███╗██║███████╗
 ██╔══██║██╔══╝  ██║   ██║██║╚════██║
 ██║  ██║███████╗╚██████╔╝██║███████║
 ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝╚══════╝
           🛡️ AEGIS DEFENSE • VERIFICATION • TICKETS • SENTINEL 🛡️
"""

def create_security_bot(use_members: bool = True, use_message_content: bool = True) -> commands.Bot:
    intents = discord.Intents.default()
    intents.guilds = True
    if use_members:
        intents.members = True
    if use_message_content:
        intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

    @bot.event
    async def on_ready():
        print(BANNER)
        logger.info(f"🛡️ Logged in as: {bot.user.name}#{bot.user.discriminator} ({bot.user.id})")
        logger.info(f"🛡️ Guarding {len(bot.guilds)} server(s)")

        activity = discord.Activity(
            type=discord.ActivityType.watching,
            name="AEGIS Defense • Security • Welcome 🛡️"
        )
        await bot.change_presence(status=discord.Status.dnd, activity=activity)
        
        # Set nickname in guilds
        for guild in bot.guilds:
            try:
                me = guild.me or await guild.fetch_member(bot.user.id)
                if me and me.guild_permissions.change_nickname:
                    await me.edit(nick=BOT_NAME)
            except Exception:
                pass

        # Register Persistent Views for Verification, Tickets, and Self-Roles
        from utils.persistent_views import (
            VerifyButtonView, TicketCreateView, TicketCloseView,
            GamingRolesView, NotificationRolesView, IdentityRolesView, ColorRolesView
        )
        from cogs.tickets import PersistentTicketLauncherView, TicketChannelControlView
        for view_cls in [
            VerifyButtonView, TicketCreateView, TicketCloseView,
            PersistentTicketLauncherView, TicketChannelControlView,
            GamingRolesView, NotificationRolesView, IdentityRolesView, ColorRolesView
        ]:
            try:
                bot.add_view(view_cls())
            except Exception as e:
                logger.debug(f"View init note: {e}")

        # Update Sentinel bot banner to animated GIF
        banner_path = os.path.join("assets", "rai_sentinel_banner.gif")
        if os.path.exists(banner_path):
            try:
                if not bot.user.banner or not str(bot.user.banner).startswith("a_"):
                    with open(banner_path, "rb") as f:
                        await bot.user.edit(banner=f.read())
                    logger.info("✨ [RAI SENTINEL] Successfully applied animated GIF profile banner!")
            except Exception as e:
                logger.debug(f"[RAI SENTINEL] Banner update notice: {e}")

        # Synchronize slash commands directly to each guild for instant response
        try:
            for guild in bot.guilds:
                bot.tree.copy_global_to(guild=guild)
                synced_guild = await bot.tree.sync(guild=guild)
                logger.info(f"🛡️ Instant-synced {len(synced_guild)} security slash commands to '{guild.name}'")
            synced = await bot.tree.sync()
            logger.info(f"🛡️ Synchronized {len(synced)} global Security slash commands.")
        except Exception as e:
            logger.error(f"Failed to sync security commands: {e}")

    @bot.tree.error
    async def on_app_command_error(interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        logger.error(f"Security slash command error: {error}")
        msg = "❌ An error occurred while executing this command."
        if isinstance(error, discord.app_commands.MissingPermissions):
            msg = "❌ You require Staff / Moderator permissions to use this command."

        try:
            if not interaction.response.is_done():
                await interaction.response.send_message(msg, ephemeral=True)
            else:
                await interaction.followup.send(msg, ephemeral=True)
        except Exception:
            pass

    return bot

async def start_sentinel(token: str, use_members: bool = True, use_message_content: bool = True):
    bot = create_security_bot(use_members=use_members, use_message_content=use_message_content)
    
    # Sentinel manages Autonomous Defense, Anti-Nuke, Anti-Raid, and Tickets
    security_extensions = [
        "cogs.autoprovision",
        "cogs.tickets",
        "cogs.moderation",
        "cogs.antinuke",
        "cogs.antiraid",
        "cogs.antispam",
        "cogs.antimention",
        "cogs.antilink",
        "cogs.whitelist",
        "cogs.security_dashboard",
    ]
    import database
    await database.init_db()

    for ext in security_extensions:
        try:
            await bot.load_extension(ext)
            logger.info(f"Loaded Sentinel module: {ext}")
        except Exception as e:
            logger.error(f"Could not load {ext}: {e}")

    await bot.start(token)

async def main():
    token = os.getenv("SECURITY_BOT_TOKEN")
    if not token or token == "YOUR_DISCORD_BOT_TOKEN_HERE":
        print("[RAI SENTINEL] Missing bot token! Please set SECURITY_BOT_TOKEN in .env")
        return

    logger.info("[RAI SENTINEL] Connecting with standard intents...")
    await start_sentinel(token, use_members=False, use_message_content=False)

if __name__ == "__main__":
    acquire_instance_lock(59125)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[RAI SENTINEL 🛡️] Shutting down cleanly.")
