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
    f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles',
    headers={'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (Audit, 1.0)'}
)

with urllib.request.urlopen(req) as resp:
    roles = json.loads(resp.read().decode('utf-8'))

roles = sorted(roles, key=lambda r: r['position'], reverse=True)
print(f"Total Roles Found: {len(roles)}\n")
print(f"{'Pos':<4} | {'Role Name':<32} | {'Color':<8} | {'Display':<10} | {'Admin':<8} | {'Role ID'}")
print("-" * 80)
for r in roles:
    pos = r['position']
    name = r['name']
    color = f"#{r['color']:06x}" if r['color'] != 0 else "Default"
    hoist = "Hoisted" if r.get('hoist') else "Normal"
    admin = "⚡ Admin" if (int(r.get('permissions', 0)) & 0x8) else "No"
    role_id = r['id']
    print(f"{pos:<4} | {name:<32} | {color:<8} | {hoist:<10} | {admin:<8} | {role_id}")
