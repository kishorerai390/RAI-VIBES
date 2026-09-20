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
    print(f"Removing '┊' Dividers -> Clean Minimalist Aesthetic")
    print(f"Server: {guild.name}")
    print("Rule: 100% Preserving Channel Layout & Ordering")
    print("==================================================")

    updated_count = 0
    skipped_count = 0

    for ch in guild.channels:
        # We only touch Text, Voice, News channels (leave categories alone)
        if isinstance(ch, discord.CategoryChannel):
            continue

        cur_name = ch.name
        new_name = cur_name

        # If it's a Voice channel:
        if isinstance(ch, discord.VoiceChannel):
            # Replace " ┊ " or "┊" or " | " with clean single space
            if " ┊ " in new_name:
                new_name = new_name.replace(" ┊ ", " ")
            elif "┊" in new_name:
                new_name = new_name.replace("┊", " ")
            elif " | " in new_name:
                new_name = new_name.replace(" | ", " ")
            elif "｜" in new_name:
                new_name = new_name.replace("｜", " ")

        # If it's a Text or News channel:
        elif isinstance(ch, (discord.TextChannel, discord.StageChannel)):
            # Replace "┊" or "｜" or " | " with aesthetic middle dot "・"
            if "┊" in new_name:
                new_name = new_name.replace("┊", "・")
            elif " ┊ " in new_name:
                new_name = new_name.replace(" ┊ ", "・")
            elif "｜" in new_name:
                new_name = new_name.replace("｜", "・")
            elif " | " in new_name:
                new_name = new_name.replace(" | ", "・")

        # Clean up any accidental double spaces
        while "  " in new_name:
            new_name = new_name.replace("  ", " ")

        if new_name != cur_name:
            try:
                # ONLY edit the name. Never change position or category.
                await ch.edit(name=new_name)
                print(f"  [UPDATED] {ch.id}: '{cur_name}' -> '{new_name}'")
                updated_count += 1
                await asyncio.sleep(0.6)
            except Exception as e:
                print(f"  [ERROR] {ch.id} ({cur_name}): {e}")
        else:
            skipped_count += 1

    print("==================================================")
    print(f"Done! {updated_count} channels updated, {skipped_count} skipped/already clean.")
    print("==================================================")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
