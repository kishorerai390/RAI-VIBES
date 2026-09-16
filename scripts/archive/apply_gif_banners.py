import urllib.request
import json
import base64
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

from dotenv import load_dotenv

load_dotenv()

token_vibes = os.getenv('DISCORD_BOT_TOKEN', '')
token_sentinel = os.getenv('SECURITY_BOT_TOKEN', '')
guild_id = os.getenv('GUILD_ID', '1457382179981099090')

def update_bot_banner(bot_name, token, gif_path):
    print(f"Uploading banner for {bot_name} ({gif_path})...")
    with open(gif_path, 'rb') as f:
        file_bytes = f.read()
    b64_str = 'data:image/gif;base64,' + base64.b64encode(file_bytes).decode('utf-8')
    
    headers = {
        'Authorization': f'Bot {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'DiscordBot'
    }
    payload = json.dumps({'banner': b64_str}).encode('utf-8')
    req = urllib.request.Request('https://discord.com/api/v10/users/@me', data=payload, headers=headers, method='PATCH')
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            banner_hash = data.get('banner')
            print(f"[{bot_name}] Banner updated successfully! Banner Hash: {banner_hash}")
            if banner_hash and banner_hash.startswith('a_'):
                print(f"[{bot_name}] CONFIRMED ANIMATED GIF BANNER (a_ prefix)!")
            else:
                print(f"[{bot_name}] Banner Hash: {banner_hash}")
    except urllib.error.HTTPError as e:
        print(f"[{bot_name}] Failed: {e.code} - {e.read().decode('utf-8')}")

def update_guild_banner(token, gif_path):
    print(f"\nAttempting server banner upload for guild {guild_id}...")
    with open(gif_path, 'rb') as f:
        file_bytes = f.read()
    b64_str = 'data:image/gif;base64,' + base64.b64encode(file_bytes).decode('utf-8')
    
    headers = {
        'Authorization': f'Bot {token}',
        'Content-Type': 'application/json',
        'User-Agent': 'DiscordBot'
    }
    payload = json.dumps({'banner': b64_str}).encode('utf-8')
    req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{guild_id}', data=payload, headers=headers, method='PATCH')
    
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            banner_hash = data.get('banner')
            print(f"[Server] Banner updated! Banner Hash: {banner_hash}")
    except urllib.error.HTTPError as e:
        print(f"[Server] Failed: {e.code} - {e.read().decode('utf-8')}")

if __name__ == '__main__':
    update_bot_banner('RAI VIBES', token_vibes, r'assets/rai_vibes_banner.gif')
    update_bot_banner('RAI SENTINEL', token_sentinel, r'assets/rai_sentinel_banner.gif')
    update_guild_banner(token_vibes, r'assets/rai_fam_server_banner.gif')
