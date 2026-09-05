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

# Thematic Emoji Mapping for Text Channels
CHANNEL_THEMATIC_MAP = {
    "1545502700840427702": "✅・verify-here",
    "1545502710101704714": "📜・rules",
    "1545502718792175646": "📢・announcements",
    "1545502722739150898": "⭐・self-roles",
    "1545502705643167876": "👋・welcome",
    "1545502730699808768": "💬・general-chat",
    "1545502734663286856": "📸・media",
    "1545772984134799490": "💡・suggestions",
    "1545775433859989614": "🌸・qotd",
    "1545775440516612168": "🔢・counting",
    "1545775448053522552": "🏆・hall-of-fame",
    "1545502738362671255": "🤖・bot-commands",
    "1545534637122527332": "🎵・song-requests",
    "1545518535827263519": "🔒・executive-chat",
    "1545502845208629328": "🛡️・staff-chat",
    "1545502850057244762": "📋・mod-logs",
    "1545514505520545886": "🎫・ticket-support",
}

def update_channel(cid, name):
    r = requests.patch(
        f"https://discord.com/api/v10/channels/{cid}",
        headers=HEADERS,
        json={"name": name}
    )
    return r.status_code == 200

def try_set_announcement_type(cid):
    r = requests.patch(
        f"https://discord.com/api/v10/channels/{cid}",
        headers=HEADERS,
        json={"type": 5}
    )
    if r.status_code == 200:
        print("  📢 Successfully converted #announcements to Discord Announcement Channel type!")

def main():
    print("🎨 Applying Thematic Icon Style to All Channels...")
    
    # Try announcement type
    try_set_announcement_type("1545502718792175646")
    
    for cid, name in CHANNEL_THEMATIC_MAP.items():
        ok = update_channel(cid, name)
        print(f"  [{cid}] -> '{name}': {ok}")
        time.sleep(0.4)

    print("\n🎉 Thematic Channel Icons Successfully Applied!")

if __name__ == "__main__":
    main()
