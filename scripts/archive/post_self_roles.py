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

    # Roles channel ID
    ROLE_CHAN_ID = 1545502722739150898
    role_chan = guild.get_channel(ROLE_CHAN_ID)

    if not role_chan:
        print("Self-roles channel not found")
        await client.close()
        return

    print(f"Purging old messages in #{role_chan.name}...")
    try:
        await role_chan.purge(limit=25)
    except Exception as e:
        print(f"Could not purge: {e}")

    DIVIDER = "<a:w_welc1:1547271923891707915><:w_dash:1547271874981920868><:w_dash:1547271874981920868><:w_dash:1547271874981920868><:w_dash:1547271874981920868><a:w_welc2:1547271930699190424>"

    # 1. Color Roles Embed
    embed1 = discord.Embed(
        title="<a:sparkle_love:1547271978883350568> ✦ RAI FAM • NAME COLOR PALETTE ✦ <a:sparkle_love:1547271978883350568>",
        description=(
            f"{DIVIDER}\n\n"
            "Customize your username color across all chat & voice channels!\n"
            "Click any button below to equip your color (clicking again removes it):\n\n"
            "🌸 **Sakura Pink** • Soft pastel cherry blossom\n"
            "💜 **Neon Violet** • Royal futuristic purple\n"
            "🩵 **Cyber Cyan** • Glowing neon turquoise\n"
            "💛 **Royal Gold** • Radiant emperor golden glow\n\n"
            f"{DIVIDER}"
        ),
        color=0xFF2A85
    )
    embed1.set_footer(text="RAI FAM 💗 • Select one color at a time")
    await role_chan.send(embed=embed1, view=ColorRolesView())

    # 2. Gaming Roles Embed
    embed2 = discord.Embed(
        title="<a:pinkflame:1547271954841731193> ✦ RAI FAM • GAMING SQUAD ROLES ✦ <a:pinkflame:1547271954841731193>",
        description=(
            f"{DIVIDER}\n\n"
            "Pick the games you play to unlock squad pings and party rooms!\n\n"
            "🔥 **Free Fire** • Squad matches, room customs & rank push\n"
            "⚡ **BGMI / PUBG** • Classic, TDM & custom matches\n"
            "🧸 **Roblox** • Chill hangouts & party games\n"
            "💻 **PC Gaming** • Steam, Valorant, GTA RP & multiplayer\n\n"
            f"{DIVIDER}"
        ),
        color=0x3498DB
    )
    embed2.set_footer(text="RAI FAM 💗 • Click to toggle roles on or off")
    await role_chan.send(embed=embed2, view=GamingRolesView())

    # 3. Notification Roles Embed
    embed3 = discord.Embed(
        title="<a:pixel_heart:1547271960336146563> ✦ SERVER NOTIFICATIONS & PINGS ✦ <a:pixel_heart:1547271960336146563>",
        description=(
            f"{DIVIDER}\n\n"
            "Stay in the loop without annoying @everyone pings! Toggle what you want:\n\n"
            "📢 **Announcements** • Major server news & feature releases\n"
            "🎁 **Giveaways** • Nitro, gift cards & community drops\n"
            "🏆 **Tournaments** • Gaming customs & esports showdowns\n"
            "🍿 **Movie & Anime** • Weekend watch parties & midnight streams\n\n"
            f"{DIVIDER}"
        ),
        color=0x2ECC71
    )
    embed3.set_footer(text="RAI FAM 💗 • No unnecessary spam pings")
    await role_chan.send(embed=embed3, view=NotificationRolesView())

    # 4. Identity & Profile Embed
    embed4 = discord.Embed(
        title="<a:heart_fire:1547271965729882322> ✦ PROFILE & IDENTITY ✦ <a:heart_fire:1547271965729882322>",
        description=(
            f"{DIVIDER}\n\n"
            "Choose your identity roles and community badges:\n\n"
            "♂️ **He / Him**\n"
            "♀️ **She / Her**\n"
            "🔞 **18+ Adult** • Unlocks mature & late-night voice lounges\n"
            "🌱 **Under 18** • Safe hangout badge\n\n"
            f"{DIVIDER}"
        ),
        color=0x9B59B6
    )
    embed4.set_footer(text="RAI FAM 💗 • Safe & welcoming for all members")
    await role_chan.send(embed=embed4, view=IdentityRolesView())

    print("✅ All 4 aesthetic self-role panels posted successfully!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
