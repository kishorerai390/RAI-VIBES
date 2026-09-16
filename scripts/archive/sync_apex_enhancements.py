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
    'User-Agent': 'DiscordBot (ApexSync, 1.0)',
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

# 1. Fetch current channels
channels = api_call(f'/guilds/{GUILD_ID}/channels')
chan_map = {c['name']: c for c in channels}

community_cat = chan_map.get('💬 ◈ COMMUNITY')
cat_id = community_cat['id'] if community_cat else None

# Move announcements under COMMUNITY category at top
ann_chan = chan_map.get('📢・announcements')
if ann_chan and cat_id:
    print("Moving announcements inside COMMUNITY category...")
    api_call(f'/channels/{ann_chan["id"]}', method='PATCH', data={'parent_id': cat_id, 'position': 0})

# Create edits-and-clips text channel if missing
if not chan_map.get('🎬・edits-and-clips') and cat_id:
    print("Creating 🎬・edits-and-clips channel...")
    api_call(f'/guilds/{GUILD_ID}/channels', method='POST', data={
        'name': '🎬・edits-and-clips',
        'type': 0,
        'parent_id': cat_id,
        'topic': 'Showcase your video edits, AMVs, clips, and GFX graphics! ✨'
    })

print("✅ Enhancements synced successfully!")
