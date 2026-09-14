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

SENTINEL_BOT_ID = "1546245134809571470"

# 1. Sleek Channel Topics (shows up at the top bar on mobile and desktop)
CHANNEL_TOPICS = {
    "1545502700840427702": "✨ Click the button below to verify your account & unlock full server access.",
    "1545502705643167876": "🌸 Member arrivals & departures • Welcome to the RAI FAM sanctuary.",
    "1545502710101704714": "📜 Official Server Codex & Guidelines • Follow Discord TOS & Server Rules.",
    "1545502718792175646": "📢 Official broadcasts, patch notes, updates & server event announcements.",
    "1545502722739150898": "🎀 Personalize your profile with custom colors, gaming alerts & notification roles.",
    "1546125872661012611": "🧭 Server navigation map, bot command directory & community FAQ.",
    "1547279073217351782": "🤝 Official affiliate servers, partner promos & community collaborations.",
    "1545502730699808768": "💬 Main community lounge • Chat, share thoughts, and earn XP to rank up!",
    "1546097792915873842": "📸 Share gaming clips, screenshots, memes, artworks & highlights.",
    "1545834933417672744": "💎 Exclusive lounge reserved for Server Boosters and VIP members.",
    "1545534637122527332": "🎵 Zero-Prefix Music Queue • Simply type song name or URL to stream.",
    "1545803554550190212": "🎮 Gaming discussions, squad recruitments, clutch clips & game strategy.",
    "1545518535827263519": "👑 High Command & Executive Governance • Confidential leadership text.",
    "1545502845208629328": "🛡️ Internal Staff Operations, shift coordination & team discussions.",
    "1545502850057244762": "📋 Discord audit logs feed • Server modifications & role changes.",
    "1545514505520545886": "🎫 24/7 Helpdesk • Click button below to create an instant private support ticket.",
    "1546540192343523399": "📝 Transparent log of mutes, kicks, warnings & administrative actions.",
    "1546593526073135107": "🚨 Real-time security telemetry • Anti-Nuke, Anti-Raid & Threat alerts.",
    "1547294258074226758": "🔒 Autonomous Sentinel terminal, whitelist audit & bot telemetry."
}

def patch_channel(cid, payload, desc):
    url = f"https://discord.com/api/v10/channels/{cid}"
    res = requests.patch(url, headers=HEADERS, json=payload)
    if res.status_code == 200:
        print(f"✅ {desc}")
    elif res.status_code == 429:
        retry_after = res.json().get("retry_after", 1.0)
        print(f"⏳ Rate limited on {desc}, waiting {retry_after}s...")
        time.sleep(retry_after + 0.3)
        requests.patch(url, headers=HEADERS, json=payload)
        print(f"✅ (After wait) {desc}")
    else:
        print(f"❌ Failed {desc}: {res.status_code}")

def main():
    print("==================================================================")
    print("     👑 ELEVATING SERVER & BOTS TO 'GOD-TIER' AESTHETICS 👑       ")
    print("==================================================================")

    # 1. Update Sentinel Bot Nickname to AEGIS 🛡️ (Divine Shield)
    print("\n[1/5] Updating Sentinel Bot to Divine Name: 'AEGIS 🛡️'...")
    if SENTINEL_TOKEN:
        s_headers = {"Authorization": f"Bot {SENTINEL_TOKEN}", "Content-Type": "application/json"}
        url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/@me"
        r = requests.patch(url, headers=s_headers, json={"nick": "AEGIS 🛡️"})
        if r.status_code == 200:
            print("✅ Sentinel renamed to 'AEGIS 🛡️' (The Divine Shield)!")
        else:
            print(f"Nickname update note: {r.status_code}")

    # 2. Update Guild Description
    print("\n[2/5] Setting Server Official Description...")
    guild_payload = {
        "description": "⚡ The Sanctuary of Sound & Gaming. High-Fidelity Audio, 24/7 Lo-Fi Lounge, Competitive Squads & Safe Cyber Community."
    }
    r = requests.patch(f"https://discord.com/api/v10/guilds/{GUILD_ID}", headers=HEADERS, json=guild_payload)
    if r.status_code == 200:
        print("✅ Server description successfully set!")
    else:
        print(f"Server description note: {r.status_code}")

    # 3. Apply Clean Channel Topics to All Text Channels
    print("\n[3/5] Setting Professional Channel Topics across all text channels...")
    for cid, topic in CHANNEL_TOPICS.items():
        patch_channel(cid, {"topic": topic}, f"Topic set on channel ID {cid}")
        time.sleep(0.4)

    # 4. Maximize Bitrate on All Voice Channels (96kbps studio quality)
    print("\n[4/5] Tuning All Voice Channels to 96kbps Studio Bitrate...")
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    if r.status_code == 200:
        channels = r.json()
        for c in channels:
            if c.get("type") == 2 and c.get("bitrate") != 96000:
                patch_channel(c["id"], {"bitrate": 96000}, f"Bitrate 96kbps on {c['name']}")
                time.sleep(0.4)

    # 5. Post God-Tier Rules Codex in #📜・rules
    print("\n[5/5] Deploying Divine Community Codex in #📜・rules...")
    rules_cid = "1545502710101704714"
    # Clean old rules
    try:
        r = requests.get(f"https://discord.com/api/v10/channels/{rules_cid}/messages?limit=10", headers=HEADERS)
        if r.status_code == 200:
            for m in r.json():
                requests.delete(f"https://discord.com/api/v10/channels/{rules_cid}/messages/{m['id']}", headers=HEADERS)
    except Exception:
        pass

    rules_embed = {
        "title": "📜 ⋆⋅ RAI FAM • THE DIVINE COMMUNITY CODEX ⋅⋆ 📜",
        "description": (
            "✦ ───────────────────────────── ✦\n\n"
            "Welcome to **RAI FAM 💗**! Our sanctuary is built on respect, chill energy, and passion for music and gaming. "
            "By participating in this server, you agree to abide by our Community Codex:\n\n"
            "### 👑 1. Respect & Member Decorum\n"
            "> • Treat every member with kindness. Harassment, discrimination, racism, hate speech, or toxicity will result in an instant ban.\n"
            "> • Do not instigate arguments or drag server drama into public channels.\n\n"
            "### 🎙️ 2. Voice Channel Etiquette\n"
            "> • Mic-spamming, ear-raping, or loud soundboard abuse in public lounges is prohibited.\n"
            "> • Respect squad capacity limits in gaming rooms (BGMI, Free Fire).\n"
            "> • Use <#1545502813889499136> when stepping away from your keyboard.\n\n"
            "### 🛡️ 3. Anti-Scam & Security Integrity\n"
            "> • Posting fake Discord Nitro links, malicious downloads, or Steam scam links triggers an immediate permanent ban by **`AEGIS 🛡️`**.\n"
            "> • Unsolicited advertising or mass DM advertising to members is strictly forbidden.\n\n"
            "### ⚙️ 4. Channel Discipline\n"
            "> • Keep music commands inside <#1545534637122527332>.\n"
            "> • Post clips and artwork in <#1546097792915873842>.\n"
            "> • For assistance or inquiries, open a ticket in <#1545514505520545886>.\n\n"
            "### ⚖️ 5. Enforcement & Staff Authority\n"
            "> • Staff decisions are final. If you have an inquiry, respectfully contact staff via private ticket.\n\n"
            "✦ ───────────────────────────── ✦\n"
            "✨ *Enjoy high-fidelity sound, lock in with your squad, and vibe with the family!* 🌸"
        ),
        "color": 0x2B2D31,
        "footer": {
            "text": "RAI FAM 💗 • Protected by AEGIS Defense Engine",
            "icon_url": "https://cdn.discordapp.com/icons/1457382179981099090/a_6c9cb2ceb28c89490237c15eb1d279cf.gif"
        }
    }
    requests.post(f"https://discord.com/api/v10/channels/{rules_cid}/messages", headers=HEADERS, json={"embeds": [rules_embed]})
    print("✅ Divine Community Codex posted in #📜・rules!")

    print("\n==================================================================")
    print("      🎉 SERVER ASCENDED TO GOD-TIER PERFECTION!                  ")
    print("==================================================================")

if __name__ == "__main__":
    main()
