import requests, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

HEADERS = {
    'Authorization': 'Bot ' + os.getenv('DISCORD_BOT_TOKEN'),
    'Content-Type': 'application/json'
}
GUILD_ID = '1457382179981099090'

def main():
    channels = requests.get(f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels', headers=HEADERS).json()
    
    # Find CYBER ARENA category
    arena_cat = next((c for c in channels if c.get('type') == 4 and 'CYBER ARENA' in c.get('name', '')), None)
    if not arena_cat:
        print("Could not find CYBER ARENA category")
        return

    cat_id = arena_cat['id']
    print(f"Found Category: {arena_cat['name']} (ID: {cat_id})")

    # Check if Fun Time VC exists
    existing = next((c for c in channels if 'fun time' in c.get('name', '').lower()), None)
    
    if existing:
        print(f"Updating existing channel {existing['name']} to '│🎪 Fun Time VC'")
        requests.patch(
            f"https://discord.com/api/v10/channels/{existing['id']}",
            headers=HEADERS,
            json={"name": "│🎪 Fun Time VC", "parent_id": cat_id}
        )
    else:
        print("Creating '│🎪 Fun Time VC' under CYBER ARENA")
        res = requests.post(
            f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
            headers=HEADERS,
            json={
                "name": "│🎪 Fun Time VC",
                "type": 2, # Voice channel
                "parent_id": cat_id
            }
        ).json()
        print("Created:", res.get("id"), res.get("name"))

    # Reorder CYBER ARENA channels
    updated_channels = requests.get(f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels', headers=HEADERS).json()
    arena_vcs = [c for c in updated_channels if c.get('parent_id') == cat_id]
    
    order = ["free fire", "bgmi", "roblox", "fun time", "gaming"]
    def get_order_idx(c):
        cname = c['name'].lower()
        for idx, keyword in enumerate(order):
            if keyword in cname:
                return idx
        return 99

    sorted_vcs = sorted(arena_vcs, key=get_order_idx)
    base_pos = arena_cat.get('position', 10) * 10
    
    positions_payload = []
    for idx, c in enumerate(sorted_vcs):
        positions_payload.append({"id": c["id"], "position": base_pos + idx})

    requests.patch(
        f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
        headers=HEADERS,
        json=positions_payload
    )
    print("✅ Fun Time VC is active and positioned in CYBER ARENA!")

if __name__ == '__main__':
    main()
