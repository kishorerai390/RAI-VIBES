import os
import sys
import asyncio
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')


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


import requests
import json
from utils.canvas import generate_channel_header

def deploy_headers_rest():
    print(f"Deploying studio channel headers via Discord REST API...")
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "User-Agent": "DiscordBot (https://github.com, 1.0)"
    }

    # Fetch guild channels via REST
    res = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=headers, timeout=10)
    if res.status_code != 200:
        print(f"[Error] Failed to fetch channels via REST API: {res.status_code} {res.text}")
        return

    all_channels = res.json()

    headers_config = [
        {
            "channel_names": ["🧭・ꜱᴇʀᴠᴇʀ-ɢᴜɪᴅᴇ", "server-guide", "guide"],
            "title": "SERVER COMPASS & GUIDE",
            "subtitle": "Your Master Navigation Hub • Welcome to RAI VIBES 💗",
            "icon": "🧭",
            "accent": (255, 0, 128),
            "embed_desc": "Welcome to **RAI VIBES**! Explore all interactive features, roles, and music lounges below."
        },
        {
            "channel_names": ["💬・ɢᴇɴᴇʀᴀʟ-ᴄʜᴀᴛ", "general-chat", "general"],
            "title": "COMMUNITY LOUNGE",
            "subtitle": "Active Hangout • Virtual Pets • Text & Voice XP",
            "icon": "💬",
            "accent": (0, 240, 255),
            "embed_desc": "The main social heartbeat of RAI VIBES. Chat, earn XP, show off pets, and vibe!"
        },
        {
            "channel_names": ["🎮・ɢᴀᴍɪɴɢ-ʜᴜʙ", "gaming-hub", "gaming"],
            "title": "ESPORTS & GAMING HUB",
            "subtitle": "Squad Matchmaking • Tournament Brackets • Mini-Games",
            "icon": "🎮",
            "accent": (255, 215, 0),
            "embed_desc": "Queue for squads (`/lfg`), split teams (`/teams`), or generate tournament brackets (`/bracket`)."
        },
        {
            "channel_names": ["🎵・ꜱᴏɴɢ-ʀᴇǫᴜᴇꜱᴛꜱ", "song-requests", "music"],
            "title": "AUDIO & MUSIC STUDIO",
            "subtitle": "Zero-Prefix Requests • Lossless 384kbps • Live Equalizer",
            "icon": "🎵",
            "accent": (155, 89, 182),
            "embed_desc": "Drop any song link or title here to play instantly. Control playback with interactive buttons below."
        },
        {
            "channel_names": ["🚨・ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ", "sentinel-logs", "security-logs"],
            "title": "SENTINEL SECURITY SHIELD",
            "subtitle": "Automated Threat Defense • Anti-Nuke • Audit Radar",
            "icon": "🚨",
            "accent": (255, 75, 75),
            "embed_desc": "Real-time audit log of anti-raid, phishing shields, and automated moderator enforcements."
        }
    ]

    for cfg in headers_config:
        target_chan = None
        for name in cfg["channel_names"]:
            for ch in all_channels:
                if ch.get("name") == name:
                    target_chan = ch
                    break
            if target_chan:
                break

        if not target_chan:
            print(f"[-] Channel for {cfg['title']} not found, skipping.")
            continue

        cid = target_chan["id"]
        cname = target_chan["name"]
        print(f"[+] Generating 1920x450 studio banner for #{cname} ({cid})...")
        buf = generate_channel_header(cfg["title"], cfg["subtitle"], cfg["icon"], cfg["accent"])
        hex_color = (cfg["accent"][0] << 16) + (cfg["accent"][1] << 8) + cfg["accent"][2]

        payload_json = {
            "embeds": [
                {
                    "title": f"{cfg['icon']} {cfg['title']}",
                    "description": cfg["embed_desc"],
                    "color": hex_color,
                    "image": {
                        "url": "attachment://header.png"
                    },
                    "footer": {
                        "text": "RAI VIBES 💗 • Studio Channel Identity",
                        "icon_url": config.RAI_ICON_URL
                    }
                }
            ],
            "attachments": [
                {
                    "id": 0,
                    "filename": "header.png"
                }
            ]
        }

        files = {
            "files[0]": ("header.png", buf.getvalue(), "image/png")
        }
        data = {
            "payload_json": json.dumps(payload_json)
        }

        try:
            post_res = requests.post(f"https://discord.com/api/v10/channels/{cid}/messages", headers=headers, data=data, files=files, timeout=15)
            if post_res.status_code in [200, 201]:
                msg_id = post_res.json().get("id")
                print(f" [Success] Deployed header in #{cname} (Msg ID: {msg_id})")
            else:
                print(f" [Error] HTTP {post_res.status_code} deploying to #{cname}: {post_res.text}")
        except Exception as e:
            print(f" [Error] Could not post header to #{cname}: {e}")

def print_help():
    print("""
Setup Wizard CLI Tool
Usage:
  python tools/setup_wizard.py [command]

Commands:
  guide    - Deploy or refresh the Master Server Guide interactive embed
  headers  - Generate & deploy luxury 1920x450 studio channel header banners
""")


async def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "guide"
    if cmd not in ["guide", "headers"]:
        print_help()
        return

    if cmd == "headers":
        deploy_headers_rest()
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
    elif len(sys.argv) > 1 and sys.argv[1] == "headers":
        deploy_headers_rest()
    else:
        asyncio.run(main())


