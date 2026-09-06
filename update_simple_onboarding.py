import os
import sys
import json
import urllib.request
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

# Default channels everyone sees
default_channel_ids = [
    "1545502705643167876", # 👋・welcome
    "1545502710101704714", # 📜・rules
    "1545502700840427702", # ✅・verify
    "1545502722739150898", # 🎭・self-roles
    "1545502730699808768", # 💬・general
    "1545502718792175646", # 📢・announcements
]

# Simple Question 1: What do you want to do here?
q1_options = [
    {
        "id": next_sf(),
        "title": "🎮 Play Games",
        "description": "Find squadmates for Free Fire, BGMI & more",
        "role_ids": ["1545516397034078269"],
        "channel_ids": ["1545803554550190212"] # 💬・gaming-text
    },
    {
        "id": next_sf(),
        "title": "🎧 Listen to Music",
        "description": "24/7 Lo-Fi beats and music listening rooms",
        "role_ids": ["1545494584203673740"],
        "channel_ids": ["1545781986193309789"] # 🎧 | LO-FI CHILL [24/7]
    },
    {
        "id": next_sf(),
        "title": "🍿 Watch Anime & Movies",
        "description": "Stream anime and watch movie nights together",
        "role_ids": ["1546062599253135420"],
        "channel_ids": ["1545502762467328185"] # 🎦 | MOVIE¹
    },
    {
        "id": next_sf(),
        "title": "💬 Just Chat & Chill",
        "description": "Hangout, talk in VC and make new friends",
        "role_ids": ["1545494584203673740"],
        "channel_ids": ["1545502730699808768"] # 💬・general
    }
]

# Simple Question 2: What games do you play?
q2_options = [
    {
        "id": next_sf(),
        "title": "Free Fire",
        "description": "Battle Royale & Custom matches",
        "role_ids": ["1545516397034078269"],
        "channel_ids": ["1545502823699980408"]
    },
    {
        "id": next_sf(),
        "title": "BGMI",
        "description": "Classics, TDM & Scrims",
        "role_ids": ["1545516399663779871"],
        "channel_ids": ["1545502829089787924"]
    },
    {
        "id": next_sf(),
        "title": "GTA RP",
        "description": "Roleplay gaming sessions",
        "role_ids": ["1546062595293978694"],
        "channel_ids": ["1545502794868457574"]
    },
    {
        "id": next_sf(),
        "title": "Roblox",
        "description": "Fun party games",
        "role_ids": ["1545516402188881991"],
        "channel_ids": ["1545502832822591539"]
    }
]

# Simple Question 3: Do you want event and giveaway alerts?
q3_options = [
    {
        "id": next_sf(),
        "title": "🎁 Giveaways & Rewards",
        "description": "Get notified when Nitro or coins are given away",
        "role_ids": ["1546088546555924534"],
        "channel_ids": []
    },
    {
        "id": next_sf(),
        "title": "📢 Server Announcements",
        "description": "Get notified for major community news",
        "role_ids": ["1546088542885642324"],
        "channel_ids": ["1545502718792175646"]
    },
    {
        "id": next_sf(),
        "title": "🏆 Tournament Pings",
        "description": "Get notified when gaming tournaments start",
        "role_ids": ["1546088548913119323"],
        "channel_ids": ["1545803554550190212"]
    }
]

prompts = [
    {
        "id": next_sf(),
        "title": "🌟 Why did you join RAI FAM?",
        "type": 0,
        "single_select": False,
        "required": False,
        "in_onboarding": True,
        "options": q1_options
    },
    {
        "id": next_sf(),
        "title": "🎮 Which games do you play?",
        "type": 0,
        "single_select": False,
        "required": False,
        "in_onboarding": True,
        "options": q2_options
    },
    {
        "id": next_sf(),
        "title": "🔔 Want special event pings?",
        "type": 0,
        "single_select": False,
        "required": False,
        "in_onboarding": True,
        "options": q3_options
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
        print("🎉 SUCCESS! Simple, high-converting onboarding questions configured!")
except Exception as e:
    print(f"Error: {e}")
