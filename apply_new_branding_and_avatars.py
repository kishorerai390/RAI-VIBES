import os
import sys
import base64
import shutil
import requests
from dotenv import load_dotenv
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Image paths from generation
GEN_VIBES_LOGO = r"C:\Users\kishore\.gemini\antigravity-ide\brain\f702fb63-3851-4c49-a66f-04de06a1d35b\rai_vibes_logo_new_1788712604558.jpg"
GEN_VIBES_BANNER = r"C:\Users\kishore\.gemini\antigravity-ide\brain\f702fb63-3851-4c49-a66f-04de06a1d35b\rai_vibes_banner_new_1788712796314.jpg"
GEN_SENTINEL_LOGO = r"C:\Users\kishore\.gemini\antigravity-ide\brain\f702fb63-3851-4c49-a66f-04de06a1d35b\rai_sentinel_logo_new_1788712815274.jpg"
GEN_SENTINEL_BANNER = r"C:\Users\kishore\.gemini\antigravity-ide\brain\f702fb63-3851-4c49-a66f-04de06a1d35b\rai_sentinel_banner_new_1788712837705.jpg"

DEST_VIBES_LOGO = ASSETS_DIR / "rai_vibes_bot_logo.jpg"
DEST_VIBES_BANNER = ASSETS_DIR / "rai_vibes_banner.jpg"
DEST_SENTINEL_LOGO = ASSETS_DIR / "rai_sentinel_logo.jpg"
DEST_SENTINEL_BANNER = ASSETS_DIR / "rai_sentinel_banner.jpg"

def copy_images():
    print("📁 Copying new high-res branding to assets directory...")
    for src, dst in [
        (GEN_VIBES_LOGO, DEST_VIBES_LOGO),
        (GEN_VIBES_BANNER, DEST_VIBES_BANNER),
        (GEN_SENTINEL_LOGO, DEST_SENTINEL_LOGO),
        (GEN_SENTINEL_BANNER, DEST_SENTINEL_BANNER),
    ]:
        if os.path.exists(src):
            shutil.copyfile(src, dst)
            print(f"  ✅ Saved: {dst.name}")
        else:
            print(f"  ⚠️ Not found: {src}")

def get_data_uri(file_path):
    with open(file_path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"

def update_discord_bot(token: str, bot_name: str, logo_path: Path, banner_path: Path):
    if not token or token.startswith("YOUR_"):
        print(f"⚠️ Skipping {bot_name}: Token not found in .env")
        return

    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

    # 1. Update Avatar
    if logo_path.exists():
        print(f"\n🚀 Updating Avatar for {bot_name}...")
        avatar_uri = get_data_uri(logo_path)
        payload = {"avatar": avatar_uri, "username": bot_name}
        r = requests.patch("https://discord.com/api/v10/users/@me", headers=headers, json=payload)
        if r.status_code == 200:
            print(f"  🎉 {bot_name} Avatar & Name updated successfully!")
        elif r.status_code == 400 and "username" in r.text.lower():
            # If username was changed recently, update avatar only
            r = requests.patch("https://discord.com/api/v10/users/@me", headers=headers, json={"avatar": avatar_uri})
            if r.status_code == 200:
                print(f"  🎉 {bot_name} Avatar updated successfully!")
            else:
                print(f"  ⚠️ Avatar update response: {r.status_code} {r.text}")
        else:
            print(f"  ⚠️ Avatar update response: {r.status_code} {r.text}")

    # 2. Update Banner
    if banner_path.exists():
        print(f"🚀 Updating Banner for {bot_name}...")
        banner_uri = get_data_uri(banner_path)
        r = requests.patch("https://discord.com/api/v10/users/@me", headers=headers, json={"banner": banner_uri})
        if r.status_code == 200:
            print(f"  🎉 {bot_name} Banner updated successfully!")
        else:
            print(f"  ⚠️ Banner update response: {r.status_code} {r.text}")

if __name__ == "__main__":
    copy_images()
    
    token_vibes = os.getenv("DISCORD_BOT_TOKEN")
    token_sentinel = os.getenv("SECURITY_BOT_TOKEN")
    
    update_discord_bot(token_vibes, "RAI VIBES", DEST_VIBES_LOGO, DEST_VIBES_BANNER)
    update_discord_bot(token_sentinel, "RAI SENTINEL", DEST_SENTINEL_LOGO, DEST_SENTINEL_BANNER)
    
    print("\n✨ All bot profile updates completed!")
