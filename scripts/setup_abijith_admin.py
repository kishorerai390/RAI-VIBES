import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath("."))
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
TARGET_GUILD_ID = 1428058914141900860  # ABIJITH 777

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
client = discord.Client(intents=intents)

from cogs.tickets import PersistentTicketLauncherView
import config

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")
    guild = client.get_guild(TARGET_GUILD_ID)
    if not guild:
        print(f"Target guild {TARGET_GUILD_ID} not found!")
        await client.close()
        return

    print(f"Setting up Bot Administration on '{guild.name}' ({guild.id})...")

    # 1. Resolve Staff Roles
    founder_role = discord.utils.get(guild.roles, id=1550205899069726810) or discord.utils.get(guild.roles, name="👑 ┆ 𝐅𝐎𝐔𝐍𝐃𝐄𝐑 🍷")
    head_admin_role = discord.utils.get(guild.roles, id=1550205902706049214) or discord.utils.get(guild.roles, name="⚡ ┆ 𝐇𝐄𝐀𝐃 𝐀𝐃𝐌𝐈𝐍 ⚡")
    mod_role = discord.utils.get(guild.roles, id=1550205905830682795) or discord.utils.get(guild.roles, name="🛡️ ┆ 𝐌𝐎𝐃𝐄𝐑𝐀𝐓𝐎𝐑 🛡️")
    verified_role = discord.utils.get(guild.roles, id=1550205910218182696) or discord.utils.get(guild.roles, name="✦ ᴠᴇʀɪꜰɪᴇᴅ")
    everyone_role = guild.default_role

    staff_roles = [r for r in [founder_role, head_admin_role, mod_role] if r is not None]
    print(f"Resolved staff roles: {[r.name for r in staff_roles]}")

    # 2. Create or find category '🔱 VIP & SENTINEL HQ'
    hq_cat = (
        discord.utils.get(guild.categories, name="🔱 VIP & SENTINEL HQ") or
        discord.utils.get(guild.categories, name="VIP & SENTINEL HQ")
    )
    cat_overwrites = {
        everyone_role: discord.PermissionOverwrite(view_channel=False, read_messages=False, connect=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, connect=True, speak=True, manage_messages=True, manage_channels=True)
    }
    for r in staff_roles:
        cat_overwrites[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, connect=True, speak=True)

    if not hq_cat:
        hq_cat = await guild.create_category("🔱 VIP & SENTINEL HQ", overwrites=cat_overwrites, position=len(guild.categories))
        print("Created category '🔱 VIP & SENTINEL HQ'")
        await asyncio.sleep(0.5)
    else:
        await hq_cat.edit(overwrites=cat_overwrites)
        print("Updated category overwrites for '🔱 VIP & SENTINEL HQ'")

    # Helper function to create text channel if missing
    async def get_or_create_text_channel(name: str, topic: str = "", overwrites: dict = None):
        ch = discord.utils.get(hq_cat.text_channels, name=name)
        if not ch:
            # Check elsewhere in guild
            ch = discord.utils.get(guild.text_channels, name=name)
            if ch:
                await ch.edit(category=hq_cat)
        if not ch:
            ch = await guild.create_text_channel(name, category=hq_cat, topic=topic, overwrites=overwrites)
            print(f"  Created text channel: {name}")
            await asyncio.sleep(0.4)
        else:
            if overwrites:
                await ch.edit(overwrites=overwrites)
            print(f"  Found/Updated channel: {name}")
        return ch

    # Helper function to create voice channel if missing
    async def get_or_create_voice_channel(name: str, user_limit: int = 0, overwrites: dict = None):
        ch = discord.utils.get(hq_cat.voice_channels, name=name)
        if not ch:
            ch = discord.utils.get(guild.voice_channels, name=name)
            if ch:
                await ch.edit(category=hq_cat)
        if not ch:
            ch = await guild.create_voice_channel(name, category=hq_cat, user_limit=user_limit, bitrate=96000, overwrites=overwrites)
            print(f"  Created voice channel: {name}")
            await asyncio.sleep(0.4)
        else:
            if overwrites:
                await ch.edit(overwrites=overwrites)
            print(f"  Found/Updated voice channel: {name}")
        return ch

    # Standard Staff Overwrites
    staff_view_only_overwrites = {
        everyone_role: discord.PermissionOverwrite(view_channel=False, read_messages=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, embed_links=True, attach_files=True)
    }
    for r in staff_roles:
        staff_view_only_overwrites[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=False)

    staff_chat_overwrites = {
        everyone_role: discord.PermissionOverwrite(view_channel=False, read_messages=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True, attach_files=True)
    }
    for r in staff_roles:
        staff_chat_overwrites[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, attach_files=True)

    # 3. Create Administration Channels
    print("\n--- Creating Channels in 🔱 VIP & SENTINEL HQ ---")

    # 1. 👑｜ᴇxᴇᴄᴜᴛɪᴠᴇ-ʟᴏᴜɴɢᴇ
    exec_ch = await get_or_create_text_channel("👑｜ᴇxᴇᴄᴜᴛɪᴠᴇ-ʟᴏᴜɴɢᴇ", topic="Private executive council & leadership lounge", overwrites=staff_chat_overwrites)

    # 2. 🛡️｜ꜱᴛᴀꜰꜰ-ᴏᴘᴇʀᴀᴛɪᴏɴꜱ
    staff_ops_ch = await get_or_create_text_channel("🛡️｜ꜱᴛᴀꜰꜰ-ᴏᴘᴇʀᴀᴛɪᴏɴꜱ", topic="Staff moderation directives, case discussions & commands", overwrites=staff_chat_overwrites)
    
    # 3. 📋｜ᴀᴜᴅɪᴛ-ʟᴏɢꜱ
    audit_ch = await get_or_create_text_channel("📋｜ᴀᴜᴅɪᴛ-ʟᴏɢꜱ", topic="Discord server audit events and administrative records", overwrites=staff_view_only_overwrites)

    # 4. 🎫｜ᴛɪᴄᴋᴇᴛ-ꜱᴜᴘᴘᴏʀᴛ
    ticket_overwrites = {
        everyone_role: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=False, add_reactions=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True)
    }
    for r in staff_roles:
        ticket_overwrites[r] = discord.PermissionOverwrite(view_channel=True, read_messages=True, send_messages=True, manage_messages=True)
    ticket_ch = await get_or_create_text_channel("🎫｜ᴛɪᴄᴋᴇᴛ-ꜱᴜᴘᴘᴏʀᴛ", topic="Official Member Support & Ticket Help Desk", overwrites=ticket_overwrites)

    # 5. 📝｜ᴍᴏᴅᴇʀᴀᴛɪᴏɴ-ʟᴏɢꜱ
    mod_logs_ch = await get_or_create_text_channel("📝｜ᴍᴏᴅᴇʀᴀᴛɪᴏɴ-ʟᴏɢꜱ", topic="Automated record of strikes, mutes, kicks and bans", overwrites=staff_view_only_overwrites)

    # 6. 🚨｜ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ
    sentinel_ch = await get_or_create_text_channel("🚨｜ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ", topic="Automated security telemetry, anti-raid, anti-spam and anti-nuke alerts", overwrites=staff_view_only_overwrites)

    # 7. 👑 | Executive Suite
    exec_voice_overwrites = {
        everyone_role: discord.PermissionOverwrite(view_channel=False, connect=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)
    }
    for r in staff_roles:
        exec_voice_overwrites[r] = discord.PermissionOverwrite(view_channel=True, connect=True, speak=True)
    exec_voice = await get_or_create_voice_channel("👑 | Executive Suite", user_limit=10, overwrites=exec_voice_overwrites)

    # 4. Deploy Embeds & Persistent Panels
    print("\n--- Deploying Admin Panels & Embeds ---")

    # Post Staff Directives in #🛡️｜ꜱᴛᴀꜰꜰ-ᴏᴘᴇʀᴀᴛɪᴏɴꜱ
    async for msg in staff_ops_ch.history(limit=5):
        if msg.author == client.user:
            await msg.delete()
    
    staff_embed = discord.Embed(
        title="🛡️ RAI SENTINEL • STAFF OPERATIONAL DIRECTIVES",
        description=(
            "**Confidential Moderator Standard Operating Procedures (SOP)**\n\n"
            "This channel is the private operations room for **Founders**, **Head Admins**, and **Moderators**. "
            "Follow the standard moderation workflow below to maintain server order and integrity.\n\n"
            "──────────────────────────────────────────────\n"
            "### ⚖️ Moderation Escalation Protocol\n"
            "1. **Minor Infraction (Excessive noise, caps, spam)**:\n"
            "   • Issue formal warning: `/warn <user> <reason>`\n"
            "2. **Voice Trolling / Mic Earrape / Channel Hopping**:\n"
            "   • Immediately isolate: `/freeze <user> 10` *(Yanks user to silent Freeze Chamber)*\n"
            "3. **Persistent Chat Abuse / Harassment**:\n"
            "   • Mute: `/servermute <user> 30 <reason>`\n"
            "4. **Severe Attacks / Raid Attempts**:\n"
            "   • Immediate expulsion: `/kick` or `/ban`\n\n"
            "### 📝 Documentation & Mod Notes\n"
            "• Record evidence & case notes on members: `/modnote add <user> <note>`\n"
            "• Check a user's previous discipline history: `/modnote view <user>`\n"
            "• Check warnings: `/strikes <user>`\n\n"
            f"### 🎟️ Support Tickets\n"
            f"When a member opens a ticket in {ticket_ch.mention}, respond promptly and click **Close Ticket** once resolved."
        ),
        color=0x3498DB
    )
    staff_embed.set_footer(text=f"{guild.name} Staff HQ • Confidential", icon_url=guild.icon.url if guild.icon else None)
    await staff_ops_ch.send(embed=staff_embed)
    print("  Posted Staff Directives in #🛡️｜ꜱᴛᴀꜰꜰ-ᴏᴘᴇʀᴀᴛɪᴏɴꜱ")

    # Post Ticket Launch Panel in #🎫｜ᴛɪᴄᴋᴇᴛ-ꜱᴜᴘᴘᴏʀᴛ
    async for msg in ticket_ch.history(limit=5):
        if msg.author == client.user:
            await msg.delete()

    ticket_embed = discord.Embed(
        title=f"🎫 {guild.name.upper()} • OFFICIAL SUPPORT HUB",
        description=(
            f"Welcome to the **{guild.name}** Support Desk!\n\n"
            "If you need private assistance from server staff, report an issue, or discuss partnerships, "
            "please select an option from the menu below to open your dedicated support channel.\n\n"
            "> 💬 **General Support & Inquiries:** Questions about server features, permissions, or rules.\n"
            "> 🚨 **Report a Member / Rule Violation:** Report harassment, scam links, or toxicity in confidence.\n"
            "> 🤝 **Partnership & Collaboration:** Connect with server leadership regarding community events.\n"
            "> 💎 **VIP / Booster Support:** Claim custom perks, roles, or special recognition.\n\n"
            "*A private ticket channel will be created instantly for you and our moderation team.*"
        ),
        color=0x9B5DE5
    )
    ticket_embed.set_image(url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop")
    ticket_embed.set_footer(text=f"{guild.name} Support Desk • Powered by RAI SENTINEL", icon_url=guild.icon.url if guild.icon else None)
    await ticket_ch.send(embed=ticket_embed, view=PersistentTicketLauncherView())
    print("  Posted Ticket Launch Panel in #🎫｜ᴛɪᴄᴋᴇᴛ-ꜱᴜᴘᴘᴏʀᴛ")

    # Post Sentinel Security Shield header in #🚨｜ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ
    async for msg in sentinel_ch.history(limit=5):
        if msg.author == client.user:
            await msg.delete()

    sentinel_embed = discord.Embed(
        title="🚨 SENTINEL SECURITY SHIELD • ACTIVE MONITORING",
        description=(
            f"**Automated Server Protection Engine Activated for {guild.name}!**\n\n"
            "• 🛡️ **Anti-Raid Protection:** Real-time burst join velocity analysis & mass-invite lockdown.\n"
            "• 🛑 **Anti-Spam Filter:** High frequency message suppression & duplicate repetition detection.\n"
            "• 🔗 **Link & Scam Shield:** Instant deletion and quarantine for malicious token loggers & phishing links.\n"
            "• 🔒 **Anti-Nuke Monitor:** Guarding channel deletions, mass role modifications, and unauthorized bot additions.\n\n"
            "*All automated security detections, kicks, and quarantine events will stream here live.*"
        ),
        color=0xE74C3C
    )
    sentinel_embed.set_footer(text="RAI SENTINEL 🛡️ Autonomous Shield Active", icon_url=guild.icon.url if guild.icon else None)
    await sentinel_ch.send(embed=sentinel_embed)
    print("  Posted Sentinel Shield Header in #🚨｜ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ")

    print(f"\n🎉 Bot administration successfully added to {guild.name}!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
