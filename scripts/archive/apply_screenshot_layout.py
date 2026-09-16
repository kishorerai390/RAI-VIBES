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

# Master Layout Definition from Screenshots
CATEGORIES_BLUEPRINT = [
    {
        "name": "📈 ◈ TEXT CHANNELS",
        "channels": [
            {"name": "📢・announcements", "type": 5, "match": ["announce"]},
            {"name": "🌷・general", "type": 0, "match": ["general", "chat"]},
            {"name": "🌷・welcome", "type": 0, "match": ["welcome"]},
            {"name": "🌷・verify-access", "type": 0, "match": ["verify"]},
            {"name": "🌷・rules", "type": 0, "match": ["rule"]},
            {"name": "🌷・self-roles", "type": 0, "match": ["role"]},
            {"name": "🌷・media-gallery", "type": 0, "match": ["media", "photo"]},
            {"name": "🌷・bot-commands", "type": 0, "match": ["bot", "cmd"]},
            {"name": "🌷・suggestions", "type": 0, "match": ["suggest"]},
            {"name": "🌷・giveaways", "type": 0, "match": ["giveaway"]},
            {"name": "🌷・leaderboard", "type": 0, "match": ["leaderboard", "rank", "level"]},
        ]
    },
    {
        "name": "🎭 | 𝑷𝑬𝑹𝑺𝑶𝑵𝑨𝑳 𝑨𝑹𝑬𝑨",
        "channels": [
            {"name": "🥂 | ・SOLO", "type": 2, "limit": 1, "match": ["solo"]},
            {"name": "🥂 | ・DUO", "type": 2, "limit": 2, "match": ["duo"]},
            {"name": "🥂 | ・TRIO", "type": 2, "limit": 3, "match": ["trio"]},
            {"name": "🥂 | ・SQUAD", "type": 2, "limit": 4, "match": ["squad"]},
            {"name": "🥂 | ・5-MAN", "type": 2, "limit": 5, "match": ["5-man", "quint"]},
            {"name": "🥂 | ・6-MAN", "type": 2, "limit": 6, "match": ["6-man", "hex"]},
            {"name": "➕ | Create Nexus VC", "type": 2, "limit": 0, "match": ["create", "nexus"]}
        ]
    },
    {
        "name": "😹 | 𝑭𝑼𝑵 𝑽𝑶𝑰𝑪𝑬 𝑪𝑯𝑨𝑵𝑵𝑬𝑳𝑺",
        "channels": [
            {"name": "🐣 | FUN TIME", "type": 2, "limit": 0, "match": ["fun time"]},
            {"name": "🗣️ | VOICE-1", "type": 2, "limit": 0, "match": ["voice-1", "voice 1"]},
            {"name": "🗣️ | VOICE-2", "type": 2, "limit": 0, "match": ["voice-2", "voice 2"]},
            {"name": "🗣️ | VOICE-3", "type": 2, "limit": 0, "match": ["voice-3", "voice 3"]},
            {"name": "🗣️ | OPEN VOICE", "type": 2, "limit": 0, "match": ["open voice"]},
            {"name": "💤 | AFK SLEEP", "type": 2, "limit": 0, "match": ["afk", "sleep"]}
        ]
    },
    {
        "name": "🎮 | 𝑮𝑨𝑴𝑰𝑵𝑮 𝒁𝑶𝑵𝑬",
        "channels": [
            {"name": "💬・gaming-text", "type": 0, "match": ["gaming-text"]},
            {"name": "⚡ | FREE FIRE", "type": 2, "limit": 0, "match": ["free fire"]},
            {"name": "⚡ | BGMI", "type": 2, "limit": 0, "match": ["bgmi"]},
            {"name": "⚡ | ROBLOX", "type": 2, "limit": 0, "match": ["roblox"]},
            {"name": "⚡ | OTHER GAMES", "type": 2, "limit": 0, "match": ["other games", "gaming lounge"]}
        ]
    },
    {
        "name": "🍃 | 𝑺𝑶𝑵𝑮 𝒁𝑶𝑵𝑬",
        "channels": [
            {"name": "🎵・song-requests", "type": 0, "match": ["song-request", "request"]},
            {"name": "🎧 | LO-FI CHILL [24/7]", "type": 2, "limit": 0, "match": ["lo-fi", "lofi"]},
            {"name": "🎧 | MUSIC LOUNGE", "type": 2, "limit": 0, "match": ["music lounge"]},
            {"name": "🎧 | KARAOKE STAGE", "type": 2, "limit": 0, "match": ["karaoke"]}
        ]
    },
    {
        "name": "🎥 | 𝑻𝑯𝑬𝑨𝑻𝑬𝑹",
        "channels": [
            {"name": "🎦 | MOVIE¹", "type": 2, "limit": 0, "match": ["movie¹", "movie1", "holo cinema", "cinema"]},
            {"name": "🎦 | MOVIE²", "type": 2, "limit": 0, "match": ["movie²", "movie2"]}
        ]
    },
    {
        "name": "🔱 | 𝑹𝑨𝑰-𝑬𝑺𝑷 !",
        "channels": [
            {"name": "☘️ | RAI FAM", "type": 2, "limit": 0, "match": ["thor fam", "rai fam", "emperor"]},
            {"name": "☘️ | VIP LOUNGE", "type": 2, "limit": 0, "match": ["inthu", "vip lounge", "high command"]}
        ]
    },
    {
        "name": "⚜️ | 𝑪𝒉𝒆𝒄𝒌𝒊𝒏𝒈 𝒁𝒐𝒏𝒆",
        "channels": [
            {"name": "🔍 | CHECKING-AREA", "type": 2, "limit": 99, "match": ["checking-area"]},
            {"name": "🔍 | PC-CHECKING", "type": 2, "limit": 99, "match": ["pc-checking"]},
            {"name": "🔍 | PHONE-CHECKING", "type": 2, "limit": 99, "match": ["phone-checking"]},
            {"name": "🔍 | IOS-CHECKING", "type": 2, "limit": 99, "match": ["ios-checking"]}
        ]
    },
    {
        "name": "🔒 | 𝑷𝑹𝑰𝑽𝑨𝑻𝑬-𝒁𝑶𝑵𝑬",
        "channels": [
            {"name": "🔮 | PVT-CHANNEL", "type": 2, "limit": 0, "match": ["pvt-channel", "private lounge"]},
            {"name": "🔮 | PVT-WORK", "type": 2, "limit": 0, "match": ["pvt-work"]}
        ]
    },
    {
        "name": "🛡️ | 𝑺𝑬𝑵𝑻𝑰𝑵𝑬𝑳 𝑫𝑬𝑭𝑬𝑵𝑺𝑬",
        "channels": [
            {"name": "🛡️・staff-hq", "type": 0, "match": ["staff-hq", "staff"]},
            {"name": "📋・mod-logs", "type": 0, "match": ["mod-logs", "log"]},
            {"name": "🎫・ticket-support", "type": 0, "match": ["ticket"]}
        ]
    }
]

def get_channels():
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    return r.json()

def main():
    print("🚀 Applying Screenshot Layout Structure...")
    channels = get_channels()
    
    existing_categories = [c for c in channels if c.get("type") == 4]
    existing_channels = [c for c in channels if c.get("type") != 4]
    
    used_channel_ids = set()
    category_id_map = {}

    # 1. Setup or reuse categories
    for cat_idx, cat_def in enumerate(CATEGORIES_BLUEPRINT):
        cat_name = cat_def["name"]
        
        matched_cat = None
        # Try matching existing category
        for ec in existing_categories:
            if ec["id"] in category_id_map.values():
                continue
            clean_ec = ec["name"].lower()
            clean_target = cat_name.lower()
            if any(k in clean_ec for k in ["text", "personal", "fun voice", "gaming", "song", "theater", "esp", "checking", "private", "sentinel"]):
                if any(k in clean_ec and k in clean_target for k in ["text", "personal", "fun", "gaming", "song", "theater", "esp", "checking", "private", "sentinel"]):
                    matched_cat = ec
                    break
        
        if matched_cat:
            print(f"🔄 Renaming Category {matched_cat['name']} -> {cat_name}")
            requests.patch(
                f"https://discord.com/api/v10/channels/{matched_cat['id']}",
                headers=HEADERS,
                json={"name": cat_name, "position": cat_idx}
            )
            category_id_map[cat_name] = matched_cat["id"]
        else:
            print(f"➕ Creating Category: {cat_name}")
            res = requests.post(
                f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
                headers=HEADERS,
                json={"name": cat_name, "type": 4, "position": cat_idx}
            ).json()
            category_id_map[cat_name] = res["id"]

    # 2. Setup or map channels into categories
    for cat_def in CATEGORIES_BLUEPRINT:
        cat_name = cat_def["name"]
        cat_id = category_id_map[cat_name]

        for ch_def in cat_def["channels"]:
            ch_name = ch_def["name"]
            ch_type = ch_def["type"]
            ch_limit = ch_def.get("limit")
            matches = ch_def.get("match", [])

            matched_ch = None
            for ec in existing_channels:
                if ec["id"] in used_channel_ids:
                    continue
                # Match by type and keyword
                if ec.get("type") in [ch_type, 0 if ch_type == 5 else ch_type]:
                    ec_name = ec["name"].lower()
                    if any(m.lower() in ec_name for m in matches):
                        matched_ch = ec
                        break

            if matched_ch:
                print(f"  🔄 Updating [{cat_name}] {matched_ch['name']} -> {ch_name}")
                used_channel_ids.add(matched_ch["id"])
                patch_payload = {
                    "name": ch_name,
                    "parent_id": cat_id
                }
                if ch_limit is not None:
                    patch_payload["user_limit"] = ch_limit
                requests.patch(
                    f"https://discord.com/api/v10/channels/{matched_ch['id']}",
                    headers=HEADERS,
                    json=patch_payload
                )
            else:
                print(f"  ➕ Creating [{cat_name}] {ch_name}")
                create_payload = {
                    "name": ch_name,
                    "type": ch_type,
                    "parent_id": cat_id
                }
                if ch_limit is not None:
                    create_payload["user_limit"] = ch_limit
                res = requests.post(
                    f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
                    headers=HEADERS,
                    json=create_payload
                ).json()
                if "id" in res:
                    used_channel_ids.add(res["id"])

    # 3. Final Ordering of all categories & channels
    print("✨ Applying global ordering...")
    all_current = get_channels()
    positions = []
    
    cat_pos = 0
    chan_pos = 0
    
    for cat_def in CATEGORIES_BLUEPRINT:
        cat_name = cat_def["name"]
        cat_id = category_id_map[cat_name]
        positions.append({"id": cat_id, "position": cat_pos})
        cat_pos += 1

        children = [c for c in all_current if c.get("parent_id") == cat_id]
        
        # Order children to match blueprint order
        ordered_children = []
        for ch_def in cat_def["channels"]:
            for ch in children:
                if ch["name"] == ch_def["name"] and ch not in ordered_children:
                    ordered_children.append(ch)
                    break
        for ch in children:
            if ch not in ordered_children:
                ordered_children.append(ch)

        for ch in ordered_children:
            positions.append({"id": ch["id"], "position": chan_pos})
            chan_pos += 1

    r_ord = requests.patch(
        f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
        headers=HEADERS,
        json=positions
    )
    print(f"Ordering sync status: {r_ord.status_code}")
    print("🎉 Server layout successfully transformed to match the screenshots!")

if __name__ == "__main__":
    main()
