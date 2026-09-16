import os
import sys
import asyncio
import discord
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

import config

TOKEN = config.DISCORD_TOKEN
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 1457382179981099090))


async def update_avatar(client: discord.Client, file_path: str):
    if not os.path.exists(file_path):
        print(f"[Error] File not found: {file_path}")
        return
    with open(file_path, "rb") as f:
        data = f.read()
    await client.user.edit(avatar=data)
    print(f"[Success] Updated bot avatar from {file_path}")


async def update_banner(client: discord.Client, file_path: str):
    if not os.path.exists(file_path):
        print(f"[Error] File not found: {file_path}")
        return
    with open(file_path, "rb") as f:
        data = f.read()
    await client.user.edit(banner=data)
    print(f"[Success] Updated bot profile banner from {file_path}")


async def upload_emojis_from_folder(client: discord.Client, folder_path: str):
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"[Error] Guild {GUILD_ID} not found.")
        return

    if not os.path.isdir(folder_path):
        print(f"[Error] Directory not found: {folder_path}")
        return

    files = [f for f in os.listdir(folder_path) if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif"))]
    print(f"Found {len(files)} potential emoji assets in {folder_path}...")

    for f in files:
        name = os.path.splitext(f)[0].replace("-", "_").replace(" ", "_").lower()
        # Check if emoji exists
        if any(e.name == name for e in guild.emojis):
            print(f" - Emoji :{name}: already exists in {guild.name}, skipping.")
            continue
        full_path = os.path.join(folder_path, f)
        try:
            with open(full_path, "rb") as img:
                emoji = await guild.create_custom_emoji(name=name, image=img.read(), reason="Branding tool upload")
                print(f" + Uploaded :{emoji.name}: ({emoji.id})")
        except Exception as e:
            print(f" x Failed to upload {name}: {e}")


def print_help():
    print("""
Branding & Assets CLI Tool
Usage:
  python tools/branding_tool.py avatar <path_to_image>
  python tools/branding_tool.py banner <path_to_image_or_gif>
  python tools/branding_tool.py upload-emojis <path_to_folder>
""")


async def main():
    if len(sys.argv) < 2:
        print_help()
        return

    cmd = sys.argv[1]
    arg = sys.argv[2] if len(sys.argv) > 2 else ""

    intents = discord.Intents.default()
    intents.guilds = True
    intents.emojis = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        if cmd == "avatar" and arg:
            await update_avatar(client, arg)
        elif cmd == "banner" and arg:
            await update_banner(client, arg)
        elif cmd == "upload-emojis" and arg:
            await upload_emojis_from_folder(client, arg)
        else:
            print_help()
        await client.close()

    await client.start(TOKEN)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print_help()
    else:
        asyncio.run(main())
