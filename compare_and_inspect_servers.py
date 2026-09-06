import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (Inspector, 1.0)'}

def fetch_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

# Source Server: THOR APEX (1525030316845301781)
thor_guild = fetch_json('https://discord.com/api/v10/guilds/1525030316845301781')
thor_channels = fetch_json('https://discord.com/api/v10/guilds/1525030316845301781/channels')
thor_roles = fetch_json('https://discord.com/api/v10/guilds/1525030316845301781/roles')

# Target Server: RAI FAM (1457382179981099090)
rai_guild = fetch_json('https://discord.com/api/v10/guilds/1457382179981099090')
rai_channels = fetch_json('https://discord.com/api/v10/guilds/1457382179981099090/channels')
rai_roles = fetch_json('https://discord.com/api/v10/guilds/1457382179981099090/roles')

print("=" * 60)
print(f"SOURCE: {thor_guild['name']} (ID: {thor_guild['id']})")
print(f"Description: {thor_guild.get('description')}")
print("=" * 60)

# Organize THOR APEX channels by Category
categories = {}
no_cat = []

for c in thor_channels:
    if c['type'] == 4: # Category
        categories[c['id']] = {'name': c['name'], 'position': c.get('position', 0), 'children': []}

for c in thor_channels:
    if c['type'] != 4:
        parent_id = c.get('parent_id')
        if parent_id and parent_id in categories:
            categories[parent_id]['children'].append(c)
        else:
            no_cat.append(c)

sorted_cats = sorted(categories.values(), key=lambda x: x['position'])

print("\n--- [THOR APEX CATEGORIES & CHANNELS] ---")
if no_cat:
    print("[NO CATEGORY]")
    for c in sorted(no_cat, key=lambda x: x.get('position', 0)):
        t = 'Text' if c['type'] == 0 else ('Voice' if c['type'] == 2 else 'Other')
        print(f"  {t:<5} | {c['name']}")

for cat in sorted_cats:
    print(f"\n📂 CATEGORY: {cat['name']}")
    for c in sorted(cat['children'], key=lambda x: x.get('position', 0)):
        t = 'Text' if c['type'] == 0 else ('Voice' if c['type'] == 2 else 'Other')
        print(f"  {t:<5} | {c['name']}")

print("\n--- [THOR APEX ROLES] ---")
for r in sorted(thor_roles, key=lambda x: x['position'], reverse=True):
    color = f"#{r['color']:06x}" if r['color'] != 0 else "Default"
    print(f"[{r['position']:2d}] {r['name']:<30} | {color:<8} | Hoist: {r.get('hoist')}")

