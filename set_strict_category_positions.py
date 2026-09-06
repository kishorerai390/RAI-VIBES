import os, sys, json, urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (Audit, 1.0)', 'Content-Type': 'application/json'}

order = [
    '1546059369085534229', # 📊 SERVER STATS 📊 (Pos 0)
    '1545803464712650844', # 💬 ◈ COMMUNITY (Pos 1)
    '1545803467145224274', # 🎭 | 𝑷𝑬𝑹𝑺𝑶𝑵𝑨𝑳 𝑨𝑹𝑬𝑨 (Pos 2)
    '1545803469196230686', # 😹 | 𝑭𝑼𝑵 𝑽𝑶𝑰𝑪𝑬 𝑪𝑯𝑨𝑵𝑵𝑬𝑳𝑺 (Pos 3)
    '1545803471289057300', # 🎮 | 𝑮𝑨𝑴𝑰𝑵𝑮 𝒁𝑶𝑵𝑬 (Pos 4)
    '1545803473528815807', # 🍃 | 𝑺𝑶𝑵𝑮 𝒁𝑶𝑵𝑬 (Pos 5)
    '1545803475798204580', # 🎥 | 𝑻𝑯𝑬𝑨𝑻𝑬𝑹 (Pos 6)
    '1545803478490812578', # 🔱 | 𝑹𝑨𝑰-𝑬𝑺𝑷 ! (Pos 7)
    '1545803480768323614', # ⚜️ | 𝑪𝒉𝒆𝒄𝒌𝒊𝒏𝒈 𝒁𝒐𝒏𝒆 (Pos 8)
    '1545803484241199217', # 🔒 | 𝑷𝑹𝑰𝑽𝑨𝑻𝑬-𝒁𝑶𝑵𝑬 (Pos 9)
    '1545803487093456906', # 🛡️ | 𝑺𝑬𝑵𝑻𝑰𝑵𝑬𝑳 𝑫𝑬𝑭𝑬𝑵𝑺𝑬 (Pos 10)
]

for pos, cat_id in enumerate(order):
    payload = {'position': pos}
    req = urllib.request.Request(
        f'https://discord.com/api/v10/channels/{cat_id}',
        data=json.dumps(payload).encode('utf-8'),
        headers=headers,
        method='PATCH'
    )
    with urllib.request.urlopen(req) as resp:
        pass
    print(f"Set category {cat_id} -> Position {pos}")

print("✅ Strict ordering applied!")
