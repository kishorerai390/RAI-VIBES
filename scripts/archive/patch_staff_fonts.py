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
headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (Fix, 1.0)', 'Content-Type': 'application/json'}

req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles', headers=headers)
with urllib.request.urlopen(req) as resp:
    roles = json.loads(resp.read().decode('utf-8'))

for r in roles:
    n = r['name'].replace(' ', '')
    role_id = r['id']
    if 'FOUNDER' in n:
        req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles/{role_id}', data=json.dumps({'name': '👑 ┆ 𝐅𝐎𝐔𝐍𝐃𝐄𝐑 🍷'}).encode('utf-8'), headers=headers, method='PATCH')
        urllib.request.urlopen(req)
        print("Updated Founder")
    elif 'HEADADMIN' in n:
        req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles/{role_id}', data=json.dumps({'name': '⚡ ┆ 𝐇𝐄𝐀𝐃 𝐀𝐃𝐌𝐈𝐍 ⚡'}).encode('utf-8'), headers=headers, method='PATCH')
        urllib.request.urlopen(req)
        print("Updated Head Admin")
    elif 'MODERATOR' in n:
        req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles/{role_id}', data=json.dumps({'name': '🛡️ ┆ 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐎𝐑 🛡️'}).encode('utf-8'), headers=headers, method='PATCH')
        urllib.request.urlopen(req)
        print("Updated Moderator")

print("✅ Staff roles completely updated!")
