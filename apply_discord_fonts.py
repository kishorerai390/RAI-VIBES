import os
import sys
import time
import json
import urllib.request
import urllib.error
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = os.getenv("GUILD_ID", "1457382179981099090")

HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json",
    "User-Agent": "DiscordBot (FontUpdate, 1.0)"
}

SMALL_CAPS_MAP = {
    'a': 'ᴀ', 'b': 'ʙ', 'c': 'ᴄ', 'd': 'ᴅ', 'e': 'ᴇ', 'f': 'ꜰ', 'g': 'ɢ',
    'h': 'ʜ', 'i': 'ɪ', 'j': 'ᴊ', 'k': 'ᴋ', 'l': 'ʟ', 'm': 'ᴍ', 'n': 'ɴ',
    'o': 'ᴏ', 'p': 'ᴘ', 'q': 'ǫ', 'r': 'ʀ', 's': 'ꜱ', 't': 'ᴛ', 'u': 'ᴜ',
    'v': 'ᴠ', 'w': 'ᴡ', 'x': 'x', 'y': 'ʏ', 'z': 'ᴢ'
}

def to_small_caps(text: str) -> str:
    return "".join(SMALL_CAPS_MAP.get(c, c) for c in text.lower())

CHANNELS_AESTHETIC_FONTS = {
    # Information
    "1545502718792175646": "📢・ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛꜱ",
    "1545502705643167876": "🌸・ᴡᴇʟᴄᴏᴍᴇ-ꜱᴀɴᴄᴛᴜᴀʀʏ",
    "1545502710101704714": "📜・ᴅɪᴠɪɴᴇ-ᴄᴏᴅᴇx",
    "1545502700840427702": "✨・ᴠᴇʀɪꜰʏ-ʜᴇʀᴇ",
    "1545502722739150898": "🎀・ᴘɪᴄᴋ-ʀᴏʟᴇꜱ",
    "1546125872661012611": "🧭・ꜱᴇʀᴠᴇʀ-ɢᴜɪᴅᴇ",
    "1547279073217351782": "🤝・ᴘᴀʀᴛɴᴇʀꜱʜɪᴘꜱ",
    "1546122222329008199": "👋・ɢᴏᴏᴅʙʏᴇꜱ",

    # The Lounge
    "1545502730699808768": "💬・ɢᴇɴᴇʀᴀʟ-ᴄʜᴀᴛ",
    "1546097792915873842": "📸・ᴍᴇᴅɪᴀ-ɢᴀʟʟᴇʀʏ",
    "1549489880776839248": "💡・ꜱᴜɢɢᴇꜱᴛɪᴏɴꜱ",
    "1545834933417672744": "💎・ᴠɪᴘ-ʟᴏᴜɴɢᴇ",
    "1549407114861215815": "⭐・ʜᴀʟʟ-ᴏꜰ-ꜰᴀᴍᴇ",
    "1549416359723532480": "🤖・ʙᴏᴛ-ᴄᴏᴍᴍᴀɴᴅꜱ",
    "1549439621497102518": "🛒・ꜱᴇʀᴠᴇʀ-ꜱʜᴏᴘ",
    "1549439624936554658": "🎁・ʀᴇᴡᴀʀᴅ-ᴇxᴄʜᴀɴɢᴇ",

    # Music & Gaming
    "1545534637122527332": "🎵・ꜱᴏɴɢ-ʀᴇǫᴜᴇꜱᴛꜱ",
    "1545803554550190212": "🎮・ɢᴀᴍɪɴɢ-ʜᴜʙ",

    # Executive & Staff
    "1545518535827263519": "👑・ᴇxᴇᴄᴜᴛɪᴠᴇ-ᴄʜᴀᴛ",
    "1545502845208629328": "🛡️・ꜱᴛᴀꜰꜰ-ʜǫ",
    "1545514505520545886": "🎫・ᴛɪᴄᴋᴇᴛ-ꜱᴜᴘᴘᴏʀᴛ",
    "1545502850057244762": "📋・ᴀᴜᴅɪᴛ-ʟᴏɢꜱ",
    "1546540192343523399": "📝・ᴍᴏᴅᴇʀᴀᴛɪᴏɴ-ʟᴏɢꜱ",
    "1546593526073135107": "🚨・ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ",
    "1547294258074226758": "🔒・ꜱᴇᴄᴜʀɪᴛʏ-ᴛᴇʀᴍɪɴᴀʟ",

    # Stats Voice Channels
    "1546099701496029194": "👥 ┊ ᴀʟʟ ᴍᴇᴍʙᴇʀꜱ: 32",
    "1546099703630798848": "👤 ┊ ᴍᴇᴍʙᴇʀꜱ: 18",
    "1546059375574130769": "🤖 ┊ ʙᴏᴛꜱ: 14"
}

def update_channel(cid, new_name):
    url = f"https://discord.com/api/v10/channels/{cid}"
    data = json.dumps({"name": new_name}).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=HEADERS, method="PATCH")
    try:
        with urllib.request.urlopen(req) as resp:
            return True, resp.status
    except urllib.error.HTTPError as e:
        if e.code == 429:
            retry_after = float(e.headers.get("Retry-After", 1.0))
            time.sleep(retry_after)
            return update_channel(cid, new_name)
        return False, f"{e.code} - {e.read().decode('utf-8', errors='ignore')}"
    except Exception as e:
        return False, str(e)

def main():
    print("✨ Applying External Discord Aesthetic Fonts across all channels...")
    for cid, name in CHANNELS_AESTHETIC_FONTS.items():
        ok, res = update_channel(cid, name)
        if ok:
            print(f"  ✅ {name}")
        else:
            print(f"  ⚠️ {cid}: {res}")
        time.sleep(0.4)

    print("\n🎉 All channels now using external aesthetic Discord fonts!")

if __name__ == "__main__":
    main()
