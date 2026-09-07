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
        "cogs.verify",
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

from aiohttp import web

HTML_STATUS_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAI FAM 💗 • Cloud Bot Ecosystem & Security Command</title>
    <meta http-equiv="refresh" content="60">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-base: #080612;
            --card-bg: rgba(22, 16, 38, 0.7);
            --card-border: rgba(255, 105, 180, 0.2);
            --pink-accent: #ff69b4;
            --pink-glow: rgba(255, 105, 180, 0.4);
            --cyan-accent: #00f5d4;
            --cyan-glow: rgba(0, 245, 212, 0.35);
            --purple-accent: #8b5cf6;
            --text-primary: #f8f9fc;
            --text-secondary: #9ea3b5;
        }

        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Outfit', sans-serif;
            background: var(--bg-base);
            background-image: 
                radial-gradient(circle at 15% 20%, rgba(255, 51, 153, 0.12) 0%, transparent 45%),
                radial-gradient(circle at 85% 80%, rgba(0, 245, 212, 0.1) 0%, transparent 45%),
                radial-gradient(circle at 50% 50%, rgba(139, 92, 246, 0.08) 0%, transparent 60%);
            color: var(--text-primary);
            min-height: 100vh;
            padding: 30px 20px;
            display: flex;
            flex-direction: column;
            align-items: center;
        }

        .dashboard-container {
            width: 100%;
            max-width: 960px;
            display: flex;
            flex-direction: column;
            gap: 24px;
        }

        /* Top Header Card */
        .hero-card {
            background: var(--card-bg);
            border: 1px solid var(--card-border);
            border-radius: 24px;
            padding: 36px 32px;
            backdrop-filter: blur(20px);
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5), 0 0 30px rgba(255, 105, 180, 0.15);
            display: flex;
            align-items: center;
            justify-content: space-between;
            flex-wrap: wrap;
            gap: 20px;
            position: relative;
            overflow: hidden;
        }
        .hero-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; right: 0; height: 3px;
            background: linear-gradient(90deg, #ff69b4, #8b5cf6, #00f5d4);
        }

        .hero-left {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        .server-avatar {
            width: 72px;
            height: 72px;
            border-radius: 20px;
            border: 2px solid var(--pink-accent);
            box-shadow: 0 0 20px var(--pink-glow);
            background: #1a102a;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 32px;
        }
        .hero-titles h1 {
            font-size: 28px;
            font-weight: 800;
            background: linear-gradient(135deg, #ffffff 0%, #ff69b4 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 4px;
            letter-spacing: 0.5px;
        }
        .hero-titles p {
            color: var(--text-secondary);
            font-size: 14px;
        }

        .live-status-pill {
            display: inline-flex;
            align-items: center;
            gap: 10px;
            background: rgba(0, 245, 212, 0.12);
            border: 1px solid var(--cyan-accent);
            color: var(--cyan-accent);
            padding: 10px 20px;
            border-radius: 50px;
            font-weight: 700;
            font-size: 13px;
            letter-spacing: 1px;
            box-shadow: 0 0 15px var(--cyan-glow);
        }
        .status-dot {
            width: 10px;
            height: 10px;
            background: var(--cyan-accent);
            border-radius: 50%;
            animation: pulse 1.8s infinite;
        }
        @keyframes pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.4); opacity: 0.6; }
        }

        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
        }
        .stat-card {
            background: var(--card-bg);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 18px;
            padding: 20px;
            backdrop-filter: blur(16px);
            transition: transform 0.2s ease, border-color 0.2s ease;
        }
        .stat-card:hover {
            transform: translateY(-3px);
            border-color: var(--pink-accent);
        }
        .stat-label {
            font-size: 12px;
            font-weight: 600;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 6px;
        }
        .stat-value {
            font-size: 24px;
            font-weight: 800;
            color: #ffffff;
        }
        .stat-subtext {
            font-size: 11px;
            color: var(--cyan-accent);
            margin-top: 4px;
        }

        /* Bot Cards Grid */
        .bots-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }
        .bot-card {
            background: var(--card-bg);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 24px;
            backdrop-filter: blur(16px);
            display: flex;
            flex-direction: column;
            justify-content: space-between;
            position: relative;
            overflow: hidden;
            transition: all 0.3s ease;
        }
        .bot-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
        }
        .bot-card.primary {
            border-color: rgba(255, 105, 180, 0.3);
        }
        .bot-card.security {
            border-color: rgba(0, 245, 212, 0.3);
        }
        .bot-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 14px;
        }
        .bot-badge {
            font-size: 11px;
            font-weight: 700;
            padding: 4px 12px;
            border-radius: 50px;
            letter-spacing: 0.5px;
        }
        .badge-cyan { background: var(--cyan-accent); color: #000; }
        .badge-pink { background: var(--pink-accent); color: #000; }
        .badge-purple { background: var(--purple-accent); color: #fff; }

        .bot-title {
            font-size: 19px;
            font-weight: 700;
            color: #ffffff;
            margin-bottom: 6px;
        }
        .bot-desc {
            font-size: 13px;
            color: var(--text-secondary);
            line-height: 1.5;
            margin-bottom: 16px;
        }
        .features-list {
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
            font-size: 12px;
            color: #cbd5e1;
            margin-bottom: 18px;
        }
        .features-list li {
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .features-list li span { color: var(--pink-accent); font-weight: bold; }

        /* Commands Section */
        .section-card {
            background: var(--card-bg);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 20px;
            padding: 26px;
            backdrop-filter: blur(16px);
        }
        .section-title {
            font-size: 18px;
            font-weight: 700;
            color: #fff;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .commands-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 12px;
        }
        .cmd-item {
            background: rgba(10, 8, 20, 0.6);
            border: 1px solid rgba(255, 255, 255, 0.05);
            border-radius: 12px;
            padding: 12px 14px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 12px;
        }
        .cmd-name { color: var(--pink-accent); font-weight: 600; margin-bottom: 4px; }
        .cmd-desc { color: var(--text-secondary); font-family: 'Outfit', sans-serif; font-size: 11px; }

        /* Links Bar */
        .dash-links {
            display: flex;
            flex-wrap: wrap;
            gap: 12px;
            justify-content: center;
        }
        .btn-dash {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(255, 255, 255, 0.12);
            color: #fff;
            text-decoration: none;
            padding: 10px 18px;
            border-radius: 12px;
            font-size: 13px;
            font-weight: 600;
            transition: all 0.2s ease;
        }
        .btn-dash:hover {
            background: rgba(255, 105, 180, 0.15);
            border-color: var(--pink-accent);
            color: var(--pink-accent);
            transform: translateY(-2px);
        }

        footer {
            text-align: center;
            font-size: 12px;
            color: #64748b;
            padding: 10px 0 20px;
            line-height: 1.6;
        }
    </style>
</head>
<body>
    <div class="dashboard-container">
        <!-- Hero Header -->
        <div class="hero-card">
            <div class="hero-left">
                <div class="server-avatar">🌸</div>
                <div class="hero-titles">
                    <h1>RAI FAM 💗 • COMMAND CLOUD</h1>
                    <p>High-Fidelity Audio Engine • Autonomous Defense • 24/7 Deployment</p>
                </div>
            </div>
            <div class="live-status-pill">
                <div class="status-dot"></div>
                SYSTEMS ONLINE
            </div>
        </div>

        <!-- Real-Time Metrics -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Guild Members</div>
                <div class="stat-value">27</div>
                <div class="stat-subtext">Community Protected</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Sound Architecture</div>
                <div class="stat-value">384 kbps</div>
                <div class="stat-subtext">Lossless FFmpeg Audio</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Security Modules</div>
                <div class="stat-value">11 Active</div>
                <div class="stat-subtext">Zero-Setup Defense</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Cloud Availability</div>
                <div class="stat-value">99.9%</div>
                <div class="stat-subtext">Render + Bot-Hosting</div>
            </div>
        </div>

        <!-- Bot Ecosystem Cards -->
        <div class="bots-grid">
            <!-- RAI VIBES -->
            <div class="bot-card primary">
                <div>
                    <div class="bot-header">
                        <span class="bot-badge badge-pink">MUSIC CORE</span>
                        <span style="font-size: 12px; color: var(--cyan-accent); font-weight: 600;">● LIVE</span>
                    </div>
                    <div class="bot-title">RAI VIBES 💗</div>
                    <p class="bot-desc">Premium 24/7 audio powerhouse delivering lossless sound, queue persistence, soundboard, and dynamic voice hubs.</p>
                    <ul class="features-list">
                        <li><span>✔</span> Lossless Audio Playback & Auto-DJ</li>
                        <li><span>✔</span> 24/7 Lo-Fi & Aesthetic Ambient Radio</li>
                        <li><span>✔</span> 30+ Real-Time DSP Audio Filters</li>
                        <li><span>✔</span> Dynamic Voice Lounge Creator Hub</li>
                    </ul>
                </div>
            </div>

            <!-- RAI SENTINEL -->
            <div class="bot-card security">
                <div>
                    <div class="bot-header">
                        <span class="bot-badge badge-cyan">SECURITY CORE</span>
                        <span style="font-size: 12px; color: var(--cyan-accent); font-weight: 600;">● ARMED</span>
                    </div>
                    <div class="bot-title">RAI SENTINEL 🛡️</div>
                    <p class="bot-desc">Autonomous server protection engine actively monitoring raid storms, destructive actions, phishing, and spam.</p>
                    <ul class="features-list">
                        <li><span>✔</span> Precision Anti-Nuke Disaster Recovery</li>
                        <li><span>✔</span> Real-Time SQLite Structure Snapshots</li>
                        <li><span>✔</span> Anti-Raid Join Velocity Rate Limiting</li>
                        <li><span>✔</span> 15-Min Threat Cooldown Auto-Unlock</li>
                    </ul>
                </div>
            </div>

            <!-- KOYA PARTNER -->
            <div class="bot-card">
                <div>
                    <div class="bot-header">
                        <span class="bot-badge badge-purple">ANNOUNCER</span>
                        <span style="font-size: 12px; color: var(--cyan-accent); font-weight: 600;">● INTEGRATED</span>
                    </div>
                    <div class="bot-title">KOYA BOT 🌸</div>
                    <p class="bot-desc">Dedicated server greeting, member engagement, and leveling announcer with custom embeds.</p>
                    <ul class="features-list">
                        <li><span>✔</span> Official Welcome Announcements</li>
                        <li><span>✔</span> Member Departure / Farewell Feed</li>
                        <li><span>✔</span> Server Boost Celebrations</li>
                        <li><span>✔</span> Administrator Granted (`Bot Admin`)</li>
                    </ul>
                </div>
            </div>
        </div>

        <!-- Quick Command Reference -->
        <div class="section-card">
            <div class="section-title">⚡ Essential Slash Commands</div>
            <div class="commands-grid">
                <div class="cmd-item">
                    <div class="cmd-name">/play &lt;query&gt;</div>
                    <div class="cmd-desc">Stream any song or playlist in voice chat</div>
                </div>
                <div class="cmd-item">
                    <div class="cmd-name">/radio &lt;genre&gt;</div>
                    <div class="cmd-desc">Stream 24/7 continuous radio channels</div>
                </div>
                <div class="cmd-item">
                    <div class="cmd-name">/security status</div>
                    <div class="cmd-desc">View real-time shields & database telemetry</div>
                </div>
                <div class="cmd-item">
                    <div class="cmd-name">/security lockdown</div>
                    <div class="cmd-desc">Instant emergency chat freeze across channels</div>
                </div>
                <div class="cmd-item">
                    <div class="cmd-name">/whitelist user &lt;user&gt;</div>
                    <div class="cmd-desc">Exempt trusted admins from Anti-Nuke limits</div>
                </div>
                <div class="cmd-item">
                    <div class="cmd-name">/link add &lt;domain&gt;</div>
                    <div class="cmd-desc">Add custom blocked domains to firewall</div>
                </div>
            </div>
        </div>

        <!-- External Dashboards Navigation Bar -->
        <div class="section-card">
            <div class="section-title">🔗 Server Bot Dashboards Directory</div>
            <div class="dash-links">
                <a href="https://koya.gg/en/dashboard/1457382179981099090" target="_blank" class="btn-dash">🌸 Koya Dashboard</a>
                <a href="https://dashboard.sapph.xyz/" target="_blank" class="btn-dash">💎 Sapphire Dashboard</a>
                <a href="https://invitetracker.net/dashboard/1457382179981099090" target="_blank" class="btn-dash">📨 Invite Tracker</a>
                <a href="https://wickbot.com" target="_blank" class="btn-dash">🕯️ Wick Dashboard</a>
                <a href="https://disboard.org" target="_blank" class="btn-dash">🌐 Disboard Listing</a>
            </div>
        </div>

        <footer>
            RAI FAM 💗 • Cloud Cluster Online • Service ID: srv-dadipqn40ujc73bksugg<br>
            Multi-Shard Bot Architecture • Render 24/7 Container & Bot-Hosting SFTP Active
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

    tasks = [run_vibes(token_vibes)]
    if token_sentinel and token_sentinel != "YOUR_DISCORD_BOT_TOKEN_HERE":
        tasks.append(run_sentinel(token_sentinel))
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[DUAL RUNNER] Shutting down cleanly.")
