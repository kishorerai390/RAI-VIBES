import os
import sys
import asyncio
from pathlib import Path
import discord
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

import config
from utils.persistent_views import (
    ColorRolesView,
    GamingRolesView,
    NotificationRolesView,
    IdentityRolesView,
    VerifyButtonView,
    TicketCreateView
)

intents = discord.Intents.default()
intents.guilds = True
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
    rules_chan = discord.utils.get(guild.text_channels, name="rules") or discord.utils.get(guild.text_channels, name="📜・rules")
    if rules_chan:
        try:
            await rules_chan.purge(limit=20)
        except Exception:
            pass
        rules_embed = discord.Embed(
            title="🌸 ⋆⋅ RAI FAM COMMUNITY GUIDELINES ⋅⋆ 🌸",
            description=(
                "Welcome to **RAI FAM 💗**! To keep our hangout safe, fun, and chill for everyone, please follow our server guidelines:\n\n"
                "**1️⃣ Mutual Respect & Kindness**\n"
                "• Treat all members with respect. Harassment, hate speech, racism, or toxicity will result in an immediate strike or ban.\n\n"
                "**2️⃣ Voice Channel Etiquette**\n"
                "• Avoid mic spamming, ear-raping, or loud soundboards in public voice lounges.\n"
                "• Respect duo/trio and squad channels.\n\n"
                "**3️⃣ No Spamming or Phishing Links**\n"
                "• Posting fake Nitro, scam steam links, or spamming text channels is strictly forbidden and auto-blocked.\n\n"
                "**4️⃣ No Self-Promotion / Unsolicited DMs**\n"
                "• Please do not send unsolicited Discord server invites in chat or members' DMs.\n\n"
                "**5️⃣ Respect Staff & High Command**\n"
                "• Follow instructions from the Staff and Guardian Team.\n\n"
                "✨ *Enjoy your time, hop into a VC, and vibe with the family!* 🍿🎵"
            ),
            color=config.COLOR_PRIMARY
        )
        rules_embed.set_thumbnail(url=config.RAI_ICON_URL)
        rules_embed.set_footer(text="RAI FAM 💗 • Safety & Guidelines", icon_url=config.RAI_ICON_URL)
        await rules_chan.send(embed=rules_embed)
        print("✅ Rules embed posted!")

    # 2. Populate #✅・verify
    verify_chan = discord.utils.get(guild.text_channels, name="verify") or discord.utils.get(guild.text_channels, name="✅・verify")
    if verify_chan:
        try:
            await verify_chan.purge(limit=20)
        except Exception:
            pass
        verify_embed = discord.Embed(
            title="🛡️ ⋆⋅ RAI FAM MEMBER VERIFICATION ⋅⋆ 🛡️",
            description=(
                "Welcome to **RAI FAM 💗**! 🍿🎵\n\n"
                "To prevent spam bots and keep our community friendly, safe, and neat, "
                "please click the **`[✅ Verify & Enter Community]`** button below to unlock all channels.\n\n"
                "By clicking verify, you agree to follow our server rules & code of conduct."
            ),
            color=config.COLOR_PRIMARY
        )
        verify_embed.set_thumbnail(url=config.RAI_ICON_URL)
        verify_embed.set_footer(text="Instant 1-Click Verification • RAI FAM💗", icon_url=config.RAI_ICON_URL)
        await verify_chan.send(embed=verify_embed, view=VerifyButtonView())
        print("✅ Verification embed posted!")

    # 3. Populate #🎭・self-roles
    roles_chan = discord.utils.get(guild.text_channels, name="self-roles") or discord.utils.get(guild.text_channels, name="🎭・self-roles")
    if roles_chan:
        try:
            await roles_chan.purge(limit=20)
        except Exception:
            pass
        
        # Color Panel
        embed_color = discord.Embed(
            title="🎨 ┃ CHOOSE YOUR NAME COLOR",
            description="Personalize your appearance across the server with our curated aesthetic colors!\nClick any button below to equip or remove your color role.",
            color=config.COLOR_PRIMARY
        )
        embed_color.add_field(
            name="✨ Available Palette",
            value="• 🌸 **Sakura Pink** (`#FF69B4`)\n• 💜 **Neon Violet** (`#9B5DE5`)\n• 🩵 **Cyber Cyan** (`#00F0FF`)\n• 💛 **Royal Gold** (`#FEE440`)",
            inline=False
        )
        await roles_chan.send(embed=embed_color, view=ColorRolesView())

        # Gaming Panel
        embed_gaming = discord.Embed(
            title="🎮 ┃ GAMING & DEVICE PLATFORMS",
            description="Select your preferred gaming platforms and titles to connect with squadmates!",
            color=config.COLOR_SECONDARY
        )
        embed_gaming.add_field(
            name="🕹️ Platform & Game Tags",
            value="• 💻 **PC Player** — Desktop & PC gaming\n• 📱 **Mobile Player** — Mobile & tablet gamers\n• 💥 **Free Fire** — Battle Royale squad pings\n• ⚡ **BGMI** — BGMI / PUBG custom rooms\n• 🧸 **Roblox** — Hangout & mini-games",
            inline=False
        )
        await roles_chan.send(embed=embed_gaming, view=GamingRolesView())

        # Notifications Panel
        embed_notif = discord.Embed(
            title="🔔 ┃ NOTIFICATION & EVENT PINGS",
            description="Choose which community alerts and event announcements you'd like to receive:",
            color=config.COLOR_GOLD
        )
        embed_notif.add_field(
            name="📢 Notification Preferences",
            value="• 🍿 **Movie Alerts** — Cinema Theater watch party reminders\n• 🎉 **Giveaways** — Nitro, coins & reward alerts\n• 📢 **Server News** — Important announcements\n• 🎵 **Music Jam** — Live listening parties & karaoke",
            inline=False
        )
        await roles_chan.send(embed=embed_notif, view=NotificationRolesView())

        # Identity Panel
        embed_id = discord.Embed(
            title="👤 ┃ IDENTITY & VERIFICATION",
            description="Select your identity tags and age verification status:",
            color=config.COLOR_DARK
        )
        embed_id.add_field(
            name="🌟 Member Identity",
            value="• 🤴 **Male** — He / Him\n• 👸 **Female** — She / Her\n• 🌈 **They / Them** — Non-Binary / Other\n• 🔞 **18+ Verified** — Adult lounge access",
            inline=False
        )
        await roles_chan.send(embed=embed_id, view=IdentityRolesView())
        print("✅ Self-roles panels posted!")

    # 4. Populate #📢・announcements
    ann_chan = discord.utils.get(guild.text_channels, name="announcements") or discord.utils.get(guild.text_channels, name="📢・announcements")
    if ann_chan:
        try:
            await ann_chan.purge(limit=20)
        except Exception:
            pass
        ann_embed = discord.Embed(
            title="🌸 ⋆⋅ WELCOME TO THE NEW RAI FAM 💗 ⋅⋆ 🌸",
            description=(
                "Welcome to the freshly upgraded **RAI FAM 💗** community!\n\n"
                "**🚀 What's New & Available:**\n"
                "• 🎙️ **Studio-Quality Bitrate (96 kbps)** across all voice lounges\n"
                "• 🎮 **4-Player Squad Gaming Channels** (Free Fire, BGMI, Roblox)\n"
                "• ➕ **Join-To-Create Dynamic Voice Rooms** (Spawn your own private lounge)\n"
                "• 🎨 **Custom Name Colors & Roles** in `<#1545502722739150898>`\n"
                "• 📻 **24/7 Lo-Fi & Tamil Nadu FM Radio**\n"
                "• 🍿 **Cinema Lounge & YouTube Watch Together**\n\n"
                "Grab your roles in `<#1545502722739150898>` and jump into voice! 💗✨"
            ),
            color=config.COLOR_PRIMARY
        )
        ann_embed.set_thumbnail(url=config.RAI_ICON_URL)
        ann_embed.set_footer(text="RAI FAM 💗 • Official Server Announcement", icon_url=config.RAI_ICON_URL)
        await ann_chan.send(embed=ann_embed)
        print("✅ Announcements embed posted!")

    # 5. Populate #🛡️・staff-hq
    staff_chan = discord.utils.get(guild.text_channels, name="staff-hq") or discord.utils.get(guild.text_channels, name="🛡️・staff-hq")
    if staff_chan:
        try:
            await staff_chan.purge(limit=20)
        except Exception:
            pass
        staff_embed = discord.Embed(
            title="🛡️ ⋆⋅ STAFF & ADMIN COMMAND CENTER ⋅⋆ 🛡️",
            description=(
                "Welcome to the Staff Zone. Here is your quick command reference:\n\n"
                "**🚨 Security & Voice Isolation:**\n"
                "• `/freeze @user [mins] [reason]` • Isolate noisy/trolling member in Freeze Chamber + Timeout\n"
                "• `/unfreeze @user` • Release member from Freeze Chamber and restore voice/chat\n"
                "• `/lockdown` • Instantly lock all public channels during a raid\n"
                "• `/unlock` • Restore chatting after lockdown\n"
                "• `/clear <amount>` • Bulk purge up to 100 messages\n"
                "• `/warn @user <reason>` • Issue official warning (Strike system)\n"
                "• `/kick @user` & `/ban @user` • Moderation actions\n\n"
                "**🎵 Music & Entertainment:**\n"
                "• `/c` • Open Rythm-style interactive command directory\n"
                "• `/play <song>` • Play high-fidelity audio\n"
                "• `/radio` • Stream 24/7 live stations\n"
                "• `/stay247` • Keep bot in voice channel 24/7\n"
            ),
            color=config.COLOR_GOLD
        )
        staff_embed.set_footer(text="RAI FAM 💗 • High Command System", icon_url=config.RAI_ICON_URL)
        await staff_chan.send(embed=staff_embed)
        print("✅ Staff HQ embed posted!")

    # 6. Populate #🎫・ticket-support
    ticket_chan = discord.utils.get(guild.text_channels, name="ticket-support") or discord.utils.get(guild.text_channels, name="🎫・ticket-support")
    if ticket_chan:
        try:
            await ticket_chan.purge(limit=20)
        except Exception:
            pass
        ticket_embed = discord.Embed(
            title="🎫 ⋆⋅ RAI FAM SUPPORT & HELP DESK ⋅⋆ 🎫",
            description=(
                "Need assistance from our staff team? Have a question or want to report an issue?\n\n"
                "Click the **`[🎫 Open Support Ticket]`** button below to create a private, confidential channel with our Staff & High Command."
            ),
            color=config.COLOR_PRIMARY
        )
        ticket_embed.set_thumbnail(url=config.RAI_ICON_URL)
        ticket_embed.set_footer(text="RAI FAM 💗 • Support Ticket Desk", icon_url=config.RAI_ICON_URL)
        await ticket_chan.send(embed=ticket_embed, view=TicketCreateView())
        print("✅ Ticket Support embed posted!")

    # 7. Populate #💎・booster-lounge
    booster_chan = discord.utils.get(guild.text_channels, name="booster-lounge") or discord.utils.get(guild.text_channels, name="💎・booster-lounge")
    if booster_chan:
        try:
            await booster_chan.purge(limit=20)
        except Exception:
            pass
        booster_embed = discord.Embed(
            title="💎 ⋆⋅ RAI FAM VIP BOOSTER LOUNGE ⋅⋆ 💎",
            description=(
                "Welcome to the exclusive VIP lounge for our amazing **Server Boosters**! 🚀\n\n"
                "**💎 Exclusive Booster Perks:**\n"
                "• 👑 Custom Hoisted Booster Badge & Role\n"
                "• 🚀 Access to private Booster Voice Lounge (`🚀 | BOOSTER LOUNGE`)\n"
                "• 🎨 Exclusive VIP Color Roles\n"
                "• 🎁 Special entry into Booster-only Giveaways & VIP Events\n\n"
                "*Thank you so much for supporting and boosting RAI FAM!* 💗✨"
            ),
            color=0xF1C40F
        )
        booster_embed.set_thumbnail(url=config.RAI_ICON_URL)
        booster_embed.set_footer(text="RAI FAM 💗 • VIP Booster Club", icon_url=config.RAI_ICON_URL)
        await booster_chan.send(embed=booster_embed)
        print("✅ Booster Lounge embed posted!")

    print("🎉 ALL SERVER TEMPLATES & EMBEDS AUTO-FILLED SUCCESSFULLY!")
    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
