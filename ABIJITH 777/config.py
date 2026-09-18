import os
from pathlib import Path
from dotenv import load_dotenv

# Load root .env
ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1428058914141900860  # ABIJITH 777
GUILD_NAME = "ABIJITH 777"

# Color Palette (Emerald Green, Royal Gold & Deep Obsidian)
COLOR_EMERALD = 0x2ECC71
COLOR_GOLD = 0xF1C40F
COLOR_CYAN = 0x00E5FF
COLOR_DARK = 0x1A1B1E
COLOR_RED = 0xE74C3C

# Known Staff & Verification Roles in ABIJITH 777
ROLE_IDS = {
    "founder": 1550205899069726810,       # 👑 ┆ 𝐅𝐎𝐔𝐍𝐃𝐄𝐑 🍷
    "head_admin": 1550205902706049214,    # ⚡ ┆ 𝐇𝐄𝐀𝐃 𝐀𝐃𝐌𝐈𝐍 ⚡
    "moderator": 1550205905830682795,     # 🛡️ ┆ 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐎𝐑 🛡️
    "verified": 1550205910218182696,      # ✦ ᴠᴇʀɪꜰɪᴇᴅ
    "member": 1550205915398152364,        # @✦ MEMBER
}

def to_sans_regular(text: str) -> str:
    """Convert standard uppercase/lowercase ASCII letters to Mathematical Sans Regular capitals."""
    out = []
    for c in text:
        if 'A' <= c <= 'Z':
            out.append(chr(ord(c) - ord('A') + 0x1D5A0))
        elif 'a' <= c <= 'z':
            out.append(chr(ord(c) - ord('a') + 0x1D5A0))
        else:
            out.append(c)
    return ''.join(out)

# Channel Layout & Styling for VIP & SENTINEL HQ
CHANNELS_VIP_SENTINEL = {
    "category": "VIP & SENTINEL HQ",
    "text": [
        (f"｜・{to_sans_regular('EXECUTIVE-LOUNGE')}", "Private executive council & leadership lounge"),
        (f"｜・{to_sans_regular('STAFF-OPERATIONS')}", "Staff moderation directives, case discussions & commands"),
        (f"｜・{to_sans_regular('AUDIT-LOGS')}", "Discord server audit events and administrative records"),
        (f"｜・{to_sans_regular('TICKET-SUPPORT')}", "Official Member Support & Ticket Help Desk"),
        (f"｜・{to_sans_regular('MODERATION-LOGS')}", "Automated record of strikes, mutes, kicks and bans"),
        (f"｜・{to_sans_regular('SENTINEL-LOGS')}", "Automated security telemetry, anti-raid, anti-spam and anti-nuke alerts"),
    ],
    "voice": [
        ("| • EXECUTIVE SUITE", 10),
    ]
}
