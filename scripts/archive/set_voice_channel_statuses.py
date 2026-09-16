import os
import sys
import time
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

VOICE_STATUSES = {
    "1545781986193309789": "🎵 24/7 Lo-Fi Chill Beats",
    "1546607696885841990": "🎯 Esports Ranked Push [4/4]",
    "1545502823699980408": "🔥 Tournament Squad Battles",
    "1545502832822591539": "🧱 Chill Gaming & Hangout",
    "1545502794868457574": "🕹️ Multiplayer Co-Op Gaming",
    "1545502782268772453": "🎧 Studio Sound Lounge",
    "1545518701414195281": "🎤 Live Singing & Open Mic",
    "1545803549559099502": "☕ Relaxed Community Hangout",
    "1545518528126394400": "🌸 Family Voice Lounge",
    "1545518531192553603": "💎 VIP Elite Voice Suite",
    "1545834935678537738": "🚀 Nitro Boosters Only",
    "1545502790888198215": "➕ Join to Auto-Spawn VC",
    "1546615478452093089": "🔒 Join to Spawn Ghost VC",
    "1545518533566271539": "👑 High Command Governance",
    "1545803607742349373": "💼 Owner Private Office"
}

def main():
    print("==================================================================")
    print("      📻 SETTING DYNAMIC VOICE CHANNEL STATUS BANNERS 📻          ")
    print("==================================================================")

    for cid, status_text in VOICE_STATUSES.items():
        url = f"https://discord.com/api/v10/channels/{cid}/voice-status"
        res = requests.put(url, headers=HEADERS, json={"status": status_text})
        if res.status_code in (200, 204):
            print(f"✅ Voice Status Set [ID: {cid}] ➔ '{status_text}'")
        elif res.status_code == 429:
            retry_after = res.json().get("retry_after", 1.0)
            time.sleep(retry_after + 0.2)
            requests.put(url, headers=HEADERS, json={"status": status_text})
            print(f"✅ (After wait) Voice Status Set [ID: {cid}] ➔ '{status_text}'")
        else:
            print(f"⚠️ Status response for {cid}: {res.status_code} {res.text}")
        time.sleep(0.4)

    print("\n==================================================================")
    print("     🎉 ALL VOICE CHANNEL STATUS BANNERS ACTIVATED!               ")
    print("==================================================================")

if __name__ == "__main__":
    main()
