import os
import sys
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv("f:/antigravity/APEX VIBES/.env")
token = os.getenv("DISCORD_BOT_TOKEN")
gid = "1457382179981099090"
headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

TARGET_BITRATE = 96000  # 96 kbps (Discord Tier 0 Maximum HD Audio)

print("🚀 Scanning all voice channels for bitrate upgrade...")

r = requests.get(f"https://discord.com/api/v10/guilds/{gid}/channels", headers=headers)
channels = r.json()

voice_channels = [c for c in channels if c.get("type") == 2]
upgraded = 0
already_hd = 0

for vc in voice_channels:
    cid = vc.get("id")
    name = vc.get("name")
    cur_bitrate = vc.get("bitrate", 64000)

    # Exclude stats channels (counter bots) from needing high bitrate if desired, but 96k is fine everywhere
    if cur_bitrate < TARGET_BITRATE:
        patch_r = requests.patch(f"https://discord.com/api/v10/channels/{cid}", headers=headers, json={"bitrate": TARGET_BITRATE})
        if patch_r.status_code == 200:
            print(f"✨ Upgraded '{name}' from {cur_bitrate // 1000} kbps -> {TARGET_BITRATE // 1000} kbps HD")
            upgraded += 1
        else:
            print(f"❌ Failed to upgrade '{name}': {patch_r.status_code} {patch_r.text}")
    else:
        already_hd += 1

print(f"\n🎉 Done! {upgraded} channels upgraded to 96 kbps HD audio. ({already_hd} channels were already at maximum bitrate).")
