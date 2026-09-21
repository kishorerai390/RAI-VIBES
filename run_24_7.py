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

from main import create_bot, load_cogs, acquire_instance_lock as acquire_vibes_lock
from security_bot import create_security_bot, BOT_NAME, acquire_instance_lock as acquire_sentinel_lock
from arcade_bot import create_arcade_bot, load_arcade_cogs, acquire_instance_lock as acquire_arcade_lock

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("DualRunner")

async def run_vibes(token: str):
    while True:
        try:
            bot = create_bot(use_members=True, use_message_content=True)
            async with bot:
                await load_cogs(bot)
                try:
                    await bot.start(token)
                except discord.errors.PrivilegedIntentsRequired:
                    logger.warning("[RAI VIBES] Privileged intents not enabled in portal. Falling back to basic intents.")
                    bot_fallback = create_bot(use_members=False, use_message_content=False)
                    async with bot_fallback:
                        await load_cogs(bot_fallback)
                        await bot_fallback.start(token)
        except asyncio.CancelledError:
            break
        except discord.errors.LoginFailure:
            logger.error("[RAI VIBES] Invalid token in DISCORD_BOT_TOKEN.")
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"[RAI VIBES] Runner error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

async def run_sentinel(token: str):
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
        "cogs.tournaments",
    ]
    import database
    await database.init_db()

    while True:
        try:
            # Use basic intents directly to prevent Discord 4014 Disallowed Intent disconnects
            bot = create_security_bot(use_members=False, use_message_content=False)
            async with bot:
                for ext in security_extensions:
                    try:
                        await bot.load_extension(ext)
                        logger.info(f"[RAI SENTINEL] Loaded extension: {ext}")
                    except Exception as e:
                        logger.error(f"[RAI SENTINEL] Could not load {ext}: {e}")
                await bot.start(token)
        except asyncio.CancelledError:
            break
        except discord.errors.LoginFailure:
            logger.warning("[RAI SENTINEL] Invalid token in SECURITY_BOT_TOKEN.")
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"[RAI SENTINEL] Error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

async def run_arcade(token: str):
    while True:
        try:
            bot = create_arcade_bot(use_members=False, use_message_content=False)
            async with bot:
                await load_arcade_cogs(bot)
                await bot.start(token)
        except asyncio.CancelledError:
            break
        except discord.errors.LoginFailure:
            logger.error("[RAI ARCADE] Invalid token in COMMUNITY_BOT_TOKEN.")
            await asyncio.sleep(60)
        except Exception as e:
            logger.error(f"[RAI ARCADE] Error: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)

from web_dashboard import start_web_server

async def keep_awake():
    url = os.getenv("RENDER_EXTERNAL_URL", "https://rai-vibes.onrender.com").rstrip("/")
    ping_url = f"{url}/ping"
    logger.info(f"🔄 [Render Keep-Awake] Monitoring active for: {ping_url}")
    import aiohttp
    await asyncio.sleep(20)
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(ping_url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    logger.info(f"💓 [Keep-Awake Pulse] Pinged {ping_url} -> Status {resp.status} (Keeping container 100% warm)")
        except Exception as e:
            logger.debug(f"[Keep-Awake Pulse Notice] {e}")
        await asyncio.sleep(180)  # Ping every 3 minutes (Render sleeps at 15 mins)

async def main():
    token_vibes = os.getenv("DISCORD_BOT_TOKEN")
    token_sentinel = os.getenv("SECURITY_BOT_TOKEN")
    token_arcade = os.getenv("COMMUNITY_BOT_TOKEN") or os.getenv("ARCADE_BOT_TOKEN")

    if not token_vibes:
        logger.error("DISCORD_BOT_TOKEN is missing!")
        return

    print("==================================================")
    print("   🌸 RAI VIBES • RAI SENTINEL • RAI ARCADE 🌸")
    print("   Cloud Bot Ecosystem • 24/7 Port Health Server  ")
    print("==================================================")

    # 1. Start HTTP Health-Check Server for Render (Prevents Port Scan Timeout)
    try:
        await start_web_server()
    except Exception as e:
        logger.warning(f"Could not bind web server: {e}")

    # 2. Start Self-Ping Task for Render
    asyncio.create_task(keep_awake())

    enable_cloud_music = os.getenv("ENABLE_CLOUD_MUSIC", "true").lower() == "true"
    tasks = []
    if enable_cloud_music and token_vibes:
        tasks.append(run_vibes(token_vibes))
    if token_sentinel and token_sentinel != "YOUR_DISCORD_BOT_TOKEN_HERE":
        tasks.append(run_sentinel(token_sentinel))
    if token_arcade and token_arcade.strip() not in ("", "YOUR_COMMUNITY_BOT_TOKEN_HERE"):
        acquire_arcade_lock(59126)
        tasks.append(run_arcade(token_arcade.strip()))
        logger.info("🎮 [RAI ARCADE] Dedicated Arcade & Economy bot initialized.")
    else:
        logger.info("ℹ️ [RAI ARCADE] Standing by. Add COMMUNITY_BOT_TOKEN in .env whenever you wish to activate RAI ARCADE.")

    if not tasks:
        logger.warning("No bots selected to run. Standing by with health web server.")
        while True:
            await asyncio.sleep(3600)
    else:
        await asyncio.gather(*tasks)

if __name__ == "__main__":
    acquire_vibes_lock(59124)
    acquire_sentinel_lock(59125)
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[ECOSYSTEM RUNNER] Shutting down cleanly.")
