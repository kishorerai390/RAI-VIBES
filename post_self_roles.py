import os
import sys
import asyncio
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

from utils.persistent_views import (
    ColorRolesView,
    GamingRolesView,
    NotificationRolesView,
    IdentityRolesView
)

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user} ({client.user.id})")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    # Find self-roles channel
    role_chan = (
        discord.utils.get(guild.text_channels, name="self-roles") or
        discord.utils.get(guild.text_channels, name="├・「⭐」self-roles") or
        discord.utils.get(guild.text_channels, name="⭐・self-roles")
    )

    if not role_chan:
        print("Self-roles channel not found")
        await client.close()
        return

    print(f"Purging old messages in #{role_chan.name}...")
    try:
        await role_chan.purge(limit=25)
    except Exception as e:
        print(f"Could not purge: {e}")

    # 1. Color Roles Embed
    embed1 = discord.Embed(
        title="🎨 ⋆⋅ NAME COLOR PALETTE ⋅⋆",
        description=(
            "Customize your username color across all text channels!\n"
            "Click any button below to equip your color (clicking again will remove it):\n\n"
            "🌸 **Sakura Pink** • Soft pastel cherry blossom\n"
            "💜 **Neon Violet** • Royal futuristic purple\n"
            "🩵 **Cyber Cyan** • Glowing neon turquoise\n"
            "💛 **Royal Gold** • Radiant emperor golden glow\n"
        ),
        color=0xFFB7C5
    )
    embed1.set_footer(text="RAI FAM 💗 • Select one color at a time")
    await role_chan.send(embed=embed1, view=ColorRolesView())

    # 2. Gaming Roles Embed
    embed2 = discord.Embed(
        title="🎮 ⋆⋅ GAMING SQUAD ROLES ⋅⋆",
        description=(
            "Pick the games you play to unlock squad pings and game channels!\n\n"
            "🔥 **Free Fire** • Squad matches & rank push\n"
            "⚡ **BGMI / PUBG** • Classic, TDM & custom rooms\n"
            "🧸 **Roblox** • Chill hangouts & party games\n"
            "📱 **Mobile Gamer** • Mobile squad player\n"
            "💻 **PC Gamer** • PC / Steam gaming player\n"
        ),
        color=0x3498DB
    )
    embed2.set_footer(text="RAI FAM 💗 • Click to toggle roles on or off")
    await role_chan.send(embed=embed2, view=GamingRolesView())

    # 3. Notification Roles Embed
    embed3 = discord.Embed(
        title="🔔 ⋆⋅ SERVER NOTIFICATIONS & PINGS ⋅⋆",
        description=(
            "Stay in the loop! Toggle what events you want to be pinged for:\n\n"
            "🎬 **Movie Alerts** • Movie streams & anime watch parties\n"
            "🎉 **Giveaway Alerts** • Nitro, gift cards & special rewards\n"
            "📢 **Server News** • Major updates & announcements\n"
            "🎧 **Music Jam** • Live DJ listening parties & radio events\n"
        ),
        color=0x2ECC71
    )
    embed3.set_footer(text="RAI FAM 💗 • No unnecessary @everyone pings")
    await role_chan.send(embed=embed3, view=NotificationRolesView())

    # 4. Identity & Profile Embed
    embed4 = discord.Embed(
        title="👤 ⋆⋅ PROFILE & IDENTITY ⋅⋆",
        description=(
            "Choose your pronouns and server badges:\n\n"
            "♂️ **He / Him**\n"
            "♀️ **She / Her**\n"
            "🌈 **They / Them**\n"
            "🔞 **18+ Verified** • Mature & late-night voice lounge discussions\n"
        ),
        color=0x9B59B6
    )
    embed4.set_footer(text="RAI FAM 💗 • Safe & welcoming for all members")
    await role_chan.send(embed=embed4, view=IdentityRolesView())

    print("✅ All 4 self-role panels posted successfully!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
