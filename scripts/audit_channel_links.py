import sys
import os
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import requests
import config
import re

headers = {"Authorization": f"Bot {config.DISCORD_TOKEN}"}
guild_id = "1457382179981099090"

chans = requests.get(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=headers).json()
valid_ids = {c["id"]: c["name"] for c in chans}

print(f"Auditing messages in {len(chans)} channels in RAI FAM...")
dead_count = 0
for c in chans:
    if c["type"] in (0, 5):
        cid = c["id"]
        cname = c["name"]
        msgs = requests.get(f"https://discord.com/api/v10/channels/{cid}/messages?limit=10", headers=headers).json()
        if isinstance(msgs, list):
            for m in msgs:
                mid = m["id"]
                txt = m.get("content", "")
                for emb in m.get("embeds", []):
                    txt += " " + (emb.get("title") or "") + " " + (emb.get("description") or "")
                    for f in emb.get("fields", []):
                        txt += " " + (f.get("name") or "") + " " + (f.get("value") or "")
                found_channels = re.findall(r"<#(\d+)>", txt)
                for f_id in found_channels:
                    if f_id not in valid_ids:
                        print(f"DEAD LINK in #{cname} (msg {mid}): <#{f_id}> (channel deleted)")
                        dead_count += 1

print(f"Audit Complete! Total Dead Links Found: {dead_count}")
