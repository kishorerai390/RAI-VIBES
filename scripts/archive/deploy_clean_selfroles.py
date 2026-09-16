import sys
from pathlib import Path
import discord
import asyncio

PROJECT_ROOT = Path(r"f:\antigravity\APEX VIBES")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import config
from utils.persistent_views import (
    ColorRolesView,
    GamingRolesView,
    NotificationRolesView,
    IdentityRolesView
)

intents = discord.Intents.default()
intents.guilds = True
client = discord.Client(intents=intents)

SELF_ROLES_CHANNEL_ID = 1545502722739150898

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    chan = client.get_channel(SELF_ROLES_CHANNEL_ID)
    if not chan:
        print("Channel not found!")
        await client.close()
        return

    # Clear old bot messages in self-roles
    try:
        async for msg in chan.history(limit=50):
            if msg.author == client.user:
                await msg.delete()
    except Exception as e:
        print(f"Error purging old messages: {e}")

    # 1. Colors Panel
    embed_color = discord.Embed(
        title="🎨 ┃ CHOOSE YOUR NAME COLOR",
        description=(
            "Personalize your appearance across the server with our curated aesthetic colors!\n"
            "Click any button below to equip or remove your color role."
        ),
        color=config.COLOR_PRIMARY
    )
    embed_color.add_field(
        name="✨ Available Palette",
        value=(
            "• 🌸 **Sakura Pink** (`#FF69B4`)\n"
            "• 💜 **Neon Violet** (`#9B5DE5`)\n"
            "• 🩵 **Cyber Cyan** (`#00F0FF`)\n"
            "• 💛 **Royal Gold** (`#FEE440`)"
        ),
        inline=False
    )
    await chan.send(embed=embed_color, view=ColorRolesView())

    # 2. Gaming & Device Platforms Panel
    embed_gaming = discord.Embed(
        title="🎮 ┃ GAMING & DEVICE PLATFORMS",
        description="Select your preferred gaming platforms and titles to connect with squadmates!",
        color=config.COLOR_SECONDARY
    )
    embed_gaming.add_field(
        name="🕹️ Platform & Game Tags",
        value=(
            "• 💻 **PC Player** — Desktop & PC gaming community\n"
            "• 📱 **Mobile Player** — Mobile & tablet gamers\n"
            "• 💥 **Free Fire** — Battle Royale squad pings\n"
            "• ⚡ **BGMI** — BGMI / PUBG custom rooms\n"
            "• 🧸 **Roblox** — Hangout & mini-games"
        ),
        inline=False
    )
    await chan.send(embed=embed_gaming, view=GamingRolesView())

    # 3. Notification Pings Panel
    embed_notif = discord.Embed(
        title="🔔 ┃ NOTIFICATION & EVENT PINGS",
        description="Choose which community alerts and event announcements you'd like to receive:",
        color=config.COLOR_GOLD
    )
    embed_notif.add_field(
        name="📢 Notification Preferences",
        value=(
            "• 🍿 **Movie Alerts** — Cinema Theater watch party reminders\n"
            "• 🎉 **Giveaways** — Nitro, coins & VIP reward alerts\n"
            "• 📢 **Server News** — Important announcements & updates\n"
            "• 🎵 **Music Jam** — Live listening parties & karaoke"
        ),
        inline=False
    )
    await chan.send(embed=embed_notif, view=NotificationRolesView())

    # 4. Identity & Pronouns Panel
    embed_id = discord.Embed(
        title="👤 ┃ IDENTITY & VERIFICATION",
        description="Select your identity tags and age verification status:",
        color=config.COLOR_DARK
    )
    embed_id.add_field(
        name="🌟 Member Identity",
        value=(
            "• 🤴 **Male** — He / Him\n"
            "• 👸 **Female** — She / Her\n"
            "• 🌈 **They / Them** — Non-Binary / Other\n"
            "• 🔞 **18+ Verified** — Adult lounge access"
        ),
        inline=False
    )
    await chan.send(embed=embed_id, view=IdentityRolesView())

    print("✨ Successfully deployed all 4 clean aesthetic self-role panels!")
    await client.close()

asyncio.run(client.start(config.DISCORD_TOKEN))
