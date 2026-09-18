import asyncio
import discord
import os
import sys
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

bot = discord.Client(intents=discord.Intents.all())

@bot.event
async def on_ready():
    for guild in bot.guilds:
        print(f"\n=== Guild: {guild.name} ({guild.id}) ===")
        for vc in guild.voice_channels:
            cat = vc.category.name if vc.category else "No Category"
            e_perms = vc.permissions_for(guild.default_role)
            print(f"[{cat}] VC: '{vc.name}' | Limit: {vc.user_limit} | @everyone Connect: {e_perms.connect}, Speak: {e_perms.speak}")
    await bot.close()

if __name__ == "__main__":
    asyncio.run(bot.start(token))
