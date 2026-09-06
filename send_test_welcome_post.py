import os, sys, json, urllib.request, io, asyncio
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'
WELCOME_CHAN_ID = '1545502705643167876' # #👋・welcome

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (TestWelcome, 1.0)', 'Content-Type': 'application/json'}

embed_data = {
    "title": "🌸 RAI FAM 💗 !",
    "description": (
        "**HEY BUDDY!** <@1457382179981099090>\n\n"
        "**Welcome To RAI FAM 💗 !**\n"
        "**Get started with below:** <#1545502710101704714>\n\n"
        "**Follow The Server Guidelines:** <#1545502710101704714>\n\n"
        "**Verify For Full Access:** <#1545502700840427702>\n\n"
        "**Claim Your Roles:** <#1545502722739150898>\n\n"
        "**Fun With Us:** <#1545801428839170220>\n\n"
        "**Gaming Zone:** <#1545803554550190212>\n\n"
        "**24/7 Lo-Fi & Beats:** <#1545781986193309789>\n\n"
        "**Join And Chill With Us!:** <#1545502730699808768>\n\n"
        "**Thanks For Joining. Hope You Have A Great Time Here!**"
    ),
    "color": 16738740, # Vibrant Sakura Pink (0xFF69B4)
    "footer": {
        "text": "Member #25 • RAI FAM Luxury Community 💗",
        "icon_url": "https://cdn.discordapp.com/icons/1457382179981099090/c39edf51a428bd0368a72b5c463a5c6f.png"
    },
    "thumbnail": {
        "url": "https://cdn.discordapp.com/icons/1457382179981099090/c39edf51a428bd0368a72b5c463a5c6f.png"
    }
}

payload = {
    "content": "🎉 Welcome to **RAI FAM 💗**! 🚀",
    "embeds": [embed_data]
}

req = urllib.request.Request(
    f"https://discord.com/api/v10/channels/{WELCOME_CHAN_ID}/messages",
    data=json.dumps(payload).encode('utf-8'),
    headers=headers,
    method='POST'
)

try:
    with urllib.request.urlopen(req) as resp:
        print("✅ Posted luxury welcome embed to #👋・welcome successfully!")
except Exception as e:
    print(f"Error posting welcome: {e}")
