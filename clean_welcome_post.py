import os, sys, json, urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'
WELCOME_CHAN_ID = '1545502705643167876' # #👋・welcome

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (WelcomeClean, 1.0)', 'Content-Type': 'application/json'}

# 1. Purge previous bot messages in #👋・welcome
try:
    req = urllib.request.Request(f'https://discord.com/api/v10/channels/{WELCOME_CHAN_ID}/messages?limit=20', headers=headers)
    with urllib.request.urlopen(req) as resp:
        msgs = json.loads(resp.read().decode('utf-8'))
    for m in msgs:
        dreq = urllib.request.Request(f"https://discord.com/api/v10/channels/{WELCOME_CHAN_ID}/messages/{m['id']}", headers=headers, method='DELETE')
        try:
            with urllib.request.urlopen(dreq) as dresp:
                pass
        except Exception:
            pass
    print("Welcome channel cleaned!")
except Exception as e:
    print(f"Purge note: {e}")

# 2. Fetch guild owner to use actual user name
req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}', headers=headers)
with urllib.request.urlopen(req) as resp:
    guild_info = json.loads(resp.read().decode('utf-8'))

owner_id = guild_info.get('owner_id')
print(f"Guild Owner ID: {owner_id}")

embed_data = {
    "title": "🌸 RAI FAM 💗 !",
    "description": (
        f"**HEY BUDDY!** **rf.rai_006** (<@{owner_id}>)\n\n"
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
    "color": 16738740, # 0xFF69B4
    "footer": {
        "text": "Member #25 • RAI FAM Luxury Community 💗",
        "icon_url": "https://cdn.discordapp.com/icons/1457382179981099090/c39edf51a428bd0368a72b5c463a5c6f.png"
    },
    "thumbnail": {
        "url": "https://cdn.discordapp.com/icons/1457382179981099090/c39edf51a428bd0368a72b5c463a5c6f.png"
    },
    "image": {
        "url": "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif"
    }
}

payload = {
    "content": f"🎉 Welcome <@{owner_id}> to **RAI FAM 💗**! 🚀",
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
        print("✅ Clean welcome message posted with real username!")
except Exception as e:
    print(f"Error posting: {e}")
