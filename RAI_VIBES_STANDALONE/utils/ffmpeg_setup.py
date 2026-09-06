import os
import sys
import shutil
import zipfile
import urllib.request
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set UTF-8 encoding for console output on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from config import BASE_DIR, CUSTOM_FFMPEG_PATH

BIN_DIR = BASE_DIR / "bin"
FFMPEG_EXE = BIN_DIR / "ffmpeg.exe"

def get_ffmpeg_executable() -> str:
    """
    Finds ffmpeg executable:
    1. Custom path in config / .env if provided
    2. Local project bin/ directory
    3. System PATH
    4. Downloads standalone static build on Windows if missing
    """
    # 1. Custom Path
    if CUSTOM_FFMPEG_PATH and Path(CUSTOM_FFMPEG_PATH).exists():
        return CUSTOM_FFMPEG_PATH

    # 2. Project bin/ directory
    if FFMPEG_EXE.exists():
        return str(FFMPEG_EXE)

    # 3. Check System PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    # 4. Check if Windows and can auto-download
    if os.name == "nt":
        print("[RAI VIBES 💗] ffmpeg not found in PATH. Checking bin directory...")
        return ensure_ffmpeg_windows()

    return "ffmpeg"

def ensure_ffmpeg_windows() -> str:
    """Downloads a minimal static build of ffmpeg.exe if not present."""
    BIN_DIR.mkdir(parents=True, exist_ok=True)
    if FFMPEG_EXE.exists():
        return str(FFMPEG_EXE)

    print("[RAI VIBES 💗] Downloading static FFmpeg for Windows (one-time setup)...")
    url = "https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
    zip_path = BIN_DIR / "ffmpeg.zip"

    try:
        urllib.request.urlretrieve(url, zip_path)
        print("[RAI VIBES 💗] Extracting ffmpeg.exe...")
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            for file_info in zip_ref.infolist():
                if file_info.filename.endswith("ffmpeg.exe"):
                    file_info.filename = "ffmpeg.exe"
                    zip_ref.extract(file_info, BIN_DIR)
                    break
        if zip_path.exists():
            zip_path.unlink()
        print("[RAI VIBES 💗] FFmpeg successfully configured at:", FFMPEG_EXE)
        return str(FFMPEG_EXE)
    except Exception as e:
        print(f"[RAI VIBES 💗] Automatic FFmpeg download failed: {e}")
        print("[RAI VIBES 💗] Please install ffmpeg or place ffmpeg.exe in the 'bin/' directory.")
        return "ffmpeg"

if __name__ == "__main__":
    path = get_ffmpeg_executable()
    print(f"FFmpeg ready: {path}")
