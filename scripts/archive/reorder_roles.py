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

# Desired Hierarchy from Top to Bottom (highest priority first)
# Note: Bot integration roles managed by Discord cannot always have their position forcibly swapped above higher bots,
# but custom server roles can be sorted cleanly.

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (Reorder, 1.0)', 'Content-Type': 'application/json'}

# 1. Fetch current roles
req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles', headers=headers)
with urllib.request.urlopen(req) as resp:
    roles = json.loads(resp.read().decode('utf-8'))

# Identify roles
role_dict = {r['name']: r for r in roles}
bot_role_pos = role_dict.get('RAI VIBES', {}).get('position', 25)

print(f"Bot role position: {bot_role_pos}")

# Logical ordering from highest to lowest below Bot role:
hierarchy_names = [
    "F O U N D E R 🍷",
    "H E A D  A D M I N ⚡",
    "M O D E R A T O R 🛡️",
    "Server Booster 🚀",
    "AUDIO BOTS 🤖",
    "DJ 🎧",
    # Colors (Must be high enough to override base member colors)
    "Sakura Pink 🌸",
    "Neon Violet 💜",
    "Cyber Cyan 🩵",
    "Royal Gold 💛",
    # Level / Tier
    "Elite Legend 👑",
    "Gold Vibe 🥇",
    "Silver Vibe 🥈",
    "Bronze Vibe 🥉",
    # Core Member
    "RAI FAMILY 🌸",
    "👥 Verified Member",
    # Interest / Games / Pings / Identity
    "Movie Alerts 🍿",
    "Giveaways 🎉",
    "Server News 📢",
    "Music Jam 🎵",
    "Free Fire 💥",
    "BGMI ⚡",
    "Roblox 🧸",
    "PC Player 💻",
    "Mobile Player 📱",
    "Male 🤴",
    "Female 👸",
    "They / Them 🌈",
    "18+ Verified 🔞",
]

payload = []
# Give positions in descending order below bot_role_pos (e.g. from pos 28 down to 1)
current_pos = min(bot_role_pos - 1, 28)

for name in hierarchy_names:
    if name in role_dict:
        r = role_dict[name]
        payload.append({"id": r['id'], "position": current_pos})
        current_pos = max(1, current_pos - 1)

print(f"Updating positions for {len(payload)} roles...")

patch_req = urllib.request.Request(
    f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles',
    data=json.dumps(payload).encode('utf-8'),
    headers=headers,
    method='PATCH'
)

try:
    with urllib.request.urlopen(patch_req) as resp:
        updated = json.loads(resp.read().decode('utf-8'))
        print("✅ Roles hierarchy successfully updated!")
except Exception as e:
    print(f"Update note: {e}")

