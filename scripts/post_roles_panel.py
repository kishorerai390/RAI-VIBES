import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090
ROLES_CHANNEL_ID = 1545502722739150898

from utils.persistent_views import GamingRolesView, NotificationRolesView

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    channel = guild.get_channel(ROLES_CHANNEL_ID)
    if not channel:
        print("Roles channel not found")
        await client.close()
        return

    print("Purging previous bot messages in #roles...")
    async for m in channel.history(limit=20):
        if m.author == client.user:
            try:
                await m.delete()
                await asyncio.sleep(0.3)
            except Exception:
                pass

    print("Posting refreshed roles embeds with interactive persistent buttons...")

    # Embed 1: Header / Codex
    header_embed = discord.Embed(
        title="🏷️ ✦ RAI FAM • ROLE SELECTION & CODEX ✦ 🏷️",
        description=(
            "Welcome to the **Role Station**! Personalize your profile and select which pings & gaming alerts you wish to receive.\n\n"
            "✨ *Click any button below to toggle a role on or off. All changes apply immediately!*"
        ),
        color=0xF1C40F
    )
    header_embed.set_thumbnail(url="https://cdn.discordapp.com/avatars/1546239150775078922/a_296e933a181d5342f239885193c8c2a1.gif?size=1024")
    await channel.send(embed=header_embed)
    await asyncio.sleep(0.5)

    # Embed 2: Gaming Squads
    gaming_embed = discord.Embed(
        title="🎮 ✦ GAMING SQUAD ROLES ✦ 🎮",
        description=(
            "Select your favorite games to receive squad pings, find teammates in `/lfg`, and access custom scrim arenas!\n\n"
            "🎯 **Valorant / CS2** • Tactical FPS Squads\n"
            "⚡ **BGMI / PUBG** • Battle Royale Squads\n"
            "🔥 **Free Fire** • Fast-Paced Action\n"
            "🏎️ **GTA RP** • Los Santos Roleplay & Heists\n"
            "🚀 **Rocket League** • Aerials & Competitive 2v2/3v3"
        ),
        color=0xFA4454
    )
    await channel.send(embed=gaming_embed, view=GamingRolesView())
    await asyncio.sleep(0.5)

    # Embed 3: Notification Pings
    notif_embed = discord.Embed(
        title="🔔 ✦ COMMUNITY NOTIFICATION PINGS ✦ 🔔",
        description=(
            "Never miss an event! Toggle specific notifications for activities you care about:\n\n"
            "📢 **Announcements** • Server updates, major news, and features\n"
            "🎁 **Giveaways** • Nitro, gift cards & coin prize pools\n"
            "🏆 **Tournaments** • Competitive bracket launches & registration\n"
            "🍿 **Movie Nights** • Cinema streams & watch-along sessions\n"
            "📻 **Live DJ / Radio** • 24/7 radio sessions & DJ takeovers"
        ),
        color=0xA55EEA
    )
    await channel.send(embed=notif_embed, view=NotificationRolesView())
    await asyncio.sleep(0.5)

    print("✅ #roles channel successfully updated!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
