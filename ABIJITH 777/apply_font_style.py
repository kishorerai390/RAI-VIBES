import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import discord
import asyncio
from config import TOKEN, GUILD_ID

def to_sans_regular(text: str) -> str:
    """Convert standard uppercase/lowercase ASCII letters to Mathematical Sans Regular capitals."""
    out = []
    for c in text:
        if 'A' <= c <= 'Z':
            out.append(chr(ord(c) - ord('A') + 0x1D5A0))
        elif 'a' <= c <= 'z':
            out.append(chr(ord(c) - ord('a') + 0x1D5A0))
        else:
            out.append(c)
    return ''.join(out)

# Complete Server Channel Map for ABIJITH 777
CATEGORY_UPDATES = {
    1550204626786193458: "TEXT CHANNELS",
    1550205957659959329: "VERIFICATION",
    1550204630636691658: "COMMUNITY AREA",
    1550204646000300082: "CREATE UR OWN VC",
    1550204650643390667: "GAMING ZONE",
    1550204663117258945: "SQUAD AREA",
    1550224008606126171: "VIP & SENTINEL HQ",
}

CHANNEL_UPDATES = {
    # Text channels (Formatted with clean fullwidth pipe ｜・ and Sans Regular Capitals)
    1550204628690272386: f"｜・{to_sans_regular('CHAT')}",
    1550205959991992471: f"｜・{to_sans_regular('VERIFY-HERE')}",
    1550224012905291886: f"｜・{to_sans_regular('EXECUTIVE-LOUNGE')}",
    1550224016659316736: f"｜・{to_sans_regular('STAFF-OPERATIONS')}",
    1550224028760019015: f"｜・{to_sans_regular('AUDIT-LOGS')}",
    1550224034354958399: f"｜・{to_sans_regular('TICKET-SUPPORT')}",
    1550224039128203415: f"｜・{to_sans_regular('MODERATION-LOGS')}",
    1550224043678900286: f"｜・{to_sans_regular('SENTINEL-LOGS')}",

    # Voice channels (Standard ASCII '| • ' followed by clean uppercase letters)
    1550204632926527549: "| • COMMUNITY VC 1",
    1550204636118655078: "| • COMMUNITY VC 2",
    1550204639339880468: "| • DRAG ME",
    1550204642766622770: "| • COMMUNITY VC 3",
    1550204648516755536: "| • JOIN TO CREATE VC",
    1550204652908314764: "| • GAMING ZONE 1",
    1550204656502968471: "| • GAMING ZONE 2",
    1550204659833114685: "| • GAMING ZONE 3",
    1550204665168269403: "| • SQUAD 1",
    1550204668389359626: "| • SQUAD 2",
    1550204671564455996: "| • SQUAD 3",
    1550204674877956186: "| • SQUAD 4",
    1550204678313091094: "| • DUO",
    1550204682943860810: "| • TRIO",
    1550224047361757245: "| • EXECUTIVE SUITE",
}

async def main():
    intents = discord.Intents.default()
    intents.guilds = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as: {client.user}", flush=True)
        guild = client.get_guild(GUILD_ID)
        if not guild:
            print(f"Guild {GUILD_ID} not found!", flush=True)
            await client.close()
            return

        print(f"\nTransforming entire ABIJITH 777 server to EXECUTIVE SUITE style...", flush=True)

        # 1. Update Categories
        print("\n--- 1. Updating Categories ---", flush=True)
        for cat_id, target_name in CATEGORY_UPDATES.items():
            cat = guild.get_channel(cat_id)
            if cat and cat.name != target_name:
                try:
                    await cat.edit(name=target_name)
                    print(f"  Category: '{cat.name}' -> '{target_name}'", flush=True)
                except Exception as e:
                    print(f"  Error updating category {cat_id}: {e}", flush=True)
                await asyncio.sleep(1.0)
            elif cat:
                print(f"  Category already matches: '{target_name}'", flush=True)

        # 2. Update Channels
        print("\n--- 2. Updating Channels ---", flush=True)
        for ch_id, target_name in CHANNEL_UPDATES.items():
            ch = guild.get_channel(ch_id)
            if ch and ch.name != target_name:
                try:
                    await asyncio.wait_for(ch.edit(name=target_name), timeout=5.0)
                    print(f"  Channel updated -> '{target_name}'", flush=True)
                except asyncio.TimeoutError:
                    print(f"  Channel '{ch.name}' is temporarily rate-limited by Discord (renamed twice recently). Will sync on next cycle.", flush=True)
                except Exception as e:
                    print(f"  Error updating channel {ch_id}: {e}", flush=True)
                await asyncio.sleep(1.0)
            elif ch:
                print(f"  Channel already matches: '{target_name}'", flush=True)

        print("\n✨ Entire ABIJITH 777 server styling successfully unified!", flush=True)
        await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
