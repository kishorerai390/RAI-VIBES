import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv("f:/antigravity/APEX VIBES/.env")
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

intents = discord.Intents.default()
intents.guilds = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user} ({client.user.id})")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print(f"❌ Guild ID {GUILD_ID} not found!")
        await client.close()
        return

    print(f"Connected to Guild: {guild.name}")

    # 1. Create or Find '🚫 | HIDE CHANNELS' Category
    hide_cat = discord.utils.get(guild.categories, name="🚫 | HIDE CHANNELS")
    if not hide_cat:
        # Check alternative name variations
        for c in guild.categories:
            if "HIDE CHANNELS" in c.name.upper():
                hide_cat = c
                break

    if not hide_cat:
        # Place at bottom of categories
        max_pos = max((c.position for c in guild.categories), default=10)
        hide_cat = await guild.create_category(
            name="🚫 | HIDE CHANNELS",
            position=max_pos + 1,
            reason="Collapsible holding room category (Thor Apex style)"
        )
        print("✅ Created Category: '🚫 | HIDE CHANNELS'")
    else:
        print(f"ℹ️ Category '🚫 | HIDE CHANNELS' already exists (ID: {hide_cat.id})")

    # 2. Configure Permissions for DRAG ME
    # @everyone can view and connect so members can be dragged or wait, but cannot speak (muted on entry)
    everyone = guild.default_role
    overwrites = {
        everyone: discord.PermissionOverwrite(
            view_channel=True,
            connect=True,
            speak=False,        # Muted on entry so waiting users don't disturb
            stream=False
        )
    }

    # 3. Create or Update '🔮 | DRAG ME' Voice Channel
    drag_vc = discord.utils.get(hide_cat.voice_channels, name="🔮 | DRAG ME")
    if not drag_vc:
        for vc in hide_cat.voice_channels:
            if "DRAG ME" in vc.name.upper():
                drag_vc = vc
                break

    if not drag_vc:
        drag_vc = await hide_cat.create_voice_channel(
            name="🔮 | DRAG ME",
            overwrites=overwrites,
            user_limit=0, # Unlimited holding capacity
            reason="Thor Apex Admin Drag & Isolation Channel"
        )
        print("✅ Created Voice Channel: '🔮 | DRAG ME' (Speak = False)")
    else:
        await drag_vc.edit(overwrites=overwrites, user_limit=0)
        print(f"ℹ️ Updated Voice Channel: '🔮 | DRAG ME' with holding permissions")

    print("\n🎉 '🚫 | HIDE CHANNELS' > '🔮 | DRAG ME' successfully configured!")
    await client.close()

if __name__ == "__main__":
    if not TOKEN:
        print("❌ DISCORD_BOT_TOKEN is missing in .env")
        sys.exit(1)
    try:
        asyncio.run(client.start(TOKEN))
    except discord.errors.LoginFailure:
        print("\n❌ Discord Bot Token in .env returned 401 Unauthorized.")
        print("👉 Please paste your current active bot token into .env: DISCORD_BOT_TOKEN=your_token")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
