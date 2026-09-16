import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'
headers = {
    'Authorization': f'Bot {TOKEN}',
    'User-Agent': 'DiscordBot (RoleFont, 1.0)',
    'Content-Type': 'application/json'
}

def api_call(endpoint, method='GET', data=None):
    url = f'https://discord.com/api/v10/{endpoint.lstrip("/")}'
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8') if data is not None else None,
        headers=headers,
        method=method
    )
    with urllib.request.urlopen(req) as resp:
        if resp.status == 204:
            return None
        return json.loads(resp.read().decode('utf-8'))

# Fetch current roles
roles = api_call(f'/guilds/{GUILD_ID}/roles')

# Map of existing role matching keywords to New Option 1 Royal Bold Serif names
rename_map = {
    "FOUNDER": "👑 ┆ 𝐅𝐎𝐔𝐍𝐃𝐄𝐑 🍷",
    "HEAD ADMIN": "⚡ ┆ 𝐇𝐄𝐀𝐃 𝐀𝐃𝐌𝐈𝐍 ⚡",
    "MODERATOR": "🛡️ ┆ 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐎𝐑 🛡️",
    "Server Booster": "🚀 ┆ 𝐒𝐄𝐑𝐕𝐄𝐑 𝐁𝐎𝐎𝐒𝐓𝐄𝐑 🚀",
    "AUDIO BOTS": "🤖 ┆ 𝐀𝐔𝐃𝐈𝐎 𝐁𝐎𝐓𝐒",
    "DJ": "🎧 ┆ 𝐃𝐉 🎧",
    "RAI FAMILY": "🌸 ┆ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘 🌸",
    "Free Fire": "🎮 ┆ 𝐅𝐑𝐄𝐄 𝐅𝐈𝐑𝐄 💥",
    "BGMI": "🎮 ┆ 𝐁𝐆𝐌𝐈 ⚡",
    "Roblox": "🎮 ┆ 𝐑𝐎𝐁𝐋𝐎𝐗 🧸",
    "Events & Giveaways": "🎉 ┆ 𝐆𝐈𝐕𝐄𝐀𝐖𝐀𝐘𝐒 & 𝐄𝐕𝐄𝐍𝐓𝐒 🎁",
    "Server News": "📢 ┆ 𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓𝐒 🔔"
}

for r in roles:
    r_name = r['name']
    for key, new_name in rename_map.items():
        if key.upper() in r_name.upper():
            print(f"Renaming '{r_name}' -> '{new_name}'...")
            try:
                api_call(f'/guilds/{GUILD_ID}/roles/{r["id"]}', method='PATCH', data={'name': new_name})
                print(f"  ✅ Updated: {new_name}")
            except Exception as e:
                print(f"  ❌ Failed: {e}")
            break

print("✅ All role fonts updated to Royal Bold Serif!")
