import os
import sys
import asyncio
import logging
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

BOT_NAME = "RAI SENTINEL 🛡️"

BANNER = """
  ██████╗  █████╗ ██╗    ███████╗███████╗███╗   ██╗████████╗██╗███╗   ██╗███████╗██╗     
  ██╔══██╗██╔══██╗██║    ██╔════╝██╔════╝████╗  ██║╚══██╔══╝██║████╗  ██║██╔════╝██║     
  ██████╔╝███████║██║    ███████╗█████╗  ██╔██╗ ██║   ██║   ██║██╔██╗ ██║█████╗  ██║     
  ██╔══██╗██╔══██║██║    ╚════██║██╔══╝  ██║╚██╗██║   ██║   ██║██║╚██╗██║██╔══╝  ██║     
  ██║  ██║██║  ██║██║    ███████║███████╗██║ ╚████║   ██║   ██║██║ ╚████║███████╗███████╗
  ╚═╝  ╚═╝╚═╝  ╚═╝╚═╝    ╚══════╝╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚═╝╚═╝  ╚═══╝╚══════╝╚══════╝
           🛡️ AUTOMATED WELCOME • VERIFICATION • TICKETS • SERVER SENTINEL 🛡️
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
            name="RAI FAM Security • Welcome • Tickets 🛡️"
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

        # Register Persistent Views for Verification, Tickets and Welcome
        from utils.persistent_views import VerifyButtonView, TicketCreateView, TicketCloseView
        from cogs.welcome import WelcomeQuickActionsView
        for view_cls in [VerifyButtonView, TicketCreateView, TicketCloseView, WelcomeQuickActionsView]:
            try:
                bot.add_view(view_cls())
            except Exception as e:
                logger.debug(f"View init note: {e}")

        try:
            for guild in bot.guilds:
                bot.tree.copy_global_to(guild=guild)
                await bot.tree.sync(guild=guild)
            synced = await bot.tree.sync()
            logger.info(f"🛡️ Synchronized {len(synced)} Security, Welcome & Ticket slash commands.")
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
    
    # Sentinel manages Welcome, Verification, Tickets, and Moderation Defense
    security_extensions = [
        "cogs.welcome",
        "cogs.verify",
        "cogs.tickets",
        "cogs.moderation",
    ]
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

    try:
        await start_sentinel(token, use_members=True, use_message_content=True)
    except discord.errors.PrivilegedIntentsRequired:
        logger.warning("[RAI SENTINEL] Privileged Gateway Intents not enabled. Falling back to basic intents.")
        try:
            await start_sentinel(token, use_members=False, use_message_content=True)
        except discord.errors.PrivilegedIntentsRequired:
            await start_sentinel(token, use_members=False, use_message_content=False)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[RAI SENTINEL 🛡️] Shutting down cleanly.")
