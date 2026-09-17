import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

CATEGORY_POSITIONS = [
    (1546059369085534229, "📊 SERVER STATS", 0),
    (1545803464712650844, "✦ INFORMATION", 1),
    (1545803478490812578, "💬 COMMUNITY", 2),
    (1550186724137640006, "🔊 VOICE LOUNGE", 3),
    (1550186748364066827, "🎮 GAMING ARENA", 4),
    (1545803487093456906, "🔱 VIP & SENTINEL HQ", 5),
]

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found!")
        await client.close()
        return

    print("Moving SERVER STATS to the very top (position 0)...")
    for cat_id, name, pos in CATEGORY_POSITIONS:
        cat = guild.get_channel(cat_id)
        if cat:
            try:
                await cat.edit(position=pos)
                print(f"  Category '{name}' set to position {pos}")
                await asyncio.sleep(0.4)
            except Exception as e:
                print(f"  Error setting position for {name}: {e}")

    print("\nSERVER STATS moved to the top successfully!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
