import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (Audit, 1.0)'}

def fetch_json(url):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

preview = fetch_json('https://discord.com/api/v10/guilds/1508380159382917130/preview')

print("=" * 60)
print(f"GUILD: {preview['name']} (ID: {preview['id']})")
print(f"Members: {preview.get('approximate_member_count', 0)} | Online: {preview.get('approximate_presence_count', 0)}")
print(f"Description: {preview.get('description')}")
print(f"Features: {', '.join(preview.get('features', []))}")
print("=" * 60)

print("\n--- [EMOJIS & STICKERS] ---")
print(f"Total Custom Emojis: {len(preview.get('emojis', []))}")
print(f"Total Custom Stickers: {len(preview.get('stickers', []))}")

print("\n--- [DISCOVERABLE TRAITS] ---")
print(f"Discovery Splash: {preview.get('discovery_splash')}")
