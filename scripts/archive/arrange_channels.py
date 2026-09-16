import sys
import os
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")
headers = {
    "Authorization": f"Bot {token}",
    "Content-Type": "application/json"
}
guild_id = "1457382179981099090"

res = requests.get(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=headers)
channels = res.json()

print(f"Total channels fetched: {len(channels)}")
categories = {c["id"]: c for c in channels if c["type"] == 4}

for cat_id, cat in sorted(categories.items(), key=lambda x: x[1].get("position", 0)):
    print(f"\n📂 [{cat['name']}] (id={cat_id}, pos={cat.get('position')})")
    child_channels = [c for c in channels if c.get("parent_id") == cat_id]
    child_channels.sort(key=lambda x: (x.get("type", 0), x.get("position", 0)))
    for ch in child_channels:
        t = "💬" if ch["type"] in (0, 5) else "🔊" if ch["type"] == 2 else f"type={ch['type']}"
        print(f"   {t} {ch['name']} (id={ch['id']}, pos={ch.get('position')})")

uncat = [c for c in channels if c["type"] != 4 and not c.get("parent_id")]
if uncat:
    print("\n⚠️ Uncategorized Channels:")
    for ch in uncat:
        t = "💬" if ch["type"] in (0, 5) else "🔊" if ch["type"] == 2 else f"type={ch['type']}"
        print(f"   {t} {ch['name']} (id={ch['id']}, pos={ch.get('position')})")
