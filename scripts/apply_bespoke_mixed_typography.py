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

# 1. Bespoke Category Typography Mix
CATEGORY_UPDATES = {
    1545803464712650844: "◈ 𝓘 𝓝 𝓕 𝓞 𝓡 𝓜 𝓐 𝓣 𝓘 𝓞 𝓝 ◈",  # Luxury Cursive Spaced
    1545803478490812578: "◈ 𝐂 𝐎 𝐌 𝐌 𝐔 𝐍 Ｉ 𝐓 Ｙ ◈",        # Bold Serif Spaced
    1550186724137640006: "◈ 𝐕 𝐎 Ｉ 𝐂 𝐄  𝐋 𝐎 𝐔 Ｎ 𝐆 𝐄 ◈",  # Bold Serif Spaced
    1550186748364066827: "◈ 𝔾 𝔸 𝕄 𝕀 ℕ 𝔾  ℤ 𝕆 ℕ 𝔼 ◈",        # Double-Struck Neon
    1545803487093456906: "◈ 𝔖 𝔗 𝔄 𝔉 𝔉  ℌ 𝔔 ◈",              # Royal Gothic Fraktur
    1546059369085534229: "◈ 𝚂 𝙴 𝚁 𝚅 𝙴 𝚁  𝚂 𝚃 𝙰 𝚃 𝚂 ◈",        # Clean Monospace
}

# 2. Bespoke Channel Typography Mix
CHANNEL_UPDATES = {
    # 🌸 INFORMATION (Cursive & Bold Serif)
    1545502700840427702: "✨┊𝐯𝐞𝐫𝐢𝐟𝐲-𝐡𝐞𝐫𝐞",
    1545502705643167876: "🌸┊𝐰𝐞𝐥𝐜𝐨𝐦𝐞",
    1545502710101704714: "📜┊ʀᴜʟᴇꜱ-ᴀɴᴅ-ɪɴꜰᴏ",
    1545502718792175646: "📢┊ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛꜱ",
    1545502722739150898: "🏷️┊ʀᴏʟᴇꜱ",
    1550159859607928882: "🤝┊ᴘᴀʀᴛɴᴇʀꜱʜɪᴘꜱ",

    # 💬 COMMUNITY (Aesthetic Small Caps)
    1545502730699808768: "💬┊ɢᴇɴᴇʀᴀʟ-ᴄʜᴀᴛ",
    1546097792915873842: "📸┊ᴍᴇᴅɪᴀ-ɢᴀʟʟᴇʀʏ",
    1550184397540556951: "🎮┊ɢᴀᴍɪɴɢ-ᴄʜᴀᴛ",
    1549416359723532480: "🤖┊ʙᴏᴛ-ᴄᴏᴍᴍᴀɴᴅꜱ",
    1550184399742697512: "💸┊ᴏᴡᴏ-ᴀʀᴄᴀᴅᴇ",
    1550187318915244183: "🎵┊ꜱᴏɴɢ-ʀᴇǫᴜᴇꜱᴛꜱ",
    1549439621497102518: "🛒┊ꜱᴇʀᴠᴇʀ-ꜱʜᴏᴘ",
    1549407114861215815: "⭐┊ʜᴀʟʟ-ᴏꜰ-ꜰᴀᴍᴇ",
    1549489880776839248: "💡┊ꜱᴜɢɢᴇꜱᴛɪᴏɴꜱ",

    # 🎮 GAMING & ESPORTS (Cyber Bold & Small Caps)
    1550187304876900543: "🎮┊ʟꜰɢ-ᴍᴀᴛᴄʜᴍᴀᴋɪɴɢ",
    1550186750289379328: "⚡ ┊ 𝗙𝗿𝗲𝗲 𝗙𝗶𝗿𝗲 𝗦𝗾𝘂𝗮𝗱",
    1550186752163975250: "⚡ ┊ 𝗕𝗚𝗠𝗜 𝗦𝗾𝘂𝗮𝗱",

    # 🎧 VOICE LOUNGE (Bold Serif & Cursive Chill)
    1550187295821402114: "➕ ┊ 𝐉𝐨𝐢𝐧 𝐭𝐨 𝐂𝐫𝐞𝐚𝐭𝐞 𝐕𝐂",
    1550186760779211003: "🎧 ┊ 𝟐𝟒/𝟕 𝐌𝐮𝐬𝐢𝐜 𝐒𝐭𝐮𝐝𝐢𝐨",
    1550186738410987591: "💬 ┊ 𝓒𝓱𝓲𝓵𝓵 𝓛𝓸𝓾𝓷𝓰𝓮 𝓘",
    1550186767632826459: "💬 ┊ 𝓒𝓱𝓲𝓵𝓵 𝓛𝓸𝓾𝓷𝓰𝓮 𝓘𝓘",
    1550186728285937727: "👥 ┊ 𝐃𝐮𝐨 𝐂𝐡𝐚𝐦𝐛𝐞𝐫",
    1550187298115551272: "💤 ┊ 𝐀𝐅𝐊 / 𝐒𝐥𝐞𝐞𝐩",

    # 🛡️ STAFF HQ & SECURITY (Royal Gothic Fraktur)
    1550187321285148782: "👑┊ᴇxᴇᴄᴜᴛɪᴠᴇ-ʟᴏᴜɴɢᴇ",
    1550187323084374079: "👑 ┊ 𝕰𝖝𝖊𝖈𝖚𝖙𝖎𝖛𝖊 𝕾𝖚𝖎𝖙𝖊",
    1545502845208629328: "🛡️┊ꜱᴛᴀꜰꜰ-ᴏᴘᴇʀᴀᴛɪᴏɴꜱ",
    1545514505520545886: "🎫┊ᴛɪᴄᴋᴇᴛ-ꜱᴜᴘᴘᴏʀᴛ",
    1546540192343523399: "📝┊ᴍᴏᴅᴇʀᴀᴛɪᴏɴ-ʟᴏɢꜱ",
    1546593526073135107: "🚨┊ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ",
    1545502850057244762: "📋┊ᴀᴜᴅɪᴛ-ʟᴏɢꜱ",
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
    print(f"Applying Bespoke Mixed Typography to {guild.name}")
    print(f"==================================================")

    # 1. Update Categories
    print("\n--- 1. Updating Categories ---")
    for cat_id, new_name in CATEGORY_UPDATES.items():
        cat = guild.get_channel(cat_id)
        if cat:
            if cat.name != new_name:
                try:
                    await cat.edit(name=new_name)
                    print(f"  ✅ Category [{cat_id}]: {new_name}")
                    await asyncio.sleep(0.6)
                except Exception as e:
                    print(f"  ⚠️ Error updating category {cat_id}: {e}")
            else:
                print(f"  ✨ Category already matches: {new_name}")

    # 2. Update Channels
    print("\n--- 2. Updating Channels ---")
    for ch_id, new_name in CHANNEL_UPDATES.items():
        ch = guild.get_channel(ch_id)
        if ch:
            if ch.name != new_name:
                try:
                    await ch.edit(name=new_name)
                    print(f"  ✅ Channel [{ch_id}]: {new_name}")
                    await asyncio.sleep(0.6)
                except Exception as e:
                    print(f"  ⚠️ Error updating channel {ch_id}: {e}")
            else:
                print(f"  ✨ Channel already matches: {new_name}")

    # 3. Verify AFK Mapping
    afk_ch = guild.get_channel(1550187298115551272)
    if afk_ch:
        try:
            await guild.edit(afk_channel=afk_ch, afk_timeout=300)
            print(f"\n  💤 AFK Channel confirmed mapped to: {afk_ch.name}")
        except Exception as e:
            print(f"  Notice updating AFK channel: {e}")

    print("\n🎉 Bespoke Mixed Font Theme successfully applied across the entire server!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
