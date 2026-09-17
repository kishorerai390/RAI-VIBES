import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090
CINEMA_CHANNEL_ID = 1550196955660029964

intents = discord.Intents.default()
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
    verified_role = discord.utils.get(guild.roles, id=1549504522953695269)
    rai_fam_role = discord.utils.get(guild.roles, id=1545494584203673740)
    booster_role = discord.utils.get(guild.roles, id=1545494591883579434)
    mod_role = discord.utils.get(guild.roles, id=1545494600347680918)
    head_admin_role = discord.utils.get(guild.roles, id=1545506927788687470)
    founder_role = discord.utils.get(guild.roles, id=1545494610489643038)

    print("\n--- 1. Enabling Stream Permission on Server Roles ---")
    roles_to_enable_stream = [
        verified_role,
        rai_fam_role,
        booster_role,
        mod_role,
        head_admin_role,
        founder_role
    ]
    for r in roles_to_enable_stream:
        if r:
            perms = r.permissions
            if not perms.stream:
                perms.update(stream=True)
                try:
                    await r.edit(permissions=perms, reason="Allow members to stream / screenshare movies & gaming")
                    print(f"  Enabled stream on role: '{r.name}'")
                    await asyncio.sleep(0.5)
                except Exception as e:
                    print(f"  Failed to edit role '{r.name}': {e}")

    print("\n--- 2. Setting Explicit Overwrites on Cinema Channel ---")
    cinema_ch = guild.get_channel(CINEMA_CHANNEL_ID)
    if not cinema_ch:
        print(f"Cinema channel {CINEMA_CHANNEL_ID} not found!")
        await client.close()
        return

    # Everyone overwrite
    ow_everyone = cinema_ch.overwrites_for(everyone)
    ow_everyone.connect = True
    ow_everyone.speak = True
    ow_everyone.stream = True
    ow_everyone.use_embedded_activities = True
    try:
        await cinema_ch.set_permissions(everyone, overwrite=ow_everyone, reason="Allow movie & screen streaming for everyone")
        print("  Set cinema permissions for @everyone: stream=True, activities=True")
    except Exception as e:
        print(f"  Error setting cinema permissions for everyone: {e}")

    # Verified role overwrite
    if verified_role:
        ow_verified = cinema_ch.overwrites_for(verified_role)
        ow_verified.connect = True
        ow_verified.speak = True
        ow_verified.stream = True
        ow_verified.use_embedded_activities = True
        try:
            await cinema_ch.set_permissions(verified_role, overwrite=ow_verified, reason="Allow streaming for verified members")
            print("  Set cinema permissions for ✦ ᴠᴇʀɪꜰɪᴇᴅ: stream=True")
        except Exception as e:
            print(f"  Error setting cinema permissions for verified: {e}")

    # Also enable stream across other community voice channels
    voice_channels_to_unlock = [
        guild.get_channel(1550186738410987591), # Chill 1
        guild.get_channel(1550186767632826459), # Chill 2
        guild.get_channel(1550186728285937727), # Duo
        guild.get_channel(1550196951503474798), # Trio
        guild.get_channel(1550196963935264870), # GTA RP
    ]
    for vc in voice_channels_to_unlock:
        if vc:
            ow = vc.overwrites_for(everyone)
            ow.stream = True
            try:
                await vc.set_permissions(everyone, overwrite=ow, reason="Allow screensharing in voice lounge")
                print(f"  Unlocked stream in '{vc.name}'")
                await asyncio.sleep(0.3)
            except Exception as e:
                print(f"  Error setting stream in {vc.name}: {e}")

    print("\nCinema streaming and screensharing fully unlocked!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
