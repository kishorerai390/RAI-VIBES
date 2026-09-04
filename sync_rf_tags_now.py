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
    print("Fetching members to apply RF tag...")
    r_guild = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}", headers=HEADERS)
    guild_data = r_guild.json()
    owner_id = guild_data.get("owner_id")

    r_members = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/members?limit=100", headers=HEADERS)
    if r_members.status_code != 200:
        print(f"Error fetching members: {r_members.status_code} {r_members.text}")
        return

    members = r_members.json()
    if not isinstance(members, list):
        print(f"Unexpected response: {members}")
        return

    tagged = 0
    for m in members:
        user = m.get("user", {})
        u_id = user.get("id")
        if user.get("bot") or u_id == owner_id:
            continue

        nick = m.get("nick") or user.get("global_name") or user.get("username", "Member")
        upper_nick = nick.upper()

        if not (upper_nick.startswith("RF ") or upper_nick.startswith("RF |") or upper_nick.startswith("RF・")):
            prefix = "RF | "
            clean_name = nick[:(32 - len(prefix))]
            new_nick = f"{prefix}{clean_name}"
            
            res = requests.patch(
                f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{u_id}",
                headers=HEADERS,
                json={"nick": new_nick}
            )
            if res.status_code == 200:
                print(f"✅ Tagged: {nick} -> {new_nick}")
                tagged += 1
            else:
                print(f"⚠️ Could not tag {nick}: {res.status_code} {res.text}")

    print(f"🎉 Tagged {tagged} members with 'RF | ' prefix!")

if __name__ == "__main__":
    main()
