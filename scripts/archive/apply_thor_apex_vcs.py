import os
import sys
import time
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"

headers = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

# Mapping of voice channels to Thor / Apex aesthetic names
THOR_VC_MAPPING = {
    # 💬 THE LOUNGE
    "1545518528126394400": "☘️┃  ʀᴀɪ ғᴀᴍ",
    "1545518531192553603": "💎┃  ᴠɪᴘ ʟᴏᴜɴɢᴇ",
    "1545834935678537738": "🚀┃  ʙᴏᴏsᴛᴇʀ ʟᴏᴜɴɢᴇ",

    # 🎵 VIBE STUDIO
    "1545502782268772453": "🎧  | ʀᴀɪ ᴢᴏɴᴇ",
    "1545518701414195281": "🎤  | ᴋᴀʀᴀᴏᴋᴇ ꜱᴛᴀɢᴇ",
    "1545781986193309789": "🌧️  | ʟᴏ-ꜰɪ ᴢᴏɴᴇ",

    # 🎮 GAMING ZONE
    "1545502823699980408": "⚡  | ꜰʀᴇᴇ ꜰɪʀᴇ",
    "1546607696885841990": "⚡  | ʙɢᴍɪ",
    "1545502832822591539": "⚡  | ʀᴏʙʟᴏx",
    "1545502794868457574": "⚡  | ɢᴀᴍɪɴɢ ʟᴏᴜɴɢᴇ",

    # ✨ FUN ZONE
    "1545803549559099502": "🗣️  | ᴏᴘᴇɴ ᴠᴏɪᴄᴇ",
    "1545502813889499136": "💤  | ᴀꜰᴋ / sʟᴇᴇᴘ",

    # ⚜️ CHECKING ZONE
    "1546608480402542652": "🔎  ┃ᴄʜᴇᴄᴋɪɴɢ-ᴀʀᴇᴀ",
    "1546608486270509167": "🔎  ┃ ᴘᴄ-ᴄʜᴇᴄᴋɪɴɢ",
    "1546608492389863437": "🔎  ┃ ᴘʜᴏɴᴇ-ᴄʜᴇᴄᴋɪɴɢ",
    "1546608498622595163": "🔎  ┃ ɪᴏs-ᴄʜᴇᴄᴋɪɴɢ",

    # 🥂 PRIVATE SUITES
    "1545502790888198215": "➕  | ᴊᴏɪɴ ᴛᴏ ᴄʀᴇᴀᴛᴇ",
    "1546615478452093089": "🔒  | ᴄʀᴇᴀᴛᴇ ɢʜᴏsᴛ ᴠᴄ",

    # 👑 EXECUTIVE ZONE
    "1545518533566271539": "👑  | ᴇxᴇᴄᴜᴛɪᴠᴇ ꜱᴜɪᴛᴇ",
    "1545803607742349373": "💼  | ᴘʀɪᴠᴀᴛᴇ ᴏꜰꜰɪᴄᴇ",
}

def rename_channel(cid, new_name):
    url = f"https://discord.com/api/v10/channels/{cid}"
    for attempt in range(4):
        resp = requests.patch(url, headers=headers, json={"name": new_name})
        if resp.status_code == 200:
            print(f"✅ Renamed [{cid}] -> {new_name}")
            return True
        elif resp.status_code == 429:
            retry_after = resp.json().get("retry_after", 1.5)
            print(f"⏳ Rate limited on {cid}, waiting {retry_after}s (attempt {attempt+1})...")
            time.sleep(retry_after + 0.3)
        else:
            print(f"❌ Failed to rename {cid} ({resp.status_code}): {resp.text}")
            return False
    return False

if __name__ == "__main__":
    print("=== APPLYING THOR APEX VC STYLING ===")
    for cid, name in THOR_VC_MAPPING.items():
        rename_channel(cid, name)
        time.sleep(0.4)
    print("\n=== ALL VOICE CHANNELS UPDATED TO THOR APEX STYLE ===")
