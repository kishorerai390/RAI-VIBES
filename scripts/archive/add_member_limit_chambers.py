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

def get_channels():
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    return r.json()

def main():
    channels = get_channels()
    
    # Find QUANTUM VOICE category
    voice_cat = None
    for c in channels:
        if c.get("type") == 4 and "QUANTUM VOICE" in c.get("name", ""):
            voice_cat = c
            break
            
    if not voice_cat:
        print("❌ Could not find QUANTUM VOICE category.")
        return

    cat_id = voice_cat["id"]
    print(f"✅ Found Category: {voice_cat['name']} (ID: {cat_id})")

    # Desired chambers with limits
    desired_chambers = [
        {"name": "│💫 Solo Chamber [1]", "limit": 1},
        {"name": "│💫 Duo Chamber [2]", "limit": 2},
        {"name": "│💫 Trio Chamber [3]", "limit": 3},
        {"name": "│💫 Squad Chamber [4]", "limit": 4},
        {"name": "│💫 5-Man Chamber [5]", "limit": 5},
        {"name": "│💫 6-Man Chamber [6]", "limit": 6},
    ]

    existing_voice = [c for c in channels if c.get("parent_id") == cat_id]
    existing_by_name = {c["name"]: c for c in existing_voice}

    for chamber in desired_chambers:
        name = chamber["name"]
        limit = chamber["limit"]
        
        # Check if already exists
        matched = None
        for c in existing_voice:
            if f"[{limit}]" in c["name"] or name.lower() in c["name"].lower():
                matched = c
                break
                
        if matched:
            print(f"🔄 Updating {matched['name']} -> {name} (Limit: {limit})")
            requests.patch(
                f"https://discord.com/api/v10/channels/{matched['id']}",
                headers=HEADERS,
                json={"name": name, "user_limit": limit}
            )
        else:
            print(f"➕ Creating {name} (Limit: {limit})")
            payload = {
                "name": name,
                "type": 2, # Voice channel
                "parent_id": cat_id,
                "user_limit": limit
            }
            res = requests.post(
                f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
                headers=HEADERS,
                json=payload
            )
            print(f"Created result: {res.status_code}")

    print("✨ Re-ordering QUANTUM VOICE channels...")
    updated_channels = get_channels()
    cat_children = [c for c in updated_channels if c.get("parent_id") == cat_id]
    
    def sort_key(c):
        cname = c["name"].lower()
        if "create" in cname or "nexus" in cname or "➕" in cname:
            return 0
        if "[1]" in cname or "solo" in cname:
            return 1
        if "[2]" in cname or "duo" in cname:
            return 2
        if "[3]" in cname or "trio" in cname:
            return 3
        if "[4]" in cname or "squad" in cname:
            return 4
        if "[5]" in cname or "5-man" in cname or "quint" in cname:
            return 5
        if "[6]" in cname or "6-man" in cname or "hex" in cname:
            return 6
        if "afk" in cname or "sleep" in cname or "💤" in cname:
            return 99
        return 10

    sorted_children = sorted(cat_children, key=sort_key)
    
    positions_payload = []
    base_pos = voice_cat.get("position", 10) + 1
    for idx, c in enumerate(sorted_children):
        positions_payload.append({"id": c["id"], "position": base_pos + idx})
        
    patch_res = requests.patch(
        f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
        headers=HEADERS,
        json=positions_payload
    )
    print(f"Positions update status: {patch_res.status_code}")
    print("🎉 Done! All requested member limit chambers are live and perfectly ordered.")

if __name__ == "__main__":
    main()
