import os
import sys
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"

HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

# Definitions of all roles with decimal color codes
ROLE_DEFINITIONS = [
    # 1. Colors (Sakura Pink: 16758725, Neon Violet: 10182121, Cyber Cyan: 62932, Royal Gold: 16704576)
    {"name": "🌸 ┊ Sakura Pink", "color": 0xFFB7C5, "mentionable": False},
    {"name": "💜 ┊ Neon Violet", "color": 0x9B5DE5, "mentionable": False},
    {"name": "🩵 ┊ Cyber Cyan", "color": 0x00F5D4, "mentionable": False},
    {"name": "💛 ┊ Royal Gold", "color": 0xFEE440, "mentionable": False},

    # 2. Level & Activity Rewards
    {"name": "💎 ┊ Rai Legend", "color": 0xDED8F6, "mentionable": True},
    {"name": "🔥 ┊ Rai Champion", "color": 0xFFAAA5, "mentionable": True},
    {"name": "✨ ┊ Rai Active", "color": 0xFFD3B6, "mentionable": False},
    {"name": "🌱 ┊ Rai Novice", "color": 0xA8E6CF, "mentionable": False},

    # 3. Gaming Roles
    {"name": "🔥 ┊ Free Fire", "color": 0xFF7700, "mentionable": True},
    {"name": "⚡ ┊ BGMI", "color": 0xF1C40F, "mentionable": True},
    {"name": "🧸 ┊ Roblox", "color": 0xE74C3C, "mentionable": True},
    {"name": "📱 ┊ Mobile Gamer", "color": 0x3498DB, "mentionable": True},
    {"name": "💻 ┊ PC Gamer", "color": 0x2980B9, "mentionable": True},

    # 4. Notifications & Alerts
    {"name": "🎬 ┊ Movie Alerts", "color": 0xE91E63, "mentionable": True},
    {"name": "🎉 ┊ Giveaway Alerts", "color": 0x2ECC71, "mentionable": True},
    {"name": "📢 ┊ Server News", "color": 0x9B59B6, "mentionable": True},
    {"name": "🎧 ┊ Music Jam", "color": 0x1ABC9C, "mentionable": True},

    # 5. Identity & Profile
    {"name": "♂️ ┊ He/Him", "color": 0x95A5A6, "mentionable": False},
    {"name": "♀️ ┊ She/Her", "color": 0xE84393, "mentionable": False},
    {"name": "🌈 ┊ They/Them", "color": 0x00CEC9, "mentionable": False},
    {"name": "🔞 ┊ 18+ Verified", "color": 0xD63031, "mentionable": False},
]

def main():
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles", headers=HEADERS)
    if r.status_code != 200:
        print(f"Failed to fetch roles: {r.status_code} {r.text}")
        return

    existing_roles = {role["name"]: role for role in r.json()}
    print(f"Found {len(existing_roles)} existing roles.")

    created = 0
    for rdef in ROLE_DEFINITIONS:
        if rdef["name"] in existing_roles:
            print(f"Already exists: {rdef['name']}")
        else:
            payload = {
                "name": rdef["name"],
                "color": rdef["color"],
                "mentionable": rdef["mentionable"],
                "hoist": False
            }
            res = requests.post(f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles", headers=HEADERS, json=payload)
            if res.status_code in (200, 201):
                print(f"✅ Created role: {rdef['name']}")
                created += 1
            else:
                print(f"❌ Failed to create role {rdef['name']}: {res.status_code} {res.text}")

    print(f"Finished creating {created} new roles!")

if __name__ == "__main__":
    main()
