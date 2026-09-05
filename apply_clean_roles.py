import sys
import os
import requests
import json
import time

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import config

headers = {
    "Authorization": f"Bot {config.DISCORD_TOKEN}",
    "Content-Type": "application/json"
}

GUILD_ID = "1457382179981099090"

ROLE_NAME_UPDATES = {
    "1545494610489643038": "F O U N D E R 🍷",
    "1545506927788687470": "H E A D  A D M I N ⚡",
    "1545494600347680918": "M O D E R A T O R 🛡️",
    "1545494591883579434": "Server Booster 🚀",
    "1545494584203673740": "RAI FAMILY 🌸",
    "1545494578512134176": "AUDIO BOTS 🤖",
    
    # Colors
    "1545516328016805979": "Sakura Pink 🌸",
    "1545516370785996882": "Neon Violet 💜",
    "1545516378046337074": "Cyber Cyan 🩵",
    "1545516381426950214": "Royal Gold 💛",

    # Device & Gaming
    "1545516406454493257": "PC Player 💻",
    "1545516404302811256": "Mobile Player 📱",
    "1545516397034078269": "Free Fire 💥",
    "1545516399663779871": "BGMI ⚡",
    "1545516402188881991": "Roblox 🧸",

    # Identity & Pronouns
    "1545516419121422377": "Male 🤴",
    "1545516421583208551": "Female 👸",
    "1545516423789543651": "They / Them 🌈",
    "1545516426893197392": "18+ Verified 🔞",

    # Notification Alerts
    "1545516408375353376": "Movie Alerts 🍿",
    "1545516411659620383": "Giveaways 🎉",
    "1545516414016815169": "Server News 📢",
    "1545516416969609296": "Music Jam 🎵",

    # Levels / Activity Tiers
    "1545516383742201919": "Rai Legend 💎",
    "1545516386887929916": "Rai Champion 🔥",
    "1545516390520193165": "Rai Active ✨",
    "1545516392969670787": "Rai Novice 🌱",
}

print(f"Applying clean aesthetic role names to Guild {GUILD_ID}...")
for role_id, new_name in ROLE_NAME_UPDATES.items():
    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles/{role_id}"
    payload = {"name": new_name}
    r = requests.patch(url, headers=headers, json=payload)
    if r.status_code == 200:
        print(f"✅ Updated Role {role_id} -> '{new_name}'")
    else:
        print(f"❌ Failed to update {role_id}: {r.status_code} - {r.text}")
    time.sleep(0.3)

print("\n✨ All role names updated cleanly!")
