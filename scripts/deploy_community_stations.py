import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from utils.persistent_views import NotificationRolesView, GamingRolesView
from cogs.arcade_panel import ArcadeStationView
import config
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

ROLES_CHANNEL_ID = 1545502722739150898  # #🏷️｜ʀᴏʟᴇꜱ
BOT_CMDS_CHANNEL_ID = 1549416359723532480  # #🤖｜ʙᴏᴛ-ᴄᴍᴅꜱ

ROLES_TO_ENSURE = [
    ("📢 ┆ Announcements", discord.Color.from_rgb(165, 94, 234)),
    ("🎁 ┆ Giveaways", discord.Color.from_rgb(46, 204, 113)),
    ("🏆 ┆ Tournaments", discord.Color.from_rgb(231, 76, 60)),
    ("🍿 ┆ Movie Nights", discord.Color.from_rgb(255, 71, 87)),
    ("⚡ ┆ Free Fire", discord.Color.from_rgb(255, 165, 2)),
    ("🎯 ┆ BGMI", discord.Color.from_rgb(46, 213, 115)),
    ("🔫 ┆ GTA RP", discord.Color.from_rgb(30, 144, 255)),
    ("🧸 ┆ Roblox", discord.Color.from_rgb(241, 196, 15)),
]

intents = discord.Intents.default()
intents.members = True
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found!")
        await client.close()
        return

    print("\n--- 1. Ensuring Self-Roles Exist in Server ---")
    for r_name, color in ROLES_TO_ENSURE:
        existing = discord.utils.get(guild.roles, name=r_name)
        if not existing:
            # Check by keyword
            keyword = r_name.split("┆")[-1].strip().lower()
            existing = next((r for r in guild.roles if keyword in r.name.lower()), None)
        
        if not existing:
            try:
                role = await guild.create_role(
                    name=r_name,
                    color=color,
                    mentionable=True,
                    reason="Automated community notification self-role"
                )
                print(f"  Created role: '{role.name}'")
                await asyncio.sleep(0.4)
            except Exception as e:
                print(f"  Failed to create role '{r_name}': {e}")
        else:
            print(f"  Role '{existing.name}' already exists.")

    print("\n--- 2. Deploying Notification & Gaming Roles Panel in #🏷️｜ʀᴏʟᴇꜱ ---")
    roles_ch = guild.get_channel(ROLES_CHANNEL_ID)
    if roles_ch:
        embed_pings = discord.Embed(
            title="🔔 ✦ COMMUNITY NOTIFICATION PINGS ✦ 🔔",
            description=(
                "Click below to subscribe or unsubscribe to community alerts with zero spam!\n\n"
                "> 📢 **Announcements:** Major server news, giveaways & patch updates.\n"
                "> 🎁 **Giveaways:** Nitro, coin drops & steam key events.\n"
                "> 🏆 **Tournaments:** Scrims, 4v4 custom rooms & competitive brackets.\n"
                "> 🍿 **Movie Nights:** Cinema watch parties in `🍿 | Movie Time 1 & 2`."
            ),
            color=0xA55EEA
        )
        embed_pings.set_footer(text="RAI FAM 💗 • Instant 1-Click Role Toggle", icon_url=config.RAI_ICON_URL)

        embed_games = discord.Embed(
            title="🎮 ✦ GAMING SQUAD ROLES ✦ 🎮",
            description=(
                "Equip your favorite game roles to find teammates and get pinged for squad rooms:\n\n"
                "> ⚡ **Free Fire:** Squad matches, CS custom rooms & clash ranked.\n"
                "> 🎯 **BGMI:** Classic erangel, arena 4v4 & tournament scrims.\n"
                "> 🔫 **GTA RP:** FiveM Tamil RP & party gameplay.\n"
                "> 🧸 **Roblox:** Mini-games, horror rooms & chilling."
            ),
            color=0x2ED573
        )
        embed_games.set_footer(text="RAI FAM 💗 • Gaming Hub", icon_url=config.RAI_ICON_URL)

        try:
            await roles_ch.send(embed=embed_pings, view=NotificationRolesView())
            await asyncio.sleep(0.5)
            await roles_ch.send(embed=embed_games, view=GamingRolesView())
            print("  Posted Notification & Gaming role panels in #🏷️｜ʀᴏʟᴇꜱ!")
        except Exception as e:
            print(f"  Failed to send role embeds: {e}")

    print("\n--- 3. Deploying 1-Click Arcade & Economy Station in #🤖｜ʙᴏᴛ-ᴄᴍᴅꜱ ---")
    bot_cmds_ch = guild.get_channel(BOT_CMDS_CHANNEL_ID)
    if bot_cmds_ch:
        embed_arcade = discord.Embed(
            title="🎮 ✦ RAI VIBES 1-CLICK ARCADE & ECONOMY STATION ✦ 🪙",
            description=(
                "Welcome to the **RAI FAM 24/7 Arcade**! Tap any button below to manage your coins, claim rewards, and test your luck instantly with zero typing:\n\n"
                "> 🪙 **Claim Daily Bonus:** Claim 500+ coins and build your daily multiplier streak!\n"
                "> 🎰 **Lucky Wheel Spin:** Free 18h Wheel of Fortune spin for jackpots up to 10,000 coins!\n"
                "> 💳 **My Wallet & Stats:** Check your coin balance and gaming history privately.\n"
                "> 🎮 **Match Squad (LFG):** Instant gateway to Free Fire, BGMI, and GTA RP matchmaking!"
            ),
            color=0x00FFCC
        )
        embed_arcade.set_image(url="https://images.unsplash.com/photo-1511512578047-dfb367046420?q=80&w=1000&auto=format&fit=crop")
        embed_arcade.set_footer(text="RAI VIBES 💗 • Autonomous Casino & Economy Hub", icon_url=config.RAI_ICON_URL)

        try:
            arcade_msg = await bot_cmds_ch.send(embed=embed_arcade, view=ArcadeStationView())
            await arcade_msg.pin()
            print("  Posted & Pinned Arcade Station in #🤖｜ʙᴏᴛ-ᴄᴍᴅꜱ!")
        except Exception as e:
            print(f"  Failed to post arcade station: {e}")

    print("\nAll community upgrades deployed successfully!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
