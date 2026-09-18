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
    guild = discord.utils.find(lambda g: "RAI FAM" in g.name, bot.guilds)
    if not guild:
        print("Guild RAI FAM not found!")
        await bot.close()
        return

    print(f"=== Optimizing Voice Permissions in {guild.name} ===")
    default_role = guild.default_role

    # 1. Update Categories for Public Lounges
    categories_to_open = [
        "🎵 MUSIC LOUNGE",
        "🔊 VOICE LOUNGE",
        "🍿 CINEMA HUB",
        "🎮 GAMING ARENA"
    ]
    for cat in guild.categories:
        if cat.name in categories_to_open:
            try:
                # Allow @everyone to view and connect at category level
                ow = cat.overwrites_for(default_role)
                ow.read_messages = True
                ow.connect = True
                ow.speak = True
                await cat.set_permissions(default_role, overwrite=ow)
                print(f"✅ Category '{cat.name}' unlocked for @everyone.")
            except Exception as e:
                print(f"Category {cat.name} note: {e}")

    # 2. Configure Voice Channels individually
    for vc in guild.voice_channels:
        cat_name = vc.category.name if vc.category else ""
        name = vc.name
        
        # A. Executive Suite -> Private to VIP & Staff
        if "Executive Suite" in name:
            try:
                ow = vc.overwrites_for(default_role)
                ow.read_messages = False
                ow.connect = False
                await vc.set_permissions(default_role, overwrite=ow)
                await vc.edit(user_limit=5)
                print(f"🔒 '{name}' kept private for VIP/Staff (Limit: 5)")
            except Exception as e:
                print(f"Error on {name}: {e}")
            continue

        # B. Server Stats -> View only, Connect Denied
        if "SERVER STATS" in cat_name or "All Members" in name or "Members:" in name or "Bots:" in name:
            try:
                ow = vc.overwrites_for(default_role)
                ow.read_messages = True
                ow.connect = False
                await vc.set_permissions(default_role, overwrite=ow)
                print(f"📊 Stats channel '{name}' set to View-Only.")
            except Exception as e:
                print(f"Error on {name}: {e}")
            continue

        # C. AFK Channel -> Allow connect, deny speak
        if "AFK" in name or "Sleep" in name:
            try:
                ow = vc.overwrites_for(default_role)
                ow.read_messages = True
                ow.connect = True
                ow.speak = False
                await vc.set_permissions(default_role, overwrite=ow)
                await vc.edit(user_limit=0)
                print(f"💤 '{name}' set to AFK mode (Unlimited, Muted).")
            except Exception as e:
                print(f"Error on {name}: {e}")
            continue

        # D. Squad Gaming Channels -> Open to everyone, with protected squad limits
        squad_limits = {
            "Duo Chamber": 2,
            "Trio Chamber": 3,
            "Free Fire Squad": 4,
            "BGMI Squad": 4,
            "GTA RP & Chill": 5,
            "Custom Room / Scrims": 8
        }
        
        matched_limit = None
        for key, limit in squad_limits.items():
            if key in name:
                matched_limit = limit
                break

        if matched_limit:
            try:
                ow = vc.overwrites_for(default_role)
                ow.read_messages = True
                ow.connect = True
                ow.speak = True
                ow.stream = True
                await vc.set_permissions(default_role, overwrite=ow)
                await vc.edit(user_limit=matched_limit)
                print(f"⚔️ '{name}' unlocked for @everyone with Squad Limit: {matched_limit} players.")
            except Exception as e:
                print(f"Error on {name}: {e}")
            continue

        # E. Public Music & Chill Lounges -> 100% Open, Unlimited (No Limited Tag)
        try:
            ow = vc.overwrites_for(default_role)
            ow.read_messages = True
            ow.connect = True
            ow.speak = True
            ow.stream = True
            await vc.set_permissions(default_role, overwrite=ow)
            await vc.edit(user_limit=0)
            print(f"🎉 '{name}' unlocked 100% (Unlimited capacity, NO LIMITED TAG).")
        except Exception as e:
            print(f"Error on {name}: {e}")

    print("\n✅ All Voice Channels in RAI FAM💗 have been successfully upgraded!")
    await bot.close()

if __name__ == "__main__":
    asyncio.run(bot.start(token))
