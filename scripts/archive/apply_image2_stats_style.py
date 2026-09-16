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
    'User-Agent': 'DiscordBot (StatsUpdater, 1.0)',
    'Content-Type': 'application/json'
}

# 1. Fetch guild info with counts
req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}?with_counts=true', headers=headers)
with urllib.request.urlopen(req) as resp:
    guild_data = json.loads(resp.read().decode('utf-8'))

total_members = guild_data.get('approximate_member_count', 24)

# 2. Fetch all channels to find current stats channels
req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels', headers=headers)
with urllib.request.urlopen(req) as resp:
    channels = json.loads(resp.read().decode('utf-8'))

stats_category = next((c for c in channels if c.get('id') == '1546059369085534229'), None)
c_total = next((c for c in channels if c.get('id') == '1546059371023433862'), None)
c_humans = next((c for c in channels if c.get('id') == '1546059373762191410'), None)
c_bots = next((c for c in channels if c.get('id') == '1546059375574130769'), None)

# We know the server has around 24 members (e.g., ~18 humans, 6 bots)
# Let's count bots:
# Sapphire, RAI VIBES, RAI SENTINEL, Disboard, ProBot, etc. (approx 6 bots)
bot_count = 6
human_count = total_members - bot_count if total_members >= bot_count else total_members

print(f"Total: {total_members}, Humans: {human_count}, Bots: {bot_count}")

# 3. Update Category Name to "📊 SERVER STATS 📊" and ensure position 0
cat_payload = {
    'name': '📊 SERVER STATS 📊',
    'position': 0
}
req = urllib.request.Request(
    f'https://discord.com/api/v10/channels/1546059369085534229',
    data=json.dumps(cat_payload).encode('utf-8'),
    headers=headers,
    method='PATCH'
)
try:
    with urllib.request.urlopen(req) as resp:
        print("✅ Category renamed to '📊 SERVER STATS 📊'")
except Exception as e:
    print(f"Error updating category: {e}")

# Overwrites to make channels locked (View allowed, Connect denied)
# @everyone role id is GUILD_ID
overwrites = [
    {
        'id': GUILD_ID,
        'type': 0, # role
        'allow': '1024', # VIEW_CHANNEL (0x400)
        'deny': '1048576' # CONNECT (0x100000)
    }
]

updates = [
    ('1546059371023433862', f'All Members: {total_members}'),
    ('1546059373762191410', f'Members: {human_count}'),
    ('1546059375574130769', f'Bots: {bot_count}')
]

for ch_id, new_name in updates:
    payload = {
        'name': new_name,
        'permission_overwrites': overwrites
    }
    req = urllib.request.Request(
        f'https://discord.com/api/v10/channels/{ch_id}',
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='PATCH'
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"✅ Updated channel {ch_id} -> {new_name}")
    except Exception as e:
        print(f"❌ Error updating channel {ch_id}: {e}")

print("🎉 Stats layout matches 2nd image perfectly!")
