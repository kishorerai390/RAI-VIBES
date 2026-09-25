import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
load_dotenv()

GUILD_ID = 1457382179981099090

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found!")
        await client.close()
        return

    print(f"Creating Activity Tier & Color Roles in: {guild.name}...")

    # 1. Tier Roles Definition
    tier_roles = [
        ("─── ACTIVITY TIERS ───", 0x2F3136, False, discord.Permissions.none()),
        ("👑・Celestial Sovereign", 0xFFA502, True, discord.Permissions(embed_links=True, attach_files=True, use_external_emojis=True, use_external_stickers=True, change_nickname=True)),
        ("💫・Nebula Elite", 0xA55EEA, True, discord.Permissions(embed_links=True, attach_files=True, use_external_emojis=True, use_external_stickers=True, change_nickname=True)),
        ("🌸・Aurora Voyager", 0xFF758C, True, discord.Permissions(change_nickname=True, use_external_emojis=True, use_external_stickers=True)),
        ("✨・Starlight Initiate", 0x70A1FF, True, discord.Permissions(use_external_emojis=True, use_external_stickers=True)),
    ]

    created_tiers = {}
    for name, col, hoist, perms in tier_roles:
        r = discord.utils.get(guild.roles, name=name)
        if not r:
            r = await guild.create_role(
                name=name,
                color=discord.Color(col),
                hoist=hoist,
                permissions=perms,
                reason="Everglow Activity Tier Role Creation"
            )
            print(f"Created tier role: {name} (id={r.id})")
        else:
            await r.edit(color=discord.Color(col), hoist=hoist, permissions=perms)
            print(f"Updated tier role: {name} (id={r.id})")
        created_tiers[name] = r
        await asyncio.sleep(0.5)

    # 2. Color Palette Roles Definition
    color_roles = [
        ("─── PALETTE COLORS ───", 0x2F3136, False),
        ("Sakura Pink", 0xFF9AA2, False),
        ("Neon Purple", 0xB388FF, False),
        ("Cyber Cyan", 0x80D8FF, False),
        ("Royal Gold", 0xFFD700, False),
    ]

    created_colors = {}
    for name, col, hoist in color_roles:
        r = discord.utils.get(guild.roles, name=name)
        if not r:
            r = await guild.create_role(
                name=name,
                color=discord.Color(col),
                hoist=hoist,
                reason="Everglow Palette Role Creation"
            )
            print(f"Created color role: {name} (id={r.id})")
        else:
            await r.edit(color=discord.Color(col), hoist=hoist)
            print(f"Updated color role: {name} (id={r.id})")
        created_colors[name] = r
        await asyncio.sleep(0.5)

    # Move roles below bot role (position 27) and above member roles
    bot_member = guild.get_member(client.user.id)
    bot_top_role = bot_member.top_role if bot_member else None
    print(f"Bot top role: {bot_top_role.name} (pos={bot_top_role.position if bot_top_role else 0})")

    print("All tier and color roles successfully created/updated!")
    await client.close()

client.run(os.getenv("DISCORD_BOT_TOKEN"))
