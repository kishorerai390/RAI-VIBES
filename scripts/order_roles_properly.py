import os
import sys
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"
headers = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles", headers=headers)
if r.status_code != 200:
    print(f"Failed to fetch roles: {r.status_code}")
    sys.exit(1)

roles = r.json()
role_map = {r["name"].strip(): r["id"] for r in roles}

# Target order from Top to Bottom
DESIRED_ORDER = [
    # Staff / Elite (under Moderator)
    "─── MANAGEMENT ───",
    "🛠️ ┆ 𝐓𝐑𝐈𝐀𝐋 𝐌𝐎𝐃",
    "─── SPECIAL & ELITE ───",
    "💎・VIP / Elite",
    "🏆・Tournament Champion",
    "🎙️・Cinema Host",
    # Game Selector
    "─── GAME SELECTOR ───",
    "🎯・Valorant / CS2",
    "⚡・BGMI / PUBG",
    "🔥・Free Fire",
    "🏎️・GTA RP",
    "🚀・Rocket League",
    # Notifications
    "─── NOTIFICATIONS ───",
    "📢・Announcements",
    "🎁・Giveaways",
    "🏆・Tournaments",
    "🍿・Movie Nights",
    "📻・Live DJ & Radio"
]

# We will move each role individually from bottom of the list to top
# Assigning increasing positions so the list ends up ordered top-down
# Let's inspect where 🛡️ ┆ 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐎𝐑 🛡️ currently sits
import unicodedata

def clean_name(n):
    return unicodedata.normalize('NFKD', n).lower()

mod_roles = [r for r in roles if "moderator" in clean_name(r["name"])]
max_allowed_pos = mod_roles[0]["position"] - 1 if mod_roles else 15

print(f"Max target position for reordering: {max_allowed_pos}")

# Start from lowest role up to highest
for idx, name in enumerate(reversed(DESIRED_ORDER)):
    rid = role_map.get(name)
    if not rid:
        print(f"Role not found: {name}")
        continue
    target_pos = 2 + idx
    if target_pos > max_allowed_pos:
        target_pos = max_allowed_pos
    
    payload = [{"id": rid, "position": target_pos}]
    res = requests.patch(f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles", headers=headers, json=payload)
    if res.status_code in (200, 204):
        print(f"  ✓ Moved '{name}' to position {target_pos}")
    else:
        print(f"  ⚠️ Error moving '{name}': {res.status_code} {res.text}")

print("✅ Role ordering completed!")
