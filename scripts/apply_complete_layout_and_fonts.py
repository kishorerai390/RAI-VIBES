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

# 1. Categories & Master Typography
CATEGORY_CONFIG = {
    # (Category Name, Desired Position)
    1545803464712650844: ("◈ 𝓘 𝓝 𝓕 𝓞 𝓡 𝓜 𝓐 𝓣 𝓘 𝓞 𝓝 ◈", 0),  # Luxury Cursive
    1545803478490812578: ("◈ 𝐂 𝐎 𝐌 𝐌 𝐔 𝐍 Ｉ 𝐓 Ｙ ◈", 1),        # Bold Serif
    1550186748364066827: ("◈ 𝔾 𝔸 𝕄 𝕀 ℕ 𝔾  ℤ 𝕆 ℕ 𝔼 ◈", 2),        # Double-Struck Neon
    1550186724137640006: ("◈ 𝐕 𝐎 Ｉ 𝐂 𝐄  𝐋 𝐎 𝐔 Ｎ 𝐆 𝐄 ◈", 3),  # Bold Serif
    1545803487093456906: ("◈ 𝔖 𝔗 𝔄 𝔉 𝔉  ℌ 𝔔 ◈", 4),              # Royal Gothic
    1546059369085534229: ("◈ 𝚂 𝙴 𝚁 𝚅 𝙴 𝚁  𝚂 𝚃 𝙰 𝚃 𝚂 ◈", 5),        # Monospace
}

# 2. Channel Names & Perfect Layout Ordering within Categories
CHANNEL_CONFIG = {
    # 🌸 INFORMATION
    1545502700840427702: ("✨┊𝐯𝐞𝐫𝐢𝐟𝐲-𝐡𝐞𝐫𝐞", 0),
    1545502705643167876: ("🌸┊𝐰𝐞𝐥𝐜𝐨𝐦𝐞", 1),
    1545502710101704714: ("📜┊ʀᴜʟᴇꜱ-ᴀɴᴅ-ɪɴꜰᴏ", 2),
    1545502718792175646: ("📢┊ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛꜱ", 3),
    1545502722739150898: ("🏷️┊ʀᴏʟᴇꜱ", 4),
    1550159859607928882: ("🤝┊ᴘᴀʀᴛɴᴇʀꜱʜɪᴘꜱ", 5),

    # 💬 COMMUNITY CHATS
    1545502730699808768: ("💬┊ɢᴇɴᴇʀᴀʟ-ᴄʜᴀᴛ", 0),
    1546097792915873842: ("📸┊ᴍᴇᴅɪᴀ-ɢᴀʟʟᴇʀʏ", 1),
    1550184397540556951: ("🎮┊ɢᴀᴍɪɴɢ-ᴄʜᴀᴛ", 2),
    1549416359723532480: ("🤖┊ʙᴏᴛ-ᴄᴍᴅꜱ", 3),
    1550184399742697512: ("💸┊ᴏᴡᴏ-ᴀʀᴄᴀᴅᴇ", 4),
    1550187318915244183: ("🎵┊ꜱᴏɴɢ-ʀᴇǫᴜᴇꜱᴛꜱ", 5),
    1549439621497102518: ("🛒┊ꜱᴇʀᴠᴇʀ-ꜱʜᴏᴘ", 6),
    1549407114861215815: ("⭐┊ʜᴀʟʟ-ᴏꜰ-ꜰᴀᴍᴇ", 7),
    1549489880776839248: ("💡┊ꜱᴜɢɢᴇꜱᴛɪᴏɴꜱ", 8),

    # 🎮 GAMING ZONE
    1550187304876900543: ("🎮┊ʟꜰɢ-ᴍᴀᴛᴄʜᴍᴀᴋɪɴɢ", 0),
    1550186750289379328: ("⚡ ┊ 𝗙𝗿𝗲𝗲 𝗙𝗶𝗿𝗲 𝗦𝗾𝘂𝗮𝗱", 1),
    1550186752163975250: ("⚡ ┊ 𝗕𝗚𝗠𝗜 𝗦𝗾𝘂𝗮𝗱", 2),

    # 🎧 VOICE LOUNGE
    1550187295821402114: ("➕ ┊ 𝐉𝐨𝐢𝐧 𝐭𝐨 𝐂𝐫𝐞𝐚𝐭𝐞 𝐕𝐂", 0),
    1550186760779211003: ("🎧 ┊ 𝟐𝟒/𝟕 𝐌𝐮𝐬𝐢𝐜 𝐒𝐭𝐮𝐝𝐢𝐨", 1),
    1550186738410987591: ("💬 ┊ 𝓒𝓱𝓲𝓵𝓵 𝓛𝓸𝓾𝓷𝓰𝓮 𝓘", 2),
    1550186767632826459: ("💬 ┊ 𝓒𝓱𝓲𝓵𝓵 𝓛𝓸𝓾𝓷𝓰𝓮 𝓘𝓘", 3),
    1550186728285937727: ("👥 ┊ 𝐃𝐮𝐨 𝐂𝐡𝐚𝐦𝐛𝐞𝐫", 4),
    1550187298115551272: ("💤 ┊ 𝐀𝐅𝐊 / 𝐒𝐥𝐞𝐞𝐩", 5),

    # 🛡️ STAFF HQ
    1550187321285148782: ("👑┊ᴇxᴇᴄᴜᴛɪᴠᴇ-ʟᴏᴜɴɢᴇ", 0),
    1550187323084374079: ("👑 ┊ 𝕰𝖝𝖊𝖈𝖚𝖙𝖎𝖛𝖊 𝕾𝖚𝖎𝖙𝖊", 1),
    1545502845208629328: ("🛡️┊ꜱᴛᴀꜰꜰ-ᴏᴘᴇʀᴀᴛɪᴏɴꜱ", 2),
    1545514505520545886: ("🎫┊ᴛɪᴄᴋᴇᴛ-ꜱᴜᴘᴘᴏʀᴛ", 3),
    1546540192343523399: ("📝┊ᴍᴏᴅᴇʀᴀᴛɪᴏɴ-ʟᴏɢꜱ", 4),
    1546593526073135107: ("🚨┊ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ", 5),
    1545502850057244762: ("📋┊ᴀᴜᴅɪᴛ-ʟᴏɢꜱ", 6),
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
    print(f"Applying Complete Master Layout & Fonts to {guild.name}")
    print(f"==================================================")

    # 1. Update Categories
    print("\n--- 1. Updating Categories & Order ---")
    for cat_id, (cat_name, pos) in CATEGORY_CONFIG.items():
        cat = guild.get_channel(cat_id)
        if cat:
            edit_kwargs = {}
            if cat.name != cat_name:
                edit_kwargs["name"] = cat_name
            if cat.position != pos:
                edit_kwargs["position"] = pos
            if edit_kwargs:
                try:
                    await cat.edit(**edit_kwargs)
                    print(f"  ✅ Category [{cat_id}]: {cat_name} (Pos: {pos})")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  ⚠️ Category edit error {cat_id}: {e}")
            else:
                print(f"  ✨ Category in position: {cat_name}")

    # 2. Update Channels & Positions
    print("\n--- 2. Updating Channels & Ordering ---")
    for ch_id, (ch_name, pos) in CHANNEL_CONFIG.items():
        ch = guild.get_channel(ch_id)
        if ch:
            edit_kwargs = {}
            if ch.name != ch_name:
                edit_kwargs["name"] = ch_name
            if ch.position != pos:
                edit_kwargs["position"] = pos
            if edit_kwargs:
                try:
                    await ch.edit(**edit_kwargs)
                    print(f"  ✅ Channel [{ch_id}]: {ch_name} (Pos: {pos})")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  ⚠️ Channel edit error {ch_id}: {e}")
            else:
                print(f"  ✨ Channel in position: {ch_name}")

    # 3. Confirm AFK Mapping
    afk_ch = guild.get_channel(1550187298115551272)
    if afk_ch:
        try:
            await guild.edit(afk_channel=afk_ch, afk_timeout=300)
            print(f"\n  💤 AFK Channel confirmed mapped to: {afk_ch.name} (5-min timeout)")
        except Exception as e:
            print(f"  Notice updating AFK channel: {e}")

    print("\n🎉 Master Layout and Mixed Font Theme 100% applied successfully!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
