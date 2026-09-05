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
    
    # Target channels to remove as requested (bot commands, media gallery, and empty clutter)
    targets_to_remove = [
        "bot-commands",
        "media-gallery",
        "qotd",
        "counting",
        "leaderboard",
        "giveaways",
        "suggestions"
    ]
    
    deleted_count = 0
    for c in channels:
        cname = c.get('name', '').lower()
        cid = c['id']
        ctype = c.get('type')
        
        # Only check text channels (type 0 or 5)
        if ctype in [0, 5]:
            matched = any(target in cname for target in targets_to_remove)
            if matched:
                print(f"🗑️ Deleting empty clutter channel: {c['name']} (ID: {cid})")
                r = requests.delete(f"https://discord.com/api/v10/channels/{cid}", headers=HEADERS)
                print(f"Status: {r.status_code}")
                deleted_count += 1
                
    print(f"🎉 Successfully removed {deleted_count} empty clutter channels!")

if __name__ == '__main__':
    main()
