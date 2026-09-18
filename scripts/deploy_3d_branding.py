import os
import sys
import shutil
import base64
import requests
from pathlib import Path
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

REPO_DIR = Path(__file__).resolve().parent.parent
ASSETS_DIR = REPO_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

BRAIN_DIR = Path(r"C:\Users\kishore\.gemini\antigravity-ide\brain\22c8bdd0-47bb-4906-8eb0-132a037ee268")

# Source files from artifact directory
FILES_MAP = {
    "VIBES": {
        "logo_src": BRAIN_DIR / "rai_vibes_3d_logo_1789750278862.jpg",
        "banner_src": BRAIN_DIR / "rai_vibes_3d_banner_1789750290783.jpg",
        "logo_dst": ASSETS_DIR / "rai_vibes_3d_logo.jpg",
        "banner_dst": ASSETS_DIR / "rai_vibes_3d_banner.jpg",
        "token": os.getenv("DISCORD_BOT_TOKEN"),
        "name": "RAI VIBES 💗"
    },
    "PLAY": {
        "logo_src": BRAIN_DIR / "rai_play_3d_logo_1789750312120.jpg",
        "banner_src": BRAIN_DIR / "rai_play_3d_banner_1789750325088.jpg",
        "logo_dst": ASSETS_DIR / "rai_play_3d_logo.jpg",
        "banner_dst": ASSETS_DIR / "rai_play_3d_banner.jpg",
        "token": os.getenv("COMMUNITY_BOT_TOKEN") or os.getenv("ARCADE_BOT_TOKEN"),
        "name": "RAI PLAY 🎮"
    },
    "SENTINEL": {
        "logo_src": BRAIN_DIR / "rai_sentinel_3d_logo_1789750345134.jpg",
        "banner_src": BRAIN_DIR / "rai_sentinel_3d_banner_1789750361433.jpg",
        "logo_dst": ASSETS_DIR / "rai_sentinel_3d_logo.jpg",
        "banner_dst": ASSETS_DIR / "rai_sentinel_3d_banner.jpg",
        "token": os.getenv("SECURITY_BOT_TOKEN"),
        "name": "RAI SENTINEL 🛡️"
    }
}

def to_data_uri(path: Path) -> str:
    with open(path, "rb") as f:
        b64 = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"

def deploy_bot_branding(key: str, cfg: dict):
    print(f"\n==========================================")
    print(f"  Deploying 3D Branding for: {cfg['name']}")
    print(f"==========================================")

    # 1. Copy files to assets
    if cfg["logo_src"].exists():
        shutil.copy2(cfg["logo_src"], cfg["logo_dst"])
        print(f"  📁 Copied 3D Logo to: {cfg['logo_dst'].name}")
    else:
        print(f"  ⚠️ Logo source not found: {cfg['logo_src']}")

    if cfg["banner_src"].exists():
        shutil.copy2(cfg["banner_src"], cfg["banner_dst"])
        print(f"  📁 Copied 3D Banner to: {cfg['banner_dst'].name}")
    else:
        print(f"  ⚠️ Banner source not found: {cfg['banner_src']}")

    token = cfg.get("token")
    if not token or token.startswith("YOUR_"):
        print(f"  ⚠️ No valid token found for {cfg['name']}. Skipping Discord API upload.")
        return

    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

    # 2. Upload Avatar (3D Logo)
    if cfg["logo_dst"].exists():
        print(f"  🚀 Uploading 3D Logo Avatar to Discord CDN...")
        avatar_uri = to_data_uri(cfg["logo_dst"])
        r = requests.patch("https://discord.com/api/v10/users/@me", headers=headers, json={"avatar": avatar_uri})
        if r.status_code == 200:
            data = r.json()
            print(f"  ✅ {cfg['name']} 3D Avatar updated successfully! (Avatar Hash: {data.get('avatar')})")
        else:
            print(f"  ⚠️ Avatar update note: {r.status_code} - {r.text[:150]}")

    # 3. Upload Banner (3D Banner)
    if cfg["banner_dst"].exists():
        print(f"  🚀 Uploading 3D Banner to Discord CDN...")
        banner_uri = to_data_uri(cfg["banner_dst"])
        r = requests.patch("https://discord.com/api/v10/users/@me", headers=headers, json={"banner": banner_uri})
        if r.status_code == 200:
            data = r.json()
            print(f"  ✅ {cfg['name']} 3D Banner updated successfully! (Banner Hash: {data.get('banner')})")
        else:
            print(f"  ⚠️ Banner update note: {r.status_code} - {r.text[:150]}")

if __name__ == "__main__":
    for k, v in FILES_MAP.items():
        deploy_bot_branding(k, v)
    print("\n🎉 3D Branding deployment process completed!")
