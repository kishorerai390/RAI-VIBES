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

    everyone = guild.default_role
    verified_role = discord.utils.get(guild.roles, id=1549504522953695269)

    # 1. Update/Rename Cinema category to '🍿 CINEMA HUB'
    cinema_cat = guild.get_channel(1550197872006398014)
    if cinema_cat:
        await cinema_cat.edit(name="🍿 CINEMA HUB", position=4)
        print("Renamed category to '🍿 CINEMA HUB'")
    else:
        cinema_cat = await guild.create_category(name="🍿 CINEMA HUB", position=4)
        print("Created '🍿 CINEMA HUB'")

    await asyncio.sleep(0.5)

    # 2. Configure Movie Time 1
    movie1 = guild.get_channel(1550196955660029964)
    if movie1:
        await movie1.edit(name="🍿 | Movie Time 1", category=cinema_cat, position=0)
        print("Configured '🍿 | Movie Time 1'")

    # 3. Create '🍿 | Movie Time 2' if it doesn't already exist
    movie2 = discord.utils.get(cinema_cat.voice_channels, name="🍿 | Movie Time 2")
    if not movie2:
        overwrites = {
            everyone: discord.PermissionOverwrite(
                connect=True,
                speak=True,
                stream=True,
                use_embedded_activities=True
            )
        }
        if verified_role:
            overwrites[verified_role] = discord.PermissionOverwrite(
                connect=True,
                speak=True,
                stream=True,
                use_embedded_activities=True
            )

        movie2 = await guild.create_voice_channel(
            name="🍿 | Movie Time 2",
            category=cinema_cat,
            bitrate=96000,
            position=1,
            overwrites=overwrites,
            reason="Adding Movie Time 2 with unblocked streaming"
        )
        print("Created '🍿 | Movie Time 2' with stream & activity permissions")
    else:
        print("'🍿 | Movie Time 2' already exists")

    await asyncio.sleep(0.5)

    # 4. Create separate '🎵 MUSIC LOUNGE' Category
    music_cat = discord.utils.get(guild.categories, name="🎵 MUSIC LOUNGE")
    if not music_cat:
        music_cat = await guild.create_category(
            name="🎵 MUSIC LOUNGE",
            position=5,
            reason="Dedicated music category separating music and movies"
        )
        print("Created '🎵 MUSIC LOUNGE' category")
    else:
        print("'🎵 MUSIC LOUNGE' already exists")

    await asyncio.sleep(0.5)

    # 5. Move 24/7 Music Studio and Midnight Lo-Fi into MUSIC LOUNGE
    music_studio = guild.get_channel(1550186760779211003)
    if music_studio:
        await music_studio.edit(category=music_cat, position=0)
        print("Moved '🎧 | 24/7 Music Studio' to 🎵 MUSIC LOUNGE")
        await asyncio.sleep(0.4)

    midnight_lofi = guild.get_channel(1550196959841878098)
    if midnight_lofi:
        await midnight_lofi.edit(category=music_cat, position=1)
        print("Moved '🌧️ | Midnight Lo-Fi' to 🎵 MUSIC LOUNGE")
        await asyncio.sleep(0.4)

    # 6. Organize category hierarchy
    category_positions = [
        (1546059369085534229, 0), # SERVER STATS
        (1545803464712650844, 1), # INFORMATION
        (1545803478490812578, 2), # COMMUNITY
        (1550186724137640006, 3), # VOICE LOUNGE
        (cinema_cat.id, 4),        # CINEMA HUB
        (music_cat.id, 5),         # MUSIC LOUNGE
        (1550186748364066827, 6), # GAMING ARENA
        (1545803487093456906, 7), # VIP & SENTINEL HQ
    ]
    for cat_id, pos in category_positions:
        cat = guild.get_channel(cat_id)
        if cat:
            try:
                await cat.edit(position=pos)
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"Error setting category pos: {e}")

    # Ensure AFK mapping
    afk_ch = guild.get_channel(1550187298115551272)
    if afk_ch:
        await guild.edit(afk_channel=afk_ch, afk_timeout=300)

    print("\nMovie Time 2 added and Music/Cinema cleanly separated!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
