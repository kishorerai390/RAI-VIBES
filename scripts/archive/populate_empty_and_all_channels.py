import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"

headers = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "DiscordBot (ChannelPurposeSetup, 1.0)"
}

DIVIDER = "<a:w_welc1:1547271923891707915><:w_dash:1547271874981920868><:w_dash:1547271874981920868><:w_dash:1547271874981920868><:w_dash:1547271874981920868><a:w_welc2:1547271930699190424>"

# 1. Post to #security-logs (both 1546942780817801226 and 1546593526073135107)
security_embed = {
    "title": "<a:pinkflame:1547271954841731193> ✦ RAI SENTINEL • SECURITY & INCIDENT LOGS ✦ <a:pinkflame:1547271954841731193>",
    "description": (
        f"{DIVIDER}\n\n"
        "🛡️ **Official Automated Security Telemetry & Incident Audit Feed**\n\n"
        "This private channel operates 24/7 as the automated defense center for **RAI FAM 💗**. "
        "RAI SENTINEL automatically logs, intercepts, and reports all server threat vectors in real-time:\n\n"
        "<:badge_1:1547271940279107665> **Anti-Raid & Mass Join Protection**\n"
        "• Flags suspicious account spikes, unverified bot waves, and alt-accounts\n"
        "• Enforces instant quarantine lockdown during raid anomalies\n\n"
        "<:badge_2:1547271946645934122> **Malicious Link & Phishing Interception**\n"
        "• Auto-deletes unauthorized server invites, scam domains, and fake nitro links\n"
        "• Applies automatic safety warnings & progressive timeouts to violators\n\n"
        "<:badge_3:1547271951297413281> **Anti-Nuke & Admin Integrity Guard**\n"
        "• Tracks rapid channel/role deletions and unauthorized webhook creations\n"
        "• Auto-strips administrative permissions from compromised staff accounts\n\n"
        "<a:pixel_heart:1547271960336146563> **Moderation Punishments Telemetry**\n"
        "• Real-time audit trails for Bans, Kicks, Chat Mutes, and Soundboard Timeouts\n\n"
        f"{DIVIDER}\n"
        "🟢 **Engine Status:** `ONLINE & ACTIVE`\n"
        "🛡️ **Guards Active:** `RAI SENTINEL 🛡️` • `Wick Engine`"
    ),
    "color": 0xFF2A85,
    "footer": {
        "text": "RAI SENTINEL 🛡️ • Automated Defense Log Engine",
        "icon_url": "https://cdn.discordapp.com/icons/1457382179981099090/48eea1fe3398ee891ba9f7682acff1c0.png"
    }
}

# 2. Post to #welcome (1545502705643167876)
welcome_embed = {
    "title": "<a:sparkle_love:1547271978883350568> ✦ WELCOME TO RAI FAM 💗 • AUDIO & CYBER SANCTUARY ✦ <a:sparkle_love:1547271978883350568>",
    "description": (
        f"{DIVIDER}\n\n"
        "Welcome to our server! We're glad to have you in **RAI FAM 💗**.\n"
        "Follow this quick 3-step quickstart to unlock and personalize your experience:\n\n"
        "<:badge_1:1547271940279107665> **Get Verified** • Visit <#1545502700840427702> and tap **`[ ✅ Verify ]`** to unlock chats & voice lounges.\n"
        "<:badge_2:1547271946645934122> **Select Roles** • Pick your gaming squads, name colors & ping alerts in <#1545502722739150898>.\n"
        "<:badge_3:1547271951297413281> **Say Hello** • Introduce yourself in <#1545502730699808768> or chill in our 24/7 music lounge <#1545502782268772453>!\n\n"
        f"{DIVIDER}\n"
        "🎵 *High-Fidelity Audio • Friendly Community • Gaming Tournaments*"
    ),
    "color": 0xFF69B4,
    "footer": {
        "text": "RAI FAM 💗 • Community Quickstart Directory"
    }
}

# 3. Post to #executive (1545518535827263519)
executive_embed = {
    "title": "<a:heart_fire:1547271965729882322> ✦ RAI FAM • EXECUTIVE COUNCIL CHAMBER ✦ <a:heart_fire:1547271965729882322>",
    "description": (
        f"{DIVIDER}\n\n"
        "**Confidential Executive Council & Strategic Leadership Hub**\n\n"
        "This private chamber is reserved strictly for the Founder, Head Admins, and Senior Leadership of **RAI FAM 💗**.\n\n"
        "• **Strategic Roadmaps** • Server updates, community partnerships, and tournament organizing\n"
        "• **Financial & Infrastructure** • Server Boost management, cloud bot hosting & bot upgrades\n"
        "• **Staff Management** • Moderator reviews, executive directives, and policy enforcement\n\n"
        f"{DIVIDER}\n"
        "👑 **Authorized Leadership Only** • All communications remain strictly confidential."
    ),
    "color": 0xF1C40F,
    "footer": {
        "text": "RAI FAM 💗 • Executive Leadership Council"
    }
}

def send_embed(chan_id, embed):
    req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/{chan_id}/messages",
        data=json.dumps({"embeds": [embed]}).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        print(f"✅ Posted purpose embed to channel {chan_id} (Message ID: {res['id']})")

# Execute posts
print("Populating channels with their dedicated purpose...")
send_embed("1546942780817801226", security_embed) # Active security-logs seen on user screen
send_embed("1546593526073135107", security_embed) # Styled security-logs in Sentinel HQ
send_embed("1545502705643167876", welcome_embed)  # welcome channel
send_embed("1545518535827263519", executive_embed)# executive channel

# Move unparented 1546942780817801226 into SENTINEL HQ category (parent: 1545502840003493928) so it's not floating
SENTINEL_HQ_CAT_ID = "1545502840003493928"
try:
    move_req = urllib.request.Request(
        f"https://discord.com/api/v10/channels/1546942780817801226",
        data=json.dumps({"parent_id": SENTINEL_HQ_CAT_ID, "position": 10}).encode("utf-8"),
        headers=headers,
        method="PATCH"
    )
    with urllib.request.urlopen(move_req) as resp:
        print("✅ Moved #security-logs under '╭・𝗦𝗘𝗡𝗧𝗜𝗡𝗘𝗟 𝗛𝗤 ✧' category!")
except Exception as e:
    print(f"Note on moving channel: {e}")

print("\n🎉 All channels successfully populated and organized!")
