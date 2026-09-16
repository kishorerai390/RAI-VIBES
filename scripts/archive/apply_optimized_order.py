import os
import sys
import time
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"

HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

CATEGORY_ORDER = [
    "1545502694930649109",  # 🌸 INFORMATION
    "1545502726232744108",  # 💬 CHAT & LOUNGE
    "1545502786161090652",  # 🔊 VOICE LOUNGES
    "1545502766120566784",  # 🎵 MUSIC & CINEMA
    "1545502817471569990",  # 🎮 GAMING ZONE
    "1545518525634838658",  # 👑 ROYAL SANCTUARY
    "1545502840452157463",  # 🛡️ STAFF ZONE
]

CHANNEL_ORDER_BY_CAT = {
    # 🌸 INFORMATION
    "1545502694930649109": [
        "1545502700840427702",  # verify-here
        "1545502710101704714",  # rules
        "1545502718792175646",  # announcements
        "1545502722739150898",  # self-roles
        "1545502705643167876",  # welcome
    ],
    # 💬 CHAT & LOUNGE
    "1545502726232744108": [
        "1545502730699808768",  # general-chat
        "1545502734663286856",  # media
        "1545772984134799490",  # suggestions
        "1545502738362671255",  # bot-commands
    ],
    # 🔊 VOICE LOUNGES
    "1545502786161090652": [
        "1545502790888198215",  # ➕ Join to Create
        "1545502799402369034",  # 🍇 Open Voice
        "1545502794868457574",  # 🐣 Fun Time
        "1545502804280352871",  # 🥂 Duo Lounge
        "1545502809896517703",  # 🥂 Trio Lounge
        "1545502813889499136",  # 💤 AFK Lounge
    ],
    # 🎵 MUSIC & CINEMA
    "1545502766120566784": [
        "1545534637122527332",  # song-requests
        "1545502782268772453",  # 🎧 Music Lounge
        "1545518701414195281",  # 📻 24/7 Radio
        "1545502762467328185",  # 🎥 Cinema Theater
    ],
    # 🎮 GAMING ZONE
    "1545502817471569990": [
        "1545502829089787924",  # 🎯 BGMI
        "1545502823699980408",  # 🔥 Free Fire
        "1545502832822591539",  # 🧱 Roblox
        "1545502836392198164",  # 🎮 Other Games
    ],
    # 👑 ROYAL SANCTUARY
    "1545518525634838658": [
        "1545518535827263519",  # executive-chat
        "1545518528126394400",  # 👑 Emperor's Throne
        "1545518531192553603",  # ⚡ High Command
        "1545518533566271539",  # 🍸 Private Lounge
    ],
    # 🛡️ STAFF ZONE
    "1545502840452157463": [
        "1545502845208629328",  # staff-chat
        "1545514505520545886",  # ticket-support
        "1545502850057244762",  # mod-logs
    ]
}

def update_bulk_positions(items):
    r = requests.patch(
        f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
        headers=HEADERS,
        json=items
    )
    return r.status_code in (200, 204), r.text

def main():
    print("✨ Updating Category Positions...")
    cat_payload = [{"id": cid, "position": idx} for idx, cid in enumerate(CATEGORY_ORDER)]
    ok, res = update_bulk_positions(cat_payload)
    print(f"Categories reordered: {ok} ({res})")
    time.sleep(0.5)

    print("✨ Updating Channel Positions within Categories...")
    for cat_id, chan_ids in CHANNEL_ORDER_BY_CAT.items():
        chan_payload = [{"id": cid, "position": idx} for idx, cid in enumerate(chan_ids)]
        ok, res = update_bulk_positions(chan_payload)
        print(f"  Category {cat_id} channels reordered: {ok}")
        time.sleep(0.4)

    print("🎉 All Channel & Category Orders Successfully Optimized!")

if __name__ == "__main__":
    main()
