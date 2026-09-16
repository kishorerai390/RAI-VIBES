import os
import sys
import json
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(r"f:\antigravity\APEX VIBES")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'
CHANNEL_ID = '1545502722739150898' # #🎭・self-roles

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (Deploy, 1.0)', 'Content-Type': 'application/json'}

# 1. Purge previous messages in #🎭・self-roles
print("Cleaning old messages in self-roles...")
try:
    req = urllib.request.Request(f'https://discord.com/api/v10/channels/{CHANNEL_ID}/messages?limit=50', headers=headers)
    with urllib.request.urlopen(req) as resp:
        msgs = json.loads(resp.read().decode('utf-8'))
    
    for m in msgs:
        dreq = urllib.request.Request(f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages/{m['id']}", headers=headers, method='DELETE')
        try:
            with urllib.request.urlopen(dreq) as dresp:
                pass
        except Exception:
            pass
    print("Channel cleaned!")
except Exception as e:
    print(f"Purge note: {e}")

# 2. Deploy Panels via discord.py client to bind persistent views
import discord
import asyncio
from utils.persistent_views import GamingRolesView, NotificationRolesView, ColorRolesView

intents = discord.Intents.default()
intents.guilds = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    chan = client.get_channel(int(CHANNEL_ID))
    if not chan:
        print("Channel not found!")
        await client.close()
        return

    # Banner Header
    embed_header = discord.Embed(
        title="🎭 ◈ RAI FAM • OFFICIAL SELF ROLES ◈ 🎭",
        description=(
            "Welcome to the **Role Customization Station**! 🌸\n\n"
            "Personalize your profile, find squadmates for games, and customize which notifications you receive.\n"
            "Click the interactive buttons below to **toggle roles instantly** on and off!"
        ),
        color=0xFF69B4
    )
    embed_header.set_image(url="https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif")
    embed_header.set_footer(text="RAI FAM 💗 • Instant 1-Click Role Engine", icon_url=chan.guild.icon.url if chan.guild.icon else None)
    await chan.send(embed=embed_header)

    # 1. Gaming Squads Panel
    embed_gaming = discord.Embed(
        title="🎮 ◈ GAMING SQUAD SELECTION ◈ 🎮",
        description=(
            "Pick the games you play to get notified for custom rooms, scrims, and squad matchmaking in <#1545803554550190212>!\n\n"
            "💥 **Free Fire** ➔ `<@&1545516397034078269>`\n"
            "⚡ **BGMI / PUBG** ➔ `<@&1545516399663779871>`\n"
            "🔫 **GTA V / RP** ➔ `<@&1546062595293978694>`\n"
            "🧸 **Roblox** ➔ `<@&1545516402188881991>`"
        ),
        color=0x9B5DE5
    )
    embed_gaming.set_footer(text="Click a button below to equip / remove your game roles", icon_url=chan.guild.icon.url if chan.guild.icon else None)
    await chan.send(embed=embed_gaming, view=GamingRolesView())

    # 2. Notification Pings Panel
    embed_notifs = discord.Embed(
        title="🔔 ◈ NOTIFICATION & EVENT PINGS ◈ 🔔",
        description=(
            "Choose which special community alerts and event announcements you'd like to receive:\n\n"
            "📢 **Announcements** ➔ `<@&1546088542885642324>`\n"
            "🎁 **Giveaways** ➔ `<@&1546088546555924534>`\n"
            "🏆 **Tournaments** ➔ `<@&1546088548913119323>`\n"
            "🍿 **Movie Nights** ➔ `<@&1546062599253135420>`"
        ),
        color=0x00F0FF
    )
    embed_notifs.set_footer(text="Click a button below to toggle notification pings", icon_url=chan.guild.icon.url if chan.guild.icon else None)
    await chan.send(embed=embed_notifs, view=NotificationRolesView())

    # 3. Custom Name Colors Panel
    embed_colors = discord.Embed(
        title="🎨 ◈ CUSTOM NAME COLORS ◈ 🎨",
        description=(
            "Equip a vibrant aesthetic color to make your username stand out in chat and voice channels!\n\n"
            "🌸 **Sakura Pink** ➔ `<@&1546088552293728268>`\n"
            "💜 **Neon Purple** ➔ `<@&1546088554747142174>`\n"
            "🩵 **Cyber Cyan** ➔ `<@&1546088557742129232>`\n"
            "💛 **Royal Gold** ➔ `<@&1546088559830634586>`\n\n"
            "*(Equipping a new color automatically replaces your previous one)*"
        ),
        color=0xFEE440
    )
    embed_colors.set_footer(text="Click a button below to equip your favorite color", icon_url=chan.guild.icon.url if chan.guild.icon else None)
    await chan.send(embed=embed_colors, view=ColorRolesView())

    print("🎉 All 3 luxury Self-Role panels deployed successfully!")
    await client.close()

asyncio.run(client.start(TOKEN))
