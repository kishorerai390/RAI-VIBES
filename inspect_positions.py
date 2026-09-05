import os
import sys
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"

HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

def main():
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    channels = r.json()
    
    categories = {c["id"]: c for c in channels if c["type"] == 4}
    sorted_cats = sorted(categories.values(), key=lambda x: x["position"])
    
    print("=== CATEGORIES IN ORDER ===")
    for cat in sorted_cats:
        print(f"[{cat['position']}] Category: {cat['name']} (ID: {cat['id']})")
        cat_channels = [c for c in channels if c.get("parent_id") == cat["id"]]
        sorted_cat_channels = sorted(cat_channels, key=lambda x: x["position"])
        for c in sorted_cat_channels:
            type_str = "TEXT" if c["type"] == 0 else ("VOICE" if c["type"] == 2 else f"TYPE {c['type']}")
            print(f"    - [{c['position']}] ({type_str}) {c['name']} (ID: {c['id']})")
        print()

    no_cat = [c for c in channels if c.get("parent_id") is None and c["type"] != 4]
    if no_cat:
        print("=== NO CATEGORY CHANNELS ===")
        for c in sorted(no_cat, key=lambda x: x["position"]):
            type_str = "TEXT" if c["type"] == 0 else ("VOICE" if c["type"] == 2 else f"TYPE {c['type']}")
            print(f"  - [{c['position']}] ({type_str}) {c['name']}")

if __name__ == "__main__":
    main()
