import os, sys, json, urllib.request, unicodedata
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (RoleSetup, 1.0)', 'Content-Type': 'application/json'}

# Fetch existing roles
req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles', headers=headers)
with urllib.request.urlopen(req) as resp:
    existing_roles = json.loads(resp.read().decode('utf-8'))

existing_names = {unicodedata.normalize('NFKD', r['name']).upper(): r['id'] for r in existing_roles}

roles_to_create = [
    # Notification & Ping Roles
    ("📢 ┆ 𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓𝐒 🔔", 0x3498db, False),
    ("🎉 ┆ 𝐆𝐈𝐕𝐄𝐀𝐖𝐀𝐘𝐒 🎁", 0x2ecc71, False),
    ("⚔️ ┆ 𝐓𝐎𝐔𝐑𝐍𝐀𝐌𝐄𝐍𝐓𝐒 🏆", 0xe67e22, False),
    # Color Roles
    ("🌸 ┆ 𝐒𝐀𝐊𝐔𝐑𝐀 𝐏𝐈𝐍𝐊", 0xff69b4, False),
    ("💜 ┆ 𝐍𝐄𝐎𝐍 𝐏𝐔𝐑𝐏𝐋𝐄", 0x9b5de5, False),
    ("🩵 ┆ 𝐂𝐘𝐁𝐄𝐑 𝐂𝐘𝐀𝐍", 0x00f0ff, False),
    ("💛 ┆ 𝐑𝐎𝐘𝐀𝐋 𝐆𝐎𝐋𝐃", 0xf1c40f, False),
]

created_map = {}
for name, color, hoist in roles_to_create:
    norm = unicodedata.normalize('NFKD', name).upper()
    if norm in existing_names:
        print(f"Role '{name}' already exists with ID {existing_names[norm]}")
        created_map[name] = existing_names[norm]
        continue

    payload = {
        'name': name,
        'color': color,
        'hoist': hoist,
        'mentionable': True
    }
    req = urllib.request.Request(
        f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles',
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='POST'
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print(f"✅ Created role '{name}' -> ID: {res.get('id')}")
        created_map[name] = res.get('id')

print("Roles creation complete!")
