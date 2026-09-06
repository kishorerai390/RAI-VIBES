import os, sys, json, urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (OnboardingAudit, 1.0)'}
req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/onboarding', headers=headers)
with urllib.request.urlopen(req) as resp:
    ob = json.loads(resp.read().decode('utf-8'))

prompts = ob.get('prompts', [])
print(f"Total Onboarding Questions: {len(prompts)}\n")
for idx, p in enumerate(prompts, 1):
    print(f"Question {idx}: {p.get('title')}")
    for opt in p.get('options', []):
        print(f"   • {opt.get('emoji', {}).get('name', '')} {opt.get('title')} ({opt.get('description', '')})")
    print()
