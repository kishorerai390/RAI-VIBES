import os, sys, json, urllib.request
from datetime import datetime
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"
HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json", "User-Agent": "DiscordBot (Onboarding, 1.0)"}

base_sf = discord.utils.time_snowflake(datetime.now())
sf_counter = 0
def next_sf():
    global sf_counter
    sf_counter += 1
    return str(base_sf + sf_counter)

# 1. Default channels
default_channel_ids = [
    "1545502705643167876", # 👋・welcome
    "1545502710101704714", # 📜・rules
    "1545502700840427702", # ✅・verify
    "1545502722739150898", # 🎭・self-roles
    "1545502730699808768", # 💬・general
    "1545502718792175646", # 📢・announcements
]

# Prompt 1: Gaming Squads
p1_options = [
    {
        "id": next_sf(),
        "title": "Free Fire",
        "description": "Squad scrims and custom rooms",
        "emoji": {"id": None, "name": "💥", "animated": False},
        "role_ids": ["1545516397034078269"],
        "channel_ids": ["1545502823699980408"]
    },
    {
        "id": next_sf(),
        "title": "BGMI / PUBG",
        "description": "Classics, TDM & tournament matchmaking",
        "emoji": {"id": None, "name": "⚡", "animated": False},
        "role_ids": ["1545516399663779871"],
        "channel_ids": ["1545502829089787924"]
    },
    {
        "id": next_sf(),
        "title": "GTA V / RP",
        "description": "Tamil & Global RP server sessions",
        "emoji": {"id": None, "name": "🔫", "animated": False},
        "role_ids": ["1546062595293978694"],
        "channel_ids": ["1545502794868457574"]
    },
    {
        "id": next_sf(),
        "title": "Roblox",
        "description": "Party games and hangouts",
        "emoji": {"id": None, "name": "🧸", "animated": False},
        "role_ids": ["1545516402188881991"],
        "channel_ids": ["1545502832822591539"]
    }
]

# Prompt 2: Notifications
p2_options = [
    {
        "id": next_sf(),
        "title": "Announcements",
        "description": "Major server news & updates",
        "emoji": {"id": None, "name": "📢", "animated": False},
        "role_ids": ["1546088542885642324"],
        "channel_ids": ["1545502718792175646"]
    },
    {
        "id": next_sf(),
        "title": "Giveaways",
        "description": "Nitro, cash & VIP role giveaway alerts",
        "emoji": {"id": None, "name": "🎁", "animated": False},
        "role_ids": ["1546088546555924534"],
        "channel_ids": []
    },
    {
        "id": next_sf(),
        "title": "Tournaments",
        "description": "Competitive scrim & cash prize alerts",
        "emoji": {"id": None, "name": "🏆", "animated": False},
        "role_ids": ["1546088548913119323"],
        "channel_ids": ["1545803554550190212"]
    },
    {
        "id": next_sf(),
        "title": "Movie Nights",
        "description": "Cinema & anime watch party pings",
        "emoji": {"id": None, "name": "🍿", "animated": False},
        "role_ids": ["1546062599253135420"],
        "channel_ids": ["1545502762467328185"]
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
        "title": "🔔 What notifications would you like to receive?",
        "type": 0,
        "single_select": False,
        "required": False,
        "in_onboarding": True,
        "options": p2_options
    }
]

payload = {
    "prompts": prompts,
    "default_channel_ids": default_channel_ids,
    "enabled": True,
    "mode": 0
}

url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/onboarding"
req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=HEADERS, method='PUT')

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("🎉 SUCCESS! Discord Onboarding strictly set to ONLY 2 questions with emojis!")
except Exception as e:
    print(f"Error: {e}")
