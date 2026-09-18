import os
import sys
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv("f:/antigravity/APEX VIBES/.env")
token = os.getenv("DISCORD_BOT_TOKEN")
guild_id = "1457382179981099090"
headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}

print("🚀 Starting All Limits Configuration for RAI FAM...")

# 1. Update Existing Text Channel Slowmodes
slowmodes = {
    "1549416359723532480": (3, "🤖｜ʙᴏᴛ-ᴄᴍᴅꜱ"),
    "1550184399742697512": (5, "💸｜ᴏᴡᴏ-ᴄʜᴀᴛ"),
    "1550187304876900543": (15, "🎮｜ʟꜰɢ-ᴍᴀᴛᴄʜᴍᴀᴋɪɴɢ"),
    "1550159859607928882": (3600, "🤝｜ᴘᴀʀᴛɴᴇʀꜱʜɪᴘꜱ"),
}

for cid, (seconds, name) in slowmodes.items():
    r = requests.patch(f"https://discord.com/api/v10/channels/{cid}", headers=headers, json={"rate_limit_per_user": seconds})
    if r.status_code == 200:
        print(f"✅ Set slowmode on {name} -> {seconds}s")
    else:
        print(f"❌ Failed slowmode on {name} ({cid}): {r.status_code} {r.text}")

# 2. Update Existing Voice Lounges with Limits
voice_limits = {
    "1550186738410987591": (12, "💬 | Chill Lounge 1"),
    "1550186767632826459": (12, "💬 | Chill Lounge 2"),
}

for cid, (limit, name) in voice_limits.items():
    r = requests.patch(f"https://discord.com/api/v10/channels/{cid}", headers=headers, json={"user_limit": limit})
    if r.status_code == 200:
        print(f"✅ Set user limit on {name} -> {limit} members")
    else:
        print(f"❌ Failed user limit on {name} ({cid}): {r.status_code} {r.text}")

# Fetch template overwrites from existing channel
template_r = requests.get("https://discord.com/api/v10/channels/1550186750289379328", headers=headers)
template_overwrites = template_r.json().get("permission_overwrites", [])

# Fetch current existing channel names to avoid duplicates
cur_channels = requests.get(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=headers).json()
existing_names = {c.get("name") for c in cur_channels}

# 3. Create New Themed Voice Channels with Limits
new_channels = [
    # (Category ID, Channel Name, User Limit)
    ("1550186748364066827", "⚔️ | 1v1 Duel Arena", 2),
    ("1550186748364066827", "🎯 | Valorant / CS2 Squad", 5),
    ("1550186724137640006", "👥 | Squad Chamber", 4),
    ("1550186724137640006", "🎧 | Focus Lounge", 6),
]

for parent_id, name, limit in new_channels:
    if name in existing_names:
        print(f"ℹ️ Channel '{name}' already exists. Skipping creation.")
        # Ensure limit is updated
        cid = next(c.get("id") for c in cur_channels if c.get("name") == name)
        requests.patch(f"https://discord.com/api/v10/channels/{cid}", headers=headers, json={"user_limit": limit})
        continue

    payload = {
        "name": name,
        "type": 2,  # Voice
        "parent_id": parent_id,
        "user_limit": limit,
        "permission_overwrites": template_overwrites
    }
    r = requests.post(f"https://discord.com/api/v10/guilds/{guild_id}/channels", headers=headers, json=payload)
    if r.status_code in [200, 201]:
        ch = r.json()
        print(f"🎉 Created voice channel '{name}' (Limit: {limit}) -> ID: {ch.get('id')}")
    else:
        print(f"❌ Failed to create '{name}': {r.status_code} {r.text}")

print("✨ All limits and channels have been deployed!")
