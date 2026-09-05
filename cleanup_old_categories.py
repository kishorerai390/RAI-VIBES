import os
import sys
import time
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

OLD_EMPTY_CATEGORY_IDS = [
    "1545502694930649109", # 🌸 INFORMATION
    "1545502726232744108", # 💬 CHAT & LOUNGE
    "1545502766120566784", # 🎵 MUSIC & CINEMA
    "1545502786161090652", # 🔊 VOICE LOUNGES
    "1545502817471569990", # 🎮 GAMING ZONE
    "1545502840452157463", # 🛡️ STAFF ZONE
    "1545776918413189252", # 🎲 FUN & GAMES
]

EXTRA_UNUSED_CHANNEL_IDS = [
    "1545502809896517703", # 🥂 Trio Lounge
    "1545502836392198164", # 🎮 Other Games
]

def delete_channel(channel_id):
    r = requests.delete(f"https://discord.com/api/v10/channels/{channel_id}", headers=HEADERS)
    return r.status_code

def main():
    print("🧹 Cleaning up old empty categories & redundant channels...")
    
    # 1. Move games/qotd/counting to CHAT MAINFRAME or appropriate category first
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    channels = r.json()
    
    chat_cat_id = "1545796157857595626" # 💬 ◈ CHAT MAINFRAME
    
    for c in channels:
        if c["name"] in ["🤖・bot-commands", "🌸・qotd", "🔢・counting"]:
            requests.patch(f"https://discord.com/api/v10/channels/{c['id']}", headers=HEADERS, json={
                "parent_id": chat_cat_id,
                "name": f"│🎮・{c['name'].split('・')[-1]}"
            })
            print(f"  Moved {c['name']} to CHAT MAINFRAME")
            time.sleep(0.3)

    for ch_id in EXTRA_UNUSED_CHANNEL_IDS:
        res = delete_channel(ch_id)
        print(f"  Deleted extra channel {ch_id} ({res})")
        time.sleep(0.3)

    for cat_id in OLD_EMPTY_CATEGORY_IDS:
        res = delete_channel(cat_id)
        print(f"  Deleted old category {cat_id} ({res})")
        time.sleep(0.3)

    print("✅ Cleanup complete!")

if __name__ == "__main__":
    main()
