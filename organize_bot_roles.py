import os, sys, json, urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'
BOT_ROLE_ID = '1545494578512134176'

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (BotRole, 1.0)', 'Content-Type': 'application/json'}

# 1. Rename role to "🤖 ┆ 𝐒𝐄𝐑𝐕𝐄𝐑 𝐁𝐎𝐓𝐒 🤖"
payload = {'name': '🤖 ┆ 𝐒𝐄𝐑𝐕𝐄𝐑 𝐁𝐎𝐓𝐒 🤖', 'color': 0x95a5a6, 'hoist': True}
req = urllib.request.Request(
    f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles/{BOT_ROLE_ID}',
    data=json.dumps(payload).encode('utf-8'),
    headers=headers,
    method='PATCH'
)
try:
    with urllib.request.urlopen(req) as resp:
        print("✅ Renamed role to '🤖 ┆ 𝐒𝐄𝐑𝐕𝐄𝐑 𝐁𝐎𝐓𝐒 🤖'")
except Exception as e:
    print(f"Role rename note: {e}")

# Known Bot User IDs in RAI FAM
bot_user_ids = [
    ('Wick', '1545519948007473222'), # Wick
    ('Sapphire', '1546049335148544095'), # Sapphire
    ('Koya', '1546048477291741248'), # Koya
    ('Invite Tracker', '1546048371565793383'), # Invite Tracker
    ('DISBOARD', '1546072104397443175'), # Disboard
    ('Rythm', '1534903565535940648'), # Rythm
    ('RAI VIBES', '1545479610550980709'), # RAI VIBES
    ('RAI SENTINEL', '1545788568272769074'), # RAI SENTINEL
]

for name, uid in bot_user_ids:
    req = urllib.request.Request(
        f'https://discord.com/api/v10/guilds/{GUILD_ID}/members/{uid}/roles/{BOT_ROLE_ID}',
        headers=headers,
        method='PUT'
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print(f"✅ Assigned '🤖 ┆ 𝐒𝐄𝐑𝐕𝐄𝐑 𝐁𝐎𝐓𝐒 🤖' to {name}")
    except Exception as e:
        print(f"Note for {name}: {e}")

print("🎉 Bot roles organized cleanly!")
