import requests, os, sys
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
    
    # Handle orphaned channel
    for c in channels:
        if "𝐑𝐅 𝐑𝐀𝐈" in c.get("name", ""):
            esp_cat = next((cat for cat in channels if cat.get('type') == 4 and '𝑹𝑨𝑰-𝑬𝑺𝑷' in cat.get('name', '')), None)
            if esp_cat:
                requests.patch(f"https://discord.com/api/v10/channels/{c['id']}", headers=HEADERS, json={"parent_id": esp_cat['id']})

    desired_categories = [
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

    desired_channel_order = {
        '📈 ◈ TEXT CHANNELS': [
            '📢・announcements', '🌷・welcome', '🌷・rules', '🌷・verify-access',
            '🌷・self-roles', '🌷・general', '🌷・media-gallery', '🌷・bot-commands',
            '🌷・suggestions', '🌷・qotd', '🌷・counting', '🌷・leaderboard', '🌷・giveaways'
        ],
        '🎭 | 𝑷𝑬𝑹𝑺𝑶𝑵𝑨𝑳 𝑨𝑹𝑬𝑨': [
            '🥂 | ・SOLO', '🥂 | ・DUO', '🥂 | ・TRIO', '🥂 | ・SQUAD', '🥂 | ・5-MAN', '🥂 | ・6-MAN', '➕ | Create Nexus VC'
        ],
        '😹 | 𝑭𝑼𝑵 𝑽𝑶𝑰𝑪𝑬 𝑪𝑯𝑨𝑵𝑵𝑬𝑳𝑺': [
            '🐣 | FUN TIME', '🗣️ | VOICE-1', '🗣️ | VOICE-2', '🗣️ | VOICE-3', '🗣️ | OPEN VOICE', '💤 | AFK SLEEP'
        ],
        '🎮 | 𝑮𝑨𝑴𝑰𝑵𝑮 𝒁𝑶𝑵𝑬': [
            '💬・gaming-text', '⚡ | FREE FIRE', '⚡ | BGMI', '⚡ | ROBLOX', '⚡ | OTHER GAMES'
        ],
        '🍃 | 𝑺𝑶𝑵𝑮 𝒁𝑶𝑵𝑬': [
            '🎵・song-requests', '🎧 | LO-FI CHILL [24/7]', '🎧 | MUSIC LOUNGE', '🎧 | KARAOKE STAGE'
        ],
        '🎥 | 𝑻𝑯𝑬𝑨𝑻𝑬𝑹': [
            '🎦 | MOVIE¹', '🎦 | MOVIE²'
        ],
        '🔱 | 𝑹𝑨𝑰-𝑬𝑺𝑷 !': [
            '☘️ | RAI FAM', '☘️ | VIP LOUNGE'
        ],
        '⚜️ | 𝑪𝒉𝒆𝒄𝒌𝒊𝒏𝒈 𝒁𝒐𝒏𝒆': [
            '🔍 | CHECKING-AREA', '🔍 | PC-CHECKING', '🔍 | PHONE-CHECKING', '🔍 | IOS-CHECKING'
        ],
        '🔒 | 𝑷𝑹𝑰𝑽𝑨𝑻𝑬-𝒁𝑶𝑵𝑬': [
            '🔒・executive-chat', '🔮 | PVT-CHANNEL', '🔮 | PVT-WORK'
        ],
        '🛡️ | 𝑺𝑬𝑵𝑻𝑰𝑵𝑬𝑳 𝑫𝑬𝑭𝑬𝑵𝑺𝑬': [
            '🛡️・staff-hq', '📋・mod-logs', '🎫・ticket-support'
        ]
    }

    updated = get_channels()
    cat_map = {c['name']: c for c in updated if c.get('type') == 4}
    
    positions = []
    cat_idx = 0
    chan_idx = 0
    
    for cat_name in desired_categories:
        if cat_name not in cat_map:
            continue
        cat_obj = cat_map[cat_name]
        positions.append({'id': cat_obj['id'], 'position': cat_idx})
        cat_idx += 1
        
        children = [c for c in updated if c.get('parent_id') == cat_obj['id']]
        desired_order = desired_channel_order.get(cat_name, [])
        
        def child_sort_key(c):
            cname = c['name']
            for idx, dname in enumerate(desired_order):
                if dname.lower() in cname.lower() or cname.lower() in dname.lower():
                    return idx
            return 99

        sorted_children = sorted(children, key=child_sort_key)
        for child in sorted_children:
            positions.append({'id': child['id'], 'position': chan_idx})
            chan_idx += 1

    r = requests.patch(f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels', headers=HEADERS, json=positions)
    print("Polish status:", r.status_code)
    print("✅ Perfect order applied!")

if __name__ == '__main__':
    main()
