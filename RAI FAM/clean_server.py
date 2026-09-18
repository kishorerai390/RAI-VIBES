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

# Categories to remove (old duplicates)
OLD_CATEGORIES = [
    "📌 ━━ INFORMATION ━━",
    "💬 ━━ COMMUNITY LOUNGE ━━",
    "🎵 ━━ APEX MUSIC & AUDIO ━━",
    "🔊 ━━ VOICE LOUNGES ━━",
    "🛡️ ━━ STAFF HEADQUARTERS ━━",
    "📊 ━━ SERVER STATS ━━"
]

# Redundant static voice channels in new categories to delete so it stays clean
REDUNDANT_VOICE = [
    "🔊・Cozy Talk 1",
    "🔊・Cozy Talk 2",
    "🔊・Duo Hangout (2 Max)",
    "🔊・Squad Hangout (4 Max)",
    "🌙・Late Night Chill Lounge",
    "🔊・HD Music Lounge [320kbps]",
    "🎥・Cinema Theater 2 [Anime & Shows]"
]

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    print(f"🧹 Starting channel cleanup for {guild.name}...")

    # 1. Delete all channels inside old duplicate categories
    for category in list(guild.categories):
        if category.name in OLD_CATEGORIES:
            print(f"Removing old category and channels: {category.name}")
            for channel in list(category.channels):
                try:
                    await channel.delete(reason="Removing duplicate congested channel")
                    print(f"  - Deleted channel: {channel.name}")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  - Error deleting channel {channel.name}: {e}")
            try:
                await category.delete(reason="Removing duplicate category")
                print(f"Deleted category: {category.name}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error deleting category {category.name}: {e}")

    # 2. Delete redundant voice channels in remaining categories
    for channel in list(guild.voice_channels):
        if channel.name in REDUNDANT_VOICE:
            try:
                await channel.delete(reason="Removing congested static voice channel")
                print(f"Deleted redundant voice channel: {channel.name}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error deleting voice channel {channel.name}: {e}")

    print("\n✅ CLEANUP COMPLETE! The server channels are now neat, organized, and uncluttered!")
    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
