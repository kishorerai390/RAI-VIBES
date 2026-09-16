import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"
HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
channels = r.json()

total_deleted = 0
for c in channels:
    if c["type"] == 0: # text channel
        r_msgs = requests.get(f"https://discord.com/api/v10/channels/{c['id']}/messages?limit=50", headers=HEADERS)
        if r_msgs.status_code == 200:
            msgs = r_msgs.json()
            for m in msgs:
                if m.get("author", {}).get("bot"):
                    for emb in m.get("embeds", []):
                        if "LEVEL UP" in emb.get("title", ""):
                            requests.delete(f"https://discord.com/api/v10/channels/{c['id']}/messages/{m['id']}", headers=HEADERS)
                            total_deleted += 1
                            print(f"Deleted level-up message {m['id']} in #{c['name']}")

print(f"Total deleted: {total_deleted}")
