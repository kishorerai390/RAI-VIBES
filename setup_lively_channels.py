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

def create_channel(name, parent_id, topic=""):
    payload = {
        "name": name,
        "type": 0,
        "parent_id": parent_id,
        "topic": topic
    }
    r = requests.post(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS, json=payload)
    if r.status_code == 201:
        return r.json()
    print(f"Error creating {name}: {r.status_code} {r.text}")
    return None

def send_embed(channel_id, title, description, color=0xFF69B4):
    payload = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
            "footer": {"text": "RAI FAM 💗 • Community Features"}
        }]
    }
    requests.post(f"https://discord.com/api/v10/channels/{channel_id}/messages", headers=HEADERS, json=payload)

def main():
    print("🚀 Setting up Lively Server Channels & Features...")
    channels = get_channels()
    chat_cat = next((c for c in channels if c["type"] == 4 and "CHAT & LOUNGE" in c["name"]), None)
    cat_id = chat_cat["id"] if chat_cat else None

    channel_map = {c["name"]: c for c in channels if c["type"] == 0}

    # 1. Setup #qotd
    if "qotd" not in channel_map:
        print("  ✨ Creating #qotd...")
        q_data = create_channel("qotd", cat_id, "Daily Question of the Day & Community Discussions")
        if q_data:
            time.sleep(0.5)
            send_embed(
                q_data["id"],
                "🌸 QUESTION OF THE DAY • RAI FAM 💗",
                "### 💡 **🎧 What is that one song you can listen to on repeat without ever getting tired of it?**\n\n*Share your thoughts below! A new question is posted every 24 hours.*",
                color=0xFF69B4
            )
            print("  ✅ #qotd created and initial question posted!")
    else:
        print("  ✅ #qotd already exists.")

    # 2. Setup #counting
    if "counting" not in channel_map:
        print("  ✨ Creating #counting...")
        c_data = create_channel("counting", cat_id, "Count to infinity! Take turns and don't break the streak!")
        if c_data:
            time.sleep(0.5)
            send_embed(
                c_data["id"],
                "🔢 ⋆⋅ THE COUNTING GAME ⋅⋆ 🔢",
                "**Rules:**\n"
                "1️⃣ Count in ascending order starting at **`1`**.\n"
                "2️⃣ You **cannot** count two numbers in a row by yourself (take turns!).\n"
                "3️⃣ If someone enters the wrong number, the streak resets to **`1`**!\n\n"
                "👉 *Start by typing `1` below!*",
                color=0x3498DB
            )
            print("  ✅ #counting created!")
    else:
        print("  ✅ #counting already exists.")

    # 3. Setup #hall-of-fame (Starboard)
    if "hall-of-fame" not in channel_map and "starboard" not in channel_map:
        print("  ✨ Creating #hall-of-fame...")
        h_data = create_channel("hall-of-fame", cat_id, "Community Starboard • Messages with 3+ ⭐ reactions get immortalized here!")
        if h_data:
            time.sleep(0.5)
            send_embed(
                h_data["id"],
                "⭐ ⋆⋅ RAI FAM HALL OF FAME ⋅⋆ ⭐",
                "Welcome to the **Community Billboard**!\n\n"
                "• When any funny, memorable, or legendary message gets **3 or more ⭐ star reactions**, the bot quotes and showcases it here!\n"
                "• React with ⭐ on your favorite messages to nominate them!",
                color=0xF1C40F
            )
            print("  ✅ #hall-of-fame created!")
    else:
        print("  ✅ #hall-of-fame already exists.")

    # 4. Reorder CHAT & LOUNGE channels
    time.sleep(1.0)
    channels = get_channels()
    chat_channels = [c for c in channels if c.get("parent_id") == cat_id and c["type"] == 0]
    
    order_preference = ["general-chat", "media", "qotd", "counting", "hall-of-fame", "suggestions", "bot-commands"]
    sorted_chat = sorted(chat_channels, key=lambda c: order_preference.index(c["name"]) if c["name"] in order_preference else 99)
    
    reorder_payload = [{"id": c["id"], "position": idx} for idx, c in enumerate(sorted_chat)]
    r = requests.patch(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS, json=reorder_payload)
    print(f"Reorder status: {r.status_code}")

    print("\n🎉 ALL LIVELY SERVER FEATURES & CHANNELS SUCCESSFULLY SET UP!")

if __name__ == "__main__":
    main()
