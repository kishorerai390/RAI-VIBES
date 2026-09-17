import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

NEW_VOICE_CHANNELS = [
    # (category_id, name, user_limit, position)
    (1550186724137640006, "👥 | Trio Chamber", 3, 5),
    (1550186724137640006, "🍿 | Cinema & Streams", 0, 6),
    (1550186724137640006, "🌧️ | Midnight Lo-Fi", 0, 7),
    (1550186748364066827, "⚡ | GTA RP & Chill", 5, 3),
    (1550186748364066827, "⚡ | Custom Room / Scrims", 8, 4),
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

    print("Creating Thor Apex inspired voice lounges...")
    for cat_id, name, limit, pos in NEW_VOICE_CHANNELS:
        cat = guild.get_channel(cat_id)
        if not cat:
            print(f"Category {cat_id} not found!")
            continue

        existing = discord.utils.get(cat.voice_channels, name=name)
        if existing:
            print(f"  Channel '{name}' already exists.")
            continue

        try:
            vc = await guild.create_voice_channel(
                name=name,
                category=cat,
                user_limit=limit,
                bitrate=96000,
                position=pos,
                reason="Adding Thor Apex inspired voice lounges"
            )
            print(f"  Created VC: '{name}' (limit={limit}, pos={pos})")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  Error creating '{name}': {e}")

    # Ensure AFK is placed at the very bottom of VOICE LOUNGE
    afk_ch = guild.get_channel(1550187298115551272)
    voice_cat = guild.get_channel(1550186724137640006)
    if afk_ch and voice_cat:
        try:
            await afk_ch.edit(position=len(voice_cat.channels))
            await guild.edit(afk_channel=afk_ch, afk_timeout=300)
            print("  AFK Channel confirmed at bottom of VOICE LOUNGE")
        except Exception as e:
            print(f"  AFK position error: {e}")

    print("\nAll new voice lounges added successfully!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
