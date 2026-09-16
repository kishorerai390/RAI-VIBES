import os
import sys
import json
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"
HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

def main():
    os.makedirs("data/backups", exist_ok=True)
    g_res = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}", headers=HEADERS)
    guild = g_res.json()

    r_res = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles", headers=HEADERS)
    roles = r_res.json()

    c_res = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    channels = c_res.json()

    snapshot = {
        "server_name": guild.get("name"),
        "server_id": GUILD_ID,
        "total_roles": len(roles),
        "total_channels": len(channels),
        "roles": roles,
        "channels": channels
    }

    backup_path = "data/backups/rai_fam_complete_snapshot.json"
    with open(backup_path, "w", encoding="utf-8") as f:
        json.dump(snapshot, f, indent=4)

    print(f"✅ Full server backup saved to: {backup_path}")

if __name__ == "__main__":
    main()
