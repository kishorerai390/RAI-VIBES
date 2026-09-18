import sys
import os
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import requests
import config

headers = {
    "Authorization": f"Bot {config.DISCORD_TOKEN}",
    "Content-Type": "application/json"
}

channel_id = "1545502718792175646"

announcement_embed = {
    "title": "⚡ ⋆⋅ RAI FAM • ASCENDED COMMUNITY REVOLUTION ⋅⋆ ⚡",
    "description": (
        "✦ ───────────────────────────── ✦\n\n"
        "Welcome to the **New Era of RAI FAM 💗**!\n\n"
        "We have overhauled the entire server architecture to deliver an elite, lag-free sanctuary for music lovers, competitive gamers, and our community family.\n\n"
        "### 🌟 What's New & Upgraded:\n"
        "> • 🤖 **Dual Divine Bots**: Powered by **`RAI VIBES 💗`** *(High-Fidelity Audio & Leveling)* and **`Sentinel 🛡️`** *(24/7 Security & Fast Tickets)*.\n"
        "> • 📊 **Everglow-Style Profiles**: Type `/serverinfo` to view live guild stats, and `/userinfo` to inspect user badges, avatars, and banners!\n"
        "> • 🎯 **Competitive Squad Caps**: BGMI & Free Fire squad rooms are locked to **4 players**, giving your team uninterrupted comms.\n"
        "> • 🎧 **Studio Audio Engine**: All voice channels boosted to **96kbps ultra bitrate** for crisp sound.\n"
        "> • 📻 **Permanent 24/7 Lo-Fi**: Non-stop chill stream in `Lo-Fi Chill 24/7`.\n\n"
        "### 🧭 Quick Access:\n"
        "> • <#1545502700840427702> — Click button to get verified\n"
        "> • <#1545502722739150898> — Pick name colors & gaming pings\n"
        "> • <#1545502710101704714> — Server rules & community codex\n\n"
        "✦ ───────────────────────────── ✦\n"
        "✨ *Thank you for being part of the journey. Hop in VC, queue your favorite tracks, and enjoy the vibe!* 🌸"
    ),
    "color": 16758968,
    "footer": {
        "text": "RAI FAM 💗 • Community Overhaul",
        "icon_url": "https://cdn.discordapp.com/icons/1457382179981099090/be8713ee7410caf956268821a50c4c07.png?size=1024"
    }
}

for mid in ["1549119243218329681", "1549107410403070135"]:
    res = requests.patch(
        f"https://discord.com/api/v10/channels/{channel_id}/messages/{mid}",
        headers=headers,
        json={"embeds": [announcement_embed]}
    )
    print(f"Patched announcement {mid}:", res.status_code)
