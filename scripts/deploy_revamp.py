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

ROLES_TO_ENSURE = [
    # (Name, Color, Hoist, Mentionable)
    ("─── MANAGEMENT ───", 0x2F3136, False, False),
    ("🛠️ ┆ 𝐓𝐑𝐈𝐀𝐋 𝐌𝐎𝐃", 0x34495E, True, True),
    ("─── SPECIAL & ELITE ───", 0x2F3136, False, False),
    ("💎・VIP / Elite", 0x00D2D3, True, True),
    ("🏆・Tournament Champion", 0xF1C40F, True, True),
    ("─── GAME SELECTOR ───", 0x2F3136, False, False),
    ("🎯・Valorant / CS2", 0xFA4454, False, True),
    ("⚡・BGMI / PUBG", 0xE67E22, False, True),
    ("🔥・Free Fire", 0xE74C3C, False, True),
    ("🏎️・GTA RP", 0x3498DB, False, True),
    ("🚀・Rocket League", 0x00CEC9, False, True),
    ("─── NOTIFICATIONS ───", 0x2F3136, False, False),
    ("📢・Announcements", 0xA55EEA, False, True),
    ("🎁・Giveaways", 0x2ECC71, False, True),
    ("🏆・Tournaments", 0xE74C3C, False, True),
    ("🍿・Movie Nights", 0xFF4757, False, True),
    ("📻・Live DJ & Radio", 0x9B59B6, False, True),
]

CATEGORIES_AND_CHANNELS = [
    {
        "name": "◈ 𝕮 𝕽 𝕰 𝕬 𝕿 𝕴 𝖁 𝕰  𝕳 𝖀 𝕭 ◈",
        "channels": [
            {"name": "📸┊media-and-clips", "type": "text", "topic": "📸 Share your gaming clips, setup photos, and community media!"},
            {"name": "🖥️┊setups-and-tech", "type": "text", "topic": "🖥️ Hardware, battlestations, mechanical keyboards, and tech banter."},
            {"name": "🎨┊art-and-design", "type": "text", "topic": "🎨 Digital art, graphic design, 3D renders, and creative showcase."}
        ]
    },
    {
        "name": "◈ ℙ ℝ 𝕆 𝔻 𝕌 ℂ 𝕋 𝕀 𝕍 𝕀 𝕋 𝕐 ◈",
        "channels": [
            {"name": "🎯┊daily-goals", "type": "text", "topic": "🎯 Post your daily goals, check in habits, and track streaks."},
            {"name": "🍅┊pomodoro-chat", "type": "text", "topic": "🍅 Synced Pomodoro focus session commands and work updates."},
            {"name": "🎧 ┊ Focus & Study VC", "type": "voice", "bitrate": 64000, "user_limit": 0}
        ]
    }
]

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"🤖 Connected as {client.user} ({client.user.id})")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"❌ Guild {GUILD_ID} not found!")
        await client.close()
        return

    print(f"🌟 Revamping Server Architecture for '{guild.name}'...")

    everyone = guild.default_role
    verified_role = discord.utils.get(guild.roles, name="✨・Verified")
    if not verified_role:
        for r in guild.roles:
            if "verified" in r.name.lower() or r.id == 1549504522953695269:
                verified_role = r
                break

    print(f"🛡️ Verified Role: {verified_role.name} ({verified_role.id})")

    # 1. ROLES AUDIT & CREATION
    print("\n--- 1. ROLES SETUP ---")
    existing_roles = {r.name.lower().strip(): r for r in guild.roles}
    created_roles = {}

    for name, color, hoist, mentionable in ROLES_TO_ENSURE:
        key = name.lower().strip()
        matched = None
        for k, r in existing_roles.items():
            if k == key or name.split("・")[-1].lower() in k:
                matched = r
                break
        
        if matched:
            print(f"  ✓ Role already exists: {matched.name}")
            created_roles[name] = matched
        else:
            try:
                new_r = await guild.create_role(
                    name=name,
                    colour=discord.Colour(color),
                    hoist=hoist,
                    mentionable=mentionable,
                    reason="Server Revamp: Role Hierarchy Initialization"
                )
                print(f"  ✨ Created role: {new_r.name} (id={new_r.id})")
                created_roles[name] = new_r
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Error creating role '{name}': {e}")

    # 2. CATEGORIES & CHANNELS SETUP
    print("\n--- 2. CATEGORIES & CHANNELS SETUP ---")
    for cat_data in CATEGORIES_AND_CHANNELS:
        cat_name = cat_data["name"]
        cat = discord.utils.get(guild.categories, name=cat_name)
        
        # Overwrites for new categories
        overwrites = {
            everyone: discord.PermissionOverwrite(view_channel=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, manage_channels=True, manage_permissions=True, send_messages=True)
        }
        if verified_role:
            overwrites[verified_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                embed_links=True,
                attach_files=True,
                read_message_history=True,
                connect=True,
                speak=True,
                stream=True
            )

        if not cat:
            try:
                cat = await guild.create_category(
                    name=cat_name,
                    overwrites=overwrites,
                    reason="Server Revamp: Category Creation"
                )
                print(f"  ✨ Created category: {cat.name}")
            except Exception as e:
                print(f"  ❌ Error creating category '{cat_name}': {e}")
                continue
        else:
            print(f"  ✓ Category already exists: {cat.name}")
            # Ensure permissions are synced
            try:
                await cat.set_permissions(everyone, view_channel=False)
                if verified_role:
                    await cat.set_permissions(verified_role, view_channel=True, send_messages=True, connect=True, speak=True, stream=True)
            except Exception as e:
                print(f"    ⚠️ Permission update warning: {e}")

        await asyncio.sleep(0.5)

        # Create Channels inside Category
        for ch_info in cat_data["channels"]:
            ch_name = ch_info["name"]
            ch_type = ch_info["type"]
            ch_topic = ch_info.get("topic", "")

            existing_ch = discord.utils.get(cat.channels, name=ch_name)
            if existing_ch:
                print(f"    ✓ Channel already exists: {existing_ch.name}")
            else:
                try:
                    if ch_type == "text":
                        new_ch = await guild.create_text_channel(
                            name=ch_name,
                            category=cat,
                            topic=ch_topic,
                            reason="Server Revamp: New Channel"
                        )
                        print(f"    ✨ Created text channel: #{new_ch.name}")
                    elif ch_type == "voice":
                        bitrate = ch_info.get("bitrate", 64000)
                        user_limit = ch_info.get("user_limit", 0)
                        new_vc = await guild.create_voice_channel(
                            name=ch_name,
                            category=cat,
                            bitrate=bitrate,
                            user_limit=user_limit,
                            reason="Server Revamp: New Voice Channel"
                        )
                        print(f"    ✨ Created voice channel: 🔊 {new_vc.name}")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"    ❌ Error creating channel '{ch_name}': {e}")

    # 3. ENSURE STARBOARD IN COMMUNITY CATEGORY
    comm_cat = discord.utils.get(guild.categories, id=1545803478490812578)
    if comm_cat:
        starboard = discord.utils.get(comm_cat.text_channels, name="⭐┊starboard") or discord.utils.get(comm_cat.text_channels, name="⭐┊ꜱᴛᴀʀʙᴏᴀʀᴅ")
        if not starboard:
            try:
                starboard = await guild.create_text_channel(
                    name="⭐┊ꜱᴛᴀʀʙᴏᴀʀᴅ",
                    category=comm_cat,
                    topic="⭐ Community Hall of Fame • Top voted messages & moments.",
                    reason="Server Revamp: Starboard Channel"
                )
                print(f"  ✨ Created starboard channel: #{starboard.name}")
            except Exception as e:
                print(f"  ⚠️ Could not create starboard: {e}")

    # 4. AUDIT & TUNE CATEGORY ORDER
    print("\n--- 3. ORDERING CATEGORIES CLEANLY ---")
    desired_order = [
        "◈ 𝚂 𝙴 𝚁 𝚅 𝙴 𝚁  𝚂 𝚃 𝙰 𝚃 𝚂 ◈",
        "◈ 𝓘 𝓝 𝓕 𝓞 𝓡 𝓜 𝓐 𝓣 𝓘 𝓞 𝓝 ◈",
        "◈ 𝐂 𝐎 𝐌 𝐌 Ｕ Ｎ Ｉ 𝐓 Ｙ ◈",
        "◈ 𝕮 𝕽 𝕰 𝕬 𝕿 𝕴 𝖁 𝕰  𝕳 𝖀 𝕭 ◈",
        "◈ ℙ ℝ 𝕆 𝔻 𝕌 ℂ 𝕋 𝕀 𝕍 𝕀 𝕋 𝕐 ◈",
        "◈ 𝔾 𝔸 𝕄 𝕀 ℕ 𝔾  ℤ 𝕆 ℕ 𝔼 ◈",
        "🍿 CINEMA HUB",
        "🎵 MUSIC LOUNGE",
        "◈ 𝐕 𝐎 Ｉ 𝐂 𝔼  𝐋 𝐎 Ｕ Ｎ 𝔾 𝔼 ◈",
        "◈ 𝔖 𝔗 𝔄 𝔉 𝔉  ℌ 𝔔 ◈"
    ]

    for target_pos, cat_name in enumerate(desired_order):
        matched_cat = discord.utils.get(guild.categories, name=cat_name)
        if matched_cat:
            try:
                if matched_cat.position != target_pos:
                    await matched_cat.edit(position=target_pos)
                    print(f"  📐 Positioned '{matched_cat.name}' at index {target_pos}")
                    await asyncio.sleep(0.3)
            except Exception as e:
                print(f"  ⚠️ Could not reposition '{cat_name}': {e}")

    print("\n✅ Server Architecture & Layout Revamp Complete!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
