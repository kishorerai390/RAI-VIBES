import os
import sys
import asyncio
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090
GUIDE_CHANNEL_ID = 1546125872661012611

intents = discord.Intents.default()
intents.guilds = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user} - Posting Server Guide...")
    chan = client.get_channel(GUIDE_CHANNEL_ID)
    if not chan:
        print("Guide channel not found!")
        await client.close()
        return

    # Purge old bot messages
    try:
        async for msg in chan.history(limit=20):
            if msg.author == client.user:
                await msg.delete()
    except Exception as e:
        print(f"Purge note: {e}")

    DIVIDER = "✦ ─── ⋆⋅☆⋅⋆ ─── ✦"

    # Embed 1: Welcome & Overview
    embed1 = discord.Embed(
        title="🧭 ⋆⋅ RAI FAM • OFFICIAL SERVER DIRECTORY ⋅⋆ 🧭",
        description=(
            f"{DIVIDER}\n\n"
            "Welcome to **RAI FAM 💗**! We are a high-fidelity sound lounge, competitive gaming hub, "
            "and active community sanctuary.\n\n"
            "This guide will help you navigate all channels, access features, and get the most out of our bots!\n\n"
            "**🚀 Quick Start Checklist:**\n"
            "> 1️⃣ Complete verification in <#1545502700840427702>\n"
            "> 2️⃣ Pick your colors & game roles in <#1545502722739150898>\n"
            "> 3️⃣ Read our community guidelines in <#1545502710101704714>\n"
            "> 4️⃣ Say hello to the crew in <#1545502730699808768>!\n\n"
            f"{DIVIDER}"
        ),
        color=0x2B2D31
    )
    if chan.guild.icon:
        embed1.set_thumbnail(url=chan.guild.icon.url)

    # Embed 2: Category Map
    embed2 = discord.Embed(
        title="🗺️ ⋆⋅ CHANNEL NAVIGATION MAP ⋅⋆ 🗺️",
        description=(
            "### ✦ INFORMATION\n"
            "> • <#1545502718792175646> — Official announcements & updates\n"
            "> • <#1545502705643167876> — Member arrival greetings\n"
            "> • <#1545502710101704714> — Server rules & conduct policy\n"
            "> • <#1545502700840427702> — 1-click verification gate\n"
            "> • <#1545502722739150898> — Self-assignable color, game & notification roles\n\n"
            "### 💬 THE LOUNGE\n"
            "> • <#1545502730699808768> — Main chat (earn XP & rank up!)\n"
            "> • <#1546097792915873842> — Clips, screenshots & gaming highlights\n"
            "> • <#1545834933417672744> — Exclusive VIP & Booster text lounge\n\n"
            "### 🎵 VIBE STUDIO\n"
            "> • <#1545534637122527332> — Zero-prefix song queue (type any song name directly!)\n"
            "> • 🌧️ **Lo-Fi Chill 24/7** — Non-stop 24/7 radio stream\n"
            "> • 🎤 **Karaoke Stage** — Live voice singing with `/karaoke` mode\n\n"
            "### 🎮 GAMING ZONE\n"
            "> • <#1545803554550190212> — Gaming chatter & squad recruitments\n"
            "> • 🎯 **BGMI Squad** — 4-player locked battlegrounds VC\n"
            "> • 🔥 **Free Fire Arena** — 4-player locked squad VC\n"
            "> • 🧱 **Roblox Hangout** — Casual gaming voice chat\n\n"
            "### 🥂 PRIVATE SUITES\n"
            "> • ➕ **Join to Create VC** — Auto-creates your private room with `/vlock` controls\n"
            "> • 🔒 **Create Ghost VC** — Auto-creates an invisible room for invited friends"
        ),
        color=0x2B2D31
    )

    # Embed 3: Bot Commands Cheat Sheet
    embed3 = discord.Embed(
        title="🤖 ⋆⋅ BOT COMMANDS CHEAT SHEET ⋅⋆ 🤖",
        description=(
            "### 🎵 AURA ✦ (Music & Audio)\n"
            "> • `/play <song>` — Stream any track or YouTube/Spotify playlist\n"
            "> • `/pause` / `/resume` — Control playback\n"
            "> • `/skip` — Skip to next song in queue\n"
            "> • `/queue` — View upcoming tracklist\n"
            "> • `/bassboost` / `/spatial8d` / `/nightcore` — Studio audio filters\n"
            "> • `/serverinfo` — Everglow-style interactive server stats\n"
            "> • `/userinfo [@member]` — Inspect badges, avatar, banner & join date\n"
            "> • `/rank` — Check your chat level and XP\n\n"
            "### 🛡️ SENTINEL 🛡️ (Security & Tickets)\n"
            "> • <#1545514505520545886> — Click button to open a private ticket\n"
            "> • Automatic Anti-Nuke, Anti-Raid & Spam Filtering enabled 24/7"
        ),
        color=0x2B2D31
    )
    embed3.set_footer(text="RAI FAM 💗 • Enjoy your stay and vibe with us!", icon_url=chan.guild.icon.url if chan.guild.icon else None)

    await chan.send(embed=embed1)
    await chan.send(embed=embed2)
    await chan.send(embed=embed3)
    print("✅ Server Guide successfully posted in #🧭・server-guide!")
    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
