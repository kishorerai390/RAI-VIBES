import os
import requests
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
HEADERS = {"Authorization": f"Bot {TOKEN}", "Content-Type": "application/json"}

ids_to_delete = [
    "1545519333126574080",
    "1545519336104661002",
    "1545519338868572221",
    "1545519330903724053"
]

for cid in ids_to_delete:
    r = requests.delete(f"https://discord.com/api/v10/channels/{cid}", headers=HEADERS)
    print(f"Deleted {cid}: {r.status_code}")
