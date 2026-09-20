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

# Target typography map for ALL categories and channels
# STYLES MIXED:
# - Categories: ✦ Framed Luxury & Themed Typographies (Script, Bold Serif, Cyber, Gothic, Monospace)
# - Text Channels: Clean Small Caps & Bold Serif with '┊' divider
# - Voice Channels: Cyber Sans, Bold Serif, Cursive Luxury & Roman Numerals
TYPOGRAPHY_MAP = {
    # ==========================================
    # 1. CATEGORIES (✦ FRAMED BESPOKE THEMES)
    # ==========================================
    1545803464712650844: "✦ 𝓘 𝓝 𝓕 𝓞 𝓡 𝓜 𝓐 𝓣 𝓘 𝓞 𝓝 ✦",        # Information (Royal Script)
    1545803478490812578: "✦ 𝐂 𝐎 𝐌 𝐌 𝐔 Ｎ Ｉ Ｔ Ｙ ✦",        # Community (Bold Serif + Fullwidth)
    1550186748364066827: "✦ 𝔾 𝔸 𝕄 𝕀 ℕ 𝔾  ℤ 𝕆 ℕ 𝔼 ✦",        # Gaming Zone (Double Struck)
    1550186724137640006: "✦ 𝐕 𝐎 𝐈 𝐂 𝐄  𝐋 𝐎 𝐔 Ｎ 𝐆 𝐄 ✦",        # Voice Lounge (Bold Serif)
    1550197872006398014: "✦ 🍿 𝐂 Ｉ Ｎ Ｅ Ｍ 𝐀  𝐇 𝐔 𝐁 ✦",        # Cinema Hub (Cinema Popcorn Bold)
    1550198448203112539: "✦ 🎵 𝐌 Ｕ Ｓ Ｉ Ｃ  𝐋 𝐎 Ｕ Ｎ 𝐆 𝐄 ✦",    # Music Lounge (Melody Bold)
    1545803487093456906: "✦ 𝔖 𝔗 𝔄 𝔉 𝔉  ℌ 𝔔 ✦",                # Staff HQ (Gothic Fraktur)
    1546059369085534229: "✦ 𝚂 𝙴 𝚁 𝚅 𝙴 𝚁  𝚂 𝚃 𝙰 𝚃 𝚂 ✦",        # Server Stats (Monospace Telemetry)

    # ==========================================
    # 2. INFORMATION CHANNELS
    # ==========================================
    1545502700840427702: "✨┊𝐯𝐞𝐫𝐢𝐟𝐲-𝐡𝐞𝐫𝐞",
    1545502705643167876: "🌸┊𝐰𝐞𝐥𝐜𝐨𝐦𝐞",
    1545502710101704714: "📜┊ʀᴜʟᴇꜱ-ᴀɴᴅ-ɪɴꜰᴏ",
    1545502718792175646: "📢┊ᴀɴɴᴏᴜɴᴄᴇᴍᴇɴᴛꜱ",
    1545502722739150898: "🏷️┊ʀᴏʟᴇꜱ",
    1550159859607928882: "🤝┊ᴘᴀʀᴛɴᴇʀꜱʜɪᴘꜱ",

    # ==========================================
    # 3. COMMUNITY CHANNELS
    # ==========================================
    1545502730699808768: "💬┊ɢᴇɴᴇʀᴀʟ-ᴄʜᴀᴛ",
    1550184397540556951: "🎮┊ɢᴀᴍɪɴɢ-ᴄʜᴀᴛ",
    1549416359723532480: "🤖┊ʙᴏᴛ-ᴄᴍᴅꜱ",
    1550184399742697512: "💸┊ᴏᴡᴏ-ᴀʀᴄᴀᴅᴇ",

    # ==========================================
    # 4. GAMING ZONE CHANNELS
    # ==========================================
    1550187304876900543: "🎮┊ʟꜰɢ-ᴍᴀᴛᴄʜᴍᴀᴋɪɴɢ",
    1550186750289379328: "⚡ ┊ 𝗙𝗿𝗲𝗲 𝗙𝗶𝗿𝗲 𝗦𝗾𝘂𝗮𝗱",
    1550186752163975250: "⚡ ┊ 𝗕𝗚𝗠𝗜 𝗦𝗾𝘂𝗮𝗱",
    1550580961513701488: "⚔️ ┊ 𝟭𝘃𝟭 𝗗𝘂𝗲𝗹 𝗔𝗿𝗲𝗻𝗮",
    1550580964122566770: "🎯 ┊ 𝗩𝗮𝗹𝗼𝗿𝗮𝗻𝘁 / 𝗖𝗦𝟮 𝗦𝗾𝘂𝗮𝗱",
    1550196963935264870: "⚡ ┊ 𝗚𝗧𝗔 𝗥𝗣 & 𝗖𝗵𝗶𝗹𝗹",
    1550196967987089480: "⚡ ┊ 𝗖𝘂𝘀𝘁𝗼𝗺 𝗥𝗼𝗼𝗺 / 𝗦𝗰𝗿𝗶𝗺𝘀",
    1550582498776322191: "🏆 ┊ 𝗧𝗼𝘂𝗿𝗻𝗮𝗺𝗲𝗻𝘁 𝗙𝗶𝗻𝗮𝗹𝘀",

    # ==========================================
    # 5. VOICE LOUNGE CHANNELS
    # ==========================================
    1550187295821402114: "➕ ┊ 𝐉𝐨𝐢𝐧 𝐭𝐨 𝐂𝐫𝐞𝐚𝐭𝐞 𝐕𝐂",
    1550186738410987591: "💬 ┊ 𝓒𝓱𝓲𝓵𝓵 𝓛𝓸𝓾𝓷𝓰𝓮 𝓘",
    1550186767632826459: "💬 ┊ 𝓒𝓱𝓲𝓵𝓵 𝓛𝓸𝓾𝓷𝓰𝓮 𝓘𝓘",
    1550186728285937727: "👥 ┊ 𝐃𝐮𝐨 𝐂𝐡𝐚𝐦𝐛𝐞𝐫",
    1550196951503474798: "👥 ┊ 𝐓𝐫𝐢𝐨 𝐂𝐡𝐚𝐦𝐛𝐞𝐫",
    1550580967427538994: "👥 ┊ 𝐒𝐪𝐮𝐚𝐝 𝐂𝐡𝐚𝐦𝐛𝐞𝐫",
    1550580969843728424: "🎧 ┊ 𝐅𝐨𝐜𝐮𝐬 𝐋𝐨𝐮𝐧𝐠𝐞",
    1550187298115551272: "💤 ┊ 𝐀𝐅𝐊 / 𝐒𝐥𝐞𝐞𝐩",

    # ==========================================
    # 6. CINEMA HUB CHANNELS
    # ==========================================
    1550584226376720476: "🍿┊ᴄɪɴᴇᴍᴀ-ᴄʜᴀᴛ",
    1550196955660029964: "🎬 ┊ 𝑴𝒐𝒗𝒊𝒆 𝑻𝒊𝒎𝒆 𝑰",
    1550198444021514331: "🎬 ┊ 𝑴𝒐𝒗𝒊𝒆 𝑻𝒊𝒎𝒆 𝑰𝑰",

    # ==========================================
    # 7. MUSIC LOUNGE CHANNELS
    # ==========================================
    1550584592707100682: "🎧┊ᴍᴜꜱɪᴄ-ꜱʜᴀʀɪɴɢ",
    1550186760779211003: "🎧 ┊ 𝟐𝟒/𝟕 𝐌𝐮𝐬𝐢𝐜 𝐒𝐭𝐮𝐝𝐢𝐨",
    1550196959841878098: "🌧️ ┊ 𝓜𝓲𝓭𝓷𝓲𝓰𝓱𝓽 𝓛𝓸-𝓕𝓲",

    # ==========================================
    # 8. STAFF HQ CHANNELS
    # ==========================================
    1550187321285148782: "👑┊ᴇxᴇᴄᴜᴛɪᴠᴇ-ʟᴏᴜɴɢᴇ",
    1545502845208629328: "🛡️┊ꜱᴛᴀꜰꜰ-ᴏᴘᴇʀᴀᴛɪᴏɴꜱ",
    1545514505520545886: "🎫┊ᴛɪᴄᴋᴇᴛ-ꜱᴜᴘᴘᴏʀᴛ",
    1546540192343523399: "📝┊ᴍᴏᴅᴇʀᴀᴛɪᴏɴ-ʟᴏɢꜱ",
    1546593526073135107: "🚨┊ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ",
    1545502850057244762: "📋┊ᴀᴜᴅɪᴛ-ʟᴏɢꜱ",
    1550187323084374079: "👑 ┊ 𝕰𝖝𝖊𝖈𝖚𝖙𝖎𝖛𝖊 𝕾𝖚𝖎𝖙𝖊",
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

    print("==================================================")
    print(f"Applying New Mixed Fonts Theme to: {guild.name}")
    print("Strict Rule: Preserving 100% of channel layout & order")
    print("==================================================")

    updated_count = 0
    skipped_count = 0

    for ch_id, target_name in TYPOGRAPHY_MAP.items():
        ch = guild.get_channel(ch_id)
        if not ch:
            # Check categories
            ch = discord.utils.get(guild.categories, id=ch_id)

        if ch:
            if ch.name != target_name:
                try:
                    # ONLY edit the name. Never specify position or category.
                    await ch.edit(name=target_name)
                    print(f"  [UPDATED] {ch.id}: '{ch.name}' -> '{target_name}'")
                    updated_count += 1
                    await asyncio.sleep(0.6)  # Safe rate limit delay
                except Exception as e:
                    print(f"  [ERROR] {ch.id}: {e}")
            else:
                print(f"  [ALREADY PERFECT] {ch.id}: '{target_name}'")
                skipped_count += 1
        else:
            print(f"  [NOT FOUND] ID {ch_id} not found in guild.")

    print("==================================================")
    print(f"Completed! {updated_count} updated, {skipped_count} already matched.")
    print("==================================================")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
