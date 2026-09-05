import os
import sys
import re
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"
HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

def main():
    print("Fetching server members to clean RF tags...")
    r_guild = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}", headers=HEADERS)
    guild_data = r_guild.json()
    owner_id = guild_data.get("owner_id")

    r_members = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/members?limit=1000", headers=HEADERS)
    if r_members.status_code != 200:
        print(f"Error fetching members: {r_members.status_code} {r_members.text}")
        return

    members = r_members.json()
    if not isinstance(members, list):
        print(f"Unexpected response: {members}")
        return

    cleaned_count = 0
    for m in members:
        user = m.get("user", {})
        u_id = user.get("id")
        if user.get("bot") or u_id == owner_id:
            continue

        nick = m.get("nick")
        if not nick:
            continue

        # Check if nickname has RF prefix
        # e.g., 'RF | name', 'RF・name', 'RF name', 'RF|name'
        clean_nick = re.sub(r'^(?:RF\s*\|\s*|RF\s*・\s*|RF\s*\|\s*|RF\s+)', '', nick, flags=re.IGNORECASE).strip()
        
        # If clean_nick is identical to global_name or username, set nick to None (reset)
        global_name = user.get("global_name") or user.get("username")
        
        if clean_nick != nick:
            payload = {"nick": clean_nick if clean_nick != global_name else None}
            res = requests.patch(
                f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{u_id}",
                headers=HEADERS,
                json=payload
            )
            if res.status_code == 200:
                print(f"✅ Cleaned: '{nick}' -> '{clean_nick}' (Reset: {payload['nick'] is None})")
                cleaned_count += 1
            else:
                print(f"⚠️ Could not update '{nick}': {res.status_code} {res.text}")

    print(f"🎉 Successfully removed RF tag from {cleaned_count} members!")

if __name__ == "__main__":
    main()
