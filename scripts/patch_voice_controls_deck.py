import asyncio
import os
import aiohttp
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = "1552359010513195099"
MESSAGE_ID = "1552359072203018282"

async def patch():
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }

    embed = {
        "title": "🎛️ ┊ ᯓ ⋆ VOICE SUITE CONTROLLER ⋆ ᯓ",
        "description": (
            "✦ ───────────────────────────────────── ✦\n\n"
            "### ⚡ **Manage Your Private Voice Suite in 1-Click**\n\n"
            "Join **`➕・Join to Create VC`** to spawn your personal squad room, then use the buttons below:\n\n"
            "• **🔒 Lock / 🔓 Unlock:** Control who can connect to your room\n"
            "• **🏷️ Rename / 👥 Limit:** Customize suite name and member slots\n"
            "• **👻 Hide / 👁️ Unhide:** Toggle stealth ghost mode\n"
            "• **✉️ Permit / 🚫 Revoke:** Grant or strip access for specific friends\n"
            "• **🎚️ Bitrate / 🌐 Region:** Switch between 32k-128k audio & RTC server regions\n"
            "• **🔇 Soundboard:** Toggle soundboard permissions on/off\n"
            "• **🎵 Summon DJ:** Pull RAI VIBES directly into your voice room\n"
            "• **🎮 Presets:** Instant squad sizes (Solo, Duo, Trio, Squad, 5-Man, Open)\n"
            "• **👢 Kick / 👑 Transfer:** Manage occupants & pass room host\n\n"
            "✦ ───────────────────────────────────── ✦\n"
            "🟢 **Active Suites:** `0`  •  👥 **Members in Voice:** `0`\n"
            "*Your custom room auto-deletes when everyone leaves.*"
        ),
        "color": 0xFF758C,
        "footer": {
            "text": "🟢 Active Suites: 0 • 👥 In Voice: 0 • 🛡️ Protected by Sentinel"
        }
    }

    components = [
        # Row 0: Access & Core Settings
        {
            "type": 1,
            "components": [
                {"type": 2, "style": 4, "label": "Lock", "emoji": {"name": "🔒"}, "custom_id": "vc_lock"},
                {"type": 2, "style": 3, "label": "Unlock", "emoji": {"name": "🔓"}, "custom_id": "vc_unlock"},
                {"type": 2, "style": 1, "label": "Rename", "emoji": {"name": "🏷️"}, "custom_id": "vc_rename"},
                {"type": 2, "style": 2, "label": "Limit", "emoji": {"name": "👥"}, "custom_id": "vc_limit"},
            ]
        },
        # Row 1: Privacy & Visibility
        {
            "type": 1,
            "components": [
                {"type": 2, "style": 2, "label": "Hide", "emoji": {"name": "👻"}, "custom_id": "vc_ghost"},
                {"type": 2, "style": 3, "label": "Unhide", "emoji": {"name": "👁️"}, "custom_id": "vc_unhide"},
                {"type": 2, "style": 1, "label": "Permit", "emoji": {"name": "✉️"}, "custom_id": "vc_permit"},
                {"type": 2, "style": 4, "label": "Revoke", "emoji": {"name": "🚫"}, "custom_id": "vc_revoke"},
            ]
        },
        # Row 2: Audio & Room Tuning
        {
            "type": 1,
            "components": [
                {"type": 2, "style": 2, "label": "Bitrate", "emoji": {"name": "🎚️"}, "custom_id": "vc_bitrate"},
                {"type": 2, "style": 2, "label": "Region", "emoji": {"name": "🌐"}, "custom_id": "vc_region"},
                {"type": 2, "style": 2, "label": "Soundboard", "emoji": {"name": "🔇"}, "custom_id": "vc_soundboard"},
                {"type": 2, "style": 1, "label": "Summon DJ", "emoji": {"name": "🎵"}, "custom_id": "vc_summon"},
            ]
        },
        # Row 3: Party & Room Management
        {
            "type": 1,
            "components": [
                {"type": 2, "style": 1, "label": "Presets", "emoji": {"name": "🎮"}, "custom_id": "vc_presets"},
                {"type": 2, "style": 4, "label": "Kick Member", "emoji": {"name": "👢"}, "custom_id": "vc_kick"},
                {"type": 2, "style": 1, "label": "Transfer Host", "emoji": {"name": "👑"}, "custom_id": "vc_transfer"},
                {"type": 2, "style": 2, "label": "Status", "emoji": {"name": "💬"}, "custom_id": "vc_status"},
            ]
        }
    ]

    url = f"https://discord.com/api/v10/channels/{CHANNEL_ID}/messages/{MESSAGE_ID}"
    payload = {
        "embeds": [embed],
        "components": components
    }

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, json=payload) as resp:
            data = await resp.json()
            if resp.status == 200:
                print("Successfully patched voice control message with 4x4 suite deck!")
            else:
                print(f"Failed to patch: {resp.status} - {data}")

if __name__ == "__main__":
    asyncio.run(patch())
