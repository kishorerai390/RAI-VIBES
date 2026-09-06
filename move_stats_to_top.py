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
    'User-Agent': 'DiscordBot (Reorder, 1.0)',
    'Content-Type': 'application/json'
}

# In Discord API, updating a category position individually via PATCH /channels/{id}
# automatically shifts the other categories!

payload = {
    'position': 0
}

req = urllib.request.Request(
    f'https://discord.com/api/v10/channels/1546059369085534229',
    data=json.dumps(payload).encode('utf-8'),
    headers=headers,
    method='PATCH'
)

with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
    print("Category PATCH result pos:", res.get('position'))

# Also make sure the 3 stats voice channels have parent_id 1546059369085534229 and position 0, 1, 2
stats_channels = [
    ('1546059371023433862', 0),
    ('1546059373762191410', 1),
    ('1546059375574130769', 2)
]

for ch_id, pos in stats_channels:
    ch_payload = {
        'parent_id': '1546059369085534229',
        'position': pos
    }
    r = urllib.request.Request(
        f'https://discord.com/api/v10/channels/{ch_id}',
        data=json.dumps(ch_payload).encode('utf-8'),
        headers=headers,
        method='PATCH'
    )
    with urllib.request.urlopen(r) as resp:
        print(f"Channel {ch_id} moved to pos {pos}")

print("✅ Done!")
