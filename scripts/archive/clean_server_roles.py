import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

ROLES_TO_PURGE_IDS = [
    1549395558014255108,  # ✦ Rising Star (0 members)
    1549395561109520438,  # ✦ Adventurer (0 members)
    1549395565584851026,  # ✦ Vanguard (0 members)
    1549395569217118280,  # ✦ Immortal (0 members)
    1546088542885642324,  # 📢 ✧ ANNOUNCEMENTS (0 members)
    1546088546555924534,  # 🎉 ✧ GIVEAWAYS (0 members)
    1546088548913119323,  # ⚔️ ✧ TOURNAMENTS (0 members)
    1546095937015910434,  # 👧 ✧ FEMALE (0 members)
    1546095941818392647,  # 🎒 ✧ UNDER 18 (0 members)
    1546540195724140574,  # Unverified (0 members)
    1547277222170198147,  # Zynrax Prime Security™
    1547277224036798465,  # Zynrax Unbypassable Security™
    1546553559863001148,  # ⚡ ┆ Bot Administrator
]

VERIFIED_ROLE_ID = 1546540194310782976
RAI_FAMILY_ROLE_ID = 1545494584203673740

client = discord.Client(intents=discord.Intents.all())

@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"Error: Guild {GUILD_ID} not found.")
        await client.close()
        return

    print(f"🌟 Connected to {guild.name} ({guild.id})")
    print(f"Current role count: {len(guild.roles)}")

    # 1. Migrate Verified members to RAI FAMILY
    ver_role = guild.get_role(VERIFIED_ROLE_ID)
    rai_role = guild.get_role(RAI_FAMILY_ROLE_ID)

    if ver_role and rai_role:
        print(f"\n🔄 Migrating members from '{ver_role.name}' to '{rai_role.name}'...")
        migrated = 0
        for m in ver_role.members:
            if rai_role not in m.roles:
                try:
                    await m.add_roles(rai_role, reason="Role consolidation to RAI FAMILY")
                    print(f"  + Added '{rai_role.name}' to {m.display_name}")
                    migrated += 1
                except Exception as e:
                    print(f"  ! Failed to add role to {m.display_name}: {e}")
        print(f"  Migrated {migrated} members successfully.")

        # Delete Verified role
        try:
            await ver_role.delete(reason="Merged into RAI FAMILY")
            print(f"  ✅ Successfully deleted redundant '{ver_role.name}' role.")
        except Exception as e:
            print(f"  ! Failed to delete '{ver_role.name}': {e}")

    # 2. Delete unwanted / dead / bot residue roles
    print("\n🗑️ Purging dead and bot-residue roles...")
    for r_id in ROLES_TO_PURGE_IDS:
        r = guild.get_role(r_id)
        if r:
            name = r.name
            try:
                await r.delete(reason="Server declutter and role simplification")
                print(f"  ✅ Deleted: {name} ({r_id})")
            except Exception as e:
                print(f"  ❌ Could not delete {name}: {e}")
        else:
            print(f"  ℹ️ Role {r_id} already deleted or not found.")

    print(f"\n🎉 Role cleanup complete! New total roles: {len(guild.roles)}")
    print("\nRemaining Active Roles Hierarchy:")
    for r in sorted(guild.roles, key=lambda x: x.position, reverse=True):
        print(f"  [{r.position:2d}] {r.name} ({len(r.members)} members)")

    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
