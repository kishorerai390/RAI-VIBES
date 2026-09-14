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

CATEGORY_NAMES = {
    "1546059369085534229": "╭── 📊 ＳＥＲＶＥＲ  ＳＴＡＴＳ ──╮",
    "1545803464712650844": "╭── ✦ ＩＮＦＯＲＭＡＴＩＯＮ ──╮",
    "1545803478490812578": "╭── 💬 ＴＨＥ  ＬＯＵＮＧＥ ──╮",
    "1545803473528815807": "╭── 🎵 ＶＩＢＥ  ＳＴＵＤＩＯ ──╮",
    "1545803471289057300": "╭── 🎮 ＧＡＭＩＮＧ  ＺＯＮＥ ──╮",
    "1545803469196230686": "╭── ✨ ＦＵＮ  ＺＯＮＥ ──╮",
    "1545803467145224274": "╭── 🥂 ＰＲＩＶＡＴＥ  ＳＵＩＴＥＳ ──╮",
    "1546608477206487192": "╭── ⚜️ ＣＨＥＣＫＩＮＧ  ＺＯＮＥ ──╮",
    "1545803484241199217": "╭── 👑 ＥＸＥＣＵＴＩＶＥ  ＺＯＮＥ ──╮",
    "1545803487093456906": "╭── 🛡️ ＳＥＮＴＩＮＥＬ  ＨＱ ──╮"
}

CHANNEL_NAMES = {
    # Server Stats
    "1546099701496029194": "👥 ╎ All Members: 31",
    "1546099703630798848": "👤 ╎ Members: 17",
    "1546059375574130769": "🤖 ╎ Bots: 14",

    # Information
    "1545502718792175646": "📢・announcements",
    "1545502705643167876": "🌸・welcome",
    "1545502710101704714": "📜・rules",
    "1545502700840427702": "✨・verify-here",
    "1545502722739150898": "🎀・self-roles",
    "1546125872661012611": "🧭・server-guide",
    "1546122222329008199": "👋・goodbyes",
    "1547279073217351782": "🤝・partnerships",

    # The Lounge
    "1545502730699808768": "💬・general-chat",
    "1546097792915873842": "📸・media-gallery",
    "1545834933417672744": "💎・vip-lounge",
    "1545518528126394400": "🌸 ╎ Rai Fam Lounge",
    "1545518531192553603": "💎 ╎ VIP Voice Lounge",
    "1545834935678537738": "🚀 ╎ Booster Lounge",

    # Vibe Studio
    "1545534637122527332": "🎵・song-requests",
    "1545781986193309789": "🌧️ ╎ Lo-Fi Chill 24/7",
    "1545502782268772453": "🎧 ╎ Vibe Lounge",
    "1545518701414195281": "🎤 ╎ Karaoke Stage",

    # Gaming Zone
    "1545803554550190212": "🎮・gaming-hub",
    "1545502823699980408": "🔥 ╎ Free Fire Arena",
    "1545502832822591539": "🧱 ╎ Roblox Chill",
    "1545502794868457574": "⚡ ╎ Gaming Lounge",
    "1546607696885841990": "🎯 ╎ BGMI Squad",

    # Fun Zone
    "1545803549559099502": "☕ ╎ Open Voice Chill",
    "1545502813889499136": "💤 ╎ AFK / Sleeping",

    # Private Suites
    "1545502790888198215": "➕ ╎ Join to Create VC",
    "1546615478452093089": "🔒 ╎ Create Private VC",

    # Checking Zone
    "1546608480402542652": "🔍 ╎ Checking Area",
    "1546608486270509167": "💻 ╎ PC Check",
    "1546608492389863437": "📱 ╎ Phone Check",
    "1546608498622595163": "🍏 ╎ iOS Check",

    # Executive Zone
    "1545518535827263519": "👑・executive-chat",
    "1545518533566271539": "👑 ╎ Executive Suite",
    "1545803607742349373": "💼 ╎ Private Office",

    # Sentinel HQ
    "1545502845208629328": "🛡️・staff-hq",
    "1545502850057244762": "📋・audit-logs",
    "1545514505520545886": "🎫・ticket-support",
    "1546540192343523399": "📝・moderation-logs",
    "1546593526073135107": "🚨・sentinel-defense-logs"
}

def update_channel(cid, payload, desc):
    url = f"https://discord.com/api/v10/channels/{cid}"
    res = requests.patch(url, headers=HEADERS, json=payload)
    if res.status_code == 200:
        print(f"✅ Renamed {desc}: {payload.get('name')}")
    elif res.status_code == 429:
        retry_after = res.json().get("retry_after", 1.0)
        print(f"⏳ Rate limited on {desc}, waiting {retry_after}s...")
        time.sleep(retry_after + 0.2)
        res = requests.patch(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            print(f"✅ Renamed (after wait) {desc}: {payload.get('name')}")
        else:
            print(f"❌ Failed to rename {desc}: {res.status_code} {res.text}")
    else:
        print(f"❌ Failed {desc}: {res.status_code} {res.text}")

def main():
    print("🚀 Starting Celestial Luxury Theme Redesign...")
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    if r.status_code != 200:
        print(f"Error fetching channels: {r.status_code} {r.text}")
        return
    current_channels = {c["id"]: c for c in r.json()}

    # 1. Update Categories
    print("\n--- Updating Categories ---")
    for cat_id, new_name in CATEGORY_NAMES.items():
        if cat_id in current_channels:
            old_name = current_channels[cat_id]["name"]
            if old_name != new_name:
                update_channel(cat_id, {"name": new_name}, f"Category [{old_name}]")
                time.sleep(0.5)
            else:
                print(f"✨ Category already styled: {new_name}")

    # 2. Update Channels
    print("\n--- Updating Channels ---")
    for chan_id, new_name in CHANNEL_NAMES.items():
        if chan_id in current_channels:
            old_name = current_channels[chan_id]["name"]
            if old_name != new_name:
                update_channel(chan_id, {"name": new_name}, f"Channel [{old_name}]")
                time.sleep(0.5)
            else:
                print(f"✨ Channel already styled: {new_name}")

    # 3. Handle orphan security-logs channel if present
    orphan_logs_id = "1547294258074226758"
    if orphan_logs_id in current_channels:
        sentinel_cat_id = "1545803487093456906"
        c_obj = current_channels[orphan_logs_id]
        if c_obj.get("parent_id") != sentinel_cat_id:
            print(f"\n📦 Moving orphaned channel {c_obj['name']} into SENTINEL HQ...")
            update_channel(orphan_logs_id, {"parent_id": sentinel_cat_id, "name": "🔒・security-terminal"}, "Orphan security-logs")

    print("\n🎉 Redesign Completed Successfully!")

if __name__ == "__main__":
    main()
