import sys
import os
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    guild = client.get_guild(1457382179981099090)
    print(f"Guild: {guild.name} ({guild.id})")
    for cat in guild.categories:
        print(f"CAT: id={cat.id} | name='{cat.name}' | pos={cat.position}")
        for ch in cat.channels:
            print(f"  CH: id={ch.id} | name='{ch.name}' | type={type(ch).__name__}")
    await client.close()

client.run(os.getenv("DISCORD_BOT_TOKEN"))
