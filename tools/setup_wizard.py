import os
import sys
import asyncio
import discord
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

import config
from utils.persistent_views import (
    ColorRolesView,
    GamingRolesView,
    NotificationRolesView,
    IdentityRolesView,
    ServerGuideView
)

TOKEN = config.DISCORD_TOKEN
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 1457382179981099090))


async def deploy_guide(client: discord.Client):
    try:
        chan = await client.fetch_channel(1546125872661012611)
    except Exception as e:
        print(f"[Error] Could not fetch guide channel: {e}")
        return

    embed = discord.Embed(
        title="🧭 RAI VIBES • THE ULTIMATE SERVER COMPASS",
        description=(
            "Welcome to **RAI VIBES** — The Cyber-Pink Premier Audio, Gaming & Social Sanctuary.\n\n"
            "Select any category below to reveal in-depth interactive instructions, voice commands, and server features.\n\n"
            "📌 **Quick Landmarks:**\n"
            "• `#✨・ᴠᴇʀɪꜰʏ-ʜᴇʀᴇ` — 1-Click Verification Gate\n"
            "• `#🎀・ᴘɪᴄᴋ-ʀᴏʟᴇꜱ` — Aesthetic Self-Roles & Identity\n"
            "• `#💬・ɢᴇɴᴇʀᴀʟ-ᴄʜᴀᴛ` — Active Lounge & Virtual Pets\n"
            "• `#🎮・ɢᴀᴍɪɴɢ-ʜᴜʙ` — Casino Games, Slots & Music Quiz\n"
            "• `#🎵・ꜱᴏɴɢ-ʀᴇǫᴜᴇꜱᴛꜱ` — Zero-Prefix High-Fidelity Music Engine\n"
            "• `#🍿・ᴍᴏᴠɪᴇ-ɴɪɢʜᴛꜱ` — Community Watch-Parties & RSVPs\n"
            "• `#📸・ᴍᴇᴅɪᴀ-ɢᴀʟʟᴇʀʏ` — Media Highlights & Aesthetic Quote Cards\n"
            "• `#🛒・ꜱᴇʀᴠᴇʀ-ꜱʜᴏᴘ` — Redeem Exclusive Perks & Badges\n"
            "• `#💡・ꜱᴜɢɢᴇꜱᴛɪᴏɴꜱ` — Interactive Community Ideas Hub"
        ),
        color=0xFF69B4
    )
    embed.set_thumbnail(url=config.RAI_ICON_URL)
    embed.set_footer(text="RAI VIBES 💗 • Select a guide section below for full details", icon_url=config.RAI_ICON_URL)

    # Fetch and edit existing guide message directly
    try:
        msg = await chan.fetch_message(1549799717183946906)
        await msg.edit(embed=embed, view=ServerGuideView())
        print(f"[Success] Updated Server Guide message ({msg.id}) with all 9 interactive options!")
    except Exception:
        new_msg = await chan.send(embed=embed, view=ServerGuideView())
        print(f"[Success] Deployed new guide embed ({new_msg.id}) in #{chan.name}!")


def print_help():
    print("""
Setup Wizard CLI Tool
Usage:
  python tools/setup_wizard.py [command]

Commands:
  guide    - Deploy or refresh the Master Server Guide interactive embed
""")


async def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "guide"
    if cmd not in ["guide"]:
        print_help()
        return

    intents = discord.Intents.default()
    intents.guilds = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        if cmd == "guide":
            await deploy_guide(client)
        await client.close()

    await client.start(TOKEN)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print_help()
    else:
        asyncio.run(main())
