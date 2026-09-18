import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
import asyncio
import discord
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

# Core essential roles to KEEP
KEEP_ROLES = [
    "Founder & Owner",
    "👑 Founder & Owner",
    "👑 Owner",
    "Administrator",
    "⚡ Co-Owner / Administrator",
    "⚡ Admin",
    "Moderator",
    "🛡️ Moderator / Staff",
    "🛡️ Mod",
    "VIP & Server Booster",
    "💎 VIP & Server Booster",
    "💎 VIP",
    "Verified Member",
    "👥 Verified Member",
    "Official Bots",
    "🤖 Official Bots",
    "RAI VIBES",
    "APEX VIBES",
    "Rythm",
    "@everyone"
]

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    print(f"🧹 Purging bloated/unnecessary roles in {guild.name}...")

    roles_to_check = list(guild.roles)
    deleted_count = 0

    for role in roles_to_check:
        # Don't delete @everyone or managed bot integration roles
        if role.is_default() or role.managed:
            continue
        
        # Check if role is in KEEP list
        should_keep = any(k.lower() in role.name.lower() for k in [
            "founder", "owner", "admin", "moderator", "mod", "booster", "vip", "verified", "bot"
        ])

        if not should_keep:
            try:
                await role.delete(reason="Removing bloated unnecessary role")
                print(f"  ❌ Deleted role: {role.name}")
                deleted_count += 1
                await asyncio.sleep(0.4)
            except Exception as e:
                print(f"  ⚠️ Could not delete '{role.name}': {e}")

    print(f"\n✅ ROLE CLEANUP COMPLETE! Deleted {deleted_count} unnecessary roles.")
    print("\n--- REMAINING CLEAN ROLES ---")
    for r in sorted(guild.roles, key=lambda x: x.position, reverse=True):
        if not r.is_default():
            print(f"  • {r.name}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
