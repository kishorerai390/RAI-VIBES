import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import config

GUILD_ID = 1457382179981099090

client = discord.Client(intents=discord.Intents.default())

TOPICS = {
    1545502700840427702: "ᯓ ⋆ click the button below to verify & unlock all server channels ⋆ ᯓ",
    1545502705643167876: "ᯓ ⋆ welcome to RAI FAM & RAI VIBES • community guidelines & entrance ⋆ ᯓ",
    1545502710101704714: "ᯓ ⋆ official server rules, bot commands & community standards ⋆ ᯓ",
    1545502718792175646: "ᯓ ⋆ official community broadcasts, events & sound engine updates ⋆ ᯓ",
    1545502722739150898: "ᯓ ⋆ select your gaming pings & notification roles below ⋆ ᯓ",
    1550159859607928882: "ᯓ ⋆ official alliances & verified server partnerships ⋆ ᯓ",
    1545502730699808768: "ᯓ ⋆ main community lounge • relax, chat & vibe ⋆ ᯓ",
    1549416359723532480: "ᯓ ⋆ bot commands, economy & level telemetry ⋆ ᯓ",
    1550184399742697512: "ᯓ ⋆ minigames, casino & arcade coin drops ⋆ ᯓ",
    1551184190073213071: "ᯓ ⋆ community hall of fame • best reacted messages ⋆ ᯓ",
    1551184138932068373: "ᯓ ⋆ share your gaming clutches, clips, photos & aesthetic edits ⋆ ᯓ",
    1551184144153714728: "ᯓ ⋆ battlestations, pc hardware, mobile gaming & tech discussion ⋆ ᯓ",
    1550184397540556951: "ᯓ ⋆ esports discussion, strategies, game updates & squad banter ⋆ ᯓ",
    1550187304876900543: "ᯓ ⋆ 1-click squad finder & in-game team code drops ⋆ ᯓ",
    1550584592707100682: "ᯓ ⋆ share your favorite tracks, playlists & music discoveries ⋆ ᯓ",
    1550584226376720476: "ᯓ ⋆ movie discussions, anime watch parties & stream banter ⋆ ᯓ",
    1552359010513195099: "ᯓ ⋆ live dynamic voice suite controller • lock, rename & limit your vc ⋆ ᯓ",
    1550187321285148782: "ᯓ ⋆ executive administration & management sanctum ⋆ ᯓ",
    1545502845208629328: "ᯓ ⋆ staff operations & team coordination ⋆ ᯓ",
    1545514505520545886: "ᯓ ⋆ private member support & assistance desk ⋆ ᯓ",
}

@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found!")
        await client.close()
        return

    print(f"Applying all refinements to {guild.name}...")

    # 1. Rename Generator Channel
    gen_vc = guild.get_channel(1550187295821402114)
    if gen_vc and gen_vc.name != "➕・Join to Create VC":
        await gen_vc.edit(name="➕・Join to Create VC")
        print("1. Renamed generator VC to '➕・Join to Create VC'")

    # 2. Position channels in Gaming Hub
    gaming_chat = guild.get_channel(1550184397540556951)
    lfg_matchmaking = guild.get_channel(1550187304876900543)
    if gaming_chat and lfg_matchmaking:
        await gaming_chat.edit(position=0)
        await asyncio.sleep(0.5)
        await lfg_matchmaking.edit(position=1)
        print("2. Ordered gaming-chat (pos 0) and lfg-matchmaking (pos 1) in gaming hub")

    # 3. Apply Everglow Channel Topics
    print("3. Applying Everglow channel topics...")
    for ch_id, topic in TOPICS.items():
        ch = guild.get_channel(ch_id)
        if ch and isinstance(ch, discord.TextChannel):
            if ch.topic != topic:
                try:
                    await ch.edit(topic=topic)
                    print(f"  Set topic on {ch.name}")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  Error setting topic on {ch.name}: {e}")

    # 4. Boost Voice Bitrate to 96 kbps
    print("4. Boosting voice channels to 96 kbps...")
    for vc in guild.voice_channels:
        # Don't alter member counter channels
        if "Members" in vc.name or "Bots" in vc.name:
            continue
        if vc.bitrate != 96000:
            try:
                await vc.edit(bitrate=96000)
                print(f"  Set bitrate to 96 kbps on {vc.name}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  Could not set bitrate on {vc.name}: {e}")

    # 5. Polish Voice Control Deck Embed in #voice-controls
    vc_controls_ch = guild.get_channel(1552359010513195099)
    if vc_controls_ch:
        try:
            msg = await vc_controls_ch.fetch_message(1552359072203018282)
            embed = discord.Embed(
                title="🎛️ ┊ ᯓ ⋆ VOICE SUITE CONTROLLER ⋆ ᯓ",
                description=(
                    "✦ ───────────────────────────────────── ✦\n\n"
                    "### ⚡ **Manage Your Private Voice Suite in 1-Click**\n\n"
                    "Join **`➕・Join to Create VC`** to spawn your personal squad room, then use the buttons below:\n\n"
                    "• **🔒 Lock Room:** Restrict room to current occupants only\n"
                    "• **🔓 Unlock Room:** Re-open your room for anyone to join\n"
                    "• **👥 Member Limit:** Set custom party slot cap (1 to 25)\n"
                    "• **✏️ Rename Suite:** Give your room a custom title\n"
                    "• **👢 Kick / Remove:** Remove unwanted occupants\n\n"
                    "✦ ───────────────────────────────────── ✦\n"
                    "*Your custom room auto-deletes when everyone leaves.*"
                ),
                color=0xFF758C
            )
            embed.set_footer(text="RAI VIBES 💗 • Dynamic Suite Engine", icon_url=config.RAI_ICON_URL)
            await msg.edit(embed=embed)
            print("5. Polished Voice Suite Controller embed with Everglow aesthetic!")
        except Exception as e:
            print(f"5. Could not edit voice control message: {e}")

    print("All 5 refinements successfully applied!")
    await client.close()

client.run(os.getenv("DISCORD_BOT_TOKEN"))
