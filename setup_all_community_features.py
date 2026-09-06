import os
import sys
import json
import urllib.request
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'
headers = {
    'Authorization': f'Bot {TOKEN}',
    'User-Agent': 'DiscordBot (SetupAll, 1.0)',
    'Content-Type': 'application/json'
}

def api_call(endpoint, method='GET', data=None):
    url = f'https://discord.com/api/v10/{endpoint.lstrip("/")}'
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8') if data is not None else None,
        headers=headers,
        method=method
    )
    with urllib.request.urlopen(req) as resp:
        if resp.status == 204:
            return None
        return json.loads(resp.read().decode('utf-8'))

guild = api_call(f'/guilds/{GUILD_ID}?with_counts=true')
channels = api_call(f'/guilds/{GUILD_ID}/channels')
chan_map = {c['name']: c for c in channels}

member_count = guild.get('approximate_member_count') or len(guild.get('roles', []))
boost_tier = guild.get('premium_tier', 0)
boost_count = guild.get('premium_subscription_count', 0)

# 1. Create or Find SERVER STATS Category at Position 0
stats_cat = chan_map.get('📊 ◈ SERVER STATS')
if not stats_cat:
    print("Creating '📊 ◈ SERVER STATS' category...")
    stats_cat = api_call(f'/guilds/{GUILD_ID}/channels', method='POST', data={
        'name': '📊 ◈ SERVER STATS',
        'type': 4,
        'position': 0
    })

stats_cat_id = stats_cat['id']

# Create Stat Voice Channels (Type 2, locked from connect)
stat_channels = [
    f"👥・Members: {member_count}",
    f"🚀・Boosts: Lvl {boost_tier} ({boost_count})",
    f"👑・Founder: rf.rai_006"
]

for name in stat_channels:
    existing = next((c for c in channels if c.get('parent_id') == stats_cat_id and (name[:3] in c.get('name', ''))), None)
    if not existing:
        print(f"Creating stat channel: {name}...")
        api_call(f'/guilds/{GUILD_ID}/channels', method='POST', data={
            'name': name,
            'type': 2, # Voice
            'parent_id': stats_cat_id,
            'permission_overwrites': [
                {
                    'id': GUILD_ID, # @everyone
                    'type': 0,
                    'allow': '1024', # View Channel
                    'deny': '1048576' # Connect (Locked)
                }
            ]
        })

# 2. Find or Create Community Category
community_cat = chan_map.get('💬 ◈ COMMUNITY')
com_cat_id = community_cat['id'] if community_cat else None

# Channels to create in COMMUNITY
new_channels = [
    {
        'name': '💬・qotd',
        'topic': 'Daily Icebreaker Question of the Day! Join the daily discussion 💡',
        'embed': {
            'title': '🌸 QUESTION OF THE DAY • RAI FAM 💗',
            'description': (
                'Welcome to **Question of the Day**! 💡✨\n\n'
                '• Every day at **9:00 AM**, RAI VIBES drops a new question here.\n'
                '• Drop your thoughts, debate, and share your favorite picks in the discussion thread!\n\n'
                '**Today\'s Icebreaker:**\n'
                '👉 *What is that one song you can listen to on repeat without ever getting tired of it?* 🎧'
            ),
            'color': 0xFF69B4
        }
    },
    {
        'name': '🔢・counting',
        'topic': 'Count sequentially to 1,000+ together! One number per message. Don\'t ruin the streak!',
        'embed': {
            'title': '🔢 ◈ THE COUNTING ARENA',
            'description': (
                'Welcome to the **RAI FAM Counting Game**! 🏆\n\n'
                '**Rules of the Game:**\n'
                '1️⃣ Type the next consecutive number (e.g. `1`, `2`, `3`, ...).\n'
                '2️⃣ **No double counting**: You cannot count twice in a row!\n'
                '3️⃣ If someone enters the wrong number or ruins the count, the score resets to **1**.\n\n'
                '👉 **Start the count now with `1`!**'
            ),
            'color': 0x00F5D4
        }
    },
    {
        'name': '⭐・hall-of-fame',
        'topic': 'Messages that receive 3 or more ⭐ reactions are immortalized here!',
        'embed': {
            'title': '⭐ ◈ RAI FAM HALL OF FAME',
            'description': (
                'Welcome to the **Community Hall of Fame / Starboard**! 🌟\n\n'
                '• See a hilarious message, legendary meme, or awesome gaming play in any chat?\n'
                '• React to it with **⭐ (Star)**!\n'
                '• Once a message gets **3+ Stars**, it will automatically be featured right here! ✨'
            ),
            'color': 0xFEE440
        }
    }
]

for ch_info in new_channels:
    cname = ch_info['name']
    existing = chan_map.get(cname)
    if not existing:
        print(f"Creating channel: {cname}...")
        created = api_call(f'/guilds/{GUILD_ID}/channels', method='POST', data={
            'name': cname,
            'type': 0,
            'parent_id': com_cat_id,
            'topic': ch_info['topic']
        })
        chan_id = created['id']
        # Post Starter Embed
        api_call(f'/channels/{chan_id}/messages', method='POST', data={'embeds': [ch_info['embed']]})
    else:
        print(f"Channel {cname} already exists.")

print("✅ All channels & server stats created successfully!")
