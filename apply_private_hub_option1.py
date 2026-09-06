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

UPDATES = [
    {"id": "1545502790888198215", "name": "➕ ╎ Join to Create VC", "position": 0},
    {"id": "1545798274265649204", "name": "🔒 ╎ Private Sanctum", "position": 1},
    {"id": "1545502804280352871", "name": "🥂 ╎ Duo Chamber", "position": 2},
    {"id": "1545798279676301346", "name": "✨ ╎ Trio Suite", "position": 3},
    {"id": "1545502799402369034", "name": "👑 ╎ Squad Lounge", "position": 4},
    {"id": "1545798287552942150", "name": "💎 ╎ Party Room", "position": 5},
    {"id": "1545798291076161688", "name": "🌸 ╎ Syndicate Room", "position": 6},
]

def apply_names():
    print("🚀 Updating Private Hub voice channels to Luxury Suite Names...")
    for item in UPDATES:
        ch_id = item["id"]
        payload = {"name": item["name"], "position": item["position"]}
        url = f"https://discord.com/api/v10/channels/{ch_id}"
        r = requests.patch(url, headers=HEADERS, json=payload)
        if r.status_code == 200:
            print(f"  ✅ Updated: {item['name']}")
        elif r.status_code == 429:
            wait = r.json().get("retry_after", 1.0)
            print(f"  ⏳ Rate limit, waiting {wait}s...")
            time.sleep(wait)
            requests.patch(url, headers=HEADERS, json=payload)
            print(f"  ✅ Updated after retry: {item['name']}")
        else:
            print(f"  ⚠️ Error on {ch_id}: {r.status_code} {r.text}")
        time.sleep(0.4)

    print("\n🎉 Luxury Suite Aesthetic successfully applied!")

if __name__ == "__main__":
    apply_names()
