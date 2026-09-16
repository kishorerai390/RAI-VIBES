import os
import sys
import json
import base64
import urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'

headers = {
    'Authorization': f'Bot {TOKEN}',
    'User-Agent': 'DiscordBot (EmojiUpload, 1.0)',
    'Content-Type': 'application/json'
}

emojis_to_upload = [
    {
        "name": "rf_crown",
        "path": r"C:\Users\kishore\.gemini\antigravity-ide\brain\fbd9983a-33ac-47d1-b10e-77a86d71c538\rf_crown_emoji_1788682277146.jpg"
    },
    {
        "name": "rf_sakura",
        "path": r"C:\Users\kishore\.gemini\antigravity-ide\brain\fbd9983a-33ac-47d1-b10e-77a86d71c538\rf_sakura_emoji_1788682300349.jpg"
    },
    {
        "name": "rf_beats",
        "path": r"C:\Users\kishore\.gemini\antigravity-ide\brain\fbd9983a-33ac-47d1-b10e-77a86d71c538\rf_beats_emoji_1788682320652.jpg"
    },
    {
        "name": "rf_freefire",
        "path": r"C:\Users\kishore\.gemini\antigravity-ide\brain\fbd9983a-33ac-47d1-b10e-77a86d71c538\rf_freefire_emoji_1788682343548.jpg"
    }
]

for item in emojis_to_upload:
    name = item["name"]
    file_path = item["path"]
    if os.path.exists(file_path):
        with open(file_path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode('utf-8')
            data_uri = f"data:image/jpeg;base64,{b64_data}"
        
        req = urllib.request.Request(
            f'https://discord.com/api/v10/guilds/{GUILD_ID}/emojis',
            data=json.dumps({'name': name, 'image': data_uri}).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                print(f"✅ Uploaded custom emoji: :{name}: (ID: {data['id']})")
        except Exception as e:
            print(f"❌ Error uploading {name}: {e}")

print("Done uploading custom emojis!")
