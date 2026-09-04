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
logger = logging.getLogger("SecuritySentinel")

def create_security_bot() -> commands.Bot:
    intents = discord.Intents.all()
    bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

    @bot.event
    async def on_ready():
        logger.info(f"🛡️ Security Sentinel logged in as: {bot.user.name} ({bot.user.id})")
        activity = discord.Activity(type=discord.ActivityType.watching, name="RAI FAM Security & Anti-Raid 🛡️")
        await bot.change_presence(status=discord.Status.dnd, activity=activity)
        
        try:
            synced = await bot.tree.sync()
            logger.info(f"Synchronized {len(synced)} Security slash commands.")
        except Exception as e:
            logger.error(f"Failed to sync security commands: {e}")

    return bot

async def main():
    token = os.getenv("SECURITY_BOT_TOKEN") or os.getenv("DISCORD_BOT_TOKEN")
    bot = create_security_bot()
    
    # Load only security, moderation, ticket, and verification modules
    security_extensions = [
        "cogs.moderation",
        "cogs.verify",
    ]
    for ext in security_extensions:
        try:
            await bot.load_extension(ext)
            logger.info(f"Loaded security module: {ext}")
        except Exception as e:
            logger.error(f"Could not load {ext}: {e}")

    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
