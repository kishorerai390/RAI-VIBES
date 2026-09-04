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

# Definitions of all roles
ROLE_DEFINITIONS = [
    # 1. Colors (Placed highest so name colors take effect)
    {"name": "🌸 ┊ Sakura Pink", "color": discord.Color.from_rgb(255, 183, 197), "mentionable": False},
    {"name": "💜 ┊ Neon Violet", "color": discord.Color.from_rgb(155, 93, 229), "mentionable": False},
    {"name": "🩵 ┊ Cyber Cyan", "color": discord.Color.from_rgb(0, 245, 212), "mentionable": False},
    {"name": "💛 ┊ Royal Gold", "color": discord.Color.from_rgb(254, 228, 64), "mentionable": False},

    # 2. Level & Activity Rewards
    {"name": "💎 ┊ Rai Legend", "color": discord.Color.from_rgb(222, 216, 246), "mentionable": True},
    {"name": "🔥 ┊ Rai Champion", "color": discord.Color.from_rgb(255, 170, 165), "mentionable": True},
    {"name": "✨ ┊ Rai Active", "color": discord.Color.from_rgb(255, 211, 182), "mentionable": False},
    {"name": "🌱 ┊ Rai Novice", "color": discord.Color.from_rgb(168, 230, 207), "mentionable": False},

    # 3. Gaming Roles
    {"name": "🔥 ┊ Free Fire", "color": discord.Color.from_rgb(255, 119, 0), "mentionable": True},
    {"name": "⚡ ┊ BGMI", "color": discord.Color.from_rgb(241, 196, 15), "mentionable": True},
    {"name": "🧸 ┊ Roblox", "color": discord.Color.from_rgb(231, 76, 60), "mentionable": True},
    {"name": "📱 ┊ Mobile Gamer", "color": discord.Color.from_rgb(52, 152, 219), "mentionable": True},
    {"name": "💻 ┊ PC Gamer", "color": discord.Color.from_rgb(41, 128, 185), "mentionable": True},

    # 4. Notifications & Alerts
    {"name": "🎬 ┊ Movie Alerts", "color": discord.Color.from_rgb(233, 30, 99), "mentionable": True},
    {"name": "🎉 ┊ Giveaway Alerts", "color": discord.Color.from_rgb(46, 204, 113), "mentionable": True},
    {"name": "📢 ┊ Server News", "color": discord.Color.from_rgb(155, 89, 182), "mentionable": True},
    {"name": "🎧 ┊ Music Jam", "color": discord.Color.from_rgb(26, 188, 156), "mentionable": True},

    # 5. Identity & Profile
    {"name": "♂️ ┊ He/Him", "color": discord.Color.from_rgb(149, 165, 166), "mentionable": False},
    {"name": "♀️ ┊ She/Her", "color": discord.Color.from_rgb(232, 67, 147), "mentionable": False},
    {"name": "🌈 ┊ They/Them", "color": discord.Color.from_rgb(0, 206, 201), "mentionable": False},
    {"name": "🔞 ┊ 18+ Verified", "color": discord.Color.from_rgb(214, 48, 49), "mentionable": False},
]

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    print(f"Creating/verifying roles in {guild.name}...")
    created_roles = {}
    for rdef in ROLE_DEFINITIONS:
        existing = discord.utils.get(guild.roles, name=rdef["name"])
        if not existing:
            try:
                role = await guild.create_role(
                    name=rdef["name"],
                    color=rdef["color"],
                    mentionable=rdef["mentionable"],
                    reason="Creating aesthetic self & activity roles"
                )
                print(f"Created role: {rdef['name']}")
                created_roles[rdef["name"]] = role
            except Exception as e:
                print(f"Failed to create role {rdef['name']}: {e}")
        else:
            print(f"Role already exists: {rdef['name']}")
            created_roles[rdef["name"]] = existing

    print("All roles processed successfully!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
