import os
import sys
import base64
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")

IMAGE_PATH = r"C:\Users\kishore\.gemini\antigravity-ide\brain\d9e61b2a-2cbb-4a9e-9232-4b96a2ab14b4\rai_vibes_icon_1788612200651.jpg"
ASSET_DEST = os.path.join(os.path.dirname(__file__), "assets", "rai_vibes_bot_logo.jpg")

# Copy to assets folder
if os.path.exists(IMAGE_PATH):
    with open(IMAGE_PATH, "rb") as src, open(ASSET_DEST, "wb") as dst:
        dst.write(src.read())
    print(f"✅ Saved bot avatar to {ASSET_DEST}")

def update_avatar():
    with open(ASSET_DEST, "rb") as f:
        img_bytes = f.read()
    b64_str = base64.b64encode(img_bytes).decode('utf-8')
    data_uri = f"data:image/jpeg;base64,{b64_str}"

    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "avatar": data_uri,
        "username": "RAI VIBES"
    }

    r = requests.patch("https://discord.com/api/v10/users/@me", headers=headers, json=payload)
    if r.status_code == 200:
        print("🎉 Bot Avatar & Username successfully updated to RAI VIBES!")
    elif r.status_code == 400 and "username" in r.text.lower():
        # Avatar only if username changed too frequently
        r = requests.patch("https://discord.com/api/v10/users/@me", headers=headers, json={"avatar": data_uri})
        if r.status_code == 200:
            print("🎉 Bot Avatar successfully updated to RAI VIBES Logo!")
        else:
            print(f"Avatar update status: {r.status_code} {r.text}")
    else:
        print(f"Update response: {r.status_code} {r.text}")

if __name__ == "__main__":
    update_avatar()
