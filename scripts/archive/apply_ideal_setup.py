import os
import sys
import time
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
VIBES_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SENTINEL_TOKEN = os.getenv("SECURITY_BOT_TOKEN")
GUILD_ID = "1457382179981099090"

HEADERS = {
    "Authorization": f"Bot {VIBES_TOKEN}",
    "Content-Type": "application/json"
}

VIBES_BOT_ID = "1546239150775078922"
SENTINEL_BOT_ID = "1546245134809571470"

# Target updates for voice channels
VOICE_UPDATES = {
    # The Lounge
    "1545518528126394400": {"name": "🌸 ╎ Rai Fam Lounge", "user_limit": 0},
    "1545518531192553603": {"name": "💎 ╎ VIP Voice Lounge", "user_limit": 10},
    "1545834935678537738": {"name": "🚀 ╎ Booster Lounge", "user_limit": 0},

    # Vibe Studio
    "1545781986193309789": {"name": "🌧️ ╎ Lo-Fi Chill 24/7", "user_limit": 0},
    "1545502782268772453": {"name": "🎧 ╎ Vibe Lounge", "user_limit": 0},
    "1545518701414195281": {"name": "🎤 ╎ Karaoke Stage", "user_limit": 0},

    # Gaming Zone
    "1546607696885841990": {"name": "🎯 ╎ BGMI Squad", "user_limit": 4},
    "1545502823699980408": {"name": "🔥 ╎ Free Fire Arena", "user_limit": 4},
    "1545502832822591539": {"name": "🧱 ╎ Roblox Hangout", "user_limit": 0},
    "1545502794868457574": {"name": "🕹️ ╎ Gaming Lounge", "user_limit": 0},

    # Fun Zone
    "1545803549559099502": {"name": "☕ ╎ Open Voice", "user_limit": 0},
    "1545502813889499136": {"name": "💤 ╎ AFK / Sleeping", "user_limit": 0},

    # Private Suites
    "1545502790888198215": {"name": "➕ ╎ Join to Create VC", "user_limit": 0},
    "1546615478452093089": {"name": "🔒 ╎ Create Ghost VC", "user_limit": 0},

    # Checking Zone
    "1546608480402542652": {"name": "🔍 ╎ Checking Area", "user_limit": 0},
    "1546608486270509167": {"name": "💻 ╎ PC Check", "user_limit": 2},
    "1546608492389863437": {"name": "📱 ╎ Phone Check", "user_limit": 2},
    "1546608498622595163": {"name": "🍏 ╎ iOS Check", "user_limit": 2},

    # Executive Zone
    "1545518533566271539": {"name": "👑 ╎ Executive Suite", "user_limit": 5},
    "1545803607742349373": {"name": "💼 ╎ Private Office", "user_limit": 2}
}

# Bitrate optimization (96kbps for voice lounges)
OPTIMAL_BITRATE = 96000

def patch_channel(cid, payload, desc):
    url = f"https://discord.com/api/v10/channels/{cid}"
    res = requests.patch(url, headers=HEADERS, json=payload)
    if res.status_code == 200:
        print(f"✅ {desc} updated ➔ {payload.get('name')} [Limit: {payload.get('user_limit', 'None')}]")
    elif res.status_code == 429:
        retry_after = res.json().get("retry_after", 1.0)
        print(f"⏳ Rate limited on {desc}, waiting {retry_after}s...")
        time.sleep(retry_after + 0.3)
        res = requests.patch(url, headers=HEADERS, json=payload)
        if res.status_code == 200:
            print(f"✅ (After wait) {desc} updated ➔ {payload.get('name')}")
        else:
            print(f"❌ Failed to update {desc}: {res.status_code} {res.text}")
    else:
        print(f"❌ Failed to update {desc}: {res.status_code} {res.text}")

def patch_nickname(bot_id, nickname, token):
    headers = {"Authorization": f"Bot {token}", "Content-Type": "application/json"}
    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{bot_id}"
    res = requests.patch(url, headers=headers, json={"nick": nickname})
    if res.status_code == 200:
        print(f"👑 Updated Bot ({bot_id}) nickname to: '{nickname}'")
    else:
        # Try /users/@me/nick
        url_me = f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/@me"
        res_me = requests.patch(url_me, headers=headers, json={"nick": nickname})
        if res_me.status_code == 200:
            print(f"👑 Updated Bot (@me) nickname to: '{nickname}'")
        else:
            print(f"⚠️ Nickname update for bot {bot_id}: {res.status_code}")

def main():
    print("==================================================================")
    print("   ✨ APPLYING 'MY WISH' IDEAL SETUP TO SERVER & BOTS ✨          ")
    print("==================================================================")

    # 1. Update Bot Nicknames
    print("\n[1/3] Updating Bot Branding & Nicknames...")
    if VIBES_TOKEN:
        patch_nickname(VIBES_BOT_ID, "AURA ✦", VIBES_TOKEN)
    if SENTINEL_TOKEN:
        patch_nickname(SENTINEL_BOT_ID, "SENTINEL 🛡️", SENTINEL_TOKEN)

    # 2. Update Voice Channels with Clean Names, Bitrate & Member Limits
    print("\n[2/3] Updating Voice Channel Names & Setting Player Limits...")
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    if r.status_code != 200:
        print(f"Error reading channels: {r.status_code}")
        return
    existing = {c["id"]: c for c in r.json()}

    for cid, updates in VOICE_UPDATES.items():
        if cid in existing:
            current = existing[cid]
            payload = {}
            if current.get("name") != updates["name"]:
                payload["name"] = updates["name"]
            if current.get("user_limit") != updates["user_limit"]:
                payload["user_limit"] = updates["user_limit"]
            if current.get("bitrate") != OPTIMAL_BITRATE:
                payload["bitrate"] = OPTIMAL_BITRATE
            
            if payload:
                patch_channel(cid, payload, f"Voice Channel [{current['name']}]")
                time.sleep(0.5)
            else:
                print(f"✨ Voice channel already optimal: {updates['name']}")

    # 3. Verify Server AFK Channel Setting
    print("\n[3/3] Checking AFK Channel Binding...")
    afk_channel_id = "1545502813889499136" # 💤 ╎ AFK / Sleeping
    res = requests.patch(
        f"https://discord.com/api/v10/guilds/{GUILD_ID}",
        headers=HEADERS,
        json={"afk_channel_id": afk_channel_id, "afk_timeout": 300}
    )
    if res.status_code == 200:
        print("✅ Server AFK channel securely bound to '💤 ╎ AFK / Sleeping' (5 min timeout)!")
    else:
        print(f"AFK binding note: {res.status_code}")

    print("\n==================================================================")
    print("   🎉 'MY WISH' SETUP SUCCESSFULLY APPLIED!                     ")
    print("==================================================================")

if __name__ == "__main__":
    main()
