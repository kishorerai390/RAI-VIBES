import os, sys, json, urllib.request, unicodedata
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (MemberSync, 1.0)', 'Content-Type': 'application/json'}

# 1. Fetch all roles
req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles', headers=headers)
with urllib.request.urlopen(req) as resp:
    roles = json.loads(resp.read().decode('utf-8'))

family_role = None
for r in roles:
    norm = unicodedata.normalize('NFKD', r['name']).upper()
    if "RAI FAMILY" in norm or "FAMILY" in norm:
        family_role = r
        break

if not family_role:
    print("Family role not found!")
    sys.exit(1)

print(f"Target Role: {family_role['name']} (ID: {family_role['id']})")

# 2. Fetch all members
req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/members?limit=1000', headers=headers)
try:
    with urllib.request.urlopen(req) as resp:
        members = json.loads(resp.read().decode('utf-8'))
except Exception as e:
    print(f"Direct member fetch error: {e}")
    members = []

updated_count = 0
for m in members:
    user = m.get('user', {})
    if user.get('bot', False):
        continue
    user_id = user.get('id')
    user_roles = m.get('roles', [])
    
    if family_role['id'] not in user_roles:
        # Add role
        add_req = urllib.request.Request(
            f'https://discord.com/api/v10/guilds/{GUILD_ID}/members/{user_id}/roles/{family_role["id"]}',
            headers=headers,
            method='PUT'
        )
        try:
            with urllib.request.urlopen(add_req) as resp:
                print(f"✅ Added {family_role['name']} to {user.get('username')}")
                updated_count += 1
        except Exception as e:
            print(f"Error updating {user.get('username')}: {e}")

print(f"🎉 Complete! Synced role to {updated_count} members.")
