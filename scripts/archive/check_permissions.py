import requests, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
HEADERS = {'Authorization': 'Bot ' + os.getenv('DISCORD_BOT_TOKEN')}
channels = requests.get('https://discord.com/api/v10/guilds/1457382179981099090/channels', headers=HEADERS).json()
for c in channels:
    if c.get('parent_id') == '1545796171547803668':
        print(f"{c['name']} (ID: {c['id']}) overwrites: {c.get('permission_overwrites')}")
