import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
TARGET_GUILD_ID = 1428058914141900860  # TEAM 777 / ABIJITH 777

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

async def transform_guild(guild: discord.Guild):
    print(f"✅ Connected to '{guild.name}' ({guild.id})! Rebuilding server...")

    # 1. Change Music Zone to Gaming Area
    music_cat = (
        discord.utils.get(guild.categories, name="| MUSIC ZONE")
        or discord.utils.get(guild.categories, name="MUSIC ZONE")
        or discord.utils.get(guild.categories, name="🎵 MUSIC LOUNGE")
    )
    if music_cat:
        await music_cat.edit(name="🎮 GAMING AREA")
        print("  Renamed music category -> '🎮 GAMING AREA'")
        gaming_names = [
            ("⚡ | Free Fire Squad", 4),
            ("⚡ | BGMI Squad", 4),
            ("⚡ | GTA RP & Chill", 5),
            ("⚡ | Custom Room / Scrims", 8),
        ]
        for idx, vc in enumerate(music_cat.voice_channels):
            if idx < len(gaming_names):
                name, limit = gaming_names[idx]
                await vc.edit(name=name, user_limit=limit, bitrate=96000)
                print(f"    Updated VC to: {name}")
                await asyncio.sleep(0.3)
    else:
        music_cat = await guild.create_category(name="🎮 GAMING AREA")
        print("  Created category '🎮 GAMING AREA'")
        await guild.create_voice_channel("⚡ | Free Fire Squad", category=music_cat, user_limit=4, bitrate=96000)
        await guild.create_voice_channel("⚡ | BGMI Squad", category=music_cat, user_limit=4, bitrate=96000)
        await guild.create_voice_channel("⚡ | GTA RP & Chill", category=music_cat, user_limit=5, bitrate=96000)

    # 2. Fix Typo in 'CREATE UR OWN VC'
    create_cat = (
        discord.utils.get(guild.categories, name="CREATE UR OWN VC")
        or discord.utils.get(guild.categories, name="🔊 VOICE LOUNGE")
    )
    if create_cat:
        for vc in create_cat.voice_channels:
            if "jion" in vc.name.lower():
                await vc.edit(name="➕ | Join to Create VC")
                print("  Fixed typo: 'JION' -> '➕ | Join to Create VC'")

    # 3. Clean Community Area & Remove DRAG ME
    comm_cat = discord.utils.get(guild.categories, name="COMMUNITY AREA")
    if comm_cat:
        await comm_cat.edit(name="🔊 VOICE LOUNGE")
        for vc in comm_cat.voice_channels:
            if "drag me" in vc.name.lower():
                await vc.delete(reason="Deleting redundant drag me channel")
                print("  Deleted redundant 'DRAG ME' channel")
                await asyncio.sleep(0.3)

    # 4. Ensure Cinema Hub with unblocked screenshare
    cinema_cat = discord.utils.get(guild.categories, name="🍿 CINEMA HUB")
    if not cinema_cat:
        cinema_cat = await guild.create_category(name="🍿 CINEMA HUB")
        print("  Created '🍿 CINEMA HUB'")
        m1 = await guild.create_voice_channel("🍿 | Movie Time 1", category=cinema_cat, bitrate=96000)
        m2 = await guild.create_voice_channel("🍿 | Movie Time 2", category=cinema_cat, bitrate=96000)
        
        overrides = {
            guild.default_role: discord.PermissionOverwrite(
                connect=True,
                speak=True,
                stream=True,
                use_embedded_activities=True,
                view_channel=True
            )
        }
        await m1.edit(overwrites=overrides)
        await m2.edit(overwrites=overrides)
        print("  Configured Movie Time 1 & 2 with unblocked stream permissions")

    print(f"\n🎉 TEAM 777 has been transformed successfully!")
    await client.close()

@client.event
async def on_ready():
    print(f"Logged in as {client.user} ({client.user.id})")
    guild = client.get_guild(TARGET_GUILD_ID)

    if not guild:
        print(f"⏳ Waiting for bot to be invited to TEAM 777 (id={TARGET_GUILD_ID})...")
        print(f"👉 INVITE LINK: https://discord.com/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot%20applications.commands")
        return

    await transform_guild(guild)

@client.event
async def on_guild_join(guild: discord.Guild):
    if guild.id == TARGET_GUILD_ID:
        print(f"🎉 Bot just joined {guild.name}! Starting transformation...")
        await transform_guild(guild)

if __name__ == "__main__":
    client.run(TOKEN)
