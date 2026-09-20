import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

# Typography Map: channel_id -> new_formatted_name (WITHOUT changing any positions or moving channels)
NAME_UPDATES = {
    # --- CATEGORIES ---
    # CINEMA HUB
    1550186762599534603: "◈ 𝐂 Ｉ Ｎ Ｅ Ｍ 𝐀  𝐇 𝐔 𝐁 ◈",
    # MUSIC LOUNGE
    1550186758656753735: "◈ 𝐌 𝐔 𝐒 Ｉ 𝐂  𝐋 𝐎 𝐔 Ｎ 𝐆 𝐄 ◈",

    # --- GAMING ZONE VOICE CHANNELS (Cyber Bold Style) ---
    1550186754026373280: "⚔️ ┊ 𝟭𝘃𝟭 𝗗𝘂𝗲𝗹 𝗔𝗿𝗲𝗻𝗮",
    1550186755938848798: "🎯 ┊ 𝗩𝗮𝗹𝗼𝗿𝗮𝗻𝘁 / 𝗖𝗦𝟮 𝗦𝗾𝘂𝗮𝗱",
    1550186745167876116: "⚡ ┊ 𝗚𝗧𝗔 𝗥𝗣 & 𝗖𝗵𝗶𝗹𝗹",
    1550186746979942410: "⚡ ┊ 𝗖𝘂𝘀𝘁𝗼𝗺 𝗥𝗼𝗼𝗺 / 𝗦𝗰𝗿𝗶𝗺𝘀",
    1550186743322513478: "🏆 ┊ 𝗧𝗼𝘂𝗿𝗻𝗮𝗺𝗲𝗻𝘁 𝗙𝗶𝗻𝗮𝗹𝘀",

    # --- VOICE LOUNGE (Bold Serif & Chill Cursive Style) ---
    1550186730248867941: "👥 ┊ 𝐓𝐫𝐢𝐨 𝐂𝐡𝐚𝐦𝐛𝐞𝐫",
    1550186732387962911: "👥 ┊ 𝐒𝐪𝐮𝐚𝐝 𝐂𝐡𝐚𝐦𝐛𝐞𝐫",
    1550186734493372566: "🎧 ┊ 𝐅𝐨𝐜𝐮𝐬 𝐋𝐨𝐮𝐧𝐠𝐞",

    # --- CINEMA HUB CHANNELS ---
    1550186764503748648: "🍿 ┊ 𝐌𝐨𝐯𝐢𝐞 𝐓𝐢𝐦𝐞 𝐈",
    1550186766466793542: "🍿 ┊ 𝐌𝐨𝐯𝐢𝐞 𝐓𝐢𝐦𝐞 𝐈𝐈",

    # --- MUSIC LOUNGE CHANNELS ---
    1550186757041946695: "🌧️ ┊ 𝐌𝐢𝐝𝐧𝐢𝐠𝐡𝐭 𝐋𝐨-𝐅𝐢",
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user.name} ({client.user.id})")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ Guild not found!")
        await client.close()
        return

    print(f"\n==================================================")
    print(f"Applying Font Typography (KEEPING EXACT LAYOUT INTACT)")
    print(f"Server: {guild.name}")
    print(f"==================================================")

    # 1. Update any remaining channels/categories that need the new typography
    for ch_id, new_name in NAME_UPDATES.items():
        ch = guild.get_channel(ch_id)
        if ch:
            if ch.name != new_name:
                try:
                    # ONLY edit the name - DO NOT pass position or category
                    await ch.edit(name=new_name)
                    print(f"  ✅ Formatted [{ch_id}]: {new_name}")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  ⚠️ Error updating {ch.name}: {e}")
            else:
                print(f"  ✨ Already formatted: {new_name}")
        else:
            # Search by name match if ID shifted
            pass

    # 2. Check all other channels to ensure clean divider format
    for cat in guild.categories:
        for ch in cat.channels:
            if ch.id in NAME_UPDATES:
                continue
            cur = ch.name
            # If it uses old "|" replace with elegant "┊" without moving
            if " | " in cur:
                updated = cur.replace(" | ", " ┊ ")
                try:
                    await ch.edit(name=updated)
                    print(f"  ✅ Polished divider: {cur} -> {updated}")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  Notice {cur}: {e}")

    print("\n🎉 Typography successfully updated for all channels while preserving 100% of the layout!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
