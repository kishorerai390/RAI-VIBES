import os
import asyncio
import discord
from dotenv import load_dotenv

load_dotenv()

async def main():
    token = os.getenv("SECURITY_BOT_TOKEN")
    if not token:
        print("No SECURITY_BOT_TOKEN found in .env")
        return

    intents = discord.Intents.default()
    bot = discord.Client(intents=intents)

    @bot.event
    async def on_ready():
        print(f"Logged in as {bot.user}")
        try:
            with open("assets/rai_sentinel_logo.jpg", "rb") as f:
                avatar_bytes = f.read()
            await bot.user.edit(avatar=avatar_bytes)
            print("Successfully updated RAI SENTINEL avatar!")
        except Exception as e:
            print(f"Could not update avatar via API: {e}")
        finally:
            await bot.close()

    await bot.start(token)

if __name__ == "__main__":
    asyncio.run(main())
