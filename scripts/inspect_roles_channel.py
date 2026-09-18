import sys
import os
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import requests
import json
import config

headers = {"Authorization": f"Bot {config.DISCORD_TOKEN}"}
guild_id = "1457382179981099090"

r = requests.get(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=headers)
channels = r.json()

for c in channels:
    if "role" in c["name"].lower():
        cid = c["id"]
        cname = c["name"]
        print(f"Channel: {cname} ({cid})")
        mr = requests.get(f"https://discord.com/api/v10/channels/{cid}/messages?limit=10", headers=headers)
        msgs = mr.json()
        for m in msgs:
            mid = m["id"]
            author = m["author"]["username"]
            print(f"  Message ID: {mid} by {author}")
            for emb in m.get("embeds", []):
                print(f"    Title: {emb.get('title')}")
                print(f"    Description:\n{emb.get('description')}")
                for f in emb.get("fields", []):
                    print(f"      Field {f.get('name')}: {f.get('value')}")
