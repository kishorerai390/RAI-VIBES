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

def get_channels():
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    return r.json()

def create_category(name, position):
    payload = {
        "name": name,
        "type": 4,
        "position": position
    }
    r = requests.post(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS, json=payload)
    if r.status_code == 201:
        return r.json()
    return None

def move_channel(channel_id, parent_id, position=0):
    payload = {
        "parent_id": parent_id,
        "position": position
    }
    r = requests.patch(f"https://discord.com/api/v10/channels/{channel_id}", headers=HEADERS, json=payload)
    return r.status_code == 200

def main():
    print("🚀 Streamlining text channel overload & organizing into clean sections...")
    channels = get_channels()
    
    categories = {c["name"]: c for c in channels if c["type"] == 4}
    
    # 1. Find or create 🎲 FUN & GAMES category right below CHAT & LOUNGE
    fun_cat = categories.get("🎲 FUN & GAMES") or categories.get("🎲 FUN & ACTIVITIES")
    chat_cat = categories.get("💬 CHAT & LOUNGE")
    
    if not fun_cat:
        print("  ✨ Creating '🎲 FUN & GAMES' category...")
        fun_cat = create_category("🎲 FUN & GAMES", position=2)
        time.sleep(0.5)

    fun_cat_id = fun_cat["id"] if fun_cat else None
    chat_cat_id = chat_cat["id"] if chat_cat else None

    # Channels to move to FUN & GAMES
    channel_map = {c["name"]: c["id"] for c in channels if c["type"] == 0}

    # Move qotd, counting, hall-of-fame, bot-commands to 🎲 FUN & GAMES
    fun_channels = ["qotd", "counting", "hall-of-fame", "bot-commands"]
    for idx, cname in enumerate(fun_channels):
        if cname in channel_map and fun_cat_id:
            move_channel(channel_map[cname], fun_cat_id, idx)
            print(f"  ✅ Moved #{cname} to 🎲 FUN & GAMES (pos {idx})")
            time.sleep(0.4)

    # Keep CHAT & LOUNGE clean with only general-chat, media, suggestions
    chat_channels = ["general-chat", "media", "suggestions"]
    for idx, cname in enumerate(chat_channels):
        if cname in channel_map and chat_cat_id:
            move_channel(channel_map[cname], chat_cat_id, idx)
            print(f"  ✅ Set #{cname} in 💬 CHAT & LOUNGE (pos {idx})")
            time.sleep(0.4)

    print("\n🎉 Text Channels Successfully Decongested & Split Elegantly!")

if __name__ == "__main__":
    main()
