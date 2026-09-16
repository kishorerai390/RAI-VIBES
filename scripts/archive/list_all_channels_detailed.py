import requests, os, sys
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
HEADERS = {'Authorization': 'Bot ' + os.getenv('DISCORD_BOT_TOKEN')}
GUILD_ID = '1457382179981099090'
channels = requests.get(f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels', headers=HEADERS).json()
categories = {c['id']: c['name'] for c in channels if c.get('type') == 4}

for c in sorted(channels, key=lambda x: (x.get('parent_id') or '', x.get('position', 0))):
    cat_name = categories.get(c.get('parent_id'), 'NO CATEGORY')
    print(f"[{cat_name}] id={c['id']} type={c.get('type')} name='{c.get('name')}' limit={c.get('user_limit')} pos={c.get('position')}")
