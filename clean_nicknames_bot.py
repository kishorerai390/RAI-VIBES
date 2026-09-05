import os
import sys
import re
import asyncio
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

async def main():
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True

    try:
        client = discord.Client(intents=intents)
    except Exception:
        intents = discord.Intents.default()
        intents.guilds = True
        client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")
        guild = client.get_guild(GUILD_ID)
        if not guild:
            print("Guild not found")
            await client.close()
            return

        owner_id = guild.owner_id
        cleaned = 0

        # Iterate all cached / voice / guild members
        for member in guild.members:
            if member.bot or member.id == owner_id:
                continue

            nick = member.nick
            if not nick:
                continue

            # Remove RF prefix
            clean_nick = re.sub(r'^(?:RF\s*\|\s*|RF\s*・\s*|RF\s*\|\s*|RF\s+)', '', nick, flags=re.IGNORECASE).strip()
            global_name = member.global_name or member.name

            if clean_nick != nick:
                try:
                    target_nick = clean_nick if clean_nick != global_name else None
                    await member.edit(nick=target_nick, reason="Remove RF tag prefix as requested")
                    print(f"✅ Cleaned: '{nick}' -> '{clean_nick}' (Reset: {target_nick is None})")
                    cleaned += 1
                    await asyncio.sleep(0.4)
                except Exception as e:
                    print(f"⚠️ Could not update '{nick}': {e}")

        print(f"🎉 Successfully cleaned {cleaned} member nicknames!")
        await client.close()

    try:
        await client.start(TOKEN)
    except discord.errors.PrivilegedIntentsRequired:
        print("Intents.members requires toggle; falling back to default intents...")
        intents = discord.Intents.default()
        intents.guilds = True
        client = discord.Client(intents=intents)
        
        @client.event
        async def on_ready():
            print(f"Logged in as {client.user}")
            guild = client.get_guild(GUILD_ID)
            owner_id = guild.owner_id if guild else None
            cleaned = 0
            if guild:
                for member in guild.members:
                    if member.bot or member.id == owner_id:
                        continue
                    nick = member.nick
                    if not nick:
                        continue
                    clean_nick = re.sub(r'^(?:RF\s*\|\s*|RF\s*・\s*|RF\s*\|\s*|RF\s+)', '', nick, flags=re.IGNORECASE).strip()
                    global_name = member.global_name or member.name
                    if clean_nick != nick:
                        try:
                            target_nick = clean_nick if clean_nick != global_name else None
                            await member.edit(nick=target_nick, reason="Remove RF tag prefix")
                            print(f"✅ Cleaned: '{nick}' -> '{clean_nick}'")
                            cleaned += 1
                        except Exception as e:
                            print(f"⚠️ Error: {e}")
            print(f"🎉 Cleaned {cleaned} member nicknames!")
            await client.close()
            
        await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
