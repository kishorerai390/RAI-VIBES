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

# Role IDs
EVERYONE_ID = "1457382179981099090"
EMPEROR_ROLE_ID = "1545494610489643038"
HEAD_ADMIN_ROLE_ID = "1545506927788687470"
GUARDIAN_ROLE_ID = "1545494600347680918"
BOT_ROLE_ID = "1545494288643657912"

# Bitwise permissions
# VIEW_CHANNEL = 1024 (1 << 10)
# CONNECT = 1048576 (1 << 20)
# SPEAK = 2097152 (1 << 21)
# STREAM = 512 (1 << 9)
# SEND_MESSAGES = 2048 (1 << 11)
# READ_MESSAGE_HISTORY = 65536 (1 << 16)

def main():
    print("Fetching existing channels...")
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    channels = r.json()
    
    chan_by_name = {c["name"]: c for c in channels}
    cat_by_name = {c["name"]: c for c in channels if c["type"] == 4}

    # 1. Clean up unused/bloated text channels to make server VC-focused
    unneeded_channels = [
        "movie-schedule", "📅・movie-schedule",
        "movie-chat", "🍿・movie-chat",
        "lofi-chat", "☕・lofi-chat",
        "suggestions", "💡・suggestions",
        "music-commands", "🎵・music-commands"
    ]
    for uname in unneeded_channels:
        if uname in chan_by_name:
            cid = chan_by_name[uname]["id"]
            res = requests.delete(f"https://discord.com/api/v10/channels/{cid}", headers=HEADERS)
            if res.status_code == 200:
                print(f"🗑️ Cleaned up text channel: #{uname}")

    # Remove old "🍿 | 𝙈𝙊𝙑𝙄𝙀𝙎 & 𝘾𝙄𝙉𝙀𝙈𝘼" category if it exists
    old_movie_cat = [c for c in channels if c["type"] == 4 and "MOVIES" in c["name"].upper()]
    for mc in old_movie_cat:
        # Check if empty or only cinema
        requests.delete(f"https://discord.com/api/v10/channels/{mc['id']}", headers=HEADERS)
        print(f"🗑️ Cleaned up category: {mc['name']}")

    # Refresh channel list
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    channels = r.json()
    cat_by_name = {c["name"]: c for c in channels if c["type"] == 4}
    chan_by_name = {c["name"]: c for c in channels}

    # 2. Setup HIDDEN / SECRET VC CATEGORY FOR EMPEROR & HEAD ADMIN
    hidden_cat_name = "👑 | 𝙍𝙊𝙔𝘼𝙇 𝙎𝘼𝙉𝘾𝙏𝙐𝘼𝙍𝙔"
    hidden_cat = None
    for c in channels:
        if c["type"] == 4 and ("ROYAL" in c["name"].upper() or "SANCTUARY" in c["name"].upper() or "HIDDEN" in c["name"].upper()):
            hidden_cat = c
            break

    hidden_overwrites = [
        {
            "id": EVERYONE_ID,
            "type": 0,
            "allow": "0",
            "deny": str(1024 | 1048576 | 2048) # VIEW_CHANNEL, CONNECT, SEND_MESSAGES
        },
        {
            "id": EMPEROR_ROLE_ID,
            "type": 0,
            "allow": str(1024 | 1048576 | 2097152 | 512 | 2048 | 65536 | 16), # Full access + Manage
            "deny": "0"
        },
        {
            "id": HEAD_ADMIN_ROLE_ID,
            "type": 0,
            "allow": str(1024 | 1048576 | 2097152 | 512 | 2048 | 65536), # Full access
            "deny": "0"
        },
        {
            "id": BOT_ROLE_ID,
            "type": 0,
            "allow": str(1024 | 1048576 | 2097152 | 2048),
            "deny": "0"
        }
    ]

    if not hidden_cat:
        res = requests.post(
            f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
            headers=HEADERS,
            json={
                "name": hidden_cat_name,
                "type": 4,
                "permission_overwrites": hidden_overwrites
            }
        )
        if res.status_code in (200, 201):
            hidden_cat = res.json()
            print(f"✅ Created hidden category: {hidden_cat_name}")
        else:
            print(f"❌ Failed to create hidden category: {res.status_code} {res.text}")
    else:
        # Update permissions
        requests.patch(
            f"https://discord.com/api/v10/channels/{hidden_cat['id']}",
            headers=HEADERS,
            json={"permission_overwrites": hidden_overwrites}
        )
        print(f"✅ Updated permissions for hidden category: {hidden_cat['name']}")

    # Create channels inside Hidden Category
    if hidden_cat:
        hidden_channels = [
            {"name": "👑 | EMPEROR'S THRONE", "type": 2, "user_limit": 0},
            {"name": "⚡ | HIGH COMMAND VC", "type": 2, "user_limit": 0},
            {"name": "🍸 | PRIVATE LOUNGE", "type": 2, "user_limit": 2},
            {"name": "🔒・executive-chat", "type": 0}
        ]
        for hc in hidden_channels:
            exists = any(c["name"] == hc["name"] and c.get("parent_id") == hidden_cat["id"] for c in channels)
            if not exists:
                payload = {
                    "name": hc["name"],
                    "type": hc["type"],
                    "parent_id": hidden_cat["id"],
                    "permission_overwrites": hidden_overwrites
                }
                if hc.get("user_limit"):
                    payload["user_limit"] = hc["user_limit"]
                res = requests.post(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS, json=payload)
                if res.status_code in (200, 201):
                    print(f"✅ Created secret channel: {hc['name']}")
                else:
                    print(f"❌ Failed to create secret channel {hc['name']}: {res.status_code} {res.text}")

    # 3. Expand Fun Voice Channels for VC-First Experience
    fun_vc_cat = next((c for c in channels if c["type"] == 4 and "FUN VOICE" in c["name"].upper()), None)
    if fun_vc_cat:
        extra_vcs = [
            {"name": "☕ | CHILL & TALK", "type": 2, "user_limit": 0},
            {"name": "🌙 | NIGHT TALKS", "type": 2, "user_limit": 0},
            {"name": "🥂 | ・ DUO 2", "type": 2, "user_limit": 2},
            {"name": "👥 | ・ SQUAD", "type": 2, "user_limit": 4},
        ]
        for evc in extra_vcs:
            exists = any(c["name"] == evc["name"] and c.get("parent_id") == fun_vc_cat["id"] for c in channels)
            if not exists:
                payload = {
                    "name": evc["name"],
                    "type": 2,
                    "parent_id": fun_vc_cat["id"],
                    "user_limit": evc["user_limit"]
                }
                res = requests.post(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS, json=payload)
                if res.status_code in (200, 201):
                    print(f"✅ Created voice channel: {evc['name']}")

    # 4. Ensure Music & Cinema Zone has both cinema & music VCs
    music_cat = next((c for c in channels if c["type"] == 4 and "MUSIC" in c["name"].upper()), None)
    if music_cat:
        # Rename category to 🎵 | 𝙈𝙐𝙎𝙄𝘾 & 𝘾𝙄𝙉𝙀𝙈𝘼
        requests.patch(
            f"https://discord.com/api/v10/channels/{music_cat['id']}",
            headers=HEADERS,
            json={"name": "🎵 | 𝙈𝙐𝙎𝙄𝘾 & 𝘾𝙄𝙉𝙀𝙈𝘼"}
        )
        music_vcs = [
            {"name": "📻 | 24-7 RADIO", "type": 2},
            {"name": "🎥 | CINEMA THEATER", "type": 2}
        ]
        for mvc in music_vcs:
            exists = any(c["name"] == mvc["name"] and c.get("parent_id") == music_cat["id"] for c in channels)
            if not exists:
                requests.post(
                    f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels",
                    headers=HEADERS,
                    json={
                        "name": mvc["name"],
                        "type": 2,
                        "parent_id": music_cat["id"]
                    }
                )
                print(f"✅ Created {mvc['name']}")

    # 5. Gaming Zone - Add squad size indicators
    gaming_cat = next((c for c in channels if c["type"] == 4 and "GAMING" in c["name"].upper()), None)
    if gaming_cat:
        for c in channels:
            if c.get("parent_id") == gaming_cat["id"] and c["type"] == 2:
                # Set limit to 4 for squad gaming
                requests.patch(
                    f"https://discord.com/api/v10/channels/{c['id']}",
                    headers=HEADERS,
                    json={"user_limit": 4}
                )

    print("\n🎉 VC-Focused Transformation & Hidden Admin Sanctuary Complete!")

if __name__ == "__main__":
    main()
