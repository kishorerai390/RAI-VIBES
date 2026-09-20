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

# 1. CATEGORY POSITIONS (Top to Bottom)
# Server Stats at top -> Info -> Community -> Music -> Cinema -> Gaming -> Voice -> Staff HQ at bottom
CATEGORY_ORDER = [
    (1546059369085534229, "SERVER STATS", 0),
    (1545803464712650844, "INFORMATION", 1),
    (1545803478490812578, "COMMUNITY", 2),
    (1550198448203112539, "MUSIC LOUNGE", 3),
    (1550197872006398014, "CINEMA HUB", 4),
    (1550186748364066827, "GAMING ZONE", 5),
    (1550186724137640006, "VOICE LOUNGE", 6),
    (1545803487093456906, "STAFF HQ", 7),
]

# 2. CHANNELS ORDER WITHIN EACH CATEGORY
CHANNEL_ORDER = {
    # --- SERVER STATS (0) ---
    1546099701496029194: 0,  # All Members
    1546099703630798848: 1,  # Members
    1546059375574130769: 2,  # Bots

    # --- INFORMATION (1) ---
    1545502700840427702: 0,  # verify-here
    1545502705643167876: 1,  # welcome
    1545502710101704714: 2,  # rules-and-info
    1545502718792175646: 3,  # announcements
    1545502722739150898: 4,  # roles
    1550159859607928882: 5,  # partnerships

    # --- COMMUNITY (2) ---
    1545502730699808768: 0,  # general-chat
    1550184397540556951: 1,  # gaming-chat
    1549416359723532480: 2,  # bot-cmds
    1550184399742697512: 3,  # owo-arcade

    # --- MUSIC LOUNGE (3) ---
    1550584592707100682: 0,  # music-sharing (Text)
    1550186760779211003: 1,  # 24/7 Music Studio (Voice)
    1550196959841878098: 2,  # Midnight Lo-Fi (Voice)

    # --- CINEMA HUB (4) ---
    1550584226376720476: 0,  # cinema-chat (Text)
    1550196955660029964: 1,  # Movie Time I (Voice)
    1550198444021514331: 2,  # Movie Time II (Voice)

    # --- GAMING ZONE (5) ---
    1550187304876900543: 0,  # lfg-matchmaking (Text)
    1550186750289379328: 1,  # Free Fire Squad
    1550186752163975250: 2,  # BGMI Squad
    1550580961513701488: 3,  # 1v1 Duel Arena
    1550580964122566770: 4,  # Valorant / CS2 Squad
    1550196963935264870: 5,  # GTA RP & Chill
    1550196967987089480: 6,  # Custom Room / Scrims
    1550582498776322191: 7,  # Tournament Finals

    # --- VOICE LOUNGE (6) ---
    1550187295821402114: 0,  # Join to Create VC
    1550186738410987591: 1,  # Chill Lounge I
    1550186767632826459: 2,  # Chill Lounge II
    1550186728285937727: 3,  # Duo Chamber
    1550196951503474798: 4,  # Trio Chamber
    1550580967427538994: 5,  # Squad Chamber
    1550580969843728424: 6,  # Focus Lounge
    1550187298115551272: 7,  # AFK / Sleep (At bottom!)

    # --- STAFF HQ (7) ---
    1550187321285148782: 0,  # executive-lounge (Text)
    1550187323084374079: 1,  # Executive Suite (Voice)
    1545502845208629328: 2,  # staff-operations
    1545514505520545886: 3,  # ticket-support
    1546540192343523399: 4,  # moderation-logs
    1546593526073135107: 5,  # sentinel-logs
    1545502850057244762: 6,  # audit-logs
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
    print(f"Fixing Server Category & Channel Order: {guild.name}")
    print("==================================================")

    # 1. Reorder Categories
    print("\n[Step 1] Ordering Categories...")
    for cat_id, name, target_pos in CATEGORY_ORDER:
        cat = discord.utils.get(guild.categories, id=cat_id)
        if cat:
            if cat.position != target_pos:
                try:
                    await cat.edit(position=target_pos)
                    print(f"  ✅ Category '{name}' moved to pos {target_pos}")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  ⚠️ Error moving category '{name}': {e}")
            else:
                print(f"  ✨ Category '{name}' already at pos {target_pos}")
        else:
            print(f"  ❌ Category {cat_id} not found!")

    # 2. Reorder Channels within Categories
    print("\n[Step 2] Ordering Channels within Categories...")
    for ch_id, target_pos in CHANNEL_ORDER.items():
        ch = guild.get_channel(ch_id)
        if ch:
            if ch.position != target_pos:
                try:
                    await ch.edit(position=target_pos)
                    print(f"  ✅ Channel '{ch.name}' moved to pos {target_pos}")
                    await asyncio.sleep(0.4)
                except Exception as e:
                    print(f"  ⚠️ Error moving channel '{ch.name}': {e}")
            else:
                print(f"  ✨ Channel '{ch.name}' already at pos {target_pos}")
        else:
            print(f"  ❌ Channel {ch_id} not found!")

    print("\n==================================================")
    print("🎉 Server Order Completely Fixed & Perfected!")
    print("==================================================")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
