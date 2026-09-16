import os
import sys
import time
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
VIBES_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"

HEADERS = {
    "Authorization": f"Bot {VIBES_TOKEN}",
    "Content-Type": "application/json"
}

DIVIDER = "✦ ───────────────────────────── ✦"

def send_embed(chan_id, embed_data, clean_first=True, desc=""):
    # 1. Clean previous bot messages if requested
    if clean_first:
        try:
            r = requests.get(f"https://discord.com/api/v10/channels/{chan_id}/messages?limit=10", headers=HEADERS)
            if r.status_code == 200:
                for m in r.json():
                    requests.delete(f"https://discord.com/api/v10/channels/{chan_id}/messages/{m['id']}", headers=HEADERS)
        except Exception:
            pass

    # 2. Post new embed
    res = requests.post(f"https://discord.com/api/v10/channels/{chan_id}/messages", headers=HEADERS, json={"embeds": [embed_data]})
    if res.status_code in (200, 201):
        print(f"✅ {desc} successfully posted in channel ID {chan_id}!")
    else:
        print(f"❌ Failed to post {desc}: {res.status_code} {res.text}")

def main():
    print("==================================================================")
    print("  🚀 DEPLOYING AUTOMATED GOD-TIER COMMUNITY HUBS ACROSS SERVER 🚀 ")
    print("==================================================================")

    # 1. OFFICIAL SERVER ASCENDED ANNOUNCEMENT (#📢・announcements)
    print("\n[1/5] Posting Ascended Server Announcement...")
    ann_embed = {
        "title": "⚡ ⋆⋅ RAI FAM • ASCENDED COMMUNITY REVOLUTION ⋅⋆ ⚡",
        "description": (
            f"{DIVIDER}\n\n"
            "Welcome to the **New Era of RAI FAM 💗**!\n\n"
            "We have overhauled the entire server architecture to deliver an elite, "
            "lag-free sanctuary for music lovers, competitive gamers, and our community family.\n\n"
            "### 🌟 What's New & Upgraded:\n"
            "> • 🤖 **Dual Divine Bots**: Powered by **`AURA ✦`** *(High-Fidelity Audio & Leveling)* and **`AEGIS 🛡️`** *(24/7 Security & Fast Tickets)*.\n"
            "> • 📊 **Everglow-Style Profiles**: Type `/serverinfo` to view live guild stats, and `/userinfo` to inspect user badges, avatars, and banners!\n"
            "> • 🎯 **Competitive Squad Caps**: BGMI & Free Fire squad rooms are locked to **4 players**, giving your team uninterrupted comms.\n"
            "> • 🎧 **Studio Audio Engine**: All voice channels boosted to **96kbps ultra bitrate** for crisp sound.\n"
            "> • 📻 **Permanent 24/7 Lo-Fi**: Non-stop chill stream in `Lo-Fi Chill 24/7`.\n\n"
            "### 🧭 Quick Access:\n"
            "> • <#1545502700840427702> — Click button to get verified\n"
            "> • <#1545502722739150898> — Pick name colors & gaming pings\n"
            "> • <#1546125872661012611> — Full server map & command directory\n\n"
            f"{DIVIDER}\n"
            "✨ *Thank you for being part of the journey. Hop in VC, queue your favorite tracks, and enjoy the vibe!* 🌸"
        ),
        "color": 0x2B2D31,
        "footer": {
            "text": "RAI FAM 💗 • Powered by AURA ✦ & AEGIS 🛡️"
        }
    }
    send_embed("1545502718792175646", ann_embed, clean_first=False, desc="Ascended Announcement")
    time.sleep(1)

    # 2. ZERO-PREFIX MUSIC QUEUE HEADER (#🎵・song-requests)
    print("\n[2/5] Posting Music Control Header in #song-requests...")
    music_embed = {
        "title": "🎵 ⋆⋅ AURA ✦ • ZERO-PREFIX MUSIC PLAYER ⋅⋆ 🎵",
        "description": (
            f"{DIVIDER}\n\n"
            "**Welcome to the dedicated RAI FAM sound engine!**\n\n"
            "You don't even need to type slash commands in this channel. "
            "Simply **type any song title, artist, or YouTube/Spotify link** directly in chat, and **`AURA ✦`** will automatically queue and stream it!\n\n"
            "### 🎛️ Audio FX & Studio Filters:\n"
            "> • `/bassboost <low|med|high|extreme>` — Deep punchy sub-bass\n"
            "> • `/spatial8d` — Immersive 360-degree rotating headphone audio\n"
            "> • `/nightcore` — High tempo & pitched dance remix\n"
            "> • `/slowed` — Slowed + Reverb midnight aesthetic\n"
            "> • `/karaoke` — Vocal attenuation for live singing\n\n"
            "### 📋 Playback Controls:\n"
            "> • `/queue` — View upcoming tracklist & live player card\n"
            "> • `/skip` — Skip to the next song in line\n"
            "> • `/volume <0-100>` — Adjust playback loudness\n"
            "> • `/lyrics` — Live synced lyrics lookup\n\n"
            f"{DIVIDER}\n"
            "🎧 *Join any voice channel and start streaming your favorite tracks!*"
        ),
        "color": 0x2B2D31,
        "footer": {
            "text": "AURA ✦ • High-Fidelity 96kbps DSP Audio Engine"
        }
    }
    send_embed("1545534637122527332", music_embed, clean_first=True, desc="Music Queue Header")
    time.sleep(1)

    # 3. MEDIA GALLERY & STARBOARD SHOWCASE (#📸・media-gallery)
    print("\n[3/5] Posting Media Gallery Header in #media-gallery...")
    media_embed = {
        "title": "📸 ⋆⋅ RAI FAM • MEDIA GALLERY & HIGHLIGHTS ⋅⋆ 📸",
        "description": (
            f"{DIVIDER}\n\n"
            "This channel is dedicated to sharing your visual creativity and epic gaming moments!\n\n"
            "### 🌟 What to Share:\n"
            "> • 🎮 Clutch gaming clips (BGMI, Free Fire, Roblox, Valorant)\n"
            "> • 🎨 Digital artwork, anime edits & photography\n"
            "> • 🎭 Hilarious memes & reaction GIFs\n"
            "> • 🖥️ Desk setups & gaming battle-stations\n\n"
            "### ⭐ The Community Starboard:\n"
            "> React to any message with **⭐ (Star)**! Messages that receive **3+ stars** are automatically enshrined on our server's **Starboard Wall of Fame**!\n\n"
            f"{DIVIDER}\n"
            "✨ *Showcase your talent and drop your best clips below!*"
        ),
        "color": 0x2B2D31,
        "footer": {
            "text": "RAI FAM 💗 • Media & Highlights Hub"
        }
    }
    send_embed("1546097792915873842", media_embed, clean_first=True, desc="Media Gallery Header")
    time.sleep(1)

    # 4. VIP LOUNGE & BOOSTER PERKS (#💎・vip-lounge)
    print("\n[4/5] Posting VIP & Booster Showcase in #vip-lounge...")
    vip_embed = {
        "title": "💎 ⋆⋅ RAI FAM • VIP & NITRO BOOSTER PERKS ⋅⋆ 💎",
        "description": (
            f"{DIVIDER}\n\n"
            "Welcome to the **Exclusive VIP Sanctuary**!\n\n"
            "This channel and the companion **`💎 ╎ VIP Voice Lounge`** are reserved for our most valued supporters, "
            "Nitro Boosters, and high-rank members.\n\n"
            "### 👑 VIP & Booster Privileges:\n"
            "> • 🎨 **Custom Hex Color Role**: Stand out with a custom glowing name color\n"
            "> • 💎 **VIP Voice Lounge Access**: Studio 96kbps dedicated voice suite\n"
            "> • 🚀 **Booster Lounge**: Exclusive Nitro supporter voice chamber\n"
            "> • 🏷️ **Custom Nickname Privileges**: Freedom to change your server alias\n"
            "> • ⚡ **Double XP Boost**: Level up 2x faster in text chats\n"
            "> • 🎫 **Priority Helpdesk Support**: Fast-track ticket dispatch\n\n"
            f"{DIVIDER}\n"
            "💖 *Thank you for supporting and powering the growth of RAI FAM!*"
        ),
        "color": 0x2B2D31,
        "footer": {
            "text": "RAI FAM 💗 • VIP & Nitro Booster Sanctuary"
        }
    }
    send_embed("1545834933417672744", vip_embed, clean_first=True, desc="VIP Lounge Header")
    time.sleep(1)

    # 5. PARTNERSHIP GUIDELINES (#🤝・partnerships)
    print("\n[5/5] Posting Partnership Guidelines in #partnerships...")
    partner_embed = {
        "title": "🤝 ⋆⋅ RAI FAM • OFFICIAL PARTNERSHIP DIRECTORY ⋅⋆ 🤝",
        "description": (
            f"{DIVIDER}\n\n"
            "Interested in collaborating or forming an official alliance with **RAI FAM 💗**?\n"
            "We are always open to connecting with active, safe, and quality Discord communities!\n\n"
            "### 📋 Partnership Requirements:\n"
            "> • Must have an active, non-toxic member base (50+ members minimum)\n"
            "> • Server must strictly adhere to Discord Community Guidelines and Terms of Service\n"
            "> • Reciprocal partner announcement post on your server with an `@everyone` or `@here` ping\n"
            "> • Must provide a permanent non-expiring invite link\n\n"
            "### 📩 How to Apply:\n"
            "> 1️⃣ Open a support ticket in <#1545514505520545886>\n"
            "> 2️⃣ Provide your server invite link, advertisement message, and banner\n"
            "> 3️⃣ A staff representative will review and post your promo within 24 hours!\n\n"
            f"{DIVIDER}\n"
            "🌐 *Let's build, connect, and grow our communities together!*"
        ),
        "color": 0x2B2D31,
        "footer": {
            "text": "RAI FAM 💗 • Partnerships & Alliances"
        }
    }
    send_embed("1547279073217351782", partner_embed, clean_first=True, desc="Partnership Guidelines")

    print("\n==================================================================")
    print("   🎉 ALL COMMUNITY HUBS AUTOMATICALLY DEPLOYED & LIVE!          ")
    print("==================================================================")

if __name__ == "__main__":
    main()
