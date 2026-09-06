import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from project root
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# Discord Configuration
DISCORD_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
BOT_PREFIX = os.getenv("BOT_PREFIX", "!")
BOT_NAME = "RAI VIBES 💗"
BOT_TAGLINE = "Chill Music • Cinema Lounge • Infinite Vibes"

# Spotify Configuration (Optional - works even without API keys via public meta resolver)
SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()

# Default Settings
DEFAULT_VOLUME = int(os.getenv("DEFAULT_VOLUME", "80"))  # 0 to 100
INACTIVITY_TIMEOUT = int(os.getenv("INACTIVITY_TIMEOUT", "300"))  # Seconds before auto-leave when empty
MAX_QUEUE_SIZE = int(os.getenv("MAX_QUEUE_SIZE", "200"))  # Capacity of 200 songs in queue

# FFmpeg Path (Automatic resolution)
CUSTOM_FFMPEG_PATH = os.getenv("FFMPEG_PATH", "").strip()

# Embed Colors (RAI VIBES Theme - Sakura Pink, Royal Purple & Gold)
COLOR_PRIMARY = 0xFF69B4     # Hot Pink / Rose
COLOR_SECONDARY = 0x9B59B6   # Royal Purple
COLOR_GOLD = 0xF1C40F        # Radiant Gold
COLOR_SUCCESS = 0x2ECC71     # Emerald Green
COLOR_WARNING = 0xE67E22     # Amber Orange
COLOR_ERROR = 0xE74C3C       # Crimson Red
COLOR_DARK = 0x18191C        # Midnight Dark

# Assets & Icons
RAI_ICON_URL = "https://cdn.discordapp.com/avatars/1545479610550980709/4176f6e6e76161728a4314c87c41fdd7.png?size=512"
YOUTUBE_ICON_URL = "https://cdn-icons-png.flaticon.com/512/1384/1384060.png"
SPOTIFY_ICON_URL = "https://cdn-icons-png.flaticon.com/512/2111/2111624.png"
MUSIC_ICON_URL = "https://cdn.discordapp.com/avatars/1545479610550980709/4176f6e6e76161728a4314c87c41fdd7.png?size=512"
