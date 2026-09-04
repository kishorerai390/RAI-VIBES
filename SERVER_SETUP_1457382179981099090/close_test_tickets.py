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
    if not guild:
        print("Guild not found")
        await client.close()
        return

    print(f"🧹 Deleting test ticket channels in {guild.name}...")
    for chan in list(guild.text_channels):
        if chan.name.startswith("ticket-"):
            try:
                await chan.delete(reason="Closing test ticket")
                print(f"  ❌ Deleted ticket channel: {chan.name}")
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"  ⚠️ Error deleting {chan.name}: {e}")

    print("\n✅ All test ticket channels have been removed!")
    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
