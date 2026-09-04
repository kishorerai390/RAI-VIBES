import os
import sys
import requests
import discord
from datetime import datetime
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"
HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

def main():
    print("Fetching server roles & channels for Onboarding setup...")
    r_roles = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles", headers=HEADERS)
    roles = {r["name"]: r["id"] for r in r_roles.json()}

    r_chans = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    channels = {c["name"]: c["id"] for c in r_chans.json()}

    # Helper to find role ID
    def get_role_id(name):
        return roles.get(name)

    # Helper to find channel ID
    def get_chan_id(name):
        return channels.get(name)

    # 1. Default channels new members see
    default_chans = [
        get_chan_id("✅・verify-here"),
        get_chan_id("👋・welcome"),
        get_chan_id("📜・rules"),
        get_chan_id("📢・announcements"),
        get_chan_id("⭐・self-roles"),
        get_chan_id("💬・general-chat"),
        get_chan_id("📸・media"),
        get_chan_id("🤖・bot-commands")
    ]
    default_chans = [cid for cid in default_chans if cid]

    base_sf = discord.utils.time_snowflake(datetime.now())
    sf_counter = 0
    def next_sf():
        nonlocal sf_counter
        sf_counter += 1
        return str(base_sf + sf_counter)

    # Prompt 1: Gaming Squads
    p1_options = [
        {
            "id": next_sf(),
            "title": "Free Fire",
            "description": "Squad matches and rank push",
            "emoji": {"name": "🔥"},
            "role_ids": [get_role_id("🔥 ┊ Free Fire")] if get_role_id("🔥 ┊ Free Fire") else [],
            "channel_ids": [get_chan_id("⚡ | FREE FIRE")] if get_chan_id("⚡ | FREE FIRE") else []
        },
        {
            "id": next_sf(),
            "title": "BGMI / PUBG",
            "description": "Classics, TDM and custom rooms",
            "emoji": {"name": "⚡"},
            "role_ids": [get_role_id("⚡ ┊ BGMI")] if get_role_id("⚡ ┊ BGMI") else [],
            "channel_ids": [get_chan_id("⚡ | BGMI")] if get_chan_id("⚡ | BGMI") else []
        },
        {
            "id": next_sf(),
            "title": "Roblox",
            "description": "Party games and hangouts",
            "emoji": {"name": "🧸"},
            "role_ids": [get_role_id("🧸 ┊ Roblox")] if get_role_id("🧸 ┊ Roblox") else [],
            "channel_ids": [get_chan_id("⚡ | ROBLOX")] if get_chan_id("⚡ | ROBLOX") else []
        },
        {
            "id": next_sf(),
            "title": "Mobile Gamer",
            "description": "Mobile gaming squad",
            "emoji": {"name": "📱"},
            "role_ids": [get_role_id("📱 ┊ Mobile Gamer")] if get_role_id("📱 ┊ Mobile Gamer") else [],
            "channel_ids": []
        },
        {
            "id": next_sf(),
            "title": "PC Gamer",
            "description": "PC & Steam gaming",
            "emoji": {"name": "💻"},
            "role_ids": [get_role_id("💻 ┊ PC Gamer")] if get_role_id("💻 ┊ PC Gamer") else [],
            "channel_ids": []
        }
    ]

    # Prompt 2: Notifications
    p2_options = [
        {
            "id": next_sf(),
            "title": "Movie & Anime Streams",
            "description": "Pings when cinema stream starts",
            "emoji": {"name": "🎬"},
            "role_ids": [get_role_id("🎬 ┊ Movie Alerts")] if get_role_id("🎬 ┊ Movie Alerts") else [],
            "channel_ids": [get_chan_id("🎥 | CINEMA THEATER")] if get_chan_id("🎥 | CINEMA THEATER") else []
        },
        {
            "id": next_sf(),
            "title": "Giveaways & Rewards",
            "description": "Pings for Nitro & game rewards",
            "emoji": {"name": "🎉"},
            "role_ids": [get_role_id("🎉 ┊ Giveaway Alerts")] if get_role_id("🎉 ┊ Giveaway Alerts") else [],
            "channel_ids": []
        },
        {
            "id": next_sf(),
            "title": "Server News & Events",
            "description": "Major server announcements",
            "emoji": {"name": "📢"},
            "role_ids": [get_role_id("📢 ┊ Server News")] if get_role_id("📢 ┊ Server News") else [],
            "channel_ids": [get_chan_id("📢・announcements")] if get_chan_id("📢・announcements") else []
        },
        {
            "id": next_sf(),
            "title": "Music Jam & Radio",
            "description": "24/7 radio and DJ hangouts",
            "emoji": {"name": "🎧"},
            "role_ids": [get_role_id("🎧 ┊ Music Jam")] if get_role_id("🎧 ┊ Music Jam") else [],
            "channel_ids": [get_chan_id("📻 | 24-7 RADIO")] if get_chan_id("📻 | 24-7 RADIO") else []
        }
    ]

    # Prompt 3: Name Color
    p3_options = [
        {
            "id": next_sf(),
            "title": "Sakura Pink",
            "description": "Pastel cherry blossom glow",
            "emoji": {"name": "🌸"},
            "role_ids": [get_role_id("🌸 ┊ Sakura Pink")] if get_role_id("🌸 ┊ Sakura Pink") else [],
            "channel_ids": []
        },
        {
            "id": next_sf(),
            "title": "Neon Violet",
            "description": "Royal futuristic purple glow",
            "emoji": {"name": "💜"},
            "role_ids": [get_role_id("💜 ┊ Neon Violet")] if get_role_id("💜 ┊ Neon Violet") else [],
            "channel_ids": []
        },
        {
            "id": next_sf(),
            "title": "Cyber Cyan",
            "description": "Glowing turquoise neon",
            "emoji": {"name": "🩵"},
            "role_ids": [get_role_id("🩵 ┊ Cyber Cyan")] if get_role_id("🩵 ┊ Cyber Cyan") else [],
            "channel_ids": []
        },
        {
            "id": next_sf(),
            "title": "Royal Gold",
            "description": "Radiant emperor gold glow",
            "emoji": {"name": "💛"},
            "role_ids": [get_role_id("💛 ┊ Royal Gold")] if get_role_id("💛 ┊ Royal Gold") else [],
            "channel_ids": []
        }
    ]

    prompts = [
        {
            "id": next_sf(),
            "title": "🎮 What games do you play?",
            "type": 0,
            "single_select": False,
            "required": False,
            "in_onboarding": True,
            "options": p1_options
        },
        {
            "id": next_sf(),
            "title": "🔔 What notifications do you want?",
            "type": 0,
            "single_select": False,
            "required": False,
            "in_onboarding": True,
            "options": p2_options
        },
        {
            "id": next_sf(),
            "title": "🎨 Choose your username color:",
            "type": 0,
            "single_select": True,
            "required": False,
            "in_onboarding": True,
            "options": p3_options
        }
    ]

    payload = {
        "prompts": prompts,
        "default_channel_ids": default_chans,
        "enabled": True,
        "mode": 0
    }

    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/onboarding"
    res = requests.put(url, headers=HEADERS, json=payload)
    if res.status_code in (200, 204):
        print("🎉 SUCCESS! Discord Onboarding Customization Questions updated with full roles & channels!")
    else:
        print(f"❌ Failed to update onboarding: {res.status_code} {res.text}")

if __name__ == "__main__":
    main()
