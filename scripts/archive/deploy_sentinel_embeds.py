import os
import sys
import json
import urllib.request
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(r"f:\antigravity\APEX VIBES")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('SECURITY_BOT_TOKEN')
GUILD_ID = '1457382179981099090'
TICKET_CHAN_ID = '1545514505520545886'
VERIFY_CHAN_ID = '1545502700840427702'

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'SentinelBot (Deploy, 1.0)', 'Content-Type': 'application/json'}

# 1. Clean #🎫・ticket-support
try:
    req = urllib.request.Request(f'https://discord.com/api/v10/channels/{TICKET_CHAN_ID}/messages?limit=20', headers=headers)
    with urllib.request.urlopen(req) as resp:
        msgs = json.loads(resp.read().decode('utf-8'))
    for m in msgs:
        dreq = urllib.request.Request(f"https://discord.com/api/v10/channels/{TICKET_CHAN_ID}/messages/{m['id']}", headers=headers, method='DELETE')
        try:
            with urllib.request.urlopen(dreq) as dresp:
                pass
        except Exception:
            pass
    print("Ticket channel cleaned!")
except Exception as e:
    print(f"Ticket clean note: {e}")

# 2. Clean #✅・verify
try:
    req = urllib.request.Request(f'https://discord.com/api/v10/channels/{VERIFY_CHAN_ID}/messages?limit=20', headers=headers)
    with urllib.request.urlopen(req) as resp:
        msgs = json.loads(resp.read().decode('utf-8'))
    for m in msgs:
        dreq = urllib.request.Request(f"https://discord.com/api/v10/channels/{VERIFY_CHAN_ID}/messages/{m['id']}", headers=headers, method='DELETE')
        try:
            with urllib.request.urlopen(dreq) as dresp:
                pass
        except Exception:
            pass
    print("Verify channel cleaned!")
except Exception as e:
    print(f"Verify clean note: {e}")

# 3. Post using discord.py to bind TicketCreateView & VerifyButtonView
import discord
import asyncio
from utils.persistent_views import TicketCreateView, VerifyButtonView

intents = discord.Intents.default()
intents.guilds = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    DIVIDER = "<a:w_welc1:1547271923891707915><:w_dash:1547271874981920868><:w_dash:1547271874981920868><:w_dash:1547271874981920868><:w_dash:1547271874981920868><a:w_welc2:1547271930699190424>"
    
    # Post Verification Gate
    vchan = client.get_channel(int(VERIFY_CHAN_ID))
    if vchan:
        embed_v = discord.Embed(
            title="<a:sparkle_love:1547271978883350568> ✦ RAI FAM • OFFICIAL MEMBER VERIFICATION ✦ <a:sparkle_love:1547271978883350568>",
            description=(
                f"{DIVIDER}\n\n"
                "Welcome to **RAI FAM 💗** — High Fidelity Audio & Cyber Sanctuary!\n\n"
                "To prevent automated spam accounts and keep our lounges friendly and secure, "
                "please complete 1-click verification to unlock all channels & dynamic voice lounges:\n\n"
                "<:badge_1:1547271940279107665> **Read Guidelines** • Agree to Discord TOS & Server Rules in <#1545502710101704714>\n"
                "<:badge_2:1547271946645934122> **Click Button** • Tap **`[ ✅ Verify & Enter Community ]`** below\n"
                "<:badge_3:1547271951297413281> **Unlock Everything** • Instantly access chats, music lounges & gaming hubs!\n\n"
                f"{DIVIDER}\n"
                "*Need help? Contact staff via <#1545514505520545886>.*"
            ),
            color=0xFF2A85
        )
        embed_v.set_thumbnail(url=vchan.guild.icon.url if vchan.guild.icon else None)
        embed_v.set_footer(text="RAI SENTINEL 🛡️ • Instant 1-Click Verification Gate", icon_url=vchan.guild.icon.url if vchan.guild.icon else None)
        await vchan.send(embed=embed_v, view=VerifyButtonView())
        print("✅ Verification Gate posted by RAI SENTINEL with EVERGLOW-style aesthetic dividers!")

    # Post Support Ticket Hub
    tchan = client.get_channel(int(TICKET_CHAN_ID))
    if tchan:
        embed_t = discord.Embed(
            title="<a:pinkflame:1547271954841731193> ✦ RAI FAM • OFFICIAL SUPPORT DESK ✦ <a:pinkflame:1547271954841731193>",
            description=(
                f"{DIVIDER}\n\n"
                "Need direct assistance from server leadership or moderators?\n\n"
                "• <a:pixel_heart:1547271960336146563> **Staff Inquiries & Reports**\n"
                "• <a:pixel_heart:1547271960336146563> **Role & Permission Assistance**\n"
                "• <a:pixel_heart:1547271960336146563> **Partnerships & Event Inquiries**\n"
                "• <a:pixel_heart:1547271960336146563> **Private Support Dispatch**\n\n"
                f"{DIVIDER}\n\n"
                "Click **`[ 📩 Open Support Ticket ]`** below to create an instant private channel with our staff team!"
            ),
            color=0x8B5CF6
        )
        embed_t.set_thumbnail(url=tchan.guild.icon.url if tchan.guild.icon else None)
        embed_t.set_footer(text="RAI SENTINEL 🛡️ • 24/7 Fast Ticket Dispatch", icon_url=tchan.guild.icon.url if tchan.guild.icon else None)
        await tchan.send(embed=embed_t, view=TicketCreateView())
        print("✅ Support Ticket Hub posted by RAI SENTINEL with EVERGLOW-style aesthetic dividers!")

    await client.close()

asyncio.run(client.start(TOKEN))
