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

# Chosen Elite Theme: Rai Royal Dynasty
CHOSEN_ROLES = [
    {
        "match": ["founder", "owner"],
        "name": "👑 ┊ 𝐄𝐌𝐏𝐄𝐑𝐎𝐑",
        "color": discord.Color.from_rgb(241, 196, 15), # Radiant Gold
        "hoist": True
    },
    {
        "match": ["co-owner", "admin", "administrator"],
        "name": "⚡ ┊ 𝐇𝐄𝐀𝐃 𝐀𝐃𝐌𝐈𝐍",
        "color": discord.Color.from_rgb(231, 76, 60), # Crimson Red
        "hoist": True
    },
    {
        "match": ["moderator", "mod", "staff"],
        "name": "🛡️ ┊ 𝐆𝐔𝐀𝐑𝐃𝐈𝐀𝐍",
        "color": discord.Color.from_rgb(52, 152, 219), # Royal Blue
        "hoist": True
    },
    {
        "match": ["vip", "booster"],
        "name": "💎 ┊ 𝐑𝐀𝐈 𝐄𝐋𝐈𝐓𝐄",
        "color": discord.Color.from_rgb(255, 105, 180), # Neon Pink
        "hoist": True
    },
    {
        "match": ["verified", "member", "active"],
        "name": "🌸 ┊ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘",
        "color": discord.Color.from_rgb(248, 165, 194), # Soft Rose
        "hoist": False
    },
    {
        "match": ["bot", "official bots"],
        "name": "🤖 ┊ 𝐀𝐔𝐃𝐈𝐎 𝐁𝐎𝐓𝐒",
        "color": discord.Color.from_rgb(149, 165, 166), # Slate
        "hoist": True
    }
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

    print(f"👑 Applying Rai Royal Dynasty roles to {guild.name}...")

    # Update matching existing roles
    for target in CHOSEN_ROLES:
        matched_role = None
        for role in guild.roles:
            if role.managed or role.is_default():
                continue
            if any(m in role.name.lower() for m in target["match"]):
                matched_role = role
                break

        if matched_role:
            try:
                await matched_role.edit(
                    name=target["name"],
                    color=target["color"],
                    hoist=target["hoist"],
                    reason="Applying Rai Royal Dynasty role theme"
                )
                print(f"  ✅ Updated Role: '{matched_role.name}' ➔ '{target['name']}'")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Could not update '{matched_role.name}': {e}")
        else:
            # Create role if missing
            try:
                new_r = await guild.create_role(
                    name=target["name"],
                    color=target["color"],
                    hoist=target["hoist"],
                    reason="Created missing Rai Dynasty role"
                )
                print(f"  + Created Role: '{target['name']}'")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  ⚠️ Could not create '{target['name']}': {e}")

    # Delete redundant roles like CO-ADMIN if still present
    for role in guild.roles:
        if role.name in ["CO-ADMIN", "Rythm", "Rythm 2"]:
            try:
                await role.delete(reason="Deleting redundant role")
                print(f"  ❌ Deleted redundant role: {role.name}")
            except Exception:
                pass

    print("\n🎉 RAI ROYAL DYNASTY ROLE THEME IS LIVE!")
    print("\n--- FINAL CLEAN ROLES ---")
    for r in sorted(guild.roles, key=lambda x: x.position, reverse=True):
        if not r.is_default():
            print(f"  • {r.name}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
