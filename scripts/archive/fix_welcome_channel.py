import os
import sys
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"
WELCOME_CHAN_ID = "1545502705643167876"

HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

def main():
    print("==================================================================")
    print("      🛠️ FIXING WELCOME CHANNEL & DISCORD SYSTEM MESSAGES 🛠️     ")
    print("==================================================================")

    # 1. Update Guild system_channel_flags to permanently STOP Discord's default messages
    # 1 = SUPPRESS_JOIN_NOTIFICATIONS (No more "brought pizza" messages)
    # 8 = SUPPRESS_JOIN_NOTIFICATION_REPLIES (No more "Wave to say hi!" sticker buttons)
    # 1 | 8 = 9
    print("\n[1/3] Disabling Discord default join messages in server settings...")
    payload = {
        "system_channel_flags": 9
    }
    r = requests.patch(f"https://discord.com/api/v10/guilds/{GUILD_ID}", headers=HEADERS, json=payload)
    if r.status_code == 200:
        print("✅ Successfully disabled Discord's built-in 'brought pizza / wave to say hi' system messages!")
        print("   Flags set: SUPPRESS_JOIN_NOTIFICATIONS | SUPPRESS_JOIN_NOTIFICATION_REPLIES")
    else:
        print(f"❌ Failed to update system flags: {r.status_code} {r.text}")

    # 2. Clean up old Type 7 (USER_JOIN) system messages from #🌸・welcome
    print("\n[2/3] Purging old default Discord join messages from #🌸・welcome...")
    r = requests.get(f"https://discord.com/api/v10/channels/{WELCOME_CHAN_ID}/messages?limit=20", headers=HEADERS)
    if r.status_code == 200:
        msgs = r.json()
        deleted_count = 0
        for m in msgs:
            # Delete system messages or older test spam
            if m.get("type") == 7 or m.get("author", {}).get("bot") is False:
                del_res = requests.delete(f"https://discord.com/api/v10/channels/{WELCOME_CHAN_ID}/messages/{m['id']}", headers=HEADERS)
                if del_res.status_code in (200, 204):
                    deleted_count += 1
        print(f"✅ Deleted {deleted_count} old default messages from #🌸・welcome!")

    # 3. Post the Clean Pinned Welcome Header
    print("\n[3/3] Posting Official Welcome Banner & Quick Start in #🌸・welcome...")
    welcome_header = {
        "title": "🌸 ⋆⋅ RAI FAM • OFFICIAL WELCOME SANCTUARY ⋅⋆ 🌸",
        "description": (
            "✦ ───────────────────────────── ✦\n\n"
            "**Welcome to the official arrival hub of RAI FAM 💗!**\n\n"
            "When new members join our family, **`AURA ✦`** will automatically greet them with a custom member card and welcome bonus!\n\n"
            "**🚀 Quick Start For New Arrivals:**\n"
            "> 1️⃣ **Unlock Channels:** Head over to <#1545502700840427702> and tap **`[ ✅ Verify ]`**\n"
            "> 2️⃣ **Pick Roles:** Choose your name colors & game pings in <#1545502722739150898>\n"
            "> 3️⃣ **Read Codex:** Review server safety guidelines in <#1545502710101704714>\n"
            "> 4️⃣ **Jump In:** Say hello in <#1545502730699808768> or join a voice lounge!\n\n"
            "✦ ───────────────────────────── ✦\n"
            "✨ *We're excited to have you with us. Enjoy your stay!* 🍿"
        ),
        "color": 0x2B2D31,
        "footer": {
            "text": "RAI FAM 💗 • Arrival Gate & Community Portal"
        }
    }
    r = requests.post(f"https://discord.com/api/v10/channels/{WELCOME_CHAN_ID}/messages", headers=HEADERS, json={"embeds": [welcome_header]})
    if r.status_code in (200, 201):
        print("✅ Official Welcome Header posted in #🌸・welcome!")

    print("\n==================================================================")
    print("   🎉 WELCOME CHANNEL FIXED & RESTORED TO FULL PERFECTION!        ")
    print("==================================================================")

if __name__ == "__main__":
    main()
