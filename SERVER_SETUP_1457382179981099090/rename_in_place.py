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

# Map of existing channels to clean Option 1 names
CHANNEL_RENAME_MAP = {
    # Text channels (clean kebab-case without emoji prefix)
    "✅-verify-here": "verify-here",
    "👋-welcome": "welcome",
    "📜-rules": "rules",
    "📢-announcements": "announcements",
    "⭐-self-roles": "self-roles",
    "💬-main-chat": "general-chat",
    "📸-media": "media",
    "🤖-bot-commands": "bot-commands",
    "💡-suggestions": "suggestions",
    "🎬-movie-schedule": "movie-schedule",
    "🍿-movie-chat": "movie-chat",
    "🎵-music-commands": "music-commands",
    "☕-lofi-chat": "lofi-chat",
    "🛡️-staff-chat": "staff-chat",
    "📋-mod-logs": "mod-logs",
    "🎫-ticket-support": "ticket-support",

    # Voice channels (clean spaced style from reference image)
    "🥂 | DUO": "🥂 | ・ DUO",
    "🥂 | TRIO": "🥂 | ・ TRIO",
    "🐣 | FUN TIME": "🐣 | FUN TIME",
    "🍇 | OPEN VOICE": "🍇 | OPEN VOICE",
    "➕ | JOIN TO CREATE": "➕ | JOIN TO CREATE",
    "💤 | AFK": "💤 | AFK",
    "🎥 | CINEMA THEATER": "🎥 | CINEMA THEATER",
    "📻 | 24-7 RADIO": "📻 | 24-7 RADIO",
    "🎧 | MUSIC LOUNGE": "🎧 | MUSIC LOUNGE",
    "⚡ | FREE FIRE": "⚡ | FREE FIRE",
    "⚡ | BGMI": "⚡ | BGMI",
    "⚡ | ROBLOX": "⚡ | ROBLOX",
    "⚡ | OTHER GAMES": "⚡ | OTHER GAMES",
}

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    print(f"✨ Renaming channels in {guild.name} to clean Option 1 style...")

    # First ensure bot has highest role / check permissions
    bot_member = guild.me
    print(f"Bot Permissions in guild: Manage Channels = {bot_member.guild_permissions.manage_channels}, Administrator = {bot_member.guild_permissions.administrator}")

    for channel in guild.channels:
        current_name = channel.name
        if current_name in CHANNEL_RENAME_MAP:
            new_name = CHANNEL_RENAME_MAP[current_name]
            if current_name != new_name:
                try:
                    await channel.edit(name=new_name)
                    print(f"  ✅ Renamed: '{current_name}' ➔ '{new_name}'")
                    await asyncio.sleep(0.4)
                except Exception as e:
                    print(f"  ⚠️ Could not rename '{current_name}': {e}")

    # Move staff-chat into Staff category if needed
    staff_cat = discord.utils.get(guild.categories, name="🛡️ | 𝙎𝙏𝘼𝙁𝙁 𝙕𝙊𝙉𝙀")
    staff_chat = discord.utils.get(guild.text_channels, name="staff-chat") or discord.utils.get(guild.text_channels, name="🛡️-staff-chat")
    if staff_cat and staff_chat and staff_chat.category != staff_cat:
        try:
            await staff_chat.edit(category=staff_cat)
            print("  ✅ Moved staff-chat into 🛡️ | 𝙎𝙏𝘼𝙁𝙁 𝙕𝙊𝙉𝙀 category!")
        except Exception as e:
            print(f"  ⚠️ Move staff-chat: {e}")

    print("\n🎉 ALL CHANNELS UPDATED TO CLEAN OPTION 1 STYLE!")
    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
