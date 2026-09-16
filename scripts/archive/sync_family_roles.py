import os
import sys
import asyncio
import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

intents = discord.Intents.all()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user} ({client.user.id})")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    family_role = discord.utils.get(guild.roles, name="🌸 ┊ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘")
    bot_role = discord.utils.get(guild.roles, name="🤖 ┊ 𝐀𝐔𝐃𝐈𝐎 𝐁𝐎𝐓𝐒")

    if not family_role:
        print("Family role not found")
        await client.close()
        return

    count = 0
    for member in guild.members:
        if member.bot:
            if bot_role and bot_role not in member.roles:
                try:
                    await member.add_roles(bot_role, reason="Auto-assign Bot role")
                    print(f"Added bot role to {member.display_name}")
                except Exception as e:
                    print(f"Error adding bot role: {e}")
        else:
            if family_role not in member.roles:
                try:
                    await member.add_roles(family_role, reason="Auto-assign RAI FAMILY role")
                    count += 1
                    print(f"Added {family_role.name} to {member.display_name}")
                except Exception as e:
                    print(f"Error adding family role to {member.display_name}: {e}")

    print(f"Auto-assigned roles to {count} existing members.")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
