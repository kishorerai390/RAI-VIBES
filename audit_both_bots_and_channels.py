import os
import sys
import json
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
VIBES_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SENTINEL_TOKEN = os.getenv("SECURITY_BOT_TOKEN")
GUILD_ID = "1457382179981099090"

def get_headers(token):
    return {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

def main():
    print("==================================================================")
    print("      🔍 COMPREHENSIVE BOT & SERVER DEEP AUDIT REPORT 🔍          ")
    print("==================================================================")

    # 1. BOT 1: RAI VIBES
    print("\n--- [1] RAI VIBES BOT DIAGNOSTICS ---")
    if not VIBES_TOKEN:
        print("❌ DISCORD_BOT_TOKEN not found in .env")
    else:
        r = requests.get("https://discord.com/api/v10/users/@me", headers=get_headers(VIBES_TOKEN))
        if r.status_code == 200:
            u = r.json()
            print(f"✅ Authenticated: {u['username']}#{u['discriminator']} (ID: {u['id']})")
        else:
            print(f"❌ Failed to authenticate: {r.status_code} {r.text}")

        # Check guild member perms
        r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{u['id']}", headers=get_headers(VIBES_TOKEN))
        if r.status_code == 200:
            m = r.json()
            print(f"✅ In Guild: Nickname='{m.get('nick')}', Roles={len(m.get('roles', []))}")
        else:
            print(f"⚠️ Could not fetch guild member info: {r.status_code}")

    # 2. BOT 2: RAI SENTINEL
    print("\n--- [2] RAI SENTINEL BOT DIAGNOSTICS ---")
    if not SENTINEL_TOKEN:
        print("❌ SECURITY_BOT_TOKEN not found in .env")
    else:
        r = requests.get("https://discord.com/api/v10/users/@me", headers=get_headers(SENTINEL_TOKEN))
        if r.status_code == 200:
            u = r.json()
            print(f"✅ Authenticated: {u['username']}#{u['discriminator']} (ID: {u['id']})")
            sentinel_id = u['id']
            # Check guild member perms
            r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/{sentinel_id}", headers=get_headers(VIBES_TOKEN or SENTINEL_TOKEN))
            if r.status_code == 200:
                m = r.json()
                print(f"✅ In Guild: Nickname='{m.get('nick')}', Roles={len(m.get('roles', []))}")
            else:
                print(f"⚠️ Could not fetch guild member info: {r.status_code}")
        else:
            print(f"❌ Failed to authenticate: {r.status_code} {r.text}")

    # 3. GUILD CONFIGURATION AUDIT
    print("\n--- [3] GUILD SETTINGS AUDIT ---")
    headers = get_headers(VIBES_TOKEN)
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}?with_counts=true", headers=headers)
    guild = r.json() if r.status_code == 200 else {}
    print(f"🏰 Guild: {guild.get('name')} (ID: {guild.get('id')})")
    print(f"👑 Owner ID: {guild.get('owner_id')}")
    print(f"👥 Total Members: {guild.get('approximate_member_count')}")
    print(f"🚀 Boost Tier: {guild.get('premium_tier')} ({guild.get('premium_subscription_count')} Boosts)")
    print(f"💤 AFK Channel ID: {guild.get('afk_channel_id')} (Timeout: {guild.get('afk_timeout')}s)")
    print(f"📢 System Channel ID: {guild.get('system_channel_id')}")
    print(f"📜 Rules Channel ID: {guild.get('rules_channel_id')}")
    print(f"🔔 Updates Channel ID: {guild.get('public_updates_channel_id')}")

    # 4. CHANNELS AUDIT & PURPOSE MAPPING
    print("\n--- [4] CHANNELS WORK & ROLE ASSIGNMENT AUDIT ---")
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=headers)
    channels = r.json() if r.status_code == 200 else []
    categories = {c["id"]: c for c in channels if c["type"] == 4}
    sorted_cats = sorted(categories.values(), key=lambda x: x["position"])

    # Channel assignments definitions
    ASSIGNMENTS = {
        # Information
        "announcements": ("Official Broadcasts", "Announcements, server changelogs, events", "Admins"),
        "welcome": ("Welcome Gate", "Automated welcome cards sent when new members join", "RAI VIBES / Sentinel"),
        "rules": ("Server Rules & Policy", "Permanent rules embed & guidelines", "Sentinel / Admin"),
        "verify-here": ("Verification Gateway", "Interactive button verification to grant Member role", "Sentinel Verify Cog"),
        "self-roles": ("Reaction Roles Panel", "Interactive dropdown/button menus for roles (gaming, notify, colors)", "RAI VIBES Roles View"),
        "server-guide": ("Navigation Map", "Directory of server channels, bots, and FAQ", "Admin / Sentinel"),
        "goodbyes": ("Farewell Logs", "Automated goodbye message when a member leaves", "RAI VIBES Welcome Cog"),
        "partnerships": ("Affiliate & Partners", "Partner server advertisements & cross-promos", "Community"),
        
        # Lounge
        "general-chat": ("Main Discussion", "Community chatting, text XP leveling, bot conversations", "All Members + RAI VIBES Leveling"),
        "media-gallery": ("Media & Artwork", "Images, clips, screenshots, memes (Starboard integration)", "All Members"),
        "vip-lounge": ("VIP Exclusive Text", "High tier booster and VIP discussion channel", "VIP & Booster Roles"),
        "Rai Fam Lounge": ("Community Voice", "Open voice chatting for server family", "All Members"),
        "VIP Voice Lounge": ("VIP Voice Suite", "Private high-bitrate voice lounge for VIPs", "VIP / High Rank"),
        "Booster Lounge": ("Nitro Boosters Voice", "Dedicated high-bitrate voice room for Nitro supporters", "Server Boosters"),

        # Vibe Studio
        "song-requests": ("Music Queue Engine", "Zero-prefix music requests (type any song name directly to queue)", "RAI VIBES Music Engine"),
        "Lo-Fi Chill 24/7": ("24/7 Radio Station", "Permanent 24/7 stream radio anchor (never leaves)", "RAI VIBES Radio Cog"),
        "Vibe Lounge": ("Audio Listening Room", "Shared music listening & chilled conversations", "All Members"),
        "Karaoke Stage": ("Singing & Performance", "Live singing with `/karaoke` voice filter enabled", "Singers & Performers"),

        # Gaming Zone
        "gaming-hub": ("Gaming Chat", "Game discussions, squad-up pings, clip sharing", "Gamers"),
        "Free Fire Arena": ("Squad Voice", "Voice room tailored for Free Fire squads", "Free Fire Gamers"),
        "Roblox Chill": ("Casual Gaming VC", "Roblox hangout & voice chat", "Roblox Gamers"),
        "Gaming Lounge": ("General Gaming VC", "Multiplayer co-op voice chat", "All Gamers"),
        "BGMI Squad": ("Esports Squad VC", "Battlegrounds Mobile India voice squad room", "BGMI Gamers"),

        # Fun Zone
        "Open Voice Chill": ("Casual Hangout VC", "General voice room for all members without time limits", "All Members"),
        "AFK / Sleeping": ("AFK Voice Channel", "Auto-moves inactive/idle voice users after timeout", "Discord Auto-AFK Engine"),

        # Private Suites
        "Join to Create VC": ("Dynamic Join-to-Create", "Instantly generates a custom temporary voice channel with full owner controls", "RAI VIBES VoiceHub Cog"),
        "Create Private VC": ("Ghost / Private Hub", "Generates an invisible ghost room hidden from everyone except invited guests", "RAI VIBES VoiceHub Cog"),

        # Checking Zone
        "Checking Area": ("Security Check Waiting", "Holding lounge for users undergoing device/account inspection", "Staff / Sentinel"),
        "PC Check": ("PC Verification VC", "Staff screen-share inspection for PC users", "Staff / Sentinel"),
        "Phone Check": ("Mobile Verification VC", "Staff inspection room for mobile gamers", "Staff / Sentinel"),
        "iOS Check": ("iOS Verification VC", "Dedicated inspection room for Apple device users", "Staff / Sentinel"),

        # Executive Zone
        "executive-chat": ("Leadership Text HQ", "Confidential strategic decisions & server governance", "Emperor / Head Admin"),
        "Executive Suite": ("Leadership Voice HQ", "Confidential executive voice discussions", "Emperor / Head Admin"),
        "Private Office": ("Owner's Private Office", "Owner solo/duo meeting room", "Server Owner"),

        # Sentinel HQ
        "staff-hq": ("Staff Operations", "Internal staff discussions, shift coordination, notes", "Moderators & Admins"),
        "audit-logs": ("Server Action Logs", "Role changes, channel updates, invites tracked", "Sentinel Log Engine"),
        "ticket-support": ("Helpdesk Panel", "Interactive button ticket system for private member support", "Sentinel Tickets Cog"),
        "moderation-logs": ("Punishment Feed", "Kicks, bans, mutes, warnings logged transparently", "Sentinel Moderation Cog"),
        "sentinel-defense-logs": ("Anti-Nuke / Anti-Raid Feed", "Instant alerts for raid detection, mass-deletions, or permission abuse", "Sentinel Anti-Nuke Cog"),
        "security-terminal": ("Sentinel Terminal", "Security audit dashboard, whitelist checks, bot telemetry", "Sentinel Admin Cog")
    }

    assigned_count = 0
    unassigned_count = 0

    for cat in sorted_cats:
        print(f"\n📁 Category: {cat['name']}")
        chans = [c for c in channels if c.get("parent_id") == cat["id"]]
        chans.sort(key=lambda x: x["position"])
        for ch in chans:
            t = "TXT" if ch["type"] in (0, 5) else "VC"
            name = ch["name"]
            # match with assignment
            matched = None
            for k, val in ASSIGNMENTS.items():
                if k.lower() in name.lower():
                    matched = val
                    break

            if matched:
                assigned_count += 1
                role, purpose, bot_task = matched
                print(f"   [{t}] {name:<28} ➔ Role: {role} | Bot/Task: {bot_task}")
            else:
                unassigned_count += 1
                print(f"   [{t}] {name:<28} ➔ [NEEDS ROLE DEFINITION]")

    print("\n==================================================================")
    print(f"📊 SUMMARY: {assigned_count} Channels Fully Assigned | {unassigned_count} Unassigned")
    print("==================================================================")

if __name__ == "__main__":
    main()
