import os
import sys
import base64
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"

HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

def main():
    print("🎨 Applying Cyber-Pink Server Theme (Icon & Banner)...")
    
    icon_path = r"C:\Users\kishore\.gemini\antigravity-ide\brain\d9e61b2a-2cbb-4a9e-9232-4b96a2ab14b4\rai_fam_cyber_pink_icon_1788617159940.jpg"
    banner_path = r"C:\Users\kishore\.gemini\antigravity-ide\brain\d9e61b2a-2cbb-4a9e-9232-4b96a2ab14b4\rai_fam_cyber_pink_banner_1788617181706.jpg"

    # Copy to project assets
    import shutil
    shutil.copy(icon_path, "assets/server_icon.jpg")
    shutil.copy(banner_path, "assets/server_banner.jpg")
    print("  Saved copies to assets/server_icon.jpg and assets/server_banner.jpg")

    with open("assets/server_icon.jpg", "rb") as f:
        icon_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"
    
    with open("assets/server_banner.jpg", "rb") as f:
        banner_b64 = f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode('utf-8')}"

    payload = {
        "icon": icon_b64,
        "banner": banner_b64,
        "description": "🌸 Welcome to RAI FAM 💗 • High Fidelity Audio & Cyber Sanctuary"
    }

    r = requests.patch(f"https://discord.com/api/v10/guilds/{GUILD_ID}", headers=HEADERS, json=payload)
    print(f"Guild update response: [{r.status_code}]")
    if r.status_code in [200, 204]:
        print("✅ Server Icon & Banner updated successfully!")
    else:
        # If server level doesn't support banner, update icon alone
        print(f"Response: {r.text}")
        payload_icon_only = {"icon": icon_b64}
        r2 = requests.patch(f"https://discord.com/api/v10/guilds/{GUILD_ID}", headers=HEADERS, json=payload_icon_only)
        print(f"Icon-only update response: [{r2.status_code}]")

if __name__ == "__main__":
    main()
