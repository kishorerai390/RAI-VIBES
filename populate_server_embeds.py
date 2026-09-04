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

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    # 1. Populate #📜・rules
    rules_chan = discord.utils.get(guild.text_channels, name="📜・rules")
    if rules_chan:
        await rules_chan.purge(limit=10)
        rules_embed = discord.Embed(
            title="📜 ⋆⋅ RAI FAM COMMUNITY GUIDELINES ⋅⋆",
            description=(
                "Welcome to **RAI FAM 💗**! To keep our hangout safe, fun, and chill for everyone, please follow our server guidelines:\n\n"
                "**1️⃣ Mutual Respect & Kindness**\n"
                "• Treat all members with respect. Harassment, hate speech, racism, or toxicity will result in an immediate ban.\n\n"
                "**2️⃣ Voice Channel Etiquette**\n"
                "• Avoid mic spamming, ear-raping, or loud soundboards in public voice lounges.\n"
                "• Respect duo/trio and squad channels.\n\n"
                "**3️⃣ No Spamming or Phishing Links**\n"
                "• Posting fake Nitro, scam steam links, or spamming text channels is strictly forbidden and auto-blocked.\n\n"
                "**4️⃣ No Self-Promotion / Invite Links**\n"
                "• Please do not send unsolicited Discord server invites in chat or members' DMs.\n\n"
                "**5️⃣ Respect Staff & Guardians**\n"
                "• Follow instructions from the **`👑 ┊ 𝐄𝐌𝐏𝐄𝐑𝐎𝐑`**, **`⚡ ┊ 𝐇𝐄𝐀𝐃 𝐀𝐃𝐌𝐈𝐍`**, and **`🛡️ ┊ 𝐆𝐔𝐀𝐑𝐃𝐈𝐀𝐍`**.\n\n"
                "✨ *Enjoy your time, hop into a VC, and vibe with the family!* 🌸"
            ),
            color=0xFFB7C5
        )
        rules_embed.set_footer(text="RAI FAM 💗 • Guidelines & Safety")
        await rules_chan.send(embed=rules_embed)
        print("✅ Rules embed posted!")

    # 2. Populate #📢・announcements
    ann_chan = discord.utils.get(guild.text_channels, name="📢・announcements")
    if ann_chan:
        await ann_chan.purge(limit=10)
        ann_embed = discord.Embed(
            title="🌸 ⋆⋅ WELCOME TO THE NEW RAI FAM 💗 ⋅⋆",
            description=(
                "Welcome to the freshly upgraded **RAI FAM 💗** community!\n\n"
                "**🚀 What's New:**\n"
                "• 🎙️ **Studio-Quality Bitrate (96 kbps)** across all voice lounges\n"
                "• 🎮 **4-Player Squad Gaming Channels** (Free Fire, BGMI, Roblox)\n"
                "• ➕ **Join-To-Create Dynamic Voice Rooms** (Make your own private voice lounge)\n"
                "• 🎨 **Custom Name Colors & Roles** in `#⭐・self-roles`\n"
                "• 📻 **24/7 Music Radio & Cinema Theater**\n"
                "• 🚀 **Launch Party Games** with `/activity` (YouTube Watch Together, Gartic, Poker, Chess)\n\n"
                "Grab your roles in **`#⭐・self-roles`** and jump into voice! 💗✨"
            ),
            color=0x9B5DE5
        )
        ann_embed.set_footer(text="RAI FAM 💗 • Official Server Announcement")
        await ann_chan.send(embed=ann_embed)
        print("✅ Announcements embed posted!")

    # 3. Populate #🛡️・staff-chat with Admin/Emperor Cheat Sheet
    staff_chan = discord.utils.get(guild.text_channels, name="🛡️・staff-chat")
    if staff_chan:
        staff_embed = discord.Embed(
            title="🛡️ ⋆⋅ STAFF & ADMIN COMMAND CENTER ⋅⋆",
            description=(
                "Welcome to the Staff Zone. Here is your quick command reference:\n\n"
                "**🚨 Security & Raid Defense:**\n"
                "• `/lockdown` • Instantly lock all public channels during a raid\n"
                "• `/unlock` • Restore chatting after lockdown\n"
                "• `/backup` • Take an instant snapshot of server structure\n"
                "• `/clear <amount>` • Bulk purge up to 100 messages\n"
                "• `/timeout <member> <mins> <reason>` • Mute a disruptive user\n"
                "• `/warn <member> <reason>` • Issue an official warning\n"
                "• `/kick <member> <reason>` • Kick a member\n\n"
                "**🎮 Voice & Entertainment:**\n"
                "• `/activity` • Launch YouTube Together, Gartic Phone, Poker, Chess in VC\n"
                "• `/play <song>` • High fidelity music streaming\n"
                "• `/rank` & `/leaderboard` • Check voice & chat leveling stats\n"
            ),
            color=0xFEE440
        )
        staff_embed.set_footer(text="RAI FAM 💗 • High Command System")
        await staff_chan.send(embed=staff_embed)
        print("✅ Staff command center posted!")

    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
