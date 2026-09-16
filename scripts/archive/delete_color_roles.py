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
headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (Cleanup, 1.0)'}

req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles', headers=headers)
with urllib.request.urlopen(req) as resp:
    roles = json.loads(resp.read().decode('utf-8'))

color_roles = ['Sakura Pink 🌸', 'Neon Violet 💜', 'Cyber Cyan 🩵', 'Royal Gold 💛']
for r in roles:
    if r['name'] in color_roles:
        role_id = r['id']
        name = r['name']
        del_req = urllib.request.Request(
            f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles/{role_id}',
            headers=headers,
            method='DELETE'
        )
        try:
            with urllib.request.urlopen(del_req) as d_resp:
                print(f"✅ Deleted color role: {name}")
        except Exception as e:
            print(f"❌ Error deleting {name}: {e}")

print("Done cleaning color roles!")
