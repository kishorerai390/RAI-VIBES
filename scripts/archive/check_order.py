import os, sys, json, urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (Audit, 1.0)'}
req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels', headers=headers)
with urllib.request.urlopen(req) as resp:
    channels = json.loads(resp.read().decode('utf-8'))

print("=== SERVER CATEGORIES (TOP TO BOTTOM) ===")
for c in sorted([x for x in channels if x.get('type') == 4], key=lambda k: k.get('position', 0)):
    print(f"Position {c.get('position')}: {c.get('name')}")
