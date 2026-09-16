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
    'User-Agent': 'DiscordBot (GamePolish, 1.0)',
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

roles = api_call(f'/guilds/{GUILD_ID}/roles')
role_map = {r['name']: r for r in roles}

desired_roles = [
    {"name": "🎮 ┆ 𝐅𝐑𝐄𝐄 𝐅𝐈𝐑𝐄 💥", "color": 0xFF7700},
    {"name": "🎮 ┆ 𝐁𝐆𝐌𝐈 ⚡", "color": 0xF1C40F},
    {"name": "🎮 ┆ 𝐆𝐓𝐀 𝐑𝐏 🔫", "color": 0x9B59B6},
    {"name": "🎮 ┆ 𝐑𝐎𝐁𝐋𝐎𝐗 🧸", "color": 0xE74C3C},
    {"name": "🍿 ┆ 𝐌𝐎𝐕𝐈𝐄 𝐍𝐈𝐆𝐇𝐓𝐒 🎬", "color": 0xE91E63},
    {"name": "🎉 ┆ 𝐆𝐈𝐕𝐄𝐀𝐖𝐀𝐘𝐒 & 𝐄𝐕𝐄𝐍𝐓𝐒 🎁", "color": 0x2ECC71},
    {"name": "📢 ┆ 𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓𝐒 🔔", "color": 0x00F5D4}
]

created_role_objects = []

for item in desired_roles:
    target_name = item['name']
    # Check if role exists
    existing = next((r for r in roles if target_name in r['name'] or (item['name'].split('┆')[1].strip()[:4].upper() in r['name'].upper())), None)
    if existing:
        print(f"Updating existing role '{existing['name']}' -> '{target_name}'...")
        updated = api_call(f'/guilds/{GUILD_ID}/roles/{existing["id"]}', method='PATCH', data={
            'name': target_name,
            'color': item['color']
        })
        created_role_objects.append(updated)
    else:
        print(f"Creating role '{target_name}'...")
        created = api_call(f'/guilds/{GUILD_ID}/roles', method='POST', data={
            'name': target_name,
            'color': item['color']
        })
        created_role_objects.append(created)

# Update #self-roles channel message
channels = api_call(f'/guilds/{GUILD_ID}/channels')
roles_chan = next((c for c in channels if "self-roles" in c['name']), None)

if roles_chan:
    print("Updating #self-roles embed...")
    embed = {
        'title': '🎭 ◈ RAI FAM • ROLE SELECTION CENTER',
        'description': (
            'Welcome to the **Role Selection Hub**! Pick the roles that match your interests so you only get pinged for what you care about! ✨\n\n'
            '### 🎮 **Gaming Squads**\n'
            '• 🔥 **Free Fire** — `@🎮 ┆ 𝐅𝐑𝐄𝐄 𝐅𝐈𝐑𝐄 💥`\n'
            '• ⚡ **BGMI / PUBG** — `@🎮 ┆ 𝐁𝐆𝐌𝐈 ⚡`\n'
            '• 🔫 **GTA V & RP** — `@🎮 ┆ 𝐆𝐓𝐀 𝐑𝐏 🔫`\n'
            '• 🧸 **Roblox** — `@🎮 ┆ 𝐑𝐎𝐁𝐋𝐎𝐗 🧸`\n\n'
            '### 🔔 **Community Notifications**\n'
            '• 🍿 **Movie Nights** — `@🍿 ┆ 𝐌𝐎𝐕𝐈𝐄 𝐍𝐈𝐆𝐇𝐓𝐒 🎬` *(Cinema & Watch Party Alerts)*\n'
            '• 🎉 **Events & Giveaways** — `@🎉 ┆ 𝐆𝐈𝐕𝐄𝐀𝐖𝐀𝐘𝐒 & 𝐄𝐕𝐄𝐍𝐓𝐒 🎁` *(Nitro & Prize Alerts)*\n'
            '• 📢 **Announcements** — `@📢 ┆ 𝐀𝐍𝐍𝐎𝐔𝐍𝐂𝐄𝐌𝐄𝐍𝐓𝐒 🔔` *(Major Server Updates)*\n\n'
            '━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n'
            '*React with or toggle your roles anytime in your profile to stay notified! 🌸*'
        ),
        'color': 0xFF69B4,
        'image': {'url': 'https://images.unsplash.com/photo-1542751371-adc38448a05e?q=80&w=1000&auto=format&fit=crop'},
        'footer': {'text': 'RAI FAM Role System • Royal Bold Theme 💗'}
    }
    api_call(f'/channels/{roles_chan["id"]}/messages', method='POST', data={'embeds': [embed]})

print("✅ Gaming and Ping roles perfected!")
