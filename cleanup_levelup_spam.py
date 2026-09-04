import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"
HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

# Find general chat
r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
channels = r.json()
gen_chan = next((c for c in channels if "general-chat" in c["name"]), None)

if gen_chan:
    # Fetch recent messages
    r_msgs = requests.get(f"https://discord.com/api/v10/channels/{gen_chan['id']}/messages?limit=50", headers=HEADERS)
    msgs = r_msgs.json()
    
    # Find duplicate bot level up messages
    level_up_ids = []
    for m in msgs:
        if m.get("author", {}).get("bot"):
            for emb in m.get("embeds", []):
                if "LEVEL UP" in emb.get("title", ""):
                    level_up_ids.append(m["id"])

    print(f"Found {len(level_up_ids)} duplicate level-up messages to clean.")
    for mid in level_up_ids:
        requests.delete(f"https://discord.com/api/v10/channels/{gen_chan['id']}/messages/{mid}", headers=HEADERS)
    print("Cleaned up duplicate messages!")
