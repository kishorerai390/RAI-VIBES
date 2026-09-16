import os
import sys
import json
import unicodedata
import urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'
headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (RemovePings, 1.0)'}

roles = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles', headers=headers)).read().decode('utf-8'))

for r in roles:
    n = r['name']
    norm = unicodedata.normalize('NFKD', n).encode('ASCII', 'ignore').decode('utf-8').upper()
    print(f"Role: {n} -> Normalized: {norm}")
    if 'GIVEAWAY' in norm or 'ANNOUNCEMENT' in norm or 'EVENT' in norm:
        del_req = urllib.request.Request(
            f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles/{r["id"]}',
            headers=headers,
            method='DELETE'
        )
        try:
            urllib.request.urlopen(del_req)
            print(f"  ✅ Successfully Deleted: {n}")
        except Exception as e:
            print(f"  ❌ Error deleting {n}: {e}")

print("Done deleting ping roles!")
