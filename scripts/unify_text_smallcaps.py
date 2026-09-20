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

# Unify verify-here and welcome to match all other Small Caps text channels
UPDATES = {
    1545502700840427702: "✨・ᴠᴇʀɪꜰʏ-ʜᴇʀᴇ",
    1545502705643167876: "🌸・ᴡᴇʟᴄᴏᴍᴇ",
}

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

    print("Unifying text channels to 100% clean Small Caps...")
    for ch_id, new_name in UPDATES.items():
        ch = guild.get_channel(ch_id)
        if ch:
            if ch.name != new_name:
                try:
                    await ch.edit(name=new_name)
                    print(f"  ✅ Updated: {ch.name} -> {new_name}")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  ⚠️ Error updating {ch.id}: {e}")
            else:
                print(f"  ✨ Already matched: {new_name}")

    print("Text channels are now 100% unified!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
