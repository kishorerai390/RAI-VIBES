import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import discord
import asyncio
import config

async def main():
    intents = discord.Intents.default()
    intents.guilds = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        guild = client.get_guild(1428058914141900860)
        if not guild:
            print("Guild not found!", flush=True)
            await client.close()
            return
        print(f"=== GUILD: {guild.name} ({guild.id}) ===", flush=True)
        for cat in guild.categories:
            print(f"\n--- CATEGORY: {cat.name} ({cat.id}) ---", flush=True)
            for ch in cat.channels:
                print(f"  [{ch.type}] {ch.name} (ID: {ch.id})", flush=True)
        print("\n--- NO CATEGORY ---", flush=True)
        for ch in guild.channels:
            if not ch.category:
                print(f"  [{ch.type}] {ch.name} (ID: {ch.id})", flush=True)
        await client.close()

    await client.start(config.DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
