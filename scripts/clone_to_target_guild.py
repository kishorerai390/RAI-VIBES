import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SOURCE_GUILD_ID = 1457382179981099090  # RAI FAM
TARGET_GUILD_ID = 1428058914141900860  # ABIJITH 777

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    source = client.get_guild(SOURCE_GUILD_ID)
    target = client.get_guild(TARGET_GUILD_ID)

    if not source:
        print(f"Source guild {SOURCE_GUILD_ID} not found!")
        await client.close()
        return

    if not target:
        print(f"Target guild {TARGET_GUILD_ID} not found! Please invite the bot to ABIJITH 777 first using:")
        print(f"https://discord.com/oauth2/authorize?client_id={client.user.id}&permissions=8&scope=bot%20applications.commands")
        await client.close()
        return

    print(f"Cloning from '{source.name}' to '{target.name}'...")

    # 1. Map roles or ensure essential roles
    role_map = {}
    for src_role in source.roles:
        if src_role.name not in ["@everyone", "RAI VIBES"]:
            tgt_role = discord.utils.get(target.roles, name=src_role.name)
            if not tgt_role:
                try:
                    tgt_role = await target.create_role(
                        name=src_role.name,
                        color=src_role.color,
                        hoist=src_role.hoist,
                        mentionable=src_role.mentionable,
                        reason="Replicating roles from source community"
                    )
                    print(f"Created role: {tgt_role.name}")
                    await asyncio.sleep(0.4)
                except Exception as e:
                    print(f"Error creating role {src_role.name}: {e}")
            if tgt_role:
                role_map[src_role.id] = tgt_role

    # 2. Replicate Categories and Channels
    for cat in sorted(source.categories, key=lambda c: c.position):
        # User specified: change music area to gaming area
        cat_name = cat.name
        if "MUSIC" in cat_name.upper():
            cat_name = "🎮 GAMING AREA"

        tgt_cat = discord.utils.get(target.categories, name=cat_name)
        if not tgt_cat:
            try:
                tgt_cat = await target.create_category(
                    name=cat_name,
                    position=cat.position,
                    reason="Replicating server structure"
                )
                print(f"Created Category: {tgt_cat.name} (pos={cat.position})")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"Error creating category {cat_name}: {e}")
                continue

        # Channels inside category
        for ch in sorted(cat.channels, key=lambda c: c.position):
            tgt_ch = discord.utils.get(tgt_cat.channels, name=ch.name)
            if not tgt_ch:
                try:
                    if isinstance(ch, discord.VoiceChannel):
                        tgt_ch = await target.create_voice_channel(
                            name=ch.name,
                            category=tgt_cat,
                            user_limit=ch.user_limit,
                            bitrate=min(ch.bitrate or 96000, 96000),
                            position=ch.position,
                            reason="Replicating voice channel"
                        )
                        print(f"  Created VC: {tgt_ch.name}")
                    else:
                        tgt_ch = await target.create_text_channel(
                            name=ch.name,
                            category=tgt_cat,
                            topic=ch.topic,
                            position=ch.position,
                            reason="Replicating text channel"
                        )
                        print(f"  Created Text: {tgt_ch.name}")
                    await asyncio.sleep(0.4)
                except Exception as e:
                    print(f"Error creating channel {ch.name}: {e}")

    # Set AFK if source afk exists
    if source.afk_channel:
        tgt_afk = discord.utils.get(target.voice_channels, name=source.afk_channel.name)
        if tgt_afk:
            await target.edit(afk_channel=tgt_afk, afk_timeout=300)
            print(f"Configured AFK channel in target: {tgt_afk.name}")

    print(f"\nSuccessfully replicated server structure into '{target.name}'!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
