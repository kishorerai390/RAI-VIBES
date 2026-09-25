import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

GUILD_ID = 1457382179981099090
VERIFIED_ROLE_ID = 1549504522953695269

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found!")
        await client.close()
        return

    print(f"Applying Variation 3A to guild: {guild.name}...")
    verified_role = guild.get_role(VERIFIED_ROLE_ID)
    everyone_role = guild.default_role

    member_overwrites = {
        everyone_role: discord.PermissionOverwrite(view_channel=False),
        verified_role: discord.PermissionOverwrite(view_channel=True, send_messages=True, connect=True)
    }

    # 1. Fetch existing categories
    cats = {cat.id: cat for cat in guild.categories}

    server_stats_cat = cats.get(1546059369085534229)
    info_cat = cats.get(1545803464712650844)
    comm_cat = cats.get(1545803478490812578)
    music_cat = cats.get(1550198448203112539)
    cinema_cat = cats.get(1550197872006398014)
    gaming_cat = cats.get(1550186748364066827)
    voice_cat = cats.get(1550186724137640006)
    staff_cat = cats.get(1545803487093456906)

    # 2. Rename existing categories
    if server_stats_cat:
        await server_stats_cat.edit(name="ᯓ ⋆ server stats")
        print("Renamed server stats category")
    if info_cat:
        await info_cat.edit(name="ᯓ ⋆ overview")
        print("Renamed overview category")
    if comm_cat:
        await comm_cat.edit(name="ᯓ ⋆ community")
        print("Renamed community category")
    if gaming_cat:
        await gaming_cat.edit(name="ᯓ ⋆ gaming hub")
        print("Renamed gaming hub category")
    if music_cat:
        await music_cat.edit(name="ᯓ ⋆ acoustic & cinema")
        print("Renamed acoustic & cinema category")
    if voice_cat:
        await voice_cat.edit(name="ᯓ ⋆ voice lounge")
        print("Renamed voice lounge category")
    if staff_cat:
        await staff_cat.edit(name="ᯓ ⋆ staff sanctum")
        print("Renamed staff sanctum category")

    # 3. Create or find new categories
    creator_cat = discord.utils.get(guild.categories, name="ᯓ ⋆ creator studio")
    if not creator_cat:
        creator_cat = await guild.create_category(
            name="ᯓ ⋆ creator studio",
            overwrites=member_overwrites,
            reason="Everglow 3A Reorganization"
        )
        print("Created category: ᯓ ⋆ creator studio")

    personal_vc_cat = discord.utils.get(guild.categories, name="ᯓ ⋆ personal vc")
    if not personal_vc_cat:
        personal_vc_cat = await guild.create_category(
            name="ᯓ ⋆ personal vc",
            overwrites=member_overwrites,
            reason="Everglow 3A Reorganization"
        )
        print("Created category: ᯓ ⋆ personal vc")

    # 4. Move Cinema channels into acoustic & cinema, then delete old cinema category
    if cinema_cat:
        for ch in list(cinema_cat.channels):
            await ch.edit(category=music_cat)
            await asyncio.sleep(0.5)
        try:
            await cinema_cat.delete(reason="Merged into acoustic & cinema")
            print("Deleted old cinema category after moving channels")
        except Exception as e:
            print(f"Could not delete old cinema category: {e}")

    # 5. Channel Renames & Re-categorizations
    channel_plans = [
        # (channel_id, new_name, target_category, user_limit)
        # OVERVIEW
        (1545502700840427702, "✨・verify-here", info_cat, None),
        (1545502705643167876, "🌸・welcome", info_cat, None),
        (1545502710101704714, "📜・rules-and-info", info_cat, None),
        (1545502718792175646, "📢・announcements", info_cat, None),
        (1545502722739150898, "🏷️・roles", info_cat, None),
        (1550159859607928882, "🤝・partnerships", info_cat, None),

        # COMMUNITY
        (1545502730699808768, "💬・general-chat", comm_cat, None),
        (1549416359723532480, "🤖・bot-cmds", comm_cat, None),
        (1550184399742697512, "💸・arcade", comm_cat, None),
        (1551184190073213071, "⭐・starboard", comm_cat, None),

        # CREATOR STUDIO
        (1551184138932068373, "📸・clips-and-media", creator_cat, None),
        (1551184144153714728, "🖥️・setups-and-tech", creator_cat, None),
        (1552354617415962785, "🎥・recording-studio", creator_cat, 0),
        (1552354619466977423, "✂️・editing-lounge", creator_cat, 0),

        # GAMING HUB
        (1550184397540556951, "💬・gaming-chat", gaming_cat, None),  # moved from community
        (1550187304876900543, "🎮・lfg-matchmaking", gaming_cat, None),
        (1550186750289379328, "⚡・free-fire-squad", gaming_cat, 4),
        (1550186752163975250, "⚡・bgmi-squad", gaming_cat, 4),
        (1550580964122566770, "🎯・valorant", gaming_cat, 5),
        (1550196963935264870, "🚗・gta-rp", gaming_cat, 0),
        (1550580961513701488, "⚔️・1v1-arena", gaming_cat, 2),
        (1550196967987089480, "🏆・custom-scrims", gaming_cat, 0),
        (1550582498776322191, "👑・tournament-finals", gaming_cat, 0),

        # ACOUSTIC & CINEMA
        (1550584592707100682, "🎧・music-sharing", music_cat, None),
        (1550584226376720476, "🍿・cinema-chat", music_cat, None),
        (1550186760779211003, "🎧・music-studio", music_cat, 0),
        (1550196959841878098, "🌧️・midnight-lofi", music_cat, 0),
        (1550196955660029964, "🎬・movie-premiere-1", music_cat, 0),
        (1550198444021514331, "🎬・movie-premiere-2", music_cat, 0),

        # PERSONAL VC
        (1552359010513195099, "🎛️・voice-controls", personal_vc_cat, None),
        (1550187295821402114, "➕・create-your-vc", personal_vc_cat, 0),

        # VOICE LOUNGE
        (1550186738410987591, "💬・cafe-lounge-1", voice_cat, 0),
        (1550186767632826459, "💬・cafe-lounge-2", voice_cat, 0),
        (1550186728285937727, "👥・duo-chamber", voice_cat, 2),
        (1550196951503474798, "🔺・trio-chamber", voice_cat, 3),
        (1550580967427538994, "🛡️・squad-chamber", voice_cat, 4),
        (1550580969843728424, "🎧・focus-study", voice_cat, 0),
        (1550187298115551272, "💤・afk-sleep", voice_cat, 0),

        # STAFF SANCTUM
        (1550187321285148782, "👑・executive-lounge", staff_cat, None),
        (1545502845208629328, "🛡️・staff-ops", staff_cat, None),
        (1545514505520545886, "🎫・tickets", staff_cat, None),
        (1546540192343523399, "📝・mod-logs", staff_cat, None),
        (1546593526073135107, "🚨・sentinel-logs", staff_cat, None),
        (1545502850057244762, "📋・audit-logs", staff_cat, None),
        (1550187323084374079, "👑・executive-suite", staff_cat, 0),
    ]

    for ch_id, name, cat, limit in channel_plans:
        ch = guild.get_channel(ch_id)
        if not ch:
            print(f"Channel {ch_id} not found!")
            continue

        kwargs = {}
        if ch.name != name:
            kwargs["name"] = name
        if ch.category_id != (cat.id if cat else None):
            kwargs["category"] = cat
        if limit is not None and isinstance(ch, discord.VoiceChannel) and ch.user_limit != limit:
            kwargs["user_limit"] = limit

        if kwargs:
            try:
                await ch.edit(**kwargs)
                print(f"Updated channel {ch_id} -> {name} in {cat.name if cat else 'None'}")
            except Exception as e:
                print(f"Error editing channel {ch_id}: {e}")
            await asyncio.sleep(0.5)

    # 6. Set Category Positions
    category_order = [
        server_stats_cat,
        info_cat,
        comm_cat,
        creator_cat,
        gaming_cat,
        music_cat,
        personal_vc_cat,
        voice_cat,
        staff_cat
    ]

    for idx, cat in enumerate(category_order):
        if cat and cat.position != idx:
            try:
                await cat.edit(position=idx)
                print(f"Set position of {cat.name} to {idx}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error setting position for {cat.name}: {e}")

    print("Variation 3A layout successfully applied!")
    await client.close()

client.run(os.getenv("DISCORD_BOT_TOKEN"))
