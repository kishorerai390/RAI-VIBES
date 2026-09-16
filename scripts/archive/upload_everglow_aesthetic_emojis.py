import os
import sys
import json
import base64
import urllib.request
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"

headers = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "DiscordBot (AestheticEmojiImporter, 1.0)"
}

EMOJIS_TO_IMPORT = [
    # Continuous Dividers
    {"name": "w_welc1", "id": "1546438659149004851", "animated": True},
    {"name": "w_welc2", "id": "1546438680451747961", "animated": True},
    
    # Badges
    {"name": "badge_1", "id": "1546438346404925490", "animated": False},
    {"name": "badge_2", "id": "1546438372896018493", "animated": False},
    {"name": "badge_3", "id": "1546438393464881322", "animated": False},
    
    # Aesthetic Animated Flames & Hearts
    {"name": "pinkflame", "id": "1538516860205801524", "animated": True},
    {"name": "pixel_heart", "id": "1538532344242114580", "animated": True},
    {"name": "heart_fire", "id": "1538532846233325689", "animated": True},
    {"name": "chanstar", "id": "1538516294297456791", "animated": True},
    {"name": "sparkle_love", "id": "1538515735859699824", "animated": True},
    {"name": "cyber_card", "id": "1538532779992686672", "animated": True},
    {"name": "arrow_color", "id": "1538532886557237359", "animated": True},
]

uploaded = {}

for item in EMOJIS_TO_IMPORT:
    name = item["name"]
    ext = "gif" if item["animated"] else "png"
    mime = "image/gif" if item["animated"] else "image/png"
    url = f"https://cdn.discordapp.com/emojis/{item['id']}.{ext}"
    
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as resp:
            data = resp.read()
            
        b64 = base64.b64encode(data).decode("utf-8")
        data_uri = f"data:{mime};base64,{b64}"
        
        post_req = urllib.request.Request(
            f"https://discord.com/api/v10/guilds/{GUILD_ID}/emojis",
            data=json.dumps({"name": name, "image": data_uri}).encode("utf-8"),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(post_req) as post_resp:
            res = json.loads(post_resp.read().decode("utf-8"))
            print(f"✅ Uploaded :{name}: -> <{'a:' if item['animated'] else ':'}{res['name']}:{res['id']}>")
            uploaded[name] = res
    except urllib.error.HTTPError as e:
        msg = e.read().decode("utf-8", errors="ignore")
        print(f"❌ Error uploading {name}: HTTP {e.code} - {msg}")
    except Exception as e:
        print(f"❌ Error uploading {name}: {e}")

with open(r"f:\antigravity\APEX VIBES\scratch\uploaded_aesthetic_emojis.json", "w", encoding="utf-8") as f:
    json.dump(uploaded, f, indent=2)

print("\n🎉 Aesthetic emoji pack import complete!")
