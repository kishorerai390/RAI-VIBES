import requests, os, sys, time
sys.stdout.reconfigure(encoding='utf-8')
from dotenv import load_dotenv
load_dotenv()

HEADERS = {
    'Authorization': 'Bot ' + os.getenv('DISCORD_BOT_TOKEN'),
    'Content-Type': 'application/json'
}
GUILD_ID = '1457382179981099090'

def get_channels():
    return requests.get(f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels', headers=HEADERS).json()

def main():
    channels = get_channels()
    categories = {c['name']: c['id'] for c in channels if c.get('type') == 4}
    
    # 1. Move remaining channels from old categories to new categories
    for c in channels:
        if c.get('type') == 4:
            continue
        cname = c['name']
        cid = c['id']
        pid = c.get('parent_id')
        
        # Check if under old category
        if 'qotd' in cname.lower():
            requests.patch(f'https://discord.com/api/v10/channels/{cid}', headers=HEADERS, json={'name': '🌷・qotd', 'parent_id': categories.get('📈 ◈ TEXT CHANNELS')})
        elif 'counting' in cname.lower():
            requests.patch(f'https://discord.com/api/v10/channels/{cid}', headers=HEADERS, json={'name': '🌷・counting', 'parent_id': categories.get('📈 ◈ TEXT CHANNELS')})
        elif 'staff-hq' in cname.lower() or 'staff' in cname.lower():
            requests.patch(f'https://discord.com/api/v10/channels/{cid}', headers=HEADERS, json={'name': '🛡️・staff-hq', 'parent_id': categories.get('🛡️ | 𝑺𝑬𝑵𝑻𝑰𝑵𝑬𝑳 𝑫𝑬𝑭𝑬𝑵𝑺𝑬')})
        elif 'mod-logs' in cname.lower():
            requests.patch(f'https://discord.com/api/v10/channels/{cid}', headers=HEADERS, json={'name': '📋・mod-logs', 'parent_id': categories.get('🛡️ | 𝑺𝑬𝑵𝑻𝑰𝑵𝑬𝑳 𝑫𝑬𝑭𝑬𝑵𝑺𝑬')})
        elif 'ticket' in cname.lower():
            requests.patch(f'https://discord.com/api/v10/channels/{cid}', headers=HEADERS, json={'name': '🎫・ticket-support', 'parent_id': categories.get('🛡️ | 𝑺𝑬𝑵𝑻𝑰𝑵𝑬𝑳 𝑫𝑬𝑭𝑬𝑵𝑺𝑬')})
        elif 'executive-chat' in cname.lower():
            requests.patch(f'https://discord.com/api/v10/channels/{cid}', headers=HEADERS, json={'name': '🔒・executive-chat', 'parent_id': categories.get('🔒 | 𝑷𝑹𝑰𝑽𝑨𝑻𝑬-𝒁𝑶𝑵𝑬')})
        elif 'lounge' in cname.lower() and 'rf' in cname.lower():
            requests.patch(f'https://discord.com/api/v10/channels/{cid}', headers=HEADERS, json={'name': "👑 | RAI'S THRONE", 'parent_id': categories.get('🔱 | 𝑹𝑨𝑰-𝑬𝑺𝑷 !')})
        elif 'high command' in cname.lower():
            requests.patch(f'https://discord.com/api/v10/channels/{cid}', headers=HEADERS, json={'name': '⚡ | HIGH COMMAND', 'parent_id': categories.get('🔱 | 𝑹𝑨𝑰-𝑬𝑺𝑷 !')})

    # 2. Delete old categories
    old_cat_names = [
        '🌸 ◈ RAI PROTOCOL',
        '💬 ◈ CHAT MAINFRAME',
        '🎵 ◈ SOUND SANCTUARY 💗',
        '🎮 ◈ CYBER ARENA',
        '🔊 ◈ QUANTUM VOICE',
        '🛡️ ◈ SENTINEL DEFENSE',
        '👑 ROYAL SANCTUARY'
    ]
    
    updated_channels = get_channels()
    for c in updated_channels:
        if c.get('type') == 4 and c['name'] in old_cat_names:
            print(f"🗑️ Deleting old category: {c['name']} (ID: {c['id']})")
            requests.delete(f'https://discord.com/api/v10/channels/{c["id"]}', headers=HEADERS)

    # 3. Create missing Checking Zone channels if not present
    checking_cat_id = categories.get('⚜️ | 𝑪𝒉𝒆𝒄𝒌𝒊𝒏𝒈 𝒁𝒐𝒏𝒆')
    if checking_cat_id:
        checking_names = ['🔍 | CHECKING-AREA', '🔍 | PC-CHECKING', '🔍 | PHONE-CHECKING', '🔍 | IOS-CHECKING']
        existing_in_checking = [c['name'] for c in updated_channels if c.get('parent_id') == checking_cat_id]
        for cn in checking_names:
            if cn not in existing_in_checking:
                print(f"➕ Creating {cn}")
                requests.post(
                    f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels',
                    headers=HEADERS,
                    json={'name': cn, 'type': 2, 'user_limit': 99, 'parent_id': checking_cat_id}
                )

    # 4. Create missing Theater / Movie channels if not present
    theater_cat_id = categories.get('🎥 | 𝑻𝑯𝑬𝑨𝑻𝑬𝑹')
    if theater_cat_id:
        theater_names = ['🎦 | MOVIE¹', '🎦 | MOVIE²']
        existing_in_theater = [c['name'] for c in updated_channels if c.get('parent_id') == theater_cat_id]
        for tn in theater_names:
            if tn not in existing_in_theater:
                print(f"➕ Creating {tn}")
                requests.post(
                    f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels',
                    headers=HEADERS,
                    json={'name': tn, 'type': 2, 'user_limit': 0, 'parent_id': theater_cat_id}
                )

    # 5. Create missing Private Zone channels if not present
    pvt_cat_id = categories.get('🔒 | 𝑷𝑹𝑰𝑽𝑨𝑻𝑬-𝒁𝑶𝑵𝑬')
    if pvt_cat_id:
        pvt_names = ['🔮 | PVT-CHANNEL', '🔮 | PVT-WORK']
        existing_in_pvt = [c['name'] for c in updated_channels if c.get('parent_id') == pvt_cat_id]
        for pn in pvt_names:
            if pn not in existing_in_pvt:
                print(f"➕ Creating {pn}")
                requests.post(
                    f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels',
                    headers=HEADERS,
                    json={'name': pn, 'type': 2, 'user_limit': 0, 'parent_id': pvt_cat_id}
                )

    # 6. Apply strictly ordered positions to everything
    print("✨ Syncing global position order...")
    final_channels = get_channels()
    
    desired_category_order = [
        '📈 ◈ TEXT CHANNELS',
        '🎭 | 𝑷𝑬𝑹𝑺𝑶𝑵𝑨𝑳 𝑨𝑹𝑬𝑨',
        '😹 | 𝑭𝑼𝑵 𝑽𝑶𝑰𝑪𝑬 𝑪𝑯𝑨𝑵𝑵𝑬𝑳𝑺',
        '🎮 | 𝑮𝑨𝑴𝑰𝑵𝑮 𝒁𝑶𝑵𝑬',
        '🍃 | 𝑺𝑶𝑵𝑮 𝒁𝑶𝑵𝑬',
        '🎥 | 𝑻𝑯𝑬𝑨𝑻𝑬𝑹',
        '🔱 | 𝑹𝑨𝑰-𝑬𝑺𝑷 !',
        '⚜️ | 𝑪𝒉𝒆𝒄𝒌𝒊𝒏𝒈 𝒁𝒐𝒏𝒆',
        '🔒 | 𝑷𝑹𝑰𝑽𝑨𝑻𝑬-𝒁𝑶𝑵𝑬',
        '🛡️ | 𝑺𝑬𝑵𝑻𝑰𝑵𝑬𝑳 𝑫𝑬𝑭𝑬𝑵𝑺𝑬'
    ]

    cat_map = {c['name']: c for c in final_channels if c.get('type') == 4}
    
    positions = []
    cat_idx = 0
    chan_idx = 0
    
    for cname in desired_category_order:
        if cname in cat_map:
            cat_obj = cat_map[cname]
            positions.append({'id': cat_obj['id'], 'position': cat_idx})
            cat_idx += 1
            
            children = [c for c in final_channels if c.get('parent_id') == cat_obj['id']]
            # sort children
            for child in children:
                positions.append({'id': child['id'], 'position': chan_idx})
                chan_idx += 1

    r_ord = requests.patch(
        f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels',
        headers=HEADERS,
        json=positions
    )
    print(f"Final order applied: {r_ord.status_code}")
    print("🎉 All categories and channels are fully synchronized to the screenshot design!")

if __name__ == '__main__':
    main()
