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

req = urllib.request.Request(
    f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels',
    headers={'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (Audit, 1.0)'}
)

with urllib.request.urlopen(req) as resp:
    chans = json.loads(resp.read().decode('utf-8'))

for c in sorted(chans, key=lambda x: (x.get('type', 0), x.get('position', 0))):
    ctype = c.get('type')
    t = 'Text ' if ctype == 0 else ('Voice' if ctype == 2 else ('Category' if ctype == 4 else 'Other   '))
    print(f"{t} | {c.get('name'):<30} | {c.get('id')}")
