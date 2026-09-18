import sys
import os
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import requests
import config
import json

headers = {"Authorization": f"Bot {config.DISCORD_TOKEN}"}
guild_id = "1457382179981099090"

inspect_chans = [
    "1545502705643167876",  # welcome
    "1545502710101704714",  # rules-and-info
    "1545502718792175646",  # announcements
    "1545502722739150898"   # roles
]

for cid in inspect_chans:
    ch = requests.get(f"https://discord.com/api/v10/channels/{cid}", headers=headers).json()
    print(f"\n==========================================")
    print(f"CHANNEL: #{ch.get('name')} ({cid})")
    print(f"==========================================")
    msgs = requests.get(f"https://discord.com/api/v10/channels/{cid}/messages?limit=10", headers=headers).json()
    for m in msgs:
        mid = m["id"]
        print(f"\n--- MSG {mid} by {m['author']['username']} ---")
        if m.get("content"):
            print(f"CONTENT:\n{m['content']}")
        for emb in m.get("embeds", []):
            print(f"EMBED TITLE: {emb.get('title')}")
            print(f"EMBED DESC:\n{emb.get('description')}")
            for f in emb.get("fields", []):
                print(f"  FIELD {f.get('name')}:\n{f.get('value')}")
