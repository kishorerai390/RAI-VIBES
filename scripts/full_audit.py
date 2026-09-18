import sys
import os
import json
import sqlite3
import urllib.request
import asyncio
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

print("=" * 65)
print("  🌸 RAI VIBES & RAI SENTINEL FULL SYSTEM AUDIT 🛡️")
print("=" * 65)

# 1. Check Data Stores
print("\n--- 1. DATA STORES & DATABASE INTEGRITY ---")
data_dir = "data"
json_files = [
    "economy.json", "levels.json", "favorites.json",
    "playlists.json", "autoroles.json", "infractions.json",
    "milestones.json", "streamers.json", "user_cooldowns.json"
]

for jf in json_files:
    p = os.path.join(data_dir, jf)
    if os.path.exists(p):
        try:
            with open(p, "r", encoding="utf-8") as f:
                d = json.load(f)
            size = os.path.getsize(p)
            print(f"  ✅ {jf:<20} VALID (Size: {size:,} bytes | Records: {len(d)})")
        except Exception as e:
            print(f"  ❌ {jf:<20} CORRUPTED: {e}")
    else:
        print(f"  ℹ️ {jf:<20} (Not yet created / empty)")

# Check SQLite Database
db_path = "database.db"
if not os.path.exists(db_path):
    db_path = "sentinel.db" if os.path.exists("sentinel.db") else None

if db_path and os.path.exists(db_path):
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print(f"\n  ✅ SQLite Database ({db_path}) CONNECTED: {len(tables)} tables:")
        for t in tables:
            cur.execute(f"SELECT count(*) FROM [{t}]")
            cnt = cur.fetchone()[0]
            print(f"     • Table '{t}': {cnt} rows")
        conn.close()
    except Exception as e:
        print(f"  ❌ SQLite Database ERROR: {e}")
else:
    print("  ℹ️ No SQLite database file found on disk.")

# 2. Check Web Server & Render Keep-Alive
print("\n--- 2. WEB HEALTH SERVER & KEEPALIVE CHECK ---")
try:
    req = urllib.request.Request("http://127.0.0.1:10000/ping")
    with urllib.request.urlopen(req, timeout=3) as resp:
        body = resp.read().decode("utf-8")
        status = resp.status
        print(f"  ✅ Health Endpoint (http://127.0.0.1:10000/ping): HTTP {status} -> {body.strip()}")
except Exception as e:
    print(f"  ❌ Health Endpoint ERROR: {e}")

try:
    req = urllib.request.Request("http://127.0.0.1:10000/")
    with urllib.request.urlopen(req, timeout=3) as resp:
        status = resp.status
        print(f"  ✅ Web UI Dashboard (http://127.0.0.1:10000/): HTTP {status} (Render Port 10000 Responsive)")
except Exception as e:
    print(f"  ❌ Web UI Dashboard ERROR: {e}")

# 3. Check Audio Dependencies & Stream Sources
print("\n--- 3. AUDIO ENGINE & STREAM DEPENDENCIES ---")
import yt_dlp
print(f"  ✅ yt-dlp installed: Version {yt_dlp.version.__version__}")
print(f"  ✅ PyNaCl Voice Encryption: {discord.voice_client.has_nacl}")

from utils.ffmpeg_setup import get_ffmpeg_executable
ffmpeg = get_ffmpeg_executable()
if os.path.exists(ffmpeg):
    import subprocess
    res = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True)
    first_line = res.stdout.splitlines()[0] if res.stdout else "UNKNOWN"
    print(f"  ✅ FFmpeg Executable: {ffmpeg}")
    print(f"     Output: {first_line}")
else:
    print(f"  ❌ FFmpeg not found at {ffmpeg}")

# Check 24/7 Radio Station URLs
from cogs.radio import RADIO_STATIONS
print(f"\n  Checking {len(RADIO_STATIONS)} Live Radio Station URLs:")
for sk, sdata in RADIO_STATIONS.items():
    url = sdata["url"]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            code = r.status
            print(f"     • [{sk}] {sdata['name'][:30]:<30} -> HTTP {code} OK")
    except Exception as e:
        print(f"     • [{sk}] {sdata['name'][:30]:<30} -> Warning: {e}")

# 4. Live Discord Bots Guild Audit
print("\n--- 4. LIVE DISCORD API & PERMISSIONS AUDIT ---")
token_vibes = os.getenv("DISCORD_BOT_TOKEN")
token_sentinel = os.getenv("SECURITY_BOT_TOKEN")

async def audit_discord():
    # Audit RAI VIBES
    client = discord.Client(intents=discord.Intents.default())
    
    @client.event
    async def on_ready():
        print(f"  🌸 RAI VIBES ({client.user.name}#{client.user.discriminator} - ID: {client.user.id}):")
        print(f"     • Latency: {round(client.latency * 1000)}ms")
        print(f"     • Connected Servers: {len(client.guilds)}")
        for g in client.guilds:
            me = g.me
            print(f"     • Server: '{g.name}' (ID: {g.id}) | Members: {g.member_count}")
            print(f"       - Nickname: '{me.nick or me.name}'")
            print(f"       - Administrator: {me.guild_permissions.administrator}")
            print(f"       - Manage Roles: {me.guild_permissions.manage_roles}")
            print(f"       - Manage Channels: {me.guild_permissions.manage_channels}")
            print(f"       - Connect & Speak: {me.guild_permissions.connect} / {me.guild_permissions.speak}")
            print(f"       - Top Role: '{me.top_role.name}' (Pos: {me.top_role.position})")
            
            # Check voice channels
            vcs = [vc.name for vc in g.voice_channels if any(k in vc.name.lower() for k in ["music", "lo-fi", "community", "chill"])]
            print(f"       - Key Voice Channels: {vcs[:3]}")
        await client.close()

    try:
        await client.start(token_vibes)
    except Exception as e:
        print(f"  ❌ RAI VIBES Connection Error: {e}")

    # Audit RAI SENTINEL
    if token_sentinel and token_sentinel != "YOUR_DISCORD_BOT_TOKEN_HERE":
        client_s = discord.Client(intents=discord.Intents.default())
        
        @client_s.event
        async def on_ready():
            print(f"\n  🛡️ RAI SENTINEL ({client_s.user.name}#{client_s.user.discriminator} - ID: {client_s.user.id}):")
            print(f"     • Latency: {round(client_s.latency * 1000)}ms")
            print(f"     • Connected Servers: {len(client_s.guilds)}")
            for g in client_s.guilds:
                me = g.me
                print(f"     • Server: '{g.name}' (ID: {g.id}) | Members: {g.member_count}")
                print(f"       - Administrator: {me.guild_permissions.administrator}")
                print(f"       - Manage Roles: {me.guild_permissions.manage_roles}")
                print(f"       - Moderate Members: {me.guild_permissions.moderate_members}")
                print(f"       - Top Role: '{me.top_role.name}' (Pos: {me.top_role.position})")
            await client_s.close()

        try:
            await client_s.start(token_sentinel)
        except Exception as e:
            print(f"  ❌ RAI SENTINEL Connection Error: {e}")

asyncio.run(audit_discord())

print("\n" + "=" * 65)
print("  AUDIT COMPLETE: All core systems and telemetry examined!")
print("=" * 65)
