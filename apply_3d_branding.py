import os
import sys
import base64
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

MUSIC_TOKEN = os.getenv("DISCORD_BOT_TOKEN", "").strip()
SECURITY_TOKEN = os.getenv("SECURITY_BOT_TOKEN", "").strip()
GUILD_ID = "1457382179981099090"

ARTIFACTS_DIR = r"C:\Users\kishore\.gemini\antigravity-ide\brain\d5e02457-f917-450f-a531-1a44a32f2ee8"

AURA_LOGO = os.path.join(ARTIFACTS_DIR, "aura_music_3d_logo_1789409403134.jpg")
AURA_BANNER = os.path.join(ARTIFACTS_DIR, "aura_music_3d_banner_1789409503672.jpg")

AEGIS_LOGO = os.path.join(ARTIFACTS_DIR, "aegis_security_3d_logo_1789409568702.jpg")
AEGIS_BANNER = os.path.join(ARTIFACTS_DIR, "aegis_security_3d_banner_1789409619625.jpg")

def to_base64_data_uri(filepath):
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return None
    with open(filepath, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{encoded}"

def update_bot_profile(bot_label, token, logo_path, banner_path, guild_nick):
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }

    # 1. Update Profile (Avatar & Banner)
    avatar_uri = to_base64_data_uri(logo_path)
    banner_uri = to_base64_data_uri(banner_path)
    
    payload = {}
    if avatar_uri:
        payload["avatar"] = avatar_uri
    if banner_uri:
        payload["banner"] = banner_uri
        
    print(f"\n[{bot_label}] Updating global avatar and banner...")
    resp = requests.patch("https://discord.com/api/v10/users/@me", headers=headers, json=payload)
    if resp.status_code in [200, 204]:
        data = resp.json()
        print(f"[{bot_label}] ✅ Successfully updated global profile! User: {data.get('username')}#{data.get('discriminator')}")
    else:
        print(f"[{bot_label}] ⚠️ Profile update status {resp.status_code}: {resp.text}")

    # 2. Update Guild Nickname
    print(f"[{bot_label}] Setting guild nickname to: '{guild_nick}'...")
    nick_resp = requests.patch(
        f"https://discord.com/api/v10/guilds/{GUILD_ID}/members/@me",
        headers=headers,
        json={"nick": guild_nick}
    )
    if nick_resp.status_code in [200, 204]:
        print(f"[{bot_label}] ✅ Successfully updated guild nickname to '{guild_nick}'!")
    else:
        print(f"[{bot_label}] ⚠️ Guild nick status {nick_resp.status_code}: {nick_resp.text}")

if __name__ == "__main__":
    print("=== APPLYING 3D LOGOS, BANNERS, AND NICKNAMES ===")
    
    # 1. AURA ✦ (Music Bot)
    update_bot_profile(
        bot_label="AURA ✦ (Music)",
        token=MUSIC_TOKEN,
        logo_path=AURA_LOGO,
        banner_path=AURA_BANNER,
        guild_nick="AURA ✦"
    )
    
    # 2. AEGIS 🛡️ (Security Bot)
    update_bot_profile(
        bot_label="AEGIS 🛡️ (Security)",
        token=SECURITY_TOKEN,
        logo_path=AEGIS_LOGO,
        banner_path=AEGIS_BANNER,
        guild_nick="AEGIS 🛡️"
    )
    print("\n=== BRANDING UPDATE COMPLETE ===")
