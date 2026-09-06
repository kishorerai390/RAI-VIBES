import os, sys, json, urllib.request, unicodedata
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'
CHANNEL_ID = '1545502722739150898' # #🎭・self-roles

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (CleanColors, 1.0)', 'Content-Type': 'application/json'}

# 1. Fetch roles and delete color roles
req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/roles', headers=headers)
with urllib.request.urlopen(req) as resp:
    roles = json.loads(resp.read().decode('utf-8'))

color_keywords = ["SAKURA PINK", "NEON PURPLE", "CYBER CYAN", "ROYAL GOLD", "COLOR", "COLOUR"]
deleted = 0
for r in roles:
    norm = unicodedata.normalize('NFKD', r['name']).upper()
    if any(k in norm for k in color_keywords):
        # Don't delete staff roles or base family
        if "FOUNDER" in norm or "ADMIN" in norm or "FAMILY" in norm or "BOOSTER" in norm:
            continue
        dreq = urllib.request.Request(f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles/{r['id']}", headers=headers, method='DELETE')
        try:
            with urllib.request.urlopen(dreq) as dresp:
                print(f"🗑️ Deleted color role: {r['name']} ({r['id']})")
                deleted += 1
        except Exception as e:
            print(f"Error deleting {r['name']}: {e}")

print(f"Deleted {deleted} color roles.")

# 2. Clean #🎭・self-roles channel
req = urllib.request.Request(f'https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=50', headers=headers)
with urllib.request.urlopen(req) as resp:
    msgs = json.loads(resp.read().decode('utf-8'))

for m in msgs:
    dreq = urllib.request.Request(f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages/{m['id']}", headers=headers, method='DELETE')
    try:
        with urllib.request.urlopen(dreq) as dresp:
            pass
    except Exception:
        pass

print("Self-roles channel cleaned!")
