import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

# Channels to delete
CHANNELS_TO_DELETE = [
    1550184318767202486,  # Duplicate text 🥂｜ᴄʜᴀᴛꜱ
    1550185065961496586,  # Duplicate text 🥂・ᴄʜᴀᴛꜱ
    1550186769755144252,  # Duplicate VC 📹 | ᴍᴏᴠɪᴇ²
    1550186756530376799,  # Redundant VC ⚡ | ᴏᴛʜᴇʀ ɢᴀ🇲🇪ꜱ
    1550186762775699541,  # Redundant VC 🌧️ | ʟᴏ-ꜰɪ ᴢᴏɴᴇ
    1550186765292146808,  # Redundant VC 🎤 | ᴋᴀʀᴀᴏᴋᴇ ꜱᴛᴀɢᴇ
    1550186774054043729,  # Duplicate VC ☘️┃ ʀᴀɪ ғᴀ🇲
]

CATEGORY_UPDATES = {
    1545803464712650844: ("╭── ✦ ＩＮＦＯＲＭＡＴＩＯＮ ──╮", 0),
    1545803478490812578: ("╭── 💬 ＣＨＡＴＳ ──╮", 1),
    1550186724137640006: ("╭── 🔊 ＶＯＩＣＥ  ＺＯＮＥ ──╮", 2),
    1550186748364066827: ("╭── 🎮 ＧＡＭＩＮＧ  ＺＯＮＥ ──╮", 3),
    1550186758577066036: ("╭── 🎵 ＭＵＳＩＣ  ＺＯＮＥ ──╮", 4),
    1550186771822940262: ("╭── 🔱 ＲＡＩ  ＦＡＭ ──╮", 5),
    1545803487093456906: ("╭── 🛡️ ＳＥＮＴＩＮＥＬ  ＨＱ ──╮", 6),
    1546059369085534229: ("╭── 📊 ＳＥＲＶＥＲ  ＳＴＡＴＳ ──╮", 7),
}

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

    print("Step 1: Deleting extra / duplicate channels...")
    for ch_id in CHANNELS_TO_DELETE:
        ch = guild.get_channel(ch_id)
        if ch:
            try:
                await ch.delete(reason="Cleaning server clutter & redundant voice channels")
                print(f"  Deleted: {ch.name} ({ch_id})")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  Failed to delete {ch_id}: {e}")

    print("\nStep 2: Updating Categories...")
    for cat_id, (name, pos) in CATEGORY_UPDATES.items():
        cat = guild.get_channel(cat_id)
        if cat and isinstance(cat, discord.CategoryChannel):
            try:
                await cat.edit(name=name, position=pos)
                print(f"  Updated Category: {name} (pos={pos})")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  Failed to update cat {cat_id}: {e}")

    voice_cat = guild.get_channel(1550186724137640006)
    gaming_cat = guild.get_channel(1550186748364066827)
    music_cat = guild.get_channel(1550186758577066036)
    rai_cat = guild.get_channel(1550186771822940262)

    print("\nStep 3: Moving & Updating Voice Channels...")
    # AFK Channel
    afk_ch = guild.get_channel(1550187298115551272)
    if afk_ch:
        try:
            await afk_ch.edit(name="🥱 | AFK", category=voice_cat, position=4)
            print("  Moved and renamed AFK channel to '🥱 | AFK'")
            await guild.edit(afk_channel=afk_ch, afk_timeout=300)
            print("  Set guild AFK channel to '🥱 | AFK' (timeout=300s)")
        except Exception as e:
            print(f"  Failed to configure AFK: {e}")

    # VOICE CHANNEL contents
    vc_configs = [
        (1550187295821402114, "📢 | JOIN TO CREATE VC", voice_cat, 0, 0),
        (1550186738410987591, "📢 | CHILL OUT ¹", voice_cat, 1, 0),
        (1550186767632826459, "📢 | CHILL OUT ²", voice_cat, 2, 0),
        (1550186728285937727, "🥂 | DUO", voice_cat, 3, 2),
    ]
    for ch_id, name, cat, pos, limit in vc_configs:
        ch = guild.get_channel(ch_id)
        if ch:
            try:
                await ch.edit(name=name, category=cat, position=pos, user_limit=limit)
                print(f"  Configured VC: {name} (limit={limit}, pos={pos})")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  Failed to configure VC {ch_id}: {e}")

    print("\nStep 4: Updating Gaming Zone...")
    gaming_configs = [
        (1550187304876900543, "🎮┃gaming-hub", gaming_cat, 0, None),
        (1550186750289379328, "⚡ | FREE FIRE", gaming_cat, 1, 4),
        (1550186752163975250, "⚡ | BGMI", gaming_cat, 2, 4),
    ]
    for ch_id, name, cat, pos, limit in gaming_configs:
        ch = guild.get_channel(ch_id)
        if ch:
            try:
                kwargs = {"name": name, "category": cat, "position": pos}
                if limit is not None:
                    kwargs["user_limit"] = limit
                await ch.edit(**kwargs)
                print(f"  Configured Gaming: {name}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  Failed to configure {ch_id}: {e}")

    print("\nStep 5: Updating Music Zone...")
    music_configs = [
        (1550187318915244183, "🎵┃song-requests", music_cat, 0, None),
        (1550186760779211003, "🎧 | RAI MUSIC 24/7", music_cat, 1, 0),
    ]
    for ch_id, name, cat, pos, limit in music_configs:
        ch = guild.get_channel(ch_id)
        if ch:
            try:
                kwargs = {"name": name, "category": cat, "position": pos}
                if limit is not None:
                    kwargs["user_limit"] = limit
                await ch.edit(**kwargs)
                print(f"  Configured Music: {name}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  Failed to configure {ch_id}: {e}")

    print("\nStep 6: Updating RAI FAM Zone...")
    rai_configs = [
        (1550187321285148782, "👑┃executive-chat", rai_cat, 0, None),
        (1550187323084374079, "👑 | RAI EXECUTIVE", rai_cat, 1, 5),
    ]
    for ch_id, name, cat, pos, limit in rai_configs:
        ch = guild.get_channel(ch_id)
        if ch:
            try:
                kwargs = {"name": name, "category": cat, "position": pos}
                if limit is not None:
                    kwargs["user_limit"] = limit
                await ch.edit(**kwargs)
                print(f"  Configured RAI: {name}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  Failed to configure {ch_id}: {e}")

    print("\nAll actions completed successfully!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
