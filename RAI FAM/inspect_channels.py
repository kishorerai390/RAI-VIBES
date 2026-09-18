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
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    print(f"\n--- CHANNELS IN {guild.name} ---")
    for category in guild.categories:
        print(f"\n[CATEGORY] {category.name}")
        for channel in category.channels:
            print(f"  - {channel.name} (type: {type(channel).__name__})")

    # Uncategorized channels
    uncategorized = [c for c in guild.channels if c.category is None and not isinstance(c, discord.CategoryChannel)]
    if uncategorized:
        print("\n[UNCATEGORIZED]")
        for c in uncategorized:
            print(f"  - {c.name} (type: {type(c).__name__})")

    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
