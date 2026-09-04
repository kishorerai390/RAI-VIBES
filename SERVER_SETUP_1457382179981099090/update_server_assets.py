import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
import asyncio
import discord
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

ICON_PATH = r"C:\Users\kishore\.gemini\antigravity-ide\brain\60a47792-e361-4210-a831-3da82766f292\rai_fam_server_icon_1788547184189.jpg"
BANNER_PATH = r"C:\Users\kishore\.gemini\antigravity-ide\brain\60a47792-e361-4210-a831-3da82766f292\rai_fam_server_banner_1788547166216.jpg"

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    # Update Server Icon
    if os.path.exists(ICON_PATH):
        try:
            with open(ICON_PATH, "rb") as f:
                icon_bytes = f.read()
            await guild.edit(icon=icon_bytes)
            print("✅ Server Icon successfully updated!")
        except Exception as e:
            print(f"⚠️ Could not set server icon via API: {e}")

    # Attempt to update Banner (Requires Server Boost Level 2)
    if os.path.exists(BANNER_PATH):
        try:
            with open(BANNER_PATH, "rb") as f:
                banner_bytes = f.read()
            await guild.edit(banner=banner_bytes)
            print("✅ Server Banner successfully updated!")
        except Exception as e:
            print(f"ℹ️ Server banner note (requires Boost Level 2 or Community Banner perk): {e}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
