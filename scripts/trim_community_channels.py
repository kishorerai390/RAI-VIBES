import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

# Channels to delete in COMMUNITY
CHANNELS_TO_DELETE = [
    1546097792915873842,  # media-gallery
    1550187318915244183,  # song-requests
    1549439621497102518,  # server-shop
    1549407114861215815,  # hall-of-fame
    1549489880776839248,  # suggestions
]

ESSENTIAL_CHANNELS = [
    (1545502730699808768, "💬｜ᴄʜᴀᴛꜱ", 0),
    (1550184397540556951, "🎮｜ꜰꜰ-ᴄʜᴀᴛ", 1),
    (1549416359723532480, "🤖｜ʙᴏᴛ-ᴄᴍᴅꜱ", 2),
    (1550184399742697512, "💸｜ᴏᴡᴏ-ᴄʜᴀᴛ", 3),
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

    print("\n--- 1. Deleting Extra Channels in COMMUNITY ---")
    for ch_id in CHANNELS_TO_DELETE:
        ch = guild.get_channel(ch_id)
        if ch:
            try:
                await ch.delete(reason="Pruning COMMUNITY clutter to match Essential 4")
                print(f"  Deleted: {ch.name} ({ch_id})")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  Failed to delete {ch_id}: {e}")

    print("\n--- 2. Renaming and Positioning Essential 4 Channels ---")
    comm_cat = guild.get_channel(1545803478490812578)
    for ch_id, name, pos in ESSENTIAL_CHANNELS:
        ch = guild.get_channel(ch_id)
        if ch:
            try:
                await ch.edit(name=name, category=comm_cat, position=pos)
                print(f"  Configured: {name} (pos={pos})")
                await asyncio.sleep(0.4)
            except Exception as e:
                print(f"  Failed to configure {ch_id}: {e}")

    print("\nCOMMUNITY trimmed to Essential 4 successfully!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
