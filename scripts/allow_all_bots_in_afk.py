import os
import sys
import asyncio
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user.name} ({client.user.id})")
    
    for guild in client.guilds:
        print(f"\n==================================================")
        print(f"Guild: {guild.name} ({guild.id})")
        
        # 1. Locate AFK channel
        afk_ch = guild.afk_channel
        if not afk_ch:
            for ch in guild.voice_channels:
                name_l = (ch.name or "").lower()
                if "afk" in name_l or "sleep" in name_l:
                    afk_ch = ch
                    break
                    
        if not afk_ch:
            print("  ❌ No AFK channel found in guild!")
            continue
            
        print(f"  Found AFK Channel: '{afk_ch.name}' (ID: {afk_ch.id})")
        
        # 2. Iterate all bot members in guild and grant full voice permissions
        bot_count = 0
        for member in guild.members:
            if member.bot:
                bot_count += 1
                try:
                    overwrite = afk_ch.overwrites_for(member)
                    overwrite.connect = True
                    overwrite.speak = True
                    overwrite.stream = True
                    overwrite.use_voice_activation = True
                    overwrite.priority_speaker = True
                    overwrite.use_soundboard = True
                    
                    await afk_ch.set_permissions(member, overwrite=overwrite, reason="Allow all bots to join and play audio in AFK")
                    print(f"  ✅ Configured permissions for bot: {member.display_name} ({member.id})")
                except Exception as e:
                    print(f"  ⚠️ Could not set permissions for {member.display_name}: {e}")
                    
        # 3. Also check roles that belong to bots (managed roles)
        for role in guild.roles:
            if role.is_bot_managed():
                try:
                    overwrite = afk_ch.overwrites_for(role)
                    overwrite.connect = True
                    overwrite.speak = True
                    overwrite.stream = True
                    overwrite.use_voice_activation = True
                    overwrite.priority_speaker = True
                    overwrite.use_soundboard = True
                    await afk_ch.set_permissions(role, overwrite=overwrite, reason="Allow bot managed role in AFK")
                    print(f"  ✅ Configured permissions for bot role: {role.name}")
                except Exception as e:
                    print(f"  ⚠️ Could not set permissions for role {role.name}: {e}")
                    
        print(f"  🎉 Finished configuring AFK channel for {bot_count} bots!")
        
    await client.close()

if __name__ == "__main__":
    client.run(token)
