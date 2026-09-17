import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

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

    # 1. Create or Find '🍿 CINEMA & MUSIC' Category
    cinema_music_cat = discord.utils.get(guild.categories, name="🍿 CINEMA & MUSIC")
    if not cinema_music_cat:
        cinema_music_cat = await guild.create_category(
            name="🍿 CINEMA & MUSIC",
            position=4,
            reason="Separate cinema and music lounges into dedicated category"
        )
        print("Created category '🍿 CINEMA & MUSIC'")
    else:
        print("Category '🍿 CINEMA & MUSIC' already exists.")

    await asyncio.sleep(0.5)

    # 2. Move Cinema & Music channels into the new category
    channels_to_move = [
        (1550196955660029964, "🍿 | Cinema & Streams", 0),
        (1550186760779211003, "🎧 | 24/7 Music Studio", 1),
        (1550196959841878098, "🌧️ | Midnight Lo-Fi", 2),
    ]
    for ch_id, name, pos in channels_to_move:
        ch = guild.get_channel(ch_id)
        if ch:
            try:
                await ch.edit(category=cinema_music_cat, position=pos)
                print(f"  Moved '{name}' to 🍿 CINEMA & MUSIC (pos={pos})")
                await asyncio.sleep(0.4)
            except Exception as e:
                print(f"  Error moving {name}: {e}")

    # 3. Clean and order VOICE LOUNGE
    voice_cat = guild.get_channel(1550186724137640006)
    voice_channels_order = [
        (1550187295821402114, 0), # Join to Create
        (1550186738410987591, 1), # Chill 1
        (1550186767632826459, 2), # Chill 2
        (1550186728285937727, 3), # Duo
        (1550196951503474798, 4), # Trio
        (1550187298115551272, 5), # AFK
    ]
    for ch_id, pos in voice_channels_order:
        ch = guild.get_channel(ch_id)
        if ch:
            try:
                await ch.edit(category=voice_cat, position=pos)
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"  Error ordering voice channel {ch_id}: {e}")

    # 4. Set Category Positions
    category_positions = [
        (1546059369085534229, 0), # SERVER STATS
        (1545803464712650844, 1), # INFORMATION
        (1545803478490812578, 2), # COMMUNITY
        (1550186724137640006, 3), # VOICE LOUNGE
        (cinema_music_cat.id, 4), # CINEMA & MUSIC
        (1550186748364066827, 5), # GAMING ARENA
        (1545803487093456906, 6), # VIP & SENTINEL HQ
    ]
    for cat_id, pos in category_positions:
        cat = guild.get_channel(cat_id)
        if cat:
            try:
                await cat.edit(position=pos)
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"  Error setting category position {cat_id}: {e}")

    # Confirm AFK
    afk_ch = guild.get_channel(1550187298115551272)
    if afk_ch:
        await guild.edit(afk_channel=afk_ch, afk_timeout=300)
        print("AFK channel confirmed.")

    print("\nSeparation and categorization complete!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
