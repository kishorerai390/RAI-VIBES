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

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)
    for r in guild.roles:
        if r.name == "⚡ Co-Owner / Administrator":
            try:
                await r.delete()
                print("Deleted duplicate Co-Owner role.")
            except Exception:
                pass
    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
