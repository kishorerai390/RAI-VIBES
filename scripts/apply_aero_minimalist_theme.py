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
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found!")
        await client.close()
        return

    info_cat = guild.get_channel(1545803464712650844)
    chats_cat = guild.get_channel(1545803478490812578)
    voice_cat = guild.get_channel(1550186724137640006)
    gaming_cat = guild.get_channel(1550186748364066827)
    music_cat = guild.get_channel(1550186758577066036)
    rai_cat = guild.get_channel(1550186771822940262)
    sentinel_cat = guild.get_channel(1545803487093456906)
    stats_cat = guild.get_channel(1546059369085534229)

    print("\n--- 1. Relocating Channels from Music & RAI FAM into Consolidated Categories ---")
    # Move song-requests to chats_cat
    song_req = guild.get_channel(1550187318915244183)
    if song_req:
        try:
            await song_req.edit(name="🎵・song-requests", category=chats_cat, position=8)
            print("  Moved song-requests to COMMUNITY CHATS")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  Error moving song-requests: {e}")

    # Move 24/7 music to voice_cat
    music_vc = guild.get_channel(1550186760779211003)
    if music_vc:
        try:
            await music_vc.edit(name="🎧 | 24/7 Music Room", category=voice_cat, position=4)
            print("  Moved music VC to VOICE LOUNGES")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  Error moving music VC: {e}")

    # Move executive-chat and executive-vc to sentinel_cat
    exec_chat = guild.get_channel(1550187321285148782)
    if exec_chat:
        try:
            await exec_chat.edit(name="👑・executive-lounge", category=sentinel_cat, position=0)
            print("  Moved executive-chat to VIP & SENTINEL HQ")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  Error moving exec_chat: {e}")

    exec_vc = guild.get_channel(1550187323084374079)
    if exec_vc:
        try:
            await exec_vc.edit(name="👑 | Executive Suite", category=sentinel_cat, position=1, user_limit=5)
            print("  Moved executive-vc to VIP & SENTINEL HQ")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  Error moving exec_vc: {e}")

    print("\n--- 2. Deleting Redundant Fragmented Categories ---")
    if music_cat:
        try:
            await music_cat.delete(reason="Decongesting server layout - merged into VOICE LOUNGES")
            print("  Deleted MUSIC ZONE category")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  Error deleting music_cat: {e}")

    if rai_cat:
        try:
            await rai_cat.delete(reason="Decongesting server layout - merged into VIP & SENTINEL HQ")
            print("  Deleted RAI FAM category")
            await asyncio.sleep(0.5)
        except Exception as e:
            print(f"  Error deleting rai_cat: {e}")

    print("\n--- 3. Updating Category Names to Sleek Aero Minimalist ---")
    category_names = {
        1545803464712650844: ("✦ INFORMATION", 0),
        1545803478490812578: ("💬 COMMUNITY CHATS", 1),
        1550186724137640006: ("🔊 VOICE LOUNGES", 2),
        1550186748364066827: ("🎮 GAMING ARENA", 3),
        1545803487093456906: ("🔱 VIP & SENTINEL HQ", 4),
        1546059369085534229: ("📊 SERVER STATS", 5),
    }
    for cat_id, (name, pos) in category_names.items():
        cat = guild.get_channel(cat_id)
        if cat:
            try:
                await cat.edit(name=name, position=pos)
                print(f"  Updated Category: {name} (pos={pos})")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  Error updating category {cat_id}: {e}")

    print("\n--- 4. Updating Channel Names to Modern Sleek Styling ---")
    channel_renames = {
        # INFORMATION
        1545502700840427702: "✨・verify-here",
        1545502705643167876: "🌸・welcome",
        1545502710101704714: "📜・rules-and-info",
        1545502718792175646: "📢・announcements",
        1545502722739150898: "🏷️・roles",
        1550159859607928882: "🤝・partnerships",

        # CHATS
        1545502730699808768: "🥂・general-chat",
        1546097792915873842: "📸・media-gallery",
        1550184397540556951: "🎮・gaming-chat",
        1549416359723532480: "🤖・bot-commands",
        1550184399742697512: "💸・owo-arcade",
        1549439621497102518: "🛒・server-shop",
        1549407114861215815: "⭐・hall-of-fame",
        1549489880776839248: "💡・suggestions",
        1550187318915244183: "🎵・song-requests",

        # VOICE LOUNGES
        1550187295821402114: "➕ | Join to Create VC",
        1550186738410987591: "💬 | Chill Lounge 1",
        1550186767632826459: "💬 | Chill Lounge 2",
        1550186728285937727: "👥 | Duo Chamber",
        1550187298115551272: "💤 | AFK / Idle",

        # GAMING ARENA
        1550187304876900543: "🎮・lfg-matchmaking",
        1550186750289379328: "⚡ | Free Fire Squad",
        1550186752163975250: "⚡ | BGMI Squad",

        # STAFF & SENTINEL
        1545502845208629328: "🛡️・staff-operations",
        1545514505520545886: "🎫・ticket-support",
        1546540192343523399: "📝・moderation-logs",
        1546593526073135107: "🚨・sentinel-logs",
        1545502850057244762: "📋・audit-logs",
    }

    for ch_id, new_name in channel_renames.items():
        ch = guild.get_channel(ch_id)
        if ch and ch.name != new_name:
            try:
                await ch.edit(name=new_name)
                print(f"  Renamed: {ch.name} -> {new_name}")
                await asyncio.sleep(0.4)
            except Exception as e:
                print(f"  Failed rename {ch_id}: {e}")

    # Re-verify AFK
    afk_ch = guild.get_channel(1550187298115551272)
    if afk_ch:
        await guild.edit(afk_channel=afk_ch, afk_timeout=300)
        print("  AFK channel confirmed mapped to 💤 | AFK / Idle")

    print("\nAero Minimalist Theme successfully applied!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
