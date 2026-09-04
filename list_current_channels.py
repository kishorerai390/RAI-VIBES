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
    
    categories = {c["id"]: c["name"] for c in channels if c["type"] == 4}
    
    for c in channels:
        cat_name = categories.get(c.get("parent_id"), "NO CATEGORY")
        print(f"[{cat_name}] Type:{c['type']} - ID:{c['id']} - Name:{c['name']}")

if __name__ == "__main__":
    main()
