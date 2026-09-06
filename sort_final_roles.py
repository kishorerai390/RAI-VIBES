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
    'User-Agent': 'DiscordBot (Reorder, 1.0)',
    'Content-Type': 'application/json'
}

roles = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles', headers=headers)).read().decode('utf-8'))
rem_map = {r['name']: r for r in roles}

clean_hierarchy = [
    "👑 ┆ 𝐅𝐎𝐔𝐍𝐃𝐄𝐑 🍷",
    "⚡ ┆ 𝐇𝐄𝐀𝐃 𝐀𝐃𝐌𝐈𝐍 ⚡",
    "🛡️ ┆ 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐎𝐑 🛡️",
    "🚀 ┆ 𝐒𝐄𝐑𝐕𝐄𝐑 𝐁𝐎𝐎𝐒𝐓𝐄𝐑 🚀",
    "🤖 ┆ 𝐀𝐔𝐃𝐈𝐎 𝐁𝐎𝐓𝐒",
    "🎧 ┆ 𝐃𝐉 🎧",
    "🌸 ┆ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘 🌸",
    "🎮 ┆ 𝐅𝐑𝐄𝐄 𝐅𝐈𝐑𝐄 💥",
    "🎮 ┆ 𝐁𝐆𝐌𝐈 ⚡",
    "🎮 ┆ 𝐆𝐓𝐀 𝐑𝐏 🔫",
    "🎮 ┆ 𝐑𝐎𝐁𝐋𝐎𝐗 🧸",
    "🍿 ┆ 𝐌𝐎𝐕𝐈𝐄 𝐍𝐈𝐆𝐇𝐓𝐒 🎬",
    "🎉 ┆ 𝐆𝐈𝐕𝐄𝐀𝐖𝐀𝐘𝐒 & 𝐄𝐕𝐄𝐍𝐓𝐒 🎁",
    "📢 ┆ 𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓𝐒 🔔"
]

payload = []
current_pos = 20
for name in clean_hierarchy:
    r = rem_map.get(name)
    if r:
        payload.append({"id": r['id'], "position": current_pos})
        current_pos -= 1

if payload:
    req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles', data=json.dumps(payload).encode('utf-8'), headers=headers, method='PATCH')
    urllib.request.urlopen(req)
    print("✅ Final hierarchy sorted!")
