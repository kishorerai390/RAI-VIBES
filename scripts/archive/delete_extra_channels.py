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
headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (Cleanup, 1.0)'}

channels = json.loads(urllib.request.urlopen(urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels', headers=headers)).read().decode('utf-8'))

unwanted = ["edits-and-clips", "qotd", "counting", "hall-of-fame"]

for c in channels:
    cname = c['name']
    for u in unwanted:
        if u in cname:
            del_req = urllib.request.Request(f'https://discord.com/api/v10/channels/{c["id"]}', headers=headers, method='DELETE')
            try:
                urllib.request.urlopen(del_req)
                print(f"✅ Deleted unwanted channel: {cname}")
            except Exception as e:
                print(f"❌ Error deleting {cname}: {e}")
            break

print("Done cleaning unwanted channels!")
