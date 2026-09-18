import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Ensure UTF-8 output encoding for Windows terminals
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BASE_DIR.parent
load_dotenv(PROJECT_ROOT / ".env")

DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
TARGET_GUILD_ID = int(os.getenv("TARGET_GUILD_ID", "1457382179981099090"))

# Colors (Hex integer)
COLOR_PRIMARY = 0x1E90FF     # Lightning Blue
COLOR_GOLD = 0xF5C518        # Nordic Gold
COLOR_SUCCESS = 0x2ECC71     # Emerald
COLOR_DARK = 0x1B1F2A        # Asgard Night
COLOR_PURPLE = 0x9B59B6
COLOR_RED = 0xE74C3C

SERVER_NAME = "⚡ APEX COMMUNITY & MUSIC ⚡"
BANNER_URL = "https://raw.githubusercontent.com/discord-bot-assets/thor-vibes/main/thor_banner.png"
RAI_ICON_URL = "https://raw.githubusercontent.com/discord-bot-assets/thor-vibes/main/thor_icon.png"
