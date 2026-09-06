import os
import sys
import json
import base64
import shutil
import urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'

IMG_PATH = r"C:\Users\kishore\.gemini\antigravity-ide\brain\fbd9983a-33ac-47d1-b10e-77a86d71c538\rai_fam_sakura_badge_1788681119344.jpg"
ASSET_DEST = r"F:\antigravity\APEX VIBES\assets\server_icon.jpg"

# Copy to assets
try:
    shutil.copyfile(IMG_PATH, ASSET_DEST)
    print("Saved logo to assets/server_icon.jpg")
except Exception as e:
    print(f"Copy note: {e}")

# Read and encode to base64
with open(IMG_PATH, "rb") as f:
    img_data = f.read()
    b64_str = base64.b64encode(img_data).decode('utf-8')
    data_uri = f"data:image/jpeg;base64,{b64_str}"

headers = {
    'Authorization': f'Bot {TOKEN}',
    'User-Agent': 'DiscordBot (LogoUpdate, 1.0)',
    'Content-Type': 'application/json'
}

req = urllib.request.Request(
    f'https://discord.com/api/v10/guilds/{GUILD_ID}',
    data=json.dumps({'icon': data_uri}).encode('utf-8'),
    headers=headers,
    method='PATCH'
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode('utf-8'))
        print("✅ Server icon updated to Concept 4 (Circular Metallic RF Badge)!")
        print(f"New Icon Hash: {res.get('icon')}")
except Exception as e:
    print(f"❌ Error updating icon: {e}")
