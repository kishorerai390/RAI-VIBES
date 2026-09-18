import asyncio
import discord
import os
import sys
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")

bot = discord.Client(intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    
    for guild in bot.guilds:
        print(f"\n==========================================")
        print(f"  Setting ALL VCs to Unlimited in: {guild.name}")
        print(f"==========================================")
        
        default_role = guild.default_role
        
        for vc in guild.voice_channels:
            cat_name = vc.category.name if vc.category else ""
            name = vc.name
            
            # Skip server stats channels (they are counters)
            if "SERVER STATS" in cat_name or "All Members" in name or "Members:" in name or "Bots:" in name:
                print(f"  [Stats VC] '{name}' -> Kept as counter")
                continue
                
            # Executive Suite: keep private staff
            if "EXECUTIVE SUITE" in name.upper():
                print(f"  [Private VIP] '{name}' -> Kept private")
                continue
                
            # For all other voice channels: set limit to 0 (Unlimited) & ensure @everyone can connect
            try:
                ow = vc.overwrites_for(default_role)
                ow.read_messages = True
                ow.connect = True
                ow.speak = False if ("AFK" in name or "Sleep" in name) else True
                ow.stream = True
                
                await vc.set_permissions(default_role, overwrite=ow)
                
                if vc.user_limit != 0:
                    await vc.edit(user_limit=0)
                    print(f"  [Unlocked Unlimited] '{name}' -> user_limit set to 0 (NO 'Voice (Limited)' tag)")
                else:
                    print(f"  [Already Unlimited] '{name}' -> user_limit: 0")
            except Exception as e:
                print(f"  [Error] '{name}': {e}")
                
    print("\n✅ All voice channels across all servers are now 100% UNLIMITED!")
    await bot.close()

if __name__ == "__main__":
    asyncio.run(bot.start(token))
