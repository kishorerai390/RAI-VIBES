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

IMAGE_PATH = r"C:\Users\kishore\.gemini\antigravity-ide\brain\d9e61b2a-2cbb-4a9e-9232-4b96a2ab14b4\rai_vibes_banner_1788612384013.jpg"
ASSET_DEST = os.path.join(os.path.dirname(__file__), "assets", "rai_vibes_banner.jpg")
SERVER_BANNER_DEST = os.path.join(os.path.dirname(__file__), "assets", "server_banner.jpg")

# Copy to assets folder
if os.path.exists(IMAGE_PATH):
    with open(IMAGE_PATH, "rb") as src:
        data = src.read()
    with open(ASSET_DEST, "wb") as dst:
        dst.write(data)
    with open(SERVER_BANNER_DEST, "wb") as dst:
        dst.write(data)
    print(f"✅ Saved banner to {ASSET_DEST}")

def update_discord_banners():
    with open(ASSET_DEST, "rb") as f:
        img_bytes = f.read()
    b64_str = base64.b64encode(img_bytes).decode('utf-8')
    data_uri = f"data:image/jpeg;base64,{b64_str}"

    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }

    # 1. Update Bot User Profile Banner
    r_bot = requests.patch("https://discord.com/api/v10/users/@me", headers=headers, json={"banner": data_uri})
    if r_bot.status_code == 200:
        print("🎉 Bot User Banner successfully updated!")
    else:
        print(f"Bot user banner update: {r_bot.status_code} {r_bot.text}")

    # 2. Update Guild / Server Banner
    r_guild = requests.patch(f"https://discord.com/api/v10/guilds/{GUILD_ID}", headers=headers, json={"banner": data_uri})
    if r_guild.status_code == 200:
        print("🎉 Server Banner successfully updated!")
    else:
        print(f"Server banner response (may require Server Boost Level 2): {r_guild.status_code} {r_guild.text}")

if __name__ == "__main__":
    update_discord_banners()
