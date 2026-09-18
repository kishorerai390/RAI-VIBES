import sys
import os
sys.path.insert(0, os.path.abspath("."))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
import requests
import config
import json

headers = {
    "Authorization": f"Bot {config.DISCORD_TOKEN}",
    "Content-Type": "application/json"
}

# 1. Allow verified members to view verify channel so it never appears as "🔒 No Access"
# RAI FAM: verify channel 1545502700840427702, verified role 1549504522953695269
# Allow view channel (1024), deny send messages (2048) and add reactions (64)
res1 = requests.put(
    "https://discord.com/api/v10/channels/1545502700840427702/permissions/1549504522953695269",
    headers=headers,
    json={"allow": "1024", "deny": "2112", "type": 0}  # 2112 = 2048 (send) + 64 (react)
)
print("Updated RAI FAM verify permissions:", res1.status_code)

# ABIJITH 777: verify channel 1550205959991992471, verified role 1550205910218182696
res2 = requests.put(
    "https://discord.com/api/v10/channels/1550205959991992471/permissions/1550205910218182696",
    headers=headers,
    json={"allow": "1024", "deny": "2112", "type": 0}
)
print("Updated ABIJITH 777 verify permissions:", res2.status_code)

# 2. Fix the Role Codex embed in #🏷️｜ʀᴏʟᴇꜱ (1545502722739150898, msg 1550045460012605551)
codex_embed = {
    "title": "✦ RAI FAM • MINIMALIST ROLE CODEX ✦",
    "description": (
        "✦ ───────────────────────────────────── ✦\n\n"
        "**RAI FAM** embraces an **Ultra-Minimal Aesthetic**.\n"
        "No bloated cosmetic tags. No profile clutter. Just pure community status.\n\n"
        "### 👑 Hierarchy & Distinction:\n"
        "> • `✦ owner` — Server Visionary & Community Founder *(Immune Vault)*\n"
        "> • `✦ staff` — Security, Moderation & Sentinel Protection\n"
        "> • `✦ booster` — Honored Server Supporters *(Pink Hoisted Status)*\n"
        "> • `✦ member` — Official Verified Community Citizen\n"
        "> • `✦ dj` — Music Engine & Audio Studio Controller\n"
        "> • `✦ verified` — Security Gate Single-Click Clearance\n\n"
        "### 🏷️ How to Obtain Roles:\n"
        "> • **Verify**: Click the button in <#1545502700840427702> to claim `✦ member`.\n"
        "> • **DJ Pass**: Purchase `✦ dj` in <#1549416359723532480> using chat coins (`/shop`).\n"
        "> • **Booster**: Boost the server to automatically unlock `✦ booster`.\n\n"
        "✦ ───────────────────────────────────── ✦"
    ),
    "color": 16758968,
    "thumbnail": {
        "url": "https://cdn.discordapp.com/icons/1457382179981099090/be8713ee7410caf956268821a50c4c07.png?size=1024"
    },
    "footer": {
        "text": "RAI FAM 💗 • Ultra-Minimal Aesthetic Design",
        "icon_url": "https://cdn.discordapp.com/icons/1457382179981099090/be8713ee7410caf956268821a50c4c07.png?size=1024"
    }
}

edit_res = requests.patch(
    "https://discord.com/api/v10/channels/1545502722739150898/messages/1550045460012605551",
    headers=headers,
    json={"embeds": [codex_embed]}
)
print("Updated Roles Codex Message:", edit_res.status_code)

# 3. Fix #🌸｜ᴡᴇʟᴄᴏᴍᴇ message 1550213606615023667
welcome_embed = {
    "title": "🌸 RAI FAM💗 !",
    "description": (
        "**HEY BUDDY!** <@1413963142148391067>\n\n"
        "**Welcome To RAI FAM💗 !**\n"
        "**Get started with below:** <#1545502710101704714>\n\n"
        "**Follow The Server Guidelines:** <#1545502710101704714>\n\n"
        "**Verify For Full Access:** <#1545502700840427702>\n\n"
        "**Role Hierarchy & Codex:** <#1545502722739150898>\n\n"
        "**Commands & Perks:** <#1549416359723532480>\n\n"
        "**Gaming Hub & LFG:** <#1550187304876900543>\n\n"
        "**24/7 Lo-Fi & Beats:** <#1550186760779211003>\n\n"
        "**Join And Chill With Us!:** <#1545502730699808768>\n\n"
        "**Thanks For Joining. Hope You Have A Great Time Here!**"
    ),
    "color": 16738740,
    "thumbnail": {
        "url": "https://cdn.discordapp.com/avatars/1413963142148391067/d46b6968d43a716e1ea0bb77442872d8.png?size=1024"
    },
    "footer": {
        "text": "Member #31 • RAI FAM Luxury Community 💗",
        "icon_url": "https://cdn.discordapp.com/icons/1457382179981099090/be8713ee7410caf956268821a50c4c07.png?size=1024"
    }
}

edit_res2 = requests.patch(
    "https://discord.com/api/v10/channels/1545502705643167876/messages/1550213606615023667",
    headers=headers,
    json={"embeds": [welcome_embed]}
)
print("Updated Welcome Message:", edit_res2.status_code)

# 4. Fix #📜｜ʀᴜʟᴇꜱ-ᴀɴᴅ-ɪɴꜰᴏ message 1549117082078158969
rules_embed = {
    "title": "📜 ✦ RAI FAM • SERVER CODEX & COMMUNITY RULES ✦ 📜",
    "description": (
        "✦ ───────────────────────────── ✦\n\n"
        "Welcome to **RAI FAM 💗**! To preserve a luxury, relaxed, and toxicity-free atmosphere, all members and guests are held to the following operational standards:\n\n"
        "### 🌸 1. Respect & Wholesome Conduct\n"
        "> • Treat all members with courtesy and kindness. Zero tolerance for hate speech, harassment, slurs, discrimination, or targeted toxicity.\n"
        "> • Keep debates civilized. Sarcasm and playful banter are welcome, but personal attacks or passive aggression will result in moderation action.\n\n"
        "### 🔊 2. Voice Lounge Etiquette\n"
        "> • Mic-spamming, ear-raping, or loud soundboard abuse in public lounges is prohibited.\n"
        "> • Respect squad capacity limits in gaming rooms (BGMI, Free Fire).\n"
        "> • Use <#1550187298115551272> when stepping away from your keyboard.\n\n"
        "### 🛡️ 3. Anti-Scam & Security Integrity\n"
        "> • Posting fake Discord Nitro links, malicious downloads, or Steam scam links triggers an immediate permanent ban by Sentinel.\n"
        "> • Unsolicited advertising or mass DM advertising to members is strictly forbidden.\n\n"
        "### ⚙️ 4. Channel Discipline\n"
        "> • Keep music commands inside <#1549416359723532480>.\n"
        "> • Post chat discussions and media in <#1545502730699808768>.\n"
        "> • For assistance or inquiries, open a ticket in <#1545514505520545886>.\n\n"
        "### ⚖️ 5. Enforcement & Staff Authority\n"
        "> • Staff decisions are final. If you have an inquiry, respectfully contact staff via private ticket.\n\n"
        "✦ ───────────────────────────── ✦\n"
        "✨ *Enjoy high-fidelity sound, lock in with your squad, and vibe with the family!* 🌸"
    ),
    "color": 16758968,
    "thumbnail": {
        "url": "https://cdn.discordapp.com/icons/1457382179981099090/be8713ee7410caf956268821a50c4c07.png?size=1024"
    },
    "footer": {
        "text": "RAI FAM 💗 • Security & Community Directives",
        "icon_url": "https://cdn.discordapp.com/icons/1457382179981099090/be8713ee7410caf956268821a50c4c07.png?size=1024"
    }
}

edit_res3 = requests.patch(
    "https://discord.com/api/v10/channels/1545502710101704714/messages/1549117082078158969",
    headers=headers,
    json={"embeds": [rules_embed]}
)
print("Updated Rules Message:", edit_res3.status_code)
