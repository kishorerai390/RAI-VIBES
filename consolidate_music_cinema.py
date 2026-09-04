import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

# Move Cinema Theater (1545502762467328185) under Music Zone (1545502766120566784)
requests.patch(
    "https://discord.com/api/v10/channels/1545502762467328185",
    headers=HEADERS,
    json={"parent_id": "1545502766120566784"}
)
# Rename Music zone to 🎵 | 𝙈𝙐𝙎𝙄𝘾 & 𝘾𝙄𝙉𝙀𝙈𝘼
requests.patch(
    "https://discord.com/api/v10/channels/1545502766120566784",
    headers=HEADERS,
    json={"name": "🎵 | 𝙈𝙐𝙎𝙄𝘾 & 𝘾𝙄𝙉𝙀𝙈𝘼"}
)
# Add 24-7 Radio if not present
requests.post(
    "https://discord.com/api/v10/guilds/1457382179981099090/channels",
    headers=HEADERS,
    json={"name": "📻 | 24-7 RADIO", "type": 2, "parent_id": "1545502766120566784"}
)
# Delete empty old category 1545502749628829696
requests.delete("https://discord.com/api/v10/channels/1545502749628829696", headers=HEADERS)
print("Consolidated Music & Cinema category!")
