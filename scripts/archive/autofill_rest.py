import os
import sys
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"
HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}
ICON_URL = "https://cdn.discordapp.com/avatars/1545479610550980709/4176f6e6e76161728a4314c87c41fdd7.png?size=512"

def post_message(channel_id, payload):
    res = requests.post(f"https://discord.com/api/v10/channels/{channel_id}/messages", headers=HEADERS, json=payload)
    if res.status_code in (200, 201):
        print(f"✅ Posted to channel {channel_id}")
    else:
        print(f"⚠️ Failed to post to {channel_id}: {res.status_code} {res.text}")

def main():
    r_chans = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    channels = {c["name"]: c["id"] for c in r_chans.json() if "id" in c}

    def get_chan(name, fallback_id=None):
        return channels.get(name, fallback_id)

    # 1. Rules Embed in #📜・rules
    rules_id = get_chan("📜・rules", "1545502710101704714")
    if rules_id:
        rules_payload = {
            "embeds": [{
                "title": "🌸 ⋆⋅ RAI FAM COMMUNITY GUIDELINES ⋅⋆ 🌸",
                "description": (
                    "Welcome to **RAI FAM 💗**! To keep our hangout safe, fun, and chill for everyone, please follow our server guidelines:\n\n"
                    "**1️⃣ Mutual Respect & Kindness**\n"
                    "• Treat all members with respect. Harassment, hate speech, racism, or toxicity will result in an immediate strike or ban.\n\n"
                    "**2️⃣ Voice Channel Etiquette**\n"
                    "• Avoid mic spamming, ear-raping, or loud soundboards in public voice lounges.\n"
                    "• Respect duo/trio and squad channels.\n\n"
                    "**3️⃣ No Spamming or Phishing Links**\n"
                    "• Posting fake Nitro, scam steam links, or spamming text channels is strictly forbidden and auto-blocked.\n\n"
                    "**4️⃣ No Self-Promotion / Unsolicited DMs**\n"
                    "• Please do not send unsolicited Discord server invites in chat or members' DMs.\n\n"
                    "**5️⃣ Respect Staff & High Command**\n"
                    "• Follow instructions from the Staff and Guardian Team.\n\n"
                    "✨ *Enjoy your time, hop into a VC, and vibe with the family!* 🍿🎵"
                ),
                "color": 16738740,
                "thumbnail": {"url": ICON_URL},
                "footer": {"text": "RAI FAM 💗 • Safety & Guidelines", "icon_url": ICON_URL}
            }]
        }
        post_message(rules_id, rules_payload)

    # 2. Verification Gate in #✅・verify
    verify_id = get_chan("✅・verify", "1545502700840427702")
    if verify_id:
        verify_payload = {
            "embeds": [{
                "title": "🛡️ ⋆⋅ RAI FAM MEMBER VERIFICATION ⋅⋆ 🛡️",
                "description": (
                    "Welcome to **RAI FAM 💗**! 🍿🎵\n\n"
                    "To prevent spam bots and keep our community friendly, safe, and neat, "
                    "please click the **`[✅ Verify & Enter Community]`** button below to unlock all channels.\n\n"
                    "By clicking verify, you agree to follow our server rules & code of conduct."
                ),
                "color": 16738740,
                "thumbnail": {"url": ICON_URL},
                "footer": {"text": "Instant 1-Click Verification • RAI FAM💗", "icon_url": ICON_URL}
            }],
            "components": [{
                "type": 1,
                "components": [{
                    "type": 2,
                    "style": 3,
                    "label": "Verify & Enter Community",
                    "emoji": {"name": "✅"},
                    "custom_id": "verify_member_btn"
                }]
            }]
        }
        post_message(verify_id, verify_payload)

    # 3. Announcements in #📢・announcements
    ann_id = get_chan("📢・announcements", "1545502718792175646")
    if ann_id:
        ann_payload = {
            "embeds": [{
                "title": "🌸 ⋆⋅ WELCOME TO THE NEW RAI FAM 💗 ⋅⋆ 🌸",
                "description": (
                    "Welcome to the freshly upgraded **RAI FAM 💗** community!\n\n"
                    "**🚀 What's New & Available:**\n"
                    "• 🎙️ **Studio-Quality Bitrate (96 kbps)** across all voice lounges\n"
                    "• 🎮 **4-Player Squad Gaming Channels** (Free Fire, BGMI, Roblox)\n"
                    "• ➕ **Join-To-Create Dynamic Voice Rooms** (Spawn your own private lounge)\n"
                    "• 🎨 **Custom Name Colors & Roles** in <#1545502722739150898>\n"
                    "• 📻 **24/7 Lo-Fi & Tamil Nadu FM Radio**\n"
                    "• 🍿 **Cinema Lounge & YouTube Watch Together**\n\n"
                    "Grab your roles in <#1545502722739150898> and jump into voice! 💗✨"
                ),
                "color": 16738740,
                "thumbnail": {"url": ICON_URL},
                "footer": {"text": "RAI FAM 💗 • Official Server Announcement", "icon_url": ICON_URL}
            }]
        }
        post_message(ann_id, ann_payload)

    # 4. Support Ticket Panel in #🎫・ticket-support
    ticket_id = get_chan("🎫・ticket-support", "1545514505520545886")
    if ticket_id:
        ticket_payload = {
            "embeds": [{
                "title": "🎫 ⋆⋅ RAI FAM SUPPORT & HELP DESK ⋅⋆ 🎫",
                "description": (
                    "Need assistance from our staff team? Have a question or want to report an issue?\n\n"
                    "Click the **`[🎫 Open Support Ticket]`** button below to create a private, confidential channel with our Staff & High Command."
                ),
                "color": 16738740,
                "thumbnail": {"url": ICON_URL},
                "footer": {"text": "RAI FAM 💗 • Support Ticket Desk", "icon_url": ICON_URL}
            }],
            "components": [{
                "type": 1,
                "components": [{
                    "type": 2,
                    "style": 1,
                    "label": "Open Support Ticket",
                    "emoji": {"name": "🎫"},
                    "custom_id": "create_ticket_btn"
                }]
            }]
        }
        post_message(ticket_id, ticket_payload)

    # 5. Booster Lounge Welcome in #💎・booster-lounge
    booster_id = get_chan("💎・booster-lounge", "1545834933417672744")
    if booster_id:
        booster_payload = {
            "embeds": [{
                "title": "💎 ⋆⋅ RAI FAM VIP BOOSTER LOUNGE ⋅⋆ 💎",
                "description": (
                    "Welcome to the exclusive VIP lounge for our amazing **Server Boosters**! 🚀\n\n"
                    "**💎 Exclusive Booster Perks:**\n"
                    "• 👑 Custom Hoisted Booster Badge & Role\n"
                    "• 🚀 Access to private Booster Voice Lounge (`🚀 | BOOSTER LOUNGE`)\n"
                    "• 🎨 Exclusive VIP Color Roles\n"
                    "• 🎁 Special entry into Booster-only Giveaways & VIP Events\n\n"
                    "*Thank you so much for supporting and boosting RAI FAM!* 💗✨"
                ),
                "color": 15844367,
                "thumbnail": {"url": ICON_URL},
                "footer": {"text": "RAI FAM 💗 • VIP Booster Club", "icon_url": ICON_URL}
            }]
        }
        post_message(booster_id, booster_payload)

    # 6. Staff Command Center in #🛡️・staff-hq
    staff_id = get_chan("🛡️・staff-hq", "1545502845208629328")
    if staff_id:
        staff_payload = {
            "embeds": [{
                "title": "🛡️ ⋆⋅ STAFF & ADMIN COMMAND CENTER ⋅⋆ 🛡️",
                "description": (
                    "Welcome to the Staff Zone. Here is your quick command reference:\n\n"
                    "**🚨 Security & Voice Isolation:**\n"
                    "• `/freeze @user [mins] [reason]` • Isolate noisy/trolling member in Freeze Chamber + Timeout\n"
                    "• `/unfreeze @user` • Release member from Freeze Chamber and restore voice/chat\n"
                    "• `/lockdown` • Instantly lock all public channels during a raid\n"
                    "• `/unlock` • Restore chatting after lockdown\n"
                    "• `/clear <amount>` • Bulk purge up to 100 messages\n"
                    "• `/warn @user <reason>` • Issue official warning (Strike system)\n"
                    "• `/kick @user` & `/ban @user` • Moderation actions\n\n"
                    "**🎵 Music & Entertainment:**\n"
                    "• `/c` • Open Rythm-style interactive command directory\n"
                    "• `/play <song>` • Play high-fidelity audio\n"
                    "• `/radio` • Stream 24/7 live stations\n"
                    "• `/stay247` • Keep bot in voice channel 24/7\n"
                ),
                "color": 15844367,
                "footer": {"text": "RAI FAM 💗 • High Command System", "icon_url": ICON_URL}
            }]
        }
        post_message(staff_id, staff_payload)

    print("✨ Finished auto-filling all server templates & embeds!")

if __name__ == "__main__":
    main()
