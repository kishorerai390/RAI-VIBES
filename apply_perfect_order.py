import sys
import os
import requests
import time
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")
headers = {
    "Authorization": f"Bot {token}",
    "Content-Type": "application/json"
}
guild_id = "1457382179981099090"

# Desired Category order
category_order = [
    "1545502694930649109", # 🌸 | WELCOME & INFO
    "1545502726232744108", # 💬 | CHAT & LOUNGE
    "1545502766120566784", # 🎵 | MUSIC & CINEMA
    "1545502817471569990", # 🎮 | GAMING ZONE
    "1545502786161090652", # 😹 | FUN VOICE CHANNELS
    "1545502840452157463", # 🛡️ | STAFF ZONE
    "1545518525634838658", # 👑 | ROYAL SANCTUARY
]

category_payload = [{"id": cat_id, "position": idx} for idx, cat_id in enumerate(category_order)]
res = requests.patch(
    f"https://discord.com/api/v10/guilds/{guild_id}/channels",
    headers=headers,
    json=category_payload
)
print("Categories sorted status:", res.status_code)

# Desired Channel ordering per category
channels_per_cat = {
    # 🌸 | WELCOME & INFO
    "1545502694930649109": [
        "1545502700840427702", # ✅・verify-here
        "1545502705643167876", # 👋・welcome
        "1545502710101704714", # 📜・rules
        "1545502718792175646", # 📢・announcements
        "1545502722739150898", # ⭐・self-roles
    ],
    # 💬 | CHAT & LOUNGE
    "1545502726232744108": [
        "1545502730699808768", # 💬・general-chat
        "1545502734663286856", # 📸・media
        "1545502738362671255", # 🤖・bot-commands
    ],
    # 🎵 | MUSIC & CINEMA
    "1545502766120566784": [
        "1545534637122527332", # 🎵・song-requests
        "1545502782268772453", # 🎧 | MUSIC LOUNGE
        "1545518701414195281", # 📻 | 24-7 RADIO
        "1545502762467328185", # 🎥 | CINEMA THEATER
    ],
    # 🎮 | GAMING ZONE
    "1545502817471569990": [
        "1545502823699980408", # ⚡ | FREE FIRE
        "1545502829089787924", # ⚡ | BGMI
        "1545502832822591539", # ⚡ | ROBLOX
        "1545502836392198164", # ⚡ | OTHER GAMES
    ],
    # 😹 | FUN VOICE CHANNELS
    "1545502786161090652": [
        "1545502790888198215", # ➕ | JOIN TO CREATE
        "1545502794868457574", # 🐣 | FUN TIME
        "1545502799402369034", # 🍇 | OPEN VOICE
        "1545502804280352871", # 🥂 | ・ DUO
        "1545502809896517703", # 🥂 | ・ TRIO
        "1545502813889499136", # 💤 | AFK
    ],
    # 🛡️ | STAFF ZONE
    "1545502840452157463": [
        "1545502845208629328", # 🛡️・staff-chat
        "1545502850057244762", # 📋・mod-logs
        "1545514505520545886", # 📩・ticket-support
    ],
    # 👑 | ROYAL SANCTUARY
    "1545518525634838658": [
        "1545518535827263519", # 🔒・executive-chat
        "1545518528126394400", # 👑 | EMPEROR'S THRONE
        "1545518531192553603", # ⚡ | HIGH COMMAND VC
        "1545518533566271539", # 🍸 | PRIVATE LOUNGE
    ]
}

# Update parent and positions for each channel
for cat_id, ch_ids in channels_per_cat.items():
    for idx, ch_id in enumerate(ch_ids):
        patch_res = requests.patch(
            f"https://discord.com/api/v10/channels/{ch_id}",
            headers=headers,
            json={"parent_id": cat_id, "position": idx}
        )
        if patch_res.status_code not in (200, 204):
            print(f"Error on channel {ch_id}: {patch_res.status_code} - {patch_res.text}")
        time.sleep(0.1)

print("\n✨ All channels and categories successfully placed and sorted in perfect order!")
