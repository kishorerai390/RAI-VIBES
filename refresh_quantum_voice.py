import requests, os, sys, time
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
    voice_cat = next(c for c in channels if c.get('type') == 4 and 'QUANTUM VOICE' in c.get('name', ''))
    cat_id = voice_cat['id']

    # Target names and limits
    chambers = [
        ('│ ➕ Create Nexus VC', 0, 1545502790888198215),
        ('│ 💫 Solo Chamber [1]', 1, 1545798274265649204),
        ('│ 💫 Duo Chamber [2]', 2, 1545502804280352871),
        ('│ 💫 Trio Chamber [3]', 3, 1545798279676301346),
        ('│ 💫 Squad Chamber [4]', 4, 1545502799402369034),
        ('│ 💫 5-Man Chamber [5]', 5, 1545798287552942150),
        ('│ 💫 6-Man Chamber [6]', 6, 1545798291076161688),
        ('│ 💤 AFK Sleep', 0, 1545502813889499136),
    ]

    positions_payload = []
    base_pos = voice_cat.get('position', 10) * 10

    for idx, (name, limit, cid) in enumerate(chambers):
        print(f"Updating ID {cid} -> {name} (limit={limit})")
        patch_data = {
            'name': name,
            'user_limit': limit,
            'parent_id': cat_id
        }
        r = requests.patch(f'https://discord.com/api/v10/channels/{cid}', headers=HEADERS, json=patch_data)
        print(f"Status {r.status_code}")
        positions_payload.append({'id': str(cid), 'position': base_pos + idx})

    r_pos = requests.patch(f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels', headers=HEADERS, json=positions_payload)
    print("Reorder status:", r_pos.status_code)
    print("✅ All channels formatted and refreshed in Discord gateway!")

if __name__ == '__main__':
    main()
