import os, sys, json, urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (Audit, 1.0)'}

try:
    req = urllib.request.Request('https://discord.com/api/v10/guilds/1525030316845301781/channels', headers=headers)
    with urllib.request.urlopen(req) as resp:
        chans = json.loads(resp.read().decode('utf-8'))
    
    for c in chans:
        cname = c.get('name', '')
        if any(w in cname.lower() for w in ['verify', 'welcome', 'rules']):
            print(f"Channel: {cname} (ID: {c['id']})")
            try:
                mreq = urllib.request.Request(f"https://discord.com/api/v10/channels/{c['id']}/messages?limit=3", headers=headers)
                with urllib.request.urlopen(mreq) as mresp:
                    msgs = json.loads(mresp.read().decode('utf-8'))
                    for m in msgs:
                        print(f"  [Author: {m.get('author',{}).get('username')}]: {m.get('content')}")
                        for e in m.get('embeds', []):
                            print(f"    Embed Title: {e.get('title')}")
                            print(f"    Embed Desc:\n{e.get('description')}\n")
            except Exception as e:
                print(f"  Could not read messages: {e}")
except Exception as e:
    print(f"Error: {e}")
