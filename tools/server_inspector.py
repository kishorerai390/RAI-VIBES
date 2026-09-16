import os
import sys
import asyncio
import discord
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)
load_dotenv(os.path.join(BASE_DIR, ".env"))

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 1457382179981099090))


async def inspect_channels(client: discord.Client):
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"[Error] Guild {GUILD_ID} not found.")
        return

    print(f"\n========================================================")
    print(f"  SERVER STRUCTURE: {guild.name} ({guild.id})")
    print(f"  Categories: {len(guild.categories)} | Text: {len(guild.text_channels)} | Voice: {len(guild.voice_channels)}")
    print(f"========================================================\n")

    for cat in sorted(guild.categories, key=lambda x: x.position):
        print(f"\n📂 CATEGORY: {cat.name} (pos: {cat.position})")
        for ch in sorted(cat.channels, key=lambda x: x.position):
            ch_type = "TEXT" if isinstance(ch, discord.TextChannel) else "VOICE"
            print(f"   └─ [{ch_type}] {ch.name} (ID: {ch.id})")

    no_cat = [c for c in guild.channels if c.category is None and not isinstance(c, discord.CategoryChannel)]
    if no_cat:
        print(f"\n📁 UNFILED CHANNELS:")
        for ch in sorted(no_cat, key=lambda x: x.position):
            ch_type = "TEXT" if isinstance(ch, discord.TextChannel) else "VOICE"
            print(f"   └─ [{ch_type}] {ch.name} (ID: {ch.id})")


async def inspect_health(client: discord.Client):
    guild = client.get_guild(GUILD_ID)
    print(f"\n========================================================")
    print(f"  BOT STATUS & TELEMETRY")
    print(f"========================================================")
    print(f"Bot User: {client.user} (ID: {client.user.id})")
    print(f"Latency: {round(client.latency * 1000, 2)} ms")
    if guild:
        print(f"Target Guild: {guild.name} ({guild.id})")
        print(f"Member Count: {guild.member_count}")
        print(f"Roles Count: {len(guild.roles)}")
        print(f"Channels Count: {len(guild.channels)}")
        print(f"Bot Perms: Administrator = {guild.me.guild_permissions.administrator}")
    else:
        print(f"Target Guild {GUILD_ID} not reached by bot!")


def print_help():
    print("""
Server Inspector CLI Tool
Usage:
  python tools/server_inspector.py [command]

Commands:
  health    - Check bot connectivity, ping, and guild permissions
  channels  - Display categorized channel structure and IDs
""")


async def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "health"
    if cmd not in ["health", "channels"]:
        print_help()
        return

    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        if cmd == "health":
            await inspect_health(client)
        elif cmd == "channels":
            await inspect_channels(client)
        await client.close()

    await client.start(TOKEN)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print_help()
    else:
        asyncio.run(main())
