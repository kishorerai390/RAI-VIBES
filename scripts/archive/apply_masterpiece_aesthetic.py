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
    "User-Agent": "DiscordBot (AestheticUpdate, 1.0)"
}

CATEGORY_MAP = {
    "1546059369085534229": "╭── 📊 ＳＥＲＶＥＲ  ＴＥＬＥＭＥＴＲＹ ──╮",
    "1545803464712650844": "╭── ✦ ＩＮＦＯＲＭＡＴＩＯＮ ──╮",
    "1545803478490812578": "╭── 💬 ＴＨＥ  ＬＯＵＮＧＥ ──╮",
    "1545803473528815807": "╭── 🎵 ＶＩＢＥ  ＳＴＵＤＩＯ ──╮",
    "1545803471289057300": "╭── 🎮 ＧＡＭＩＮＧ  ＺＯＮＥ ──╮",
    "1545803469196230686": "╭── ✨ ＦＵＮ  ＆  ＶＩＢＥＳ ──╮",
    "1545803467145224274": "╭── 🥂 ＰＲＩＶＡＴＥ  ＳＵＩＴＥＳ ──╮",
    "1546608477206487192": "╭── ⚜️ ＣＨＥＣＫＩＮＧ  ＺＯＮＥ ──╮",
    "1545803484241199217": "╭── 👑 ＥＸＥＣＵＴＩ𝐕Ｅ  ＺＯＮＥ ──╮",
    "1545803487093456906": "╭── 🛡️ ＳＥＮＴＩＮＥＬ  ＨＱ ──╮"
}

CHANNEL_MAP = {
    # Text - Information
    "1545502718792175646": "📢・announcements",
    "1545502705643167876": "🌸・welcome-sanctuary",
    "1545502710101704714": "📜・divine-codex",
    "1545502700840427702": "✨・verify-here",
    "1545502722739150898": "🎀・pick-roles",
    "1546125872661012611": "🧭・server-guide",
    "1547279073217351782": "🤝・partnerships",
    "1546122222329008199": "👋・goodbyes",

    # Text - The Lounge
    "1545502730699808768": "💬・general-chat",
    "1546097792915873842": "📸・media-gallery",
    "1549489880776839248": "💡・suggestions",
    "1545834933417672744": "💎・vip-lounge",
    "1549407114861215815": "⭐・hall-of-fame",
    "1549416359723532480": "🤖・bot-commands",
    "1549439621497102518": "🛒・server-shop",
    "1549439624936554658": "🎁・reward-exchange",

    # Text - Music & Gaming
    "1545534637122527332": "🎵・song-requests",
    "1545803554550190212": "🎮・gaming-hub",

    # Text - Executive & Staff
    "1545518535827263519": "👑・executive-chat",
    "1545502845208629328": "🛡️・staff-hq",
    "1545514505520545886": "🎫・ticket-support",
    "1545502850057244762": "📋・audit-logs",
    "1546540192343523399": "📝・moderation-logs",
    "1546593526073135107": "🚨・sentinel-defense-logs",
    "1547294258074226758": "🔒・security-terminal",

    # Voice - Vibe Studio
    "1545502782268772453": "🎧 ┊ ʀᴀɪ ᴢᴏɴᴇ",
    "1545781986193309789": "🌧️ ┊ ʟᴏ-ꜰɪ ᴢᴏɴᴇ",
    "1545518701414195281": "🎤 ┊ ᴋᴀʀᴀᴏᴋᴇ ꜱᴛᴀɢᴇ",

    # Voice - Gaming Zone
    "1545502794868457574": "⚡ ┊ ɢᴀᴍɪɴɢ ʟᴏᴜɴɢᴇ",
    "1546607696885841990": "⚡ ┊ ʙɢᴍɪ ꜱǫᴜᴀᴅ",
    "1545502823699980408": "⚡ ┊ ꜰʀᴇᴇ ꜰɪʀᴇ",
    "1545502832822591539": "⚡ ┊ ʀᴏʙʟᴏx ᴄʜᴀᴍʙᴇʀ",

    # Voice - Fun Zone
    "1545803549559099502": "🗣️ ┊ ᴏᴘᴇɴ ᴠᴏɪᴄᴇ",
    "1545518528126394400": "☘️ ┊ ʀᴀɪ ғᴀᴍ",
    "1545502813889499136": "💤 ┊ ᴀꜰᴋ / sʟᴇᴇᴘ",

    # Voice - Private Suites
    "1545502790888198215": "➕ ┊ ᴊᴏɪɴ ᴛᴏ ᴄʀᴇᴀᴛᴇ",
    "1546615478452093089": "🔒 ┊ ᴄʀᴇᴀᴛᴇ ɢʜᴏsᴛ ᴠᴄ",
    "1545518531192553603": "💎 ┊ ᴠɪᴘ ʟᴏᴜɴɢᴇ",
    "1545834935678537738": "🚀 ┊ ʙᴏᴏsᴛᴇʀ ʟᴏᴜɴɢᴇ",

    # Voice - Checking Zone
    "1546608480402542652": "🔎 ┊ ᴄʜᴇᴄᴋɪɴɢ-ᴀʀᴇᴀ",
    "1546608486270509167": "🔎 ┊ ᴘᴄ-ᴄʜᴇᴄᴋɪɴɢ",
    "1546608492389863437": "🔎 ┊ ᴘʜᴏɴᴇ-ᴄʜᴇᴄᴋɪɴɢ",
    "1546608498622595163": "🔎 ┊ ɪᴏs-ᴄʜᴇᴄᴋɪɴɢ",

    # Voice - Executive Zone
    "1545803607742349373": "💼 ┊ ᴘʀɪᴠᴀᴛᴇ ᴏꜰꜰɪᴄᴇ",
    "1545518533566271539": "👑 ┊ ᴇxᴇᴄᴜᴛɪᴠᴇ ꜱᴜɪᴛᴇ"
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
    print("🎨 Applying Masterpiece Aesthetic Layout to RAI FAM...")

    # 1. Update Categories
    print("\n1. Updating Categories...")
    for cid, name in CATEGORY_MAP.items():
        ok, res = update_channel(cid, name)
        if ok:
            print(f"  ✅ Category: {name}")
        else:
            print(f"  ⚠️ Category {cid}: {res}")
        time.sleep(0.4)

    # 2. Update Channels
    print("\n2. Updating Channels...")
    for cid, name in CHANNEL_MAP.items():
        ok, res = update_channel(cid, name)
        if ok:
            print(f"  ✅ Channel: {name}")
        else:
            print(f"  ⚠️ Channel {cid}: {res}")
        time.sleep(0.4)

    print("\n✨ Masterpiece Aesthetic Layout Successfully Applied! 🌸")

if __name__ == "__main__":
    main()
