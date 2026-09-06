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
AFK_CHAN_ID = '1545502813889499136' # 💤 | AFK SLEEP

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (VCOptimize, 1.0)', 'Content-Type': 'application/json'}

# 1. Configure Official Server AFK Channel
guild_payload = {
    'afk_channel_id': AFK_CHAN_ID,
    'afk_timeout': 300 # 5 Minutes
}
req = urllib.request.Request(
    f'https://discord.com/api/v10/guilds/{GUILD_ID}',
    data=json.dumps(guild_payload).encode('utf-8'),
    headers=headers,
    method='PATCH'
)
try:
    with urllib.request.urlopen(req) as resp:
        print("✅ Configured official Server AFK Channel -> '💤 | AFK SLEEP' (5-Min Auto Timeout)!")
except Exception as e:
    print(f"AFK set error: {e}")

# 2. Fetch all channels and optimize bitrates for gaming & music
req = urllib.request.Request(f'https://discord.com/api/v10/guilds/{GUILD_ID}/channels', headers=headers)
with urllib.request.urlopen(req) as resp:
    channels = json.loads(resp.read().decode('utf-8'))

high_fidelity_vcs = [
    '1545502782268772453', # 🎧 | MUSIC LOUNGE
    '1545781986193309789', # 🎧 | LO-FI CHILL [24/7]
    '1545518701414195281', # 🎧 | KARAOKE STAGE
    '1545502823699980408', # ⚡ | FREE FIRE
    '1545502829089787924', # ⚡ | BGMI
    '1545502832822591539', # ⚡ | ROBLOX
    '1545502794868457574', # ⚡ | OTHER GAMES
    '1545502762467328185', # 🎦 | MOVIE¹
    '1545803585550426234', # 🎦 | MOVIE²
    '1545518528126394400', # ☘️ | RAI FAM
    '1545518531192553603', # ☘️ | VIP LOUNGE
    '1545834935678537738', # 🚀 | BOOSTER LOUNGE
]

for ch_id in high_fidelity_vcs:
    ch = next((c for c in channels if c.get('id') == ch_id), None)
    if ch and ch.get('bitrate') != 96000:
        patch_req = urllib.request.Request(
            f'https://discord.com/api/v10/channels/{ch_id}',
            data=json.dumps({'bitrate': 96000}).encode('utf-8'),
            headers=headers,
            method='PATCH'
        )
        try:
            with urllib.request.urlopen(patch_req) as resp:
                print(f"✅ Upgraded {ch.get('name')} to 96kbps High-Fidelity Audio!")
        except Exception as e:
            pass

print("🎉 All Voice Channels optimized with their respective specialized features!")
