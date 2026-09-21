import os
import sys
import requests
import unicodedata
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"
headers = {"Authorization": f"Bot {TOKEN}"}

# 1. Fetch Guild Channels
ch_res = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=headers)
channels = ch_res.json()

# Group by category
categories = [c for c in channels if c.get("type") == 4]
categories.sort(key=lambda x: x.get("position", 0))

print("=" * 60)
print("  🏛️ SERVER ARCHITECTURE AUDIT REPORT")
print("=" * 60)

for cat in categories:
    cid = cat["id"]
    cname = cat["name"]
    pos = cat["position"]
    print(f"\n📂 [CAT {pos}] {cname}")
    childs = [c for c in channels if c.get("parent_id") == cid]
    childs.sort(key=lambda x: x.get("position", 0))
    for ch in childs:
        t = "TEXT " if ch.get("type") in (0, 5) else "VOICE"
        print(f"   • [{t}] {ch['name']} ({ch['id']})")

# Uncategorized channels
orphan = [c for c in channels if c.get("type") != 4 and not c.get("parent_id")]
if orphan:
    print("\n📂 [UNCATEGORIZED]")
    for ch in orphan:
        print(f"   • {ch['name']} ({ch['id']})")

print("\n" + "=" * 60)
