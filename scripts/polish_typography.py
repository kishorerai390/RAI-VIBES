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

# Renames for total typography consistency
CHANNEL_RENAMES = {
    "1551184138932068373": "📸・ᴍᴇᴅɪᴀ-ᴀɴᴅ-ᴄʟɪᴘꜱ",
    "1551184144153714728": "🖥️・ꜱᴇᴛᴜᴘꜱ-ᴀɴᴅ-ᴛᴇᴄʜ",
    "1551184148566253578": "🎨・ᴀʀᴛ-ᴀɴᴅ-ᴅᴇꜱɪɢɴ",
    "1551184168845574147": "🎯・ᴅᴀɪʟʏ-ɢᴏᴀʟꜱ",
    "1551184180904333424": "🍅・ᴘᴏᴍᴏᴅᴏʀᴏ-ᴄʜᴀᴛ",
    "1551184190073213071": "⭐・ꜱᴛᴀʀʙᴏᴀʀᴅ",
}

CATEGORY_RENAMES = {
    # ◈ 𝕮 𝕽 𝕰 𝕬 𝕿 𝕴 𝖁 𝕰  𝕳 𝖀 𝕭 ◈ -> ✦ 𝕮 𝕽 𝕰 𝕬 𝕿 𝕴 𝖁 𝕰  𝕳 𝖀 𝕭 ✦
    "1551184136931250269": "✦ 𝕮 𝕽 𝕰 𝕬 𝕿 𝕴 𝖁 𝕰  𝕳 𝖀 𝕭 ✦",
    # ◈ ℙ ℝ 𝕆 𝔻 𝕌 ℂ 𝕋 𝕀 𝕍 𝕀 𝕋 𝕐 ◈ -> ✦ ℙ ℝ 𝕆 𝔻 𝕌 ℂ 𝕋 𝕀 𝕍 𝕀 𝕋 𝕐 ✦
    "1551184152504832040": "✦ ℙ ℝ 𝕆 𝔻 𝕌 ℂ 𝕋 𝕀 𝕍 𝕀 𝕋 𝕐 ✦",
}

for cid, new_name in CHANNEL_RENAMES.items():
    r = requests.patch(f"https://discord.com/api/v10/channels/{cid}", headers=headers, json={"name": new_name})
    if r.status_code == 200:
        print(f"✓ Renamed channel {cid} to '{new_name}'")
    else:
        print(f"⚠️ Channel rename error: {r.status_code} {r.text}")

for cid, new_name in CATEGORY_RENAMES.items():
    r = requests.patch(f"https://discord.com/api/v10/channels/{cid}", headers=headers, json={"name": new_name})
    if r.status_code == 200:
        print(f"✓ Renamed category {cid} to '{new_name}'")
    else:
        print(f"⚠️ Category rename error: {r.status_code} {r.text}")

print("✨ Typography polish complete!")
