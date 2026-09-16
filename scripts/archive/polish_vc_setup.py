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
    
    # 1. Delete redundant Movies category
    for c in channels:
        if c["type"] == 4 and "MOVIES" in c["name"].upper():
            # Delete it
            requests.delete(f"https://discord.com/api/v10/channels/{c['id']}", headers=HEADERS)
            print(f"Deleted old category: {c['name']}")

    # 2. Update Music Zone category name to 🎵 | 𝙈𝙐𝙎𝙄𝘾 & 𝘾𝙄𝙉𝙀𝙈𝘼
    music_cat = next((c for c in channels if c["type"] == 4 and "MUSIC" in c["name"].upper()), None)
    if music_cat:
        requests.patch(
            f"https://discord.com/api/v10/channels/{music_cat['id']}",
            headers=HEADERS,
            json={"name": "🎵 | 𝙈𝙐𝙎𝙄𝘾 & 𝘾𝙄𝙉𝙀𝙈𝘼"}
        )
        print("Updated category name: 🎵 | 𝙈𝙐𝙎𝙄𝘾 & 𝘾𝙄𝙉𝙀𝙈𝘼")

        # Add Radio & Cinema under Music Category
        for name in ["📻 | 24-7 RADIO", "🎥 | CINEMA THEATER"]:
            exists = any(c["name"] == name for c in channels)
            if not exists:
                requests.post(
                    f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
                    headers=HEADERS,
                    json={"name": name, "type": 2, "parent_id": music_cat["id"]}
                )
                print(f"Created: {name}")

    # 3. Add Chill & Talk, Night Talks to Fun Voice
    fun_cat = next((c for c in channels if c["type"] == 4 and "FUN VOICE" in c["name"].upper()), None)
    if fun_cat:
        for vname in ["☕ | CHILL & TALK", "🌙 | NIGHT TALKS"]:
            exists = any(c["name"] == vname for c in channels)
            if not exists:
                requests.post(
                    f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
                    headers=HEADERS,
                    json={"name": vname, "type": 2, "parent_id": fun_cat["id"]}
                )
                print(f"Created: {vname}")

    print("Polish complete!")

if __name__ == "__main__":
    main()
