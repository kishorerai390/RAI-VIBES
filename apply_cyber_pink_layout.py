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

# The Master Cyber-Pink Blueprint
LAYOUT_BLUEPRINT = [
    {
        "category": "🌸 ◈ RAI PROTOCOL",
        "channels": [
            {"match": ["verify"], "name": "│✦・verify-access", "type": 0},
            {"match": ["rules", "guideline"], "name": "│✦・server-rules", "type": 0},
            {"match": ["announce"], "name": "│✦・announcements", "type": 5},
            {"match": ["self-roles", "role"], "name": "│✦・self-roles", "type": 0},
            {"match": ["welcome"], "name": "│✦・welcome-hub", "type": 0}
        ]
    },
    {
        "category": "💬 ◈ CHAT MAINFRAME",
        "channels": [
            {"match": ["general", "chat"], "name": "│💬・general-vibe", "type": 0},
            {"match": ["media", "photos"], "name": "│📸・media-gallery", "type": 0},
            {"match": ["suggestion"], "name": "│💡・suggestions", "type": 0},
            {"match": ["giveaway"], "name": "│🎉・giveaways", "type": 0},
            {"match": ["hall-of-fame", "starboard", "level", "leaderboard"], "name": "│🏆・leaderboard", "type": 0}
        ]
    },
    {
        "category": "🎵 ◈ SOUND SANCTUARY 💗",
        "channels": [
            {"match": ["song-request", "request"], "name": "│🎵・song-requests", "type": 0},
            {"match": ["lo-fi", "lofi"], "name": "│✨ Lo-Fi Chillroom [24/7]", "type": 2},
            {"match": ["music lounge", "music"], "name": "│🎧 Music Lounge", "type": 2},
            {"match": ["karaoke", "radio"], "name": "│🎤 Karaoke Stage", "type": 2},
            {"match": ["cinema", "theater"], "name": "│🎬 Holo Cinema", "type": 2}
        ]
    },
    {
        "category": "🎮 ◈ CYBER ARENA",
        "channels": [
            {"match": ["free fire", "freefire"], "name": "│🔥 Free Fire", "type": 2},
            {"match": ["bgmi", "pubg"], "name": "│🎯 BGMI Squad", "type": 2},
            {"match": ["roblox"], "name": "│🧱 Roblox Grid", "type": 2},
            {"match": ["other games", "gaming", "fun time"], "name": "│🎮 Gaming Lounge", "type": 2}
        ]
    },
    {
        "category": "🔊 ◈ QUANTUM VOICE",
        "channels": [
            {"match": ["join to create"], "name": "│➕ Create Nexus VC", "type": 2},
            {"match": ["duo"], "name": "│💫 Duo Chamber [2]", "type": 2, "user_limit": 2},
            {"match": ["trio", "open voice", "squad"], "name": "│💫 Squad Chamber [4]", "type": 2, "user_limit": 4},
            {"match": ["afk", "sleep"], "name": "│💤 AFK Sleep", "type": 2}
        ]
    },
    {
        "category": "🛡️ ◈ SENTINEL DEFENSE",
        "channels": [
            {"match": ["staff", "staff-chat", "mod"], "name": "│🛡️・staff-hq", "type": 0},
            {"match": ["logs", "mod-logs"], "name": "│📋・mod-logs", "type": 0},
            {"match": ["ticket", "ticket-support"], "name": "│🎫・ticket-support", "type": 0}
        ]
    }
]

def get_channels():
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    return r.json()

def update_channel(channel_id, payload):
    r = requests.patch(f"https://discord.com/api/v10/channels/{channel_id}", headers=HEADERS, json=payload)
    return r.status_code

def create_channel(guild_id, payload):
    r = requests.post(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=HEADERS, json=payload)
    return r.json()

def main():
    print("🚀 Applying Cyber-Pink Hologram layout...")
    channels = get_channels()
    existing_categories = {c["name"].lower(): c for c in channels if c["type"] == 4}
    existing_channels = [c for c in channels if c["type"] != 4]
    
    used_channel_ids = set()
    category_id_map = {}
    
    # 1. Ensure or update Categories
    for cat_idx, section in enumerate(LAYOUT_BLUEPRINT):
        cat_name = section["category"]
        found_cat = None
        for name, c in existing_categories.items():
            # Match keywords
            if any(k in name for k in [cat_name.lower().split("◈")[-1].strip(), cat_name.lower()]):
                found_cat = c
                break
        
        if found_cat:
            cat_id = found_cat["id"]
            update_channel(cat_id, {"name": cat_name, "position": cat_idx})
            print(f"✅ Updated Category: {cat_name} (ID: {cat_id})")
        else:
            new_cat = create_channel(GUILD_ID, {"name": cat_name, "type": 4, "position": cat_idx})
            cat_id = new_cat["id"]
            print(f"✨ Created Category: {cat_name} (ID: {cat_id})")
            
        category_id_map[cat_name] = cat_id
        time.sleep(0.4)

    # 2. Map and update Channels
    channels = get_channels() # Refresh
    existing_channels = [c for c in channels if c["type"] != 4]

    channel_pos = 0
    for section in LAYOUT_BLUEPRINT:
        cat_name = section["category"]
        parent_id = category_id_map[cat_name]
        
        for ch_spec in section["channels"]:
            target_name = ch_spec["name"]
            ch_type = ch_spec["type"]
            matches = ch_spec["match"]
            
            # Find best existing channel matching spec
            matched_channel = None
            for c in existing_channels:
                if c["id"] in used_channel_ids:
                    continue
                c_name_clean = c["name"].lower().replace("・", " ").replace("│", "").replace("✦", "").replace("💬", "").replace("🎵", "").replace("✨", "").strip()
                
                # Direct match
                if any(m in c_name_clean for m in matches):
                    if (ch_type == 2 and c["type"] == 2) or (ch_type != 2 and c["type"] != 2):
                        matched_channel = c
                        break
            
            payload = {
                "name": target_name,
                "parent_id": parent_id,
                "position": channel_pos
            }
            if "user_limit" in ch_spec:
                payload["user_limit"] = ch_spec["user_limit"]

            if matched_channel:
                used_channel_ids.add(matched_channel["id"])
                update_channel(matched_channel["id"], payload)
                print(f"  📌 Renamed & Moved: {matched_channel['name']} ➔ {target_name}")
            else:
                create_payload = {
                    "name": target_name,
                    "type": ch_type,
                    "parent_id": parent_id,
                    "position": channel_pos
                }
                if "user_limit" in ch_spec:
                    create_payload["user_limit"] = ch_spec["user_limit"]
                new_ch = create_channel(GUILD_ID, create_payload)
                used_channel_ids.add(new_ch["id"])
                print(f"  ✨ Created New Channel: {target_name}")
            
            channel_pos += 1
            time.sleep(0.35)

    print("\n🎉 Cyber-Pink Hologram Layout applied successfully!")

if __name__ == "__main__":
    main()
