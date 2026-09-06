import os
import sys
import time
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"

HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

CATEGORY_RENAMES = {
    "1546059369085534229": "╭── 📊 ＳＥＲＶＥＲ  ＳＴＡＴＳ ──╮",
    "1545803464712650844": "╭── ✦ ＩＮＦＯＲＭＡＴＩＯＮ ──╮",
    "1545803467145224274": "╭── 🥂 ＰＲＩＶＡＴＥ  ＨＵＢ ──╮",
    "1545803469196230686": "╭── 🐣 ＦＵＮ  ＺＯＮＥ ──╮",
    "1545803471289057300": "╭── 🎮 ＧＡＭＩＮＧ  ＺＯＮＥ ──╮",
    "1545803473528815807": "╭── 🎵 ＶＩＢＥ  ＳＴＵＤＩＯ ──╮",
    "1545803475798204580": "╭── 🍿 ＣＩＮＥＭＡ  ＨＵＢ ──╮",
    "1545803478490812578": "╭── 💬 ＴＨＥ  ＬＯＵＮＧＥ ──╮",
    "1545803480768323614": "╭── 🔍 ＣＨＥＣＫＩＮＧ  ＺＯＮＥ ──╮",
    "1545803484241199217": "╭── 🔒 ＥＸＥＣＵＴＩＶＥ  ＺＯＮＥ ──╮",
    "1545803487093456906": "╭── 🛡️ ＳＥＮＴＩＮＥＬ  ＨＱ ──╮"
}

CHANNEL_RENAMES = {
    # Stats
    "1546099701496029194": "👥 ╎ all-members: 25",
    "1546099703630798848": "👤 ╎ humans: 16",
    "1546059375574130769": "🤖 ╎ bots: 9",
    
    # Information
    "1546125872661012611": "🧭・server-guide",
    "1545502718792175646": "📢・announcements",
    "1545502705643167876": "🌸・welcome",
    "1546122222329008199": "👋・goodbyes",
    "1545502710101704714": "📜・rules",
    "1545502700840427702": "✨・verify",
    "1545502722739150898": "🎀・self-roles",
    
    # Lounge
    "1545502730699808768": "💬・general-chat",
    "1546097792915873842": "📺・anime-hub",
    "1545834933417672744": "💎・vip-lounge",
    "1545834935678537738": "🚀 ╎ Booster Lounge",
    "1545518528126394400": "🌸 ╎ Rai Fam Lounge",
    "1545518531192553603": "💎 ╎ VIP Voice Lounge",
    
    # Music & Audio
    "1545534637122527332": "🎵・song-requests",
    "1545502782268772453": "🎧 ╎ Vibe Lounge",
    "1545518701414195281": "🎤 ╎ Karaoke Stage",
    "1545781986193309789": "🌧️ ╎ Lo-Fi Chill",
    
    # Gaming
    "1545803554550190212": "🎮・gaming-chat",
    "1545502829089787924": "⚡ ╎ BGMI Squad",
    "1545502823699980408": "⚡ ╎ Free Fire",
    "1545502832822591539": "⚡ ╎ Roblox Chill",
    "1545502794868457574": "⚡ ╎ Gaming Lounge",
    
    # Private Hub
    "1545502790888198215": "➕ ╎ Create Nexus VC",
    "1545798274265649204": "🥂 ╎ Solo [1]",
    "1545502804280352871": "🥂 ╎ Duo [2]",
    "1545798279676301346": "🥂 ╎ Trio [3]",
    "1545502799402369034": "🥂 ╎ Squad [4]",
    "1545798287552942150": "🥂 ╎ 5-Man [5]",
    "1545798291076161688": "🥂 ╎ 6-Man [6]",
    
    # Cinema
    "1545502762467328185": "🍿 ╎ Cinema Screen 1",
    "1545803585550426234": "🍿 ╎ Cinema Screen 2",
    
    # Fun
    "1545801428839170220": "🐣 ╎ Fun Time",
    "1545502813889499136": "💤 ╎ AFK Chill",
    "1545803549559099502": "🗣️ ╎ Open Voice",
    "1545803541267095675": "🗣️ ╎ Voice 1",
    "1545803544379260979": "🗣️ ╎ Voice 2",
    "1545803546958635039": "🗣️ ╎ Voice 3",
    
    # Checking Zone
    "1545803594614444122": "🔍 ╎ Checking Area",
    "1545803597315448933": "💻 ╎ PC Checking",
    "1545803600029155488": "📱 ╎ Phone Checking",
    "1545803602419781652": "🍏 ╎ iOS Checking",
    
    # Executive Zone
    "1545518535827263519": "🔒・executive-chat",
    "1545518533566271539": "🔮 ╎ Private Suite",
    "1545803607742349373": "💼 ╎ Private Office",
    
    # Sentinel HQ
    "1545502845208629328": "🛡️・staff-hq",
    "1545502850057244762": "📋・mod-logs",
    "1545514505520545886": "🎫・ticket-support"
}

def update_channels():
    print("🚀 Applying Masterpiece Aesthetic Layout to Discord Server...")
    
    # 1. Update Categories
    print("\n📁 Updating Categories...")
    for cat_id, new_name in CATEGORY_RENAMES.items():
        url = f"https://discord.com/api/v10/channels/{cat_id}"
        r = requests.patch(url, headers=HEADERS, json={"name": new_name})
        if r.status_code == 200:
            print(f"  ✅ Category updated: {new_name}")
        elif r.status_code == 429:
            retry_after = r.json().get("retry_after", 1.0)
            print(f"  ⏳ Rate limited, sleeping {retry_after}s...")
            time.sleep(retry_after)
            r = requests.patch(url, headers=HEADERS, json={"name": new_name})
            print(f"  ✅ Category updated after retry: {new_name}")
        else:
            print(f"  ⚠️ Error updating {cat_id}: {r.status_code} {r.text}")
        time.sleep(0.35)

    # 2. Update Channels
    print("\n# Updating Channels...")
    for ch_id, new_name in CHANNEL_RENAMES.items():
        url = f"https://discord.com/api/v10/channels/{ch_id}"
        r = requests.patch(url, headers=HEADERS, json={"name": new_name})
        if r.status_code == 200:
            print(f"  ✅ Channel updated: {new_name}")
        elif r.status_code == 429:
            retry_after = r.json().get("retry_after", 1.0)
            print(f"  ⏳ Rate limited, sleeping {retry_after}s...")
            time.sleep(retry_after)
            r = requests.patch(url, headers=HEADERS, json={"name": new_name})
            print(f"  ✅ Channel updated after retry: {new_name}")
        else:
            print(f"  ⚠️ Error updating {ch_id}: {r.status_code} {r.text}")
        time.sleep(0.35)

    print("\n✨ Masterpiece Aesthetic Layout completely applied!")

if __name__ == "__main__":
    update_channels()
