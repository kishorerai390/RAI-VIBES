import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
import asyncio
import aiohttp
import discord
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    print("🤖 Auto-configuring Discord Onboarding with valid snowflakes...")

    # Fetch IDs
    c_verify = discord.utils.get(guild.text_channels, name="✅-verify-here")
    c_welcome = discord.utils.get(guild.text_channels, name="👋-welcome")
    c_rules = discord.utils.get(guild.text_channels, name="📜-rules")
    c_announcements = discord.utils.get(guild.text_channels, name="📢-announcements")
    c_main = discord.utils.get(guild.text_channels, name="💬-main-chat")
    c_media = discord.utils.get(guild.text_channels, name="📸-media")
    c_movie_sched = discord.utils.get(guild.text_channels, name="🎬-movie-schedule")
    c_movie_chat = discord.utils.get(guild.text_channels, name="🍿-movie-chat")
    c_music_cmd = discord.utils.get(guild.text_channels, name="🎵-music-commands")
    c_lofi = discord.utils.get(guild.text_channels, name="☕-lofi-chat")
    
    vc_cinema = discord.utils.get(guild.voice_channels, name="🎥 | CINEMA THEATER")
    vc_radio = discord.utils.get(guild.voice_channels, name="📻 | 24-7 RADIO")
    vc_music = discord.utils.get(guild.voice_channels, name="🎧 | MUSIC LOUNGE")
    vc_freefire = discord.utils.get(guild.voice_channels, name="⚡ | FREE FIRE")
    vc_bgmi = discord.utils.get(guild.voice_channels, name="⚡ | BGMI")
    vc_roblox = discord.utils.get(guild.voice_channels, name="⚡ | ROBLOX")
    vc_fun = discord.utils.get(guild.voice_channels, name="🐣 | FUN TIME")
    vc_open = discord.utils.get(guild.voice_channels, name="🍇 | OPEN VOICE")

    r_movie = discord.utils.get(guild.roles, name="🍿 Movie Night Ping")
    r_lofi = discord.utils.get(guild.roles, name="☕ Lo-Fi & Chill")
    r_gamer = discord.utils.get(guild.roles, name="🎮 Console Gamer") or discord.utils.get(guild.roles, name="🖥️ PC Gamer")
    r_viber = discord.utils.get(guild.roles, name="🌟 Active Vibers") or discord.utils.get(guild.roles, name="👥 Verified Member")

    default_channels = [c.id for c in [c_verify, c_welcome, c_rules, c_announcements, c_main, c_movie_sched, c_music_cmd] if c]

    # Generate Snowflakes
    base_sf = discord.utils.time_snowflake(datetime.now())
    
    prompt_id = str(base_sf)
    opt1_id = str(base_sf + 1)
    opt2_id = str(base_sf + 2)
    opt3_id = str(base_sf + 3)
    opt4_id = str(base_sf + 4)

    prompt_options = [
        {
            "id": opt1_id,
            "title": "Watch Movies & Anime",
            "description": "Stream cinema, anime marathons, and join watch parties",
            "emoji": {"name": "🍿"},
            "role_ids": [str(r_movie.id)] if r_movie else [],
            "channel_ids": [str(c.id) for c in [c_movie_sched, c_movie_chat, vc_cinema] if c]
        },
        {
            "id": opt2_id,
            "title": "Listen to Music & Lo-Fi",
            "description": "24/7 radio stations, 200% volume music bot, and study cafes",
            "emoji": {"name": "🎵"},
            "role_ids": [str(r_lofi.id)] if r_lofi else [],
            "channel_ids": [str(c.id) for c in [c_music_cmd, c_lofi, vc_radio, vc_music] if c]
        },
        {
            "id": opt3_id,
            "title": "Play Games (BGMI, Free Fire, Roblox)",
            "description": "Squad up for mobile & PC gaming voice lobbies",
            "emoji": {"name": "🎮"},
            "role_ids": [str(r_gamer.id)] if r_gamer else [],
            "channel_ids": [str(c.id) for c in [vc_freefire, vc_bgmi, vc_roblox] if c]
        },
        {
            "id": opt4_id,
            "title": "Chill, Chat & Make Friends",
            "description": "Meet community members and hang out in casual voice rooms",
            "emoji": {"name": "💬"},
            "role_ids": [str(r_viber.id)] if r_viber else [],
            "channel_ids": [str(c.id) for c in [c_main, c_media, vc_fun, vc_open] if c]
        }
    ]

    payload = {
        "prompts": [
            {
                "id": prompt_id,
                "title": "What do you want to do in this community?",
                "type": 0,
                "single_select": False,
                "required": False,
                "in_onboarding": True,
                "options": prompt_options
            }
        ],
        "default_channel_ids": [str(cid) for cid in default_channels],
        "enabled": True,
        "mode": 0
    }

    url = f"https://discord.com/api/v10/guilds/{GUILD_ID}/onboarding"
    headers = {
        "Authorization": f"Bot {TOKEN}",
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        async with session.put(url, json=payload, headers=headers) as resp:
            status = resp.status
            text = await resp.text()
            if status in [200, 204]:
                print("🎉 SUCCESS! Discord Onboarding has been automatically configured and enabled!")
            else:
                print(f"Status {status}: {text}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
