import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('SECURITY_BOT_TOKEN')
MOD_LOGS_ID = '1545502850057244762' # #📋・mod-logs

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'SentinelBot (ModLogsInit, 1.0)', 'Content-Type': 'application/json'}

embed_data = {
    "title": "🛡️ RAI SENTINEL • MODERATION & SECURITY LOGS ONLINE",
    "description": (
        "**Real-Time Security & Audit Telemetry Active** 📡\n\n"
        "This channel automatically records and displays all server safety actions:\n\n"
        "• 🔨 **Bans & Unbans** (Manual & Anti-Raid)\n"
        "• 👢 **Kicks & Server Ejections**\n"
        "• ⏳ **Timeouts & Mutes** (Chat & Voice)\n"
        "• 🔊 **Soundboard Interruption Punishments** (15-Min Auto-Timeout)\n"
        "• ⚠️ **AutoMod & Phishing Link Interceptions**\n"
        "• 🔒 **Channel Lockdowns & Server Freezes**\n"
        "• 📝 **Message Purges & Deleted Content**\n\n"
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        "🟢 **Status:** `ACTIVE & MONITORING 24/7`\n"
        "🛡️ **Guard:** `RAI SENTINEL 🛡️` & `Wick`"
    ),
    "color": 3066993, # #2ECC71 (Emerald Green)
    "footer": {
        "text": "RAI SENTINEL 🛡️ • Automated Defense Log Engine",
        "icon_url": "https://cdn.discordapp.com/icons/1457382179981099090/c39edf51a428bd0368a72b5c463a5c6f.png"
    }
}

payload = {
    "embeds": [embed_data]
}

req = urllib.request.Request(
    f"https://discord.com/api/v10/channels/{MOD_LOGS_ID}/messages",
    data=json.dumps(payload).encode('utf-8'),
    headers=headers,
    method='POST'
)

try:
    with urllib.request.urlopen(req) as resp:
        print("✅ Posted Mod-Logs initialization card successfully!")
except Exception as e:
    print(f"Error posting to mod-logs: {e}")
