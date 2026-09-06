import os
import sys
import json
import urllib.request
from datetime import datetime
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(r"F:\antigravity\APEX VIBES\.env")
TOKEN = (os.getenv("DISCORD_BOT_TOKEN") or "").strip()
GUILD_ID = "1457382179981099090"
HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json", "User-Agent": "DiscordBot (Onboarding, 1.0)"}

def make_request(url, method="GET", data=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bot {TOKEN}")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", "DiscordBot (Onboarding, 1.0)")
    if data:
        body = json.dumps(data).encode("utf-8")
        req.data = body
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode("utf-8"))

# 1. Fetch existing roles
existing_roles = make_request(f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles")
role_map = {r["name"]: r["id"] for r in existing_roles}

# 2. Define identity roles to ensure exist
identity_roles_to_create = [
    {"name": "👦 ┆ 𝐌𝐀𝐋𝐄 👦", "color": 0x3498DB, "hoist": False, "mentionable": False},
    {"name": "👧 ┆ 𝐅𝐄𝐌𝐀𝐋𝐄 👧", "color": 0xE91E63, "hoist": False, "mentionable": False},
    {"name": "🔞 ┆ 𝟏𝟖+ 𝐀𝐃𝐔𝐋𝐓 🔞", "color": 0x9B59B6, "hoist": False, "mentionable": False},
    {"name": "🎒 ┆ 𝐔𝐍𝐃𝐄𝐑 𝟏𝟖 🎒", "color": 0x1ABC9C, "hoist": False, "mentionable": False},
]

for ir in identity_roles_to_create:
    if ir["name"] not in role_map:
        new_role = make_request(f"https://discord.com/api/v10/guilds/{GUILD_ID}/roles", method="POST", data=ir)
        role_map[ir["name"]] = new_role["id"]
        print(f"Created role: {ir['name']} (ID: {new_role['id']})")
    else:
        print(f"Role already exists: {ir['name']} (ID: {role_map[ir['name']]})")

male_role_id = role_map["👦 ┆ 𝐌𝐀𝐋𝐄 👦"]
female_role_id = role_map["👧 ┆ 𝐅𝐄𝐌𝐀𝐋𝐄 👧"]
adult_role_id = role_map["🔞 ┆ 𝟏𝟖+ 𝐀𝐃𝐔𝐋𝐓 🔞"]
under18_role_id = role_map["🎒 ┆ 𝐔𝐍𝐃𝐄𝐑 𝟏𝟖 🎒"]

base_sf = discord.utils.time_snowflake(datetime.now())
sf_counter = 0
def next_sf():
    global sf_counter
    sf_counter += 1
    return str(base_sf + sf_counter)

# Channels
default_channel_ids = [
    "1545502705643167876", # 👋・welcome
    "1545502710101704714", # 📜・rules
    "1545502700840427702", # ✅・verify
    "1545502722739150898", # 🎭・self-roles
    "1545502730699808768", # 💬・general
    "1545502718792175646", # 📢・announcements
]

# Question 1: What brings you to RAI FAM?
q1_options = [
    {
        "id": next_sf(),
        "title": "🎮 Play Games",
        "description": "Find squadmates for Free Fire, BGMI & more",
        "role_ids": ["1545516397034078269"],
        "channel_ids": ["1545803554550190212"]
    },
    {
        "id": next_sf(),
        "title": "🎧 Listen to Music",
        "description": "24/7 Lo-Fi beats and music listening rooms",
        "role_ids": ["1545494584203673740"],
        "channel_ids": ["1545781986193309789"]
    },
    {
        "id": next_sf(),
        "title": "🍿 Watch Anime & Movies",
        "description": "Stream anime and watch movie nights together",
        "role_ids": ["1546062599253135420"],
        "channel_ids": ["1545502762467328185"]
    },
    {
        "id": next_sf(),
        "title": "💬 Just Chat & Chill",
        "description": "Hangout, talk in VC and make new friends",
        "role_ids": ["1545494584203673740"],
        "channel_ids": ["1545502730699808768"]
    }
]

# Question 2: Which games do you play?
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

# Question 3 (REPLACEMENT): Member Identification (Gender & Identity)
q3_options = [
    {
        "id": next_sf(),
        "title": "👦 Male / Boy",
        "description": "He / Him",
        "role_ids": [male_role_id],
        "channel_ids": []
    },
    {
        "id": next_sf(),
        "title": "👧 Female / Girl",
        "description": "She / Her",
        "role_ids": [female_role_id],
        "channel_ids": []
    },
    {
        "id": next_sf(),
        "title": "🔞 18+ Adult",
        "description": "Age 18 and above",
        "role_ids": [adult_role_id],
        "channel_ids": []
    },
    {
        "id": next_sf(),
        "title": "🎒 Under 18",
        "description": "Teen / Student",
        "role_ids": [under18_role_id],
        "channel_ids": []
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
        "title": "👤 How should we identify you?",
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
res = make_request(url, method="PUT", data=payload)
print("🎉 SUCCESS! Onboarding updated with Member Identification options!")
