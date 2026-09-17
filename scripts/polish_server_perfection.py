import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

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

    everyone = guild.default_role
    founder_role = discord.utils.get(guild.roles, id=1545494610489643038)
    head_admin_role = discord.utils.get(guild.roles, id=1545506927788687470)
    mod_role = discord.utils.get(guild.roles, id=1545494600347680918)
    rai_fam_role = discord.utils.get(guild.roles, id=1545494584203673740)
    booster_role = discord.utils.get(guild.roles, id=1545494591883579434)
    verified_role = discord.utils.get(guild.roles, id=1549504522953695269)

    print("\n--- 1. Harmonizing Channel Names ---")
    name_updates = {
        1549416359723532480: "🤖｜ʙᴏᴛ-ᴄᴍᴅꜱ",
        1550187304876900543: "🎮｜ɢᴀᴍɪɴɢ-ʜᴜʙ",
        1550187318915244183: "🎵｜ꜱᴏɴɢ-ʀᴇǫᴜᴇꜱᴛꜱ",
        1550187321285148782: "👑｜ᴇxᴇᴄᴜᴛɪᴠᴇ-ᴄʜᴀᴛ",
    }
    for ch_id, new_name in name_updates.items():
        ch = guild.get_channel(ch_id)
        if ch and ch.name != new_name:
            try:
                await ch.edit(name=new_name)
                print(f"  Renamed: {ch.name} -> {new_name}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  Failed rename {ch_id}: {e}")

    print("\n--- 2. Setting Channel Permissions ---")
    # Read-only information channels
    readonly_channels = [
        1545502705643167876,  # welcome-sanctuary
        1550159859607928882,  # partnerships
        1550187304876900543,  # gaming-hub
    ]
    for ch_id in readonly_channels:
        ch = guild.get_channel(ch_id)
        if ch:
            try:
                ow = ch.overwrites_for(everyone)
                ow.send_messages = False
                ow.read_messages = True
                await ch.set_permissions(everyone, overwrite=ow, reason="Security: lock read-only channel")
                print(f"  Locked for messaging: {ch.name}")
                await asyncio.sleep(0.5)
            except Exception as e:
                print(f"  Failed permission for {ch.name}: {e}")

    # AFK Channel speak restriction
    afk_ch = guild.get_channel(1550187298115551272)
    if afk_ch:
        try:
            ow = afk_ch.overwrites_for(everyone)
            ow.speak = False
            await afk_ch.set_permissions(everyone, overwrite=ow, reason="AFK: Mute by default")
            print("  AFK speak disabled for @everyone")
        except Exception as e:
            print(f"  Failed AFK permission: {e}")

    # Executive Suite Restrictions
    exec_chat = guild.get_channel(1550187321285148782)
    exec_vc = guild.get_channel(1550187323084374079)

    vip_roles = [r for r in [founder_role, head_admin_role, mod_role, rai_fam_role, booster_role] if r]

    if exec_chat:
        try:
            # Hide from everyone
            ow_ev = exec_chat.overwrites_for(everyone)
            ow_ev.view_channel = False
            await exec_chat.set_permissions(everyone, overwrite=ow_ev, reason="VIP: private channel")
            
            # Grant to VIP roles
            for r in vip_roles:
                ow_vip = exec_chat.overwrites_for(r)
                ow_vip.view_channel = True
                ow_vip.send_messages = True
                ow_vip.read_message_history = True
                await exec_chat.set_permissions(r, overwrite=ow_vip)
            print("  Secured executive-chat for VIP roles only")
        except Exception as e:
            print(f"  Failed exec_chat permissions: {e}")

    if exec_vc:
        try:
            # Hide/lock from everyone
            ow_ev = exec_vc.overwrites_for(everyone)
            ow_ev.view_channel = False
            ow_ev.connect = False
            await exec_vc.set_permissions(everyone, overwrite=ow_ev, reason="VIP: private voice suite")

            # Grant to VIP roles
            for r in vip_roles:
                ow_vip = exec_vc.overwrites_for(r)
                ow_vip.view_channel = True
                ow_vip.connect = True
                ow_vip.speak = True
                await exec_vc.set_permissions(r, overwrite=ow_vip)
            print("  Secured executive suite VC for VIP roles only")
        except Exception as e:
            print(f"  Failed exec_vc permissions: {e}")

    print("\n--- 3. Perfecting Order Within Categories ---")
    desired_order = {
        # INFORMATION
        1545502700840427702: 0,  # verify-here
        1545502705643167876: 1,  # welcome-sanctuary
        1545502710101704714: 2,  # divine-codex
        1545502718792175646: 3,  # announcements
        1545502722739150898: 4,  # role-info
        1550159859607928882: 5,  # partnerships

        # CHATS
        1545502730699808768: 0,  # chats
        1546097792915873842: 1,  # media
        1550184397540556951: 2,  # ff-chat
        1549416359723532480: 3,  # bot-cmds
        1550184399742697512: 4,  # owo-chat
        1549439621497102518: 5,  # server-shop
        1549407114861215815: 6,  # hall-of-fame
        1549489880776839248: 7,  # suggestions

        # VOICE ZONE
        1550187295821402114: 0,  # JOIN TO CREATE VC
        1550186738410987591: 1,  # CHILL OUT 1
        1550186767632826459: 2,  # CHILL OUT 2
        1550186728285937727: 3,  # DUO
        1550187298115551272: 4,  # AFK

        # GAMING ZONE
        1550187304876900543: 0,  # gaming-hub
        1550186750289379328: 1,  # FREE FIRE
        1550186752163975250: 2,  # BGMI

        # MUSIC ZONE
        1550187318915244183: 0,  # song-requests
        1550186760779211003: 1,  # RAI MUSIC 24/7

        # RAI FAM
        1550187321285148782: 0,  # executive-chat
        1550187323084374079: 1,  # RAI EXECUTIVE
    }

    for ch_id, pos in desired_order.items():
        ch = guild.get_channel(ch_id)
        if ch and ch.position != pos:
            try:
                await ch.edit(position=pos)
                await asyncio.sleep(0.4)
            except Exception as e:
                print(f"  Order error for {ch_id}: {e}")

    print("\nAdjustment complete!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
