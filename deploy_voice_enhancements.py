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

EVERYONE_ID = "1457382179981099090"

def main():
    # 1. Fetch guild info and channels
    g_res = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}?with_counts=true", headers=HEADERS)
    guild_data = g_res.json()
    approx_members = guild_data.get("approximate_member_count", len(guild_data.get("members", [])) or 1)
    premium_tier = guild_data.get("premium_tier", 0)
    boosts = guild_data.get("premium_subscription_count", 0)

    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    channels = r.json()

    # 2. Boost bitrate on all voice channels to 96,000 (Max crystal-clear quality)
    print("Boosting bitrate on all voice channels...")
    for c in channels:
        if c["type"] == 2: # Voice channel
            res = requests.patch(
                f"https://discord.com/api/v10/channels/{c['id']}",
                headers=HEADERS,
                json={"bitrate": 96000}
            )
            if res.status_code == 200:
                print(f"🎙️ Set bitrate to 96kbps: {c['name']}")

    # 3. Create or Update Top Stats Category: 📊 | 𝙎𝙀𝙍𝙑𝙀𝙍 𝙎𝙏𝘼𝙏𝙎
    stats_cat = next((c for c in channels if c["type"] == 4 and "STATS" in c["name"].upper()), None)
    stats_overwrites = [
        {
            "id": EVERYONE_ID,
            "type": 0,
            "allow": str(1024), # View Channel
            "deny": str(1048576) # Connect = False (Locked display)
        }
    ]

    if not stats_cat:
        res = requests.post(
            f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
            headers=HEADERS,
            json={
                "name": "📊 | 𝙎𝙀𝙍𝙑𝙀𝙍 𝙎𝙏𝘼𝙏𝙎",
                "type": 4,
                "position": 0,
                "permission_overwrites": stats_overwrites
            }
        )
        stats_cat = res.json()
        print(f"✅ Created stats category: {stats_cat['name']}")

    # Stats channels
    stats_channels = [
        {"name": f"👥・Members: {approx_members}", "type": 2},
        {"name": "🎙️・In Voice: 0 Active", "type": 2},
        {"name": f"💎・Boosts: {boosts} (Lvl {premium_tier})", "type": 2}
    ]

    for sch in stats_channels:
        exists = next((c for c in channels if c.get("parent_id") == stats_cat["id"] and sch["name"][:3] in c["name"][:3]), None)
        if not exists:
            requests.post(
                f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
                headers=HEADERS,
                json={
                    "name": sch["name"],
                    "type": 2,
                    "parent_id": stats_cat["id"],
                    "permission_overwrites": stats_overwrites
                }
            )
            print(f"✅ Created counter: {sch['name']}")

    print("Voice enhancements deployed successfully!")

if __name__ == "__main__":
    main()
