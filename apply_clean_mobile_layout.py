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

# Exact ID to New Name Map (Guaranteed 100% match)
EXACT_RENAME_MAP = {
    # Categories
    "1545502694930649109": "🌸 INFORMATION",
    "1545502726232744108": "💬 CHAT & LOUNGE",
    "1545502766120566784": "🎵 MUSIC & CINEMA",
    "1545502786161090652": "🔊 VOICE LOUNGES",
    "1545502817471569990": "🎮 GAMING ZONE",
    "1545518525634838658": "👑 ROYAL SANCTUARY",
    "1545502840452157463": "🛡️ STAFF ZONE",

    # Text Channels
    "1545502700840427702": "verify-here",
    "1545502705643167876": "welcome",
    "1545502710101704714": "rules",
    "1545502718792175646": "announcements",
    "1545502722739150898": "self-roles",
    "1545502730699808768": "general-chat",
    "1545502734663286856": "media",
    "1545502738362671255": "bot-commands",
    "1545534637122527332": "song-requests",
    "1545518535827263519": "executive-chat",
    "1545502845208629328": "staff-chat",
    "1545502850057244762": "mod-logs",
    "1545514505520545886": "ticket-support",

    # Voice Channels
    "1545502782268772453": "🎧 Music Lounge",
    "1545518701414195281": "📻 24/7 Radio",
    "1545502762467328185": "🎥 Cinema Theater",
    "1545502790888198215": "➕ Join to Create",
    "1545502794868457574": "🐣 Fun Time",
    "1545502799402369034": "🍇 Open Voice",
    "1545502804280352871": "🥂 Duo Lounge",
    "1545502809896517703": "🥂 Trio Lounge",
    "1545502813889499136": "💤 AFK Lounge",
    "1545502823699980408": "🔥 Free Fire",
    "1545502829089787924": "🎯 BGMI",
    "1545502832822591539": "🧱 Roblox",
    "1545502836392198164": "🎮 Other Games",
    "1545518528126394400": "👑 Emperor's Throne",
    "1545518531192553603": "⚡ High Command",
    "1545518533566271539": "🍸 Private Lounge",
}

def get_channels():
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    return r.json()

def update_channel(channel_id, new_name):
    r = requests.patch(
        f"https://discord.com/api/v10/channels/{channel_id}",
        headers=HEADERS,
        json={"name": new_name}
    )
    if r.status_code == 200:
        return True
    elif r.status_code == 429:
        retry_after = r.json().get("retry_after", 2)
        print(f"  ⏳ Rate limited, waiting {retry_after}s...")
        time.sleep(retry_after)
        return update_channel(channel_id, new_name)
    else:
        print(f"  ❌ Error updating {channel_id}: {r.status_code} {r.text}")
        return False

def main():
    print("✨ Applying Direct-ID Mobile Optimization...")
    channels = get_channels()
    
    for c in channels:
        cid = str(c["id"])
        cname = c["name"]
        if cid in EXACT_RENAME_MAP:
            target_name = EXACT_RENAME_MAP[cid]
            if cname != target_name:
                print(f"Renaming [{cid}]: '{cname}' -> '{target_name}'")
                success = update_channel(cid, target_name)
                if success:
                    print(f"  ✅ Updated successfully!")
                time.sleep(0.5)

    # Check suggestions channel
    channels = get_channels()
    chat_cat = next((c for c in channels if c["type"] == 4 and "CHAT & LOUNGE" in c["name"]), None)
    sugg_chan = next((c for c in channels if "suggestion" in c["name"].lower()), None)
    
    if not sugg_chan:
        print("\n💡 Creating #suggestions channel under CHAT & LOUNGE...")
        payload = {
            "name": "suggestions",
            "type": 0,
            "parent_id": chat_cat["id"] if chat_cat else None,
            "topic": "Share your suggestions, feature requests, and feedback to improve RAI FAM 💗"
        }
        r = requests.post(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS, json=payload)
        if r.status_code == 201:
            sdata = r.json()
            sid = sdata["id"]
            print(f"  ✅ Created #suggestions (ID: {sid})")
            
            # Post embed
            embed_payload = {
                "embeds": [{
                    "title": "💡 SERVER SUGGESTIONS & FEEDBACK",
                    "description": (
                        "Welcome to the **RAI FAM 💗** suggestion box!\n\n"
                        "💡 **How to submit:**\n"
                        "• Type your idea, bot feature request, or server improvement below.\n"
                        "• React with 👍 or 👎 to vote on fellow members' ideas.\n\n"
                        "✨ *The staff team regularly reviews all community feedback!*"
                    ),
                    "color": 0xFF69B4,
                    "footer": {"text": "RAI VIBES • Community Feedback"}
                }]
            }
            requests.post(f"https://discord.com/api/v10/channels/{sid}/messages", headers=HEADERS, json=embed_payload)
            print("  ✅ Sent Suggestion Guide Embed!")
    else:
        print(f"\n✅ Suggestions channel exists: #{sugg_chan['name']}")

    print("\n🎉 ALL DONE! Check Discord now.")

if __name__ == "__main__":
    main()
