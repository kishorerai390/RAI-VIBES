import sys
import os
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import requests
import config

headers = {"Authorization": f"Bot {config.DISCORD_TOKEN}"}

for g in ["1457382179981099090", "1428058914141900860"]:
    r = requests.get(f"https://discord.com/api/v10/guilds/{g}/channels", headers=headers).json()
    print(f"\n=== Guild {g} ===")
    for c in r:
        cid = c["id"]
        ctype = c["type"]
        cname = c["name"]
        print(f"{cid} | {ctype} | {repr(cname)}")
