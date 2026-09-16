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


async def list_roles(client: discord.Client):
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"[Error] Guild {GUILD_ID} not found.")
        return

    print(f"\n========================================================")
    print(f"  ROLE INVENTORY: {guild.name} ({guild.id})")
    print(f"  Total Roles: {len(guild.roles)}")
    print(f"========================================================\n")
    
    for r in sorted(guild.roles, key=lambda x: x.position, reverse=True):
        print(f"[{r.position:02d}] {r.name:<35} | ID: {r.id} | Members: {len(r.members)}")


async def audit_empty_roles(client: discord.Client):
    guild = client.get_guild(GUILD_ID)
    if not guild:
        return

    empty = [r for r in guild.roles if len(r.members) == 0 and not r.is_default() and not r.managed]
    print(f"\n[Audit] Found {len(empty)} unmanaged empty roles:")
    for r in empty:
        print(f" - {r.name} (ID: {r.id})")


def print_help():
    print("""
Role Manager CLI Tool
Usage:
  python tools/role_manager.py [command]

Commands:
  list    - List all roles with IDs, positions, and member counts
  empty   - Identify unused / 0-member custom roles
""")


async def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"
    if cmd not in ["list", "empty"]:
        print_help()
        return

    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True

    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        if cmd == "list":
            await list_roles(client)
        elif cmd == "empty":
            await audit_empty_roles(client)
        await client.close()

    await client.start(TOKEN)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ["--help", "-h", "help"]:
        print_help()
    else:
        asyncio.run(main())
