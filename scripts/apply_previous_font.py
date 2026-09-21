import os
import sys
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"
headers = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

# 1. Channels with exact previous separator: ┊ (box drawings light vertical) and small-caps
PREVIOUS_FONT_CHANNELS = {
    "1551184138932068373": "📸┊ᴍᴇᴅɪᴀ-ᴀɴᴅ-ᴄʟɪᴘꜱ",
    "1551184144153714728": "🖥️┊ꜱᴇᴛᴜᴘꜱ-ᴀɴᴅ-ᴛᴇᴄʜ",
    "1551184148566253578": "🎨┊ᴀʀᴛ-ᴀɴᴅ-ᴅᴇꜱɪɢɴ",
    "1551184168845574147": "🎯┊ᴅᴀɪʟʏ-ɢᴏᴀʟꜱ",
    "1551184180904333424": "🍅┊ᴘᴏᴍᴏᴅᴏʀᴏ-ᴄʜᴀᴛ",
    "1551184185186590730": "🎧 ┊ 𝐅𝐨𝐜𝐮𝐬 & 𝐒𝐭𝐮𝐝𝐲 𝐕𝐂",
    "1551184190073213071": "⭐┊ꜱᴛᴀʀʙᴏᴀʀᴅ",
}

# 2. Categories with exact previous diamond bookends: ◈
PREVIOUS_FONT_CATEGORIES = {
    "1551184133621948469": "◈ 𝕮 𝕽 𝕰 𝕬 𝕿 𝕴 𝖁 𝕰  𝕳 𝖀 𝕭 ◈",
    "1551184160142655549": "◈ ℙ ℝ 𝕆 𝔻 𝕌 ℂ 𝕋 𝕀 𝕍 𝕀 𝕋 𝕐 ◈",
}

print("Applying previous font style to all newly added channels...")
for cid, target_name in PREVIOUS_FONT_CHANNELS.items():
    r = requests.patch(f"https://discord.com/api/v10/channels/{cid}", headers=headers, json={"name": target_name})
    if r.status_code == 200:
        print(f"  ✓ Channel {cid} -> {target_name}")
    else:
        print(f"  ⚠️ Failed channel {cid}: {r.status_code} {r.text}")

print("\nApplying previous font style to all newly added categories...")
for cid, target_name in PREVIOUS_FONT_CATEGORIES.items():
    r = requests.patch(f"https://discord.com/api/v10/channels/{cid}", headers=headers, json={"name": target_name})
    if r.status_code == 200:
        print(f"  ✓ Category {cid} -> {target_name}")
    else:
        print(f"  ⚠️ Failed category {cid}: {r.status_code} {r.text}")

print("\n✨ Done applying previous font!")
