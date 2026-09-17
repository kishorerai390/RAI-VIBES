import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

CATEGORY_UPDATES = {
    1545803464712650844: "✦ INFORMATION",
    1545803478490812578: "💬 COMMUNITY",
    1550186724137640006: "🔊 VOICE LOUNGE",
    1550186748364066827: "🎮 GAMING ARENA",
    1545803487093456906: "🔱 VIP & SENTINEL HQ",
    1546059369085534229: "📊 SERVER STATS",
}

CHANNEL_UPDATES = {
    # INFORMATION
    1545502700840427702: "✨｜ᴠᴇʀɪꜰʏ-ʜᴇʀᴇ",
    1545502705643167876: "🌸｜ᴡᴇʟᴄᴏᴍᴇ",
    1545502710101704714: "📜｜ʀᴜʟᴇꜱ-ᴀɴᴅ-ɪɴꜰᴏ",
    1545502718792175646: "📢｜ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛꜱ",
    1545502722739150898: "🏷️｜ʀᴏʟᴇꜱ",
    1550159859607928882: "🤝｜ᴘᴀʀᴛɴᴇʀꜱʜɪᴘꜱ",

    # COMMUNITY
    1545502730699808768: "💬｜ɢᴇɴᴇʀᴀʟ-ᴄʜᴀᴛ",
    1546097792915873842: "📸｜ᴍᴇᴅɪᴀ-ɢᴀʟʟᴇʀʏ",
    1550184397540556951: "🎮｜ɢᴀᴍɪɴɢ-ᴄʜᴀᴛ",
    1549416359723532480: "🤖｜ʙᴏᴛ-ᴄᴏᴍᴍᴀɴᴅꜱ",
    1550184399742697512: "💸｜ᴏᴡᴏ-ᴀʀᴄᴀᴅᴇ",
    1550187318915244183: "🎵｜ꜱᴏɴɢ-ʀᴇǫᴜᴇꜱᴛꜱ",
    1549439621497102518: "🛒｜ꜱᴇʀᴠᴇʀ-ꜱʜᴏᴘ",
    1549407114861215815: "⭐｜ʜᴀʟʟ-ᴏꜰ-ꜰᴀᴍᴇ",
    1549489880776839248: "💡｜ꜱᴜɢɢᴇꜱᴛɪᴏɴꜱ",

    # VOICE LOUNGE
    1550187295821402114: "➕ | Join to Create VC",
    1550186760779211003: "🎧 | 24/7 Music Studio",
    1550186738410987591: "💬 | Chill Lounge 1",
    1550186767632826459: "💬 | Chill Lounge 2",
    1550186728285937727: "👥 | Duo Chamber",
    1550187298115551272: "💤 | AFK / Sleep",

    # GAMING ARENA
    1550187304876900543: "🎮｜ʟꜰɢ-ᴍᴀᴛᴄʜᴍᴀᴋɪɴɢ",
    1550186750289379328: "⚡ | Free Fire Squad",
    1550186752163975250: "⚡ | BGMI Squad",

    # VIP & SENTINEL HQ
    1550187321285148782: "👑｜ᴇxᴇᴄᴜᴛɪᴠᴇ-ʟᴏᴜɴɢᴇ",
    1550187323084374079: "👑 | Executive Suite",
    1545502845208629328: "🛡️｜ꜱᴛᴀꜰꜰ-ᴏᴘᴇʀᴀᴛɪᴏɴꜱ",
    1545514505520545886: "🎫｜ᴛɪᴄᴋᴇᴛ-ꜱᴜᴘᴘᴏʀᴛ",
    1546540192343523399: "📝｜ᴍᴏᴅᴇʀᴀᴛɪᴏɴ-ʟᴏɢꜱ",
    1546593526073135107: "🚨｜ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ",
    1545502850057244762: "📋｜ᴀᴜᴅɪᴛ-ʟᴏɢꜱ",

    # SERVER STATS
    1546099701496029194: "👥 | Total Members: 30",
    1546099703630798848: "👤 | Humans: 18",
    1546059375574130769: "🤖 | Bots: 12",
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

    print("\n--- 1. Applying Cyber Apex Minimalist Categories ---")
    for cat_id, new_name in CATEGORY_UPDATES.items():
        cat = guild.get_channel(cat_id)
        if cat and cat.name != new_name:
            try:
                await cat.edit(name=new_name)
                print(f"  Category: {new_name}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  Error updating category {cat_id}: {e}")

    print("\n--- 2. Applying Cyber Apex Minimalist Channels ---")
    for ch_id, new_name in CHANNEL_UPDATES.items():
        ch = guild.get_channel(ch_id)
        if ch and ch.name != new_name:
            try:
                await ch.edit(name=new_name)
                print(f"  Channel: {new_name}")
                await asyncio.sleep(0.4)
            except Exception as e:
                print(f"  Error updating channel {ch_id}: {e}")

    # Ensure AFK mapping is intact
    afk_ch = guild.get_channel(1550187298115551272)
    if afk_ch:
        await guild.edit(afk_channel=afk_ch, afk_timeout=300)
        print("  AFK Channel confirmed mapped to 💤 | AFK / Sleep")

    print("\nCyber Apex Minimalist theme applied successfully!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
