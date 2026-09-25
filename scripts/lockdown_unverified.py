import discord, asyncio, os, sys, aiohttp
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()
token = os.getenv('DISCORD_BOT_TOKEN')

async def main():
    headers = {'Authorization': f'Bot {token}', 'Content-Type': 'application/json'}
    # 1. Disable Discord Onboarding so it does not force public channels
    async with aiohttp.ClientSession() as session:
        body = {'enabled': False, 'default_channel_ids': ['1545502700840427702']}
        async with session.put('https://discord.com/api/v10/guilds/1457382179981099090/onboarding', headers=headers, json=body) as resp:
            print('Disabled Discord onboarding:', resp.status)

    intents = discord.Intents.default()
    client = discord.Client(intents=intents)
    await client.login(token)
    guild = await client.fetch_guild(1457382179981099090)
    everyone = guild.default_role
    roles = await guild.fetch_roles()
    verified_role = discord.utils.get(roles, name='✨・Verified')
    print(f'Verified role: {verified_role.name} ({verified_role.id})')

    channels_to_hide = [
        1545502730699808768, # general-chat
        1545502722739150898, # roles
        1545502718792175646, # announcements
        1545514505520545886, # tickets
        1550187304876900543, # lfg-matchmaking
        1550584226376720476, # cinema-chat
        1550584592707100682, # music-sharing
        1552359010513195099, # voice-controls
        1550184397540556951, # gaming-chat
        1550184399742697512, # owo-arcade
        1551184138932068373, # clips-and-media
        1551184144153714728, # setups-and-tech
        1551184190073213071, # starboard
        1545502705643167876, # welcome
        1550159859607928882, # partnerships
        1549416359723532480  # bot-cmds
    ]

    for cid in channels_to_hide:
        try:
            ch = await client.fetch_channel(cid)
            ow_e = ch.overwrites_for(everyone)
            ow_e.view_channel = False
            ow_e.send_messages = False
            await ch.set_permissions(everyone, overwrite=ow_e)

            ow_v = ch.overwrites_for(verified_role)
            ow_v.view_channel = True
            if ch.type == discord.ChannelType.text:
                ow_v.send_messages = True
                ow_v.read_message_history = True
            await ch.set_permissions(verified_role, overwrite=ow_v)
            print(f'  ✓ Locked text channel: {ch.name}')
            await asyncio.sleep(0.3)
        except Exception as e:
            print(f'  Error on {cid}: {e}')

    # Hide all categories
    cats_to_hide = [
        1545803478490812578, # COMMUNITY
        1552374823676551220, # CREATOR STUDIO
        1550186748364066827, # GAMING ZONE
        1550198448203112539, # ACOUSTIC & CINEMA
        1552374826423943188, # PRIVATE SUITES
        1550186724137640006, # VOICE LOUNGE
        1545803487093456906  # STAFF HQ
    ]
    for cat_id in cats_to_hide:
        try:
            cat = await client.fetch_channel(cat_id)
            ow_e = cat.overwrites_for(everyone)
            ow_e.view_channel = False
            await cat.set_permissions(everyone, overwrite=ow_e)

            if cat_id != 1545803487093456906: # Not staff
                ow_v = cat.overwrites_for(verified_role)
                ow_v.view_channel = True
                await cat.set_permissions(verified_role, overwrite=ow_v)
            print(f'  ✓ Locked category: {cat.name}')
            await asyncio.sleep(0.3)
        except Exception as e:
            print(f'  Error on cat {cat_id}: {e}')

    # Keep ONLY verify-here visible to @everyone
    try:
        verify_ch = await client.fetch_channel(1545502700840427702)
        ow_e = verify_ch.overwrites_for(everyone)
        ow_e.view_channel = True
        ow_e.send_messages = False
        await verify_ch.set_permissions(everyone, overwrite=ow_e)
        print('  ✓ verify-here visible to everyone')
    except Exception as e:
        print(f'  Error verify-here: {e}')

    # Ensure verified users cannot see verify-here once verified
    try:
        ow_v = verify_ch.overwrites_for(verified_role)
        ow_v.view_channel = False
        await verify_ch.set_permissions(verified_role, overwrite=ow_v)
        print('  ✓ verify-here hidden from verified members (clean sidebar!)')
    except Exception as e:
        print(f'  Error verify-here verified perm: {e}')

    print('Complete verification lockdown successfully applied!')
    await client.close()

if __name__ == '__main__':
    asyncio.run(main())
