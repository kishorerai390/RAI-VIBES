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
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles", headers=HEADERS)
    roles = r.json()
    for role in roles:
        print(f"Role: {role['name']} - ID: {role['id']}")

if __name__ == "__main__":
    main()
