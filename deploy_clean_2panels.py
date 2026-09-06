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
CHANNEL_ID = '1545502722739150898' # #🎭・self-roles

import discord
import asyncio
from utils.persistent_views import GamingRolesView, NotificationRolesView

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
            "Welcome to the **Role Selection Hub**! 🌸\n\n"
            "Pick your gaming squads to find teammates in <#1545803554550190212> and choose which community alerts you wish to receive.\n"
            "Click the interactive buttons below to **toggle roles on & off instantly**!"
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
            "Select the games you play to get pinged for custom rooms, matches & squad finding:\n\n"
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
            "Choose which special community announcements and event pings you want to receive:\n\n"
            "📢 **Announcements** ➔ `<@&1546088542885642324>`\n"
            "🎁 **Giveaways** ➔ `<@&1546088546555924534>`\n"
            "🏆 **Tournaments** ➔ `<@&1546088548913119323>`\n"
            "🍿 **Movie Nights** ➔ `<@&1546062599253135420>`"
        ),
        color=0x00F0FF
    )
    embed_notifs.set_footer(text="Click a button below to toggle notification pings", icon_url=chan.guild.icon.url if chan.guild.icon else None)
    await chan.send(embed=embed_notifs, view=NotificationRolesView())

    print("🎉 Clean 2-panel Self-Roles deployed successfully without color roles!")
    await client.close()

asyncio.run(client.start(TOKEN))
