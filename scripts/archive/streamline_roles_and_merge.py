import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'
headers = {
    'Authorization': f'Bot {TOKEN}',
    'User-Agent': 'DiscordBot (RoleCleanup, 1.0)',
    'Content-Type': 'application/json'
}

def api_call(endpoint, method='GET', data=None):
    url = f'https://discord.com/api/v10/{endpoint.lstrip("/")}'
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8') if data is not None else None,
        headers=headers,
        method=method
    )
    with urllib.request.urlopen(req) as resp:
        if resp.status == 204:
            return None
        return json.loads(resp.read().decode('utf-8'))

# 1. Fetch current roles
roles = api_call(f'/guilds/{GUILD_ID}/roles')
role_map = {r['name']: r for r in roles}

# 2. Roles to Delete
roles_to_delete = [
    "PC Player 💻",
    "Mobile Player 📱",
    "Elite Legend 👑",
    "Gold Vibe 🥇",
    "Silver Vibe 🥈",
    "Bronze Vibe 🥉",
    "Male 🤴",
    "Female 👸",
    "They / Them 🌈",
    "18+ Verified 🔞",
    "Movie Alerts 🍿",
    "Music Jam 🎵",
    "👥 Verified Member" # Merged into RAI FAMILY 🌸
]

# Ensure RAI FAMILY 🌸 exists
rai_fam_role = role_map.get("RAI FAMILY 🌸") or role_map.get("🌸 ┊ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘")
verified_role = role_map.get("👥 Verified Member")

# 3. Migrate members from Verified Member to RAI FAMILY
if verified_role and rai_fam_role:
    print(f"Migrating members from '{verified_role['name']}' to '{rai_fam_role['name']}'...")
    try:
        members = api_call(f'/guilds/{GUILD_ID}/members?limit=1000')
        for m in members:
            m_roles = m.get('roles', [])
            user_id = m['user']['id']
            if verified_role['id'] in m_roles and rai_fam_role['id'] not in m_roles:
                new_roles = list(set(m_roles + [rai_fam_role['id']]))
                api_call(f'/guilds/{GUILD_ID}/members/{user_id}', method='PATCH', data={'roles': new_roles})
                print(f"Migrated user {m['user']['username']}")
    except Exception as e:
        print(f"Migration note: {e}")

# 4. Rename Giveaways role to '🎉 Events & Giveaways'
giveaways_role = role_map.get("Giveaways 🎉")
if giveaways_role:
    print("Renaming 'Giveaways 🎉' to '🎉 Events & Giveaways'...")
    api_call(f'/guilds/{GUILD_ID}/roles/{giveaways_role["id"]}', method='PATCH', data={
        'name': '🎉 Events & Giveaways',
        'color': 0x2ECC71
    })

# 5. Delete clutter roles
for name in roles_to_delete:
    r = role_map.get(name)
    if r:
        print(f"Deleting redundant role: {name} ({r['id']})...")
        try:
            api_call(f'/guilds/{GUILD_ID}/roles/{r["id"]}', method='DELETE')
            print(f"  -> Deleted {name}")
        except Exception as e:
            print(f"  -> Could not delete {name}: {e}")

# 6. Re-fetch and reorder remaining roles cleanly
print("\nReordering clean streamlined roles...")
remaining_roles = api_call(f'/guilds/{GUILD_ID}/roles')
rem_map = {r['name']: r for r in remaining_roles}

clean_hierarchy = [
    "F O U N D E R 🍷",
    "H E A D  A D M I N ⚡",
    "M O D E R A T O R 🛡️",
    "Server Booster 🚀",
    "AUDIO BOTS 🤖",
    "DJ 🎧",
    # Colors
    "Sakura Pink 🌸",
    "Neon Violet 💜",
    "Cyber Cyan 🩵",
    "Royal Gold 💛",
    # Community & Games
    "RAI FAMILY 🌸",
    "Free Fire 💥",
    "BGMI ⚡",
    "Roblox 🧸",
    "🎉 Events & Giveaways",
    "Server News 📢",
]

payload = []
current_pos = 25
for name in clean_hierarchy:
    r = rem_map.get(name)
    if r:
        payload.append({"id": r['id'], "position": current_pos})
        current_pos -= 1

if payload:
    try:
        api_call(f'/guilds/{GUILD_ID}/roles', method='PATCH', data=payload)
        print("✅ Hierarchy updated!")
    except Exception as e:
        print(f"Hierarchy note: {e}")

print("✅ Role streamling and merge complete!")
