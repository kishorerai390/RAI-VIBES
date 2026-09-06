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

from aiohttp import web

HTML_STATUS_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAI FAM Bot Cloud • 24/7 Status</title>
    <meta http-equiv="refresh" content="30">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            background: #0d0a1a;
            color: #f0f0f5;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            background: rgba(26, 21, 40, 0.85);
            border: 1px solid #ff3399;
            border-radius: 20px;
            padding: 40px;
            max-width: 520px;
            width: 100%;
            text-align: center;
            box-shadow: 0 0 40px rgba(255, 51, 153, 0.25);
            backdrop-filter: blur(12px);
        }
        h1 {
            color: #ff69b4;
            font-size: 26px;
            margin-bottom: 8px;
            letter-spacing: 1px;
        }
        .subtitle {
            color: #a09cb0;
            font-size: 14px;
            margin-bottom: 24px;
        }
        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(0, 245, 212, 0.15);
            border: 1px solid #00f5d4;
            color: #00f5d4;
            padding: 8px 18px;
            border-radius: 50px;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 24px;
        }
        .status-dot {
            width: 10px;
            height: 10px;
            background: #00f5d4;
            border-radius: 50%;
            box-shadow: 0 0 8px #00f5d4;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.3); opacity: 0.7; }
        }
        .bot-card {
            background: rgba(13, 10, 26, 0.7);
            border-radius: 12px;
            padding: 16px;
            margin-bottom: 14px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            border: 1px solid rgba(255, 255, 255, 0.08);
        }
        .bot-info { text-align: left; }
        .bot-name { font-weight: 600; font-size: 16px; }
        .bot-role { font-size: 12px; color: #999; }
        .badge-live {
            background: #00f5d4;
            color: #000;
            font-size: 11px;
            font-weight: bold;
            padding: 4px 10px;
            border-radius: 12px;
        }
        footer {
            margin-top: 24px;
            font-size: 12px;
            color: #666;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🌸 RAI FAM DISCORD CLOUD 🛡️</h1>
        <p class="subtitle">24/7 Render Container • High-Fidelity Sound Engine</p>
        
        <div class="status-pill">
            <div class="status-dot"></div>
            ALL SYSTEMS OPERATIONAL
        </div>

        <div class="bot-card">
            <div class="bot-info">
                <div class="bot-name">RAI VIBES 💗</div>
                <div class="bot-role">Music • 24/7 Radio • Audio FX</div>
            </div>
            <div class="badge-live">ONLINE</div>
        </div>

        <div class="bot-card">
            <div class="bot-info">
                <div class="bot-name">RAI SENTINEL 🛡️</div>
                <div class="bot-role">Verification • Tickets • AutoMod</div>
            </div>
            <div class="badge-live">ONLINE</div>
        </div>

        <footer>
            Health Status: 200 OK • Render Web Service Active
        </footer>
    </div>
</body>
</html>
"""

async def handle_health_check(request):
    return web.Response(text=HTML_STATUS_PAGE, content_type="text/html")

async def handle_ping_check(request):
    return web.json_response({"status": "healthy", "service": "RAI-VIBES-CLOUD", "code": 200})

async def start_web_server():
    port = int(os.getenv("PORT", "10000"))
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    app.router.add_get("/health", handle_health_check)
    app.router.add_get("/ping", handle_ping_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 [Render Health Server] Listening on 0.0.0.0:{port} (200 OK endpoint ready!)")

async def keep_awake():
    url = os.getenv("RENDER_EXTERNAL_URL")
    if not url:
        return
    logger.info(f"🔄 [Render Keep-Awake] Monitoring active for: {url}")
    import aiohttp
    await asyncio.sleep(60)
    async with aiohttp.ClientSession() as session:
        while True:
            try:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    logger.debug(f"[Render Keep-Awake] Pinged {url} -> Status {resp.status}")
            except Exception as e:
                logger.debug(f"[Render Keep-Awake] Ping notice: {e}")
            await asyncio.sleep(600)  # Ping every 10 minutes

async def main():
    token_vibes = os.getenv("DISCORD_BOT_TOKEN")
    token_sentinel = os.getenv("SECURITY_BOT_TOKEN")

    if not token_vibes:
        logger.error("DISCORD_BOT_TOKEN is missing!")
        return

    print("==================================================")
    print("   🌸 RAI VIBES & RAI SENTINEL 24/7 CLOUD RUNNER 🌸")
    print("   Render Web Service • 24/7 Port Health Server   ")
    print("==================================================")

    # 1. Start HTTP Health-Check Server for Render (Prevents Port Scan Timeout)
    try:
        await start_web_server()
    except Exception as e:
        logger.warning(f"Could not bind web server: {e}")

    # 2. Start Self-Ping Task for Render
    asyncio.create_task(keep_awake())

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
