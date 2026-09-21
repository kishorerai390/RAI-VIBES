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
    print(f"Failed to fetch roles: {r.status_code} {r.text}")
    sys.exit(1)

roles = r.json()
role_by_name = {r["name"].strip(): r for r in roles}

# Desired order from Highest (top) to Lowest (bottom) among the roles we manage
# Everything below 🛡️ ┆ 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐎𝐑 🛡️
ORDER_FROM_TOP = [
    "─── MANAGEMENT ───",
    "🛠️ ┆ 𝐓𝐑𝐈𝐀𝐋 𝐌𝐎𝐃",
    "─── SPECIAL & ELITE ───",
    "💎・VIP / Elite",
    "🏆・Tournament Champion",
    "🎙️・Cinema Host",
    "💖・RAI FAM",
    "✨・Verified",
    "─── GAME SELECTOR ───",
    "🎯・Valorant / CS2",
    "⚡・BGMI / PUBG",
    "🔥・Free Fire",
    "🏎️・GTA RP",
    "🚀・Rocket League",
    "─── NOTIFICATIONS ───",
    "📢・Announcements",
    "🎁・Giveaways",
    "🏆・Tournaments",
    "🍿・Movie Nights",
    "📻・Live DJ & Radio"
]

# Build patch payload
# In Discord, higher number = higher position
# Lowest role in ORDER_FROM_TOP will have position 2, next 3, etc.
payload = []
base_pos = 2
for name in reversed(ORDER_FROM_TOP):
    r_obj = role_by_name.get(name)
    if r_obj:
        payload.append({"id": r_obj["id"], "position": base_pos})
        base_pos += 1

print(f"Applying position updates for {len(payload)} roles...")
res = requests.patch(f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles", headers=headers, json=payload)
if res.status_code in (200, 204):
    print("✅ Roles reordered successfully!")
else:
    print(f"⚠️ Reorder response: {res.status_code} {res.text}")
