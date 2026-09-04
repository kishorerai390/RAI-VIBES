import os
import sys
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

# Mapping of text channel names to aesthetic emoji styles
CHANNEL_NAME_MAPPING = {
    "verify-here": "✅・verify-here",
    "welcome": "👋・welcome",
    "rules": "📜・rules",
    "announcements": "📢・announcements",
    "self-roles": "⭐・self-roles",
    "general-chat": "💬・general-chat",
    "media": "📸・media",
    "bot-commands": "🤖・bot-commands",
    "suggestions": "💡・suggestions",
    "movie-schedule": "📅・movie-schedule",
    "movie-chat": "🍿・movie-chat",
    "music-commands": "🎵・music-commands",
    "lofi-chat": "☕・lofi-chat",
    "staff-chat": "🛡️・staff-chat",
    "mod-logs": "📋・mod-logs",
    "ticket-support": "📩・ticket-support"
}

def main():
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    channels = r.json()
    
    for c in channels:
        old_name = c["name"]
        if old_name in CHANNEL_NAME_MAPPING:
            new_name = CHANNEL_NAME_MAPPING[old_name]
            res = requests.patch(
                f"https://discord.com/api/v10/channels/{c['id']}",
                headers=HEADERS,
                json={"name": new_name}
            )
            if res.status_code == 200:
                print(f"Renamed: #{old_name} -> #{new_name}")
            else:
                print(f"Failed to rename #{old_name}: {res.status_code} {res.text}")

if __name__ == "__main__":
    main()
