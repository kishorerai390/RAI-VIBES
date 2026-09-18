import os
import sys
import json
from pathlib import Path
from typing import Dict, Any
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

REPO_DIR = Path(__file__).resolve().parent.parent
load_dotenv(REPO_DIR / ".env")

sys.path.insert(0, str(REPO_DIR))
from utils.canvas import generate_channel_header
import config

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
HEADERS_DIR = REPO_DIR / "assets" / "headers"
HEADERS_DIR.mkdir(parents=True, exist_ok=True)

DISCORD_API = "https://discord.com/api/v10"
GUILD_ID = "1457382179981099090"

CHANNEL_CONFIGS = [
    {
        "channel_id": "1545502705643167876",
        "channel_name": "🌸｜welcome",
        "file_name": "header_welcome.png",
        "title": "WELCOME TO RAI FAM",
        "subtitle": "The Ultimate Sanctuary for High-Fidelity Music, Gaming & Chill Community Vibes",
        "badge": "OFFICIAL SANCTUARY GATEWAY",
        "accent": (255, 20, 147),
        "secondary": (0, 240, 255),
        "embed_title": "🌸 Welcome to RAI FAM 💗",
        "embed_description": (
            "We are thrilled to have you here! **RAI FAM** is an elite community built around high-fidelity audio, "
            "gaming, active chill chats, and rich economy rewards.\n\n"
            "**Quick Navigation:**\n"
            "• Read the community rules in <#1545502710101704714>\n"
            "• Claim your community roles in <#1545502722739150898>\n"
            "• Join the social lounge in <#1545502730699808768>\n"
            "• Queue for squad games in <#1550187304876900543>\n"
            "• Play lossless music anytime using `/play` in any voice channel!"
        )
    },
    {
        "channel_id": "1545502710101704714",
        "channel_name": "📜｜rules-and-info",
        "file_name": "header_rules.png",
        "title": "SERVER PROTOCOLS & SAFETY",
        "subtitle": "Zero-Tolerance Conduct Standards • Mutual Respect • Sentinel AI Protected",
        "badge": "SENTINEL ENFORCEMENT CHARTER",
        "accent": (255, 215, 0),
        "secondary": (255, 50, 70),
        "embed_title": "📜 Community Code & Server Protocols",
        "embed_description": (
            "To preserve a welcoming and toxic-free environment for everyone, all members must respect the following standards:\n\n"
            "**1. Respect & Decency:** Treat every member and staff member with dignity. Harassment, hate speech, toxicity, and personal attacks result in immediate moderation action.\n"
            "**2. Strictly Safe For Work:** No NSFW, suggestive, explicit, or inappropriate content or media anywhere.\n"
            "**3. Zero Romance & Dating Content:** In accordance with server charter, dating, romance, shipping, or virtual marriage content is strictly prohibited.\n"
            "**4. No Unsolicited Promotion:** Do not advertise external Discord servers, unsolicited products, or suspicious links.\n"
            "**5. Automated Sentinel Defense:** RAI SENTINEL actively monitors for raid patterns, phishing URLs, spam floods, and token exploits 24/7."
        )
    },
    {
        "channel_id": "1550184399742697512",
        "channel_name": "💸｜owo-chat",
        "file_name": "header_owo.png",
        "title": "CYBER VAULT & CASINO",
        "subtitle": "Animated Slots • Co-op Bank Heists • Daily Treasury & Mini-Games",
        "badge": "ARCADE ECONOMY SECTOR",
        "accent": (0, 230, 120),
        "secondary": (255, 215, 0),
        "embed_title": "💸 Cyber Vault, Casino & Economy Hub",
        "embed_description": (
            "Step into the high-stakes economy district powered by **RAI PLAY**!\n\n"
            "**Available Economy Commands:**\n"
            "• `/balance` — Check your wallet and bank treasury\n"
            "• `/daily` — Claim your 24-hour reward coins\n"
            "• `/casino slots amount:[x]` — Spin the live 3D animated slot machine\n"
            "• `/heist` — Assemble a 4-player co-op squad to crack the server vault\n"
            "• `/coinflip choice:[heads/tails] amount:[x]` — Double your stakes\n"
            "• `/leaderboard` — View the top millionaires in the server"
        )
    },
    {
        "channel_id": "1550184397540556951",
        "channel_name": "🎮｜ff-chat",
        "file_name": "header_ff.png",
        "title": "FREE FIRE TACTICAL HUB",
        "subtitle": "Custom Scrims • Squad Comms • Battle Royale Strategies & Highlights",
        "badge": "ESPORTS COMBAT ARENA",
        "accent": (255, 51, 102),
        "secondary": (255, 140, 0),
        "embed_title": "🎮 Free Fire Squad Hub & Scrims",
        "embed_description": (
            "The official combat lounge for Free Fire players in RAI FAM!\n\n"
            "• Share custom room IDs, passwords, and scrimmage schedules\n"
            "• Discuss weapons, gunsmith loadouts, and map drop rotations\n"
            "• Find ranked rush squads and clash squad partners\n"
            "• Post your clutch highlight clips and tournament victories"
        )
    },
    {
        "channel_id": "1549416359723532480",
        "channel_name": "🤖｜bot-cmds",
        "file_name": "header_botcmds.png",
        "title": "NEURAL COMMAND TERMINAL",
        "subtitle": "Interact with RAI VIBES, RAI PLAY & RAI SENTINEL via Slash Commands",
        "badge": "CYBERNETIC INTERFACE",
        "accent": (0, 240, 255),
        "secondary": (255, 0, 128),
        "embed_title": "🤖 Neural Command Directory",
        "embed_description": (
            "Use slash commands (`/`) in this channel to interact with the bot cluster:\n\n"
            "🎵 **RAI VIBES 💗 (Music & Audio):**\n"
            "`/play`, `/pause`, `/skip`, `/queue`, `/nowplaying`, `/volume`, `/equalizer`, `/aidj`, `/radio`\n\n"
            "🎮 **RAI PLAY 🎮 (Arcade & Leveling):**\n"
            "`/rank`, `/profile`, `/leaderboard`, `/casino`, `/heist`, `/musicbattle`, `/trivia`, `/lfg`, `/teams`\n\n"
            "🛡️ **RAI SENTINEL 🛡️ (Security & Moderation):**\n"
            "`/verify`, `/status`, `/audit`, `/purge`, `/lock`, `/unlock`, `/slowmode`"
        )
    },
    {
        "channel_id": "1550187304876900543",
        "channel_name": "🎮｜lfg-matchmaking",
        "file_name": "header_lfg.png",
        "title": "SQUAD MATCHMAKING & LFG",
        "subtitle": "Find Duo & Squad Partners • Team Splitter • Ranked Arenas",
        "badge": "MULTI-GAME LOBBY",
        "accent": (30, 120, 255),
        "secondary": (0, 240, 255),
        "embed_title": "🎮 Looking For Group (LFG) & Squad Finder",
        "embed_description": (
            "Never play alone! Form squads and find teammates across multiple titles:\n\n"
            "• Use `/lfg game:[title] squad_size:[number] rank:[tier]` to create an open squad card\n"
            "• Click **Join Squad** on any active card to jump into the lobby\n"
            "• Use `/teams members:[names] num_teams:[2-4]` to generate balanced tournament teams\n"
            "• Move into the Voice Lounges once your squad is ready!"
        )
    },
    {
        "channel_id": "1550187321285148782",
        "channel_name": "👑｜executive-lounge",
        "file_name": "header_executive.png",
        "title": "EXECUTIVE APEX LOUNGE",
        "subtitle": "VIP Headquarters • Governance • Server Telemetry & Strategy",
        "badge": "RESTRICTED VIP APEX",
        "accent": (255, 215, 0),
        "secondary": (155, 89, 182),
        "embed_title": "👑 Executive & VIP Headquarters",
        "embed_description": (
            "Exclusive chamber reserved for Server Administrators, Staff Executives, and VIP Diamond Boosters.\n\n"
            "• High-level community governance, roadmap planning & feature launches\n"
            "• Server telemetry, cluster health status, and Sentinel security audits\n"
            "• Private executive voice discussions and event scheduling"
        )
    }
]

def render_headers():
    print("==================================================")
    print("  Generating 3D Channel Header Banners (1920x600)")
    print("==================================================")
    for cfg in CHANNEL_CONFIGS:
        out_file = HEADERS_DIR / cfg["file_name"]
        print(f"[+] Rendering 3D Header for #{cfg['channel_name']} -> {out_file.name}...")
        buf = generate_channel_header(
            title=cfg["title"],
            subtitle=cfg["subtitle"],
            accent_color=cfg["accent"],
            secondary_color=cfg["secondary"],
            badge_tag=cfg["badge"]
        )
        with open(out_file, "wb") as f:
            f.write(buf.read())
        print(f"    Saved {out_file.stat().st_size:,} bytes.")

def deploy_headers_to_discord():
    print("\n==================================================")
    print("  Deploying 3D Channel Headers to Discord API")
    print("==================================================")
    if not TOKEN:
        print("[-] ERROR: DISCORD_BOT_TOKEN not found in .env")
        return

    headers_auth = {"Authorization": f"Bot {TOKEN}"}

    for cfg in CHANNEL_CONFIGS:
        cid = cfg["channel_id"]
        cname = cfg["channel_name"]
        img_path = HEADERS_DIR / cfg["file_name"]

        print(f"\n[+] Processing #{cname} (Channel ID: {cid})...")

        # 1. Inspect recent messages to check if already deployed
        res_get = requests.get(f"{DISCORD_API}/channels/{cid}/messages?limit=10", headers=headers_auth)
        existing_msg = None
        if res_get.status_code == 200:
            msgs = res_get.json()
            for m in msgs:
                embeds = m.get("embeds", [])
                for e in embeds:
                    if "Studio 3D Channel Identity" in (e.get("footer", {}).get("text") or ""):
                        existing_msg = m
                        break
                if existing_msg:
                    break

        hex_color = (cfg["accent"][0] << 16) + (cfg["accent"][1] << 8) + cfg["accent"][2]

        payload = {
            "embeds": [
                {
                    "title": cfg["embed_title"],
                    "description": cfg["embed_description"],
                    "color": hex_color,
                    "image": {
                        "url": "attachment://header.png"
                    },
                    "footer": {
                        "text": "RAI VIBES 💗 • Studio 3D Channel Identity",
                        "icon_url": config.RAI_ICON_URL
                    }
                }
            ]
        }

        with open(img_path, "rb") as f:
            file_bytes = f.read()

        files = {
            "files[0]": ("header.png", file_bytes, "image/png"),
            "payload_json": (None, json.dumps(payload), "application/json")
        }

        if existing_msg:
            mid = existing_msg["id"]
            print(f"    Found existing studio header message ({mid}). Updating...")
            res_patch = requests.patch(
                f"{DISCORD_API}/channels/{cid}/messages/{mid}",
                headers=headers_auth,
                files=files
            )
            if res_patch.status_code in [200, 201]:
                print(f"    ✅ Successfully updated 3D header in #{cname}!")
            else:
                print(f"    [-] Update failed ({res_patch.status_code}): {res_patch.text}. Posting new message...")
                # Retry by posting new
                files_new = {
                    "files[0]": ("header.png", file_bytes, "image/png"),
                    "payload_json": (None, json.dumps(payload), "application/json")
                }
                res_post = requests.post(f"{DISCORD_API}/channels/{cid}/messages", headers=headers_auth, files=files_new)
                if res_post.status_code in [200, 201]:
                    print(f"    ✅ Successfully posted new 3D header in #{cname}!")
                else:
                    print(f"    ❌ Post failed ({res_post.status_code}): {res_post.text}")
        else:
            print(f"    No existing header found. Posting new 3D header...")
            res_post = requests.post(
                f"{DISCORD_API}/channels/{cid}/messages",
                headers=headers_auth,
                files=files
            )
            if res_post.status_code in [200, 201]:
                print(f"    ✅ Successfully posted 3D header in #{cname}!")
            else:
                print(f"    ❌ Post failed ({res_post.status_code}): {res_post.text}")

if __name__ == "__main__":
    render_headers()
    deploy_headers_to_discord()
