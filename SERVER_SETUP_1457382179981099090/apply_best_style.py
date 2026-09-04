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

# OPTION 1: Clean kebab text channels + reference spaced voice channels
PERFECT_STRUCTURE = [
    {
        "category": "🌸 | 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 & 𝙄𝙉𝙁𝙊",
        "channels": [
            {"name": "verify-here", "type": "text"},
            {"name": "welcome", "type": "text"},
            {"name": "rules", "type": "text"},
            {"name": "announcements", "type": "text"},
            {"name": "self-roles", "type": "text"},
        ]
    },
    {
        "category": "💬 | 𝘾𝙃𝘼𝙏 & 𝙇𝙊𝙐𝙉𝙂𝙀",
        "channels": [
            {"name": "general-chat", "type": "text"},
            {"name": "media", "type": "text"},
            {"name": "bot-commands", "type": "text"},
            {"name": "suggestions", "type": "text"},
        ]
    },
    {
        "category": "🍿 | 𝙈𝙊𝙑𝙄𝙀𝙎 & 𝘾𝙄𝙉𝙀𝙈𝘼",
        "channels": [
            {"name": "movie-schedule", "type": "text"},
            {"name": "movie-chat", "type": "text"},
            {"name": "🎥 | CINEMA THEATER", "type": "voice", "limit": 0},
        ]
    },
    {
        "category": "🎵 | 𝙈𝙐𝙎𝙄𝘾 𝙕𝙊𝙉𝙀",
        "channels": [
            {"name": "music-commands", "type": "text"},
            {"name": "lofi-chat", "type": "text"},
            {"name": "📻 | 24-7 RADIO", "type": "voice", "limit": 0},
            {"name": "🎧 | MUSIC LOUNGE", "type": "voice", "limit": 0},
        ]
    },
    {
        "category": "😹 | 𝙁𝙐𝙉 𝙑𝙊𝙄𝘾𝙀 𝘾𝙃𝘼𝙉𝙉𝙀𝙇𝙎",
        "channels": [
            {"name": "➕ | JOIN TO CREATE", "type": "voice", "limit": 0},
            {"name": "🐣 | FUN TIME", "type": "voice", "limit": 0},
            {"name": "🍇 | VOICE-1", "type": "voice", "limit": 0},
            {"name": "🍇 | VOICE-2", "type": "voice", "limit": 0},
            {"name": "🍇 | OPEN VOICE", "type": "voice", "limit": 0},
            {"name": "🥂 | ・ DUO", "type": "voice", "limit": 2},
            {"name": "🥂 | ・ TRIO", "type": "voice", "limit": 3},
            {"name": "💤 | AFK", "type": "voice", "limit": 0},
        ]
    },
    {
        "category": "🎮 | 𝙂𝘼𝙈𝙄𝙉𝙂 𝙕𝙊𝙉𝙀",
        "channels": [
            {"name": "⚡ | FREE FIRE", "type": "voice", "limit": 0},
            {"name": "⚡ | BGMI", "type": "voice", "limit": 0},
            {"name": "⚡ | ROBLOX", "type": "voice", "limit": 0},
            {"name": "⚡ | OTHER GAMES", "type": "voice", "limit": 0},
        ]
    },
    {
        "category": "🛡️ | 𝙎𝙏𝘼𝙁𝙁 𝙕𝙊𝙉𝙀",
        "channels": [
            {"name": "staff-chat", "type": "text"},
            {"name": "mod-logs", "type": "text"},
            {"name": "ticket-support", "type": "text"},
        ]
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

    print(f"🚀 Deploying Option 1 (Cleanest Pro Setup) for {guild.name}...")

    # 1. Clean old channels
    for chan in list(guild.channels):
        try:
            await chan.delete(reason="Applying clean Option 1 layout")
            print(f"Deleted old: {chan.name}")
            await asyncio.sleep(0.3)
        except Exception as e:
            print(f"Error deleting {chan.name}: {e}")

    # 2. Build perfect structure
    for section in PERFECT_STRUCTURE:
        cat_name = section["category"]
        category = await guild.create_category(name=cat_name)
        print(f"\nCreated Category: {cat_name}")
        await asyncio.sleep(0.5)

        for c_info in section["channels"]:
            c_name = c_info["name"]
            c_type = c_info["type"]
            limit = c_info.get("limit", 0)

            if c_type == "text":
                c = await guild.create_text_channel(name=c_name, category=category)
                print(f"  + Text: #{c_name}")
            elif c_type == "voice":
                c = await guild.create_voice_channel(name=c_name, category=category, user_limit=limit)
                print(f"  + Voice: 🔊 {c_name} (Limit: {limit})")
            await asyncio.sleep(0.4)

    # 3. Post interactive embeds
    from deploy_clean_embeds import VerifyButtonView, MovieRolesView, NotificationRolesView, MusicRolesView, TicketCreateView, COLOR_PINK, COLOR_GOLD, COLOR_PURPLE

    v_chan = discord.utils.get(guild.text_channels, name="verify-here")
    if v_chan:
        v_embed = discord.Embed(
            title=f"🌸 {guild.name.upper()} • VERIFICATION 🌸",
            description=(
                f"Welcome to **{guild.name}**! 💗🍿🎵\n\n"
                "Click the green **`[✅ Verify & Enter Community]`** button below to unlock all channels!"
            ),
            color=COLOR_PINK
        )
        await v_chan.send(embed=v_embed, view=VerifyButtonView())

    r_chan = discord.utils.get(guild.text_channels, name="rules")
    if r_chan:
        r_embed = discord.Embed(
            title=f"📜 {guild.name.upper()} • SERVER RULES 📜",
            description=(
                "**1️⃣ Good Vibes:** Be respectful & friendly to everyone.\n"
                "**2️⃣ No Spam:** Keep text channels clean & readable.\n"
                "**3️⃣ Voice Etiquette:** Respect mic turns in gaming & music lounges.\n"
                "**4️⃣ Music & Movies:** Enjoy `/play` and cinema watch parties!\n"
                "**5️⃣ Follow Discord ToS.**"
            ),
            color=COLOR_GOLD
        )
        await r_chan.send(embed=r_embed)

    s_chan = discord.utils.get(guild.text_channels, name="self-roles")
    if s_chan:
        await s_chan.send(embed=discord.Embed(title="🍿 Movie & Cinema Roles", description="Click to get notified for watch parties!", color=COLOR_PINK), view=MovieRolesView())
        await s_chan.send(embed=discord.Embed(title="📢 Announcement & Event Roles", description="Toggle server pings and giveaways!", color=COLOR_GOLD), view=NotificationRolesView())
        await s_chan.send(embed=discord.Embed(title="🎵 Music Genre Roles", description="Pick your favorite audio genres!", color=COLOR_PURPLE), view=MusicRolesView())

    t_chan = discord.utils.get(guild.text_channels, name="ticket-support")
    if t_chan:
        t_embed = discord.Embed(
            title=f"🎫 {guild.name.upper()} • SUPPORT DESK",
            description="Need help from server moderators? Click **`[📩 Open Support Ticket]`** below!",
            color=COLOR_PINK
        )
        await t_chan.send(embed=t_embed, view=TicketCreateView())

    print("\n🎉 OPTION 1 PERFECT PRO LAYOUT IS LIVE!")
    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
