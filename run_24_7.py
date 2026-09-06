import os
import sys
import asyncio
import logging
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

from main import create_bot, load_cogs
from security_bot import create_security_bot, BOT_NAME

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DualRunner")

async def run_vibes(token: str):
    bot = create_bot(use_members=True, use_message_content=True)
    async with bot:
        await load_cogs(bot)
        try:
            await bot.start(token)
        except discord.errors.PrivilegedIntentsRequired:
            logger.warning("[RAI VIBES] Falling back to basic intents.")
            bot_fallback = create_bot(use_members=False, use_message_content=True)
            async with bot_fallback:
                await load_cogs(bot_fallback)
                await bot_fallback.start(token)

async def run_sentinel(token: str):
    security_extensions = [
        "cogs.verify",
        "cogs.tickets",
        "cogs.moderation",
    ]
    try:
        bot = create_security_bot(use_members=True, use_message_content=True)
        async with bot:
            for ext in security_extensions:
                try:
                    await bot.load_extension(ext)
                    logger.info(f"[RAI SENTINEL] Loaded extension: {ext}")
                except Exception as e:
                    logger.error(f"Could not load {ext}: {e}")
            await bot.start(token)
    except discord.errors.LoginFailure:
        logger.warning("[RAI SENTINEL] Invalid token in SECURITY_BOT_TOKEN. Skipping Sentinel until a valid token is provided.")
    except discord.errors.PrivilegedIntentsRequired:
        logger.warning("[RAI SENTINEL] Privileged Gateway Intents missing, falling back to basic.")
        bot_fallback = create_security_bot(use_members=False, use_message_content=False)
        async with bot_fallback:
            for ext in security_extensions:
                try:
                    await bot_fallback.load_extension(ext)
                    logger.info(f"[RAI SENTINEL] Loaded extension: {ext}")
                except Exception as e:
                    logger.error(f"Could not load {ext}: {e}")
            try:
                await bot_fallback.start(token)
            except discord.errors.LoginFailure:
                logger.warning("[RAI SENTINEL] Invalid token in SECURITY_BOT_TOKEN.")
    except Exception as e:
        logger.error(f"[RAI SENTINEL] Error: {e}")

async def main():
    token_vibes = os.getenv("DISCORD_BOT_TOKEN")
    token_sentinel = os.getenv("SECURITY_BOT_TOKEN")

    if not token_vibes:
        logger.error("DISCORD_BOT_TOKEN is missing!")
        return

    print("==================================================")
    print("   🌸 RAI VIBES & RAI SENTINEL 24/7 CLOUD RUNNER 🌸")
    print("   Single-Process • Low RAM (<45MB) • 24/7 Active ")
    print("==================================================")

    while True:
        try:
            tasks = [run_vibes(token_vibes)]
            if token_sentinel and token_sentinel != "YOUR_DISCORD_BOT_TOKEN_HERE":
                tasks.append(run_sentinel(token_sentinel))
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Runner error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[DUAL RUNNER] Shutting down cleanly.")
