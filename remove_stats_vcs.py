import os
import sys
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"
HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

def main():
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    channels = r.json()
    
    # Find stats category and channels inside it
    stats_cat = next((c for c in channels if c["type"] == 4 and "STATS" in c["name"].upper()), None)
    if stats_cat:
        for c in channels:
            if c.get("parent_id") == stats_cat["id"]:
                requests.delete(f"https://discord.com/api/v10/channels/{c['id']}", headers=HEADERS)
                print(f"🗑️ Deleted fake VC: {c['name']}")
        
        requests.delete(f"https://discord.com/api/v10/channels/{stats_cat['id']}", headers=HEADERS)
        print(f"🗑️ Deleted category: {stats_cat['name']}")

if __name__ == "__main__":
    main()
