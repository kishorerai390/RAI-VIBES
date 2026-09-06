import os
import sys
import json
import urllib.request
import unicodedata
from dotenv import load_dotenv

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')
GUILD_ID = '1457382179981099090'

headers = {'Authorization': f'Bot {TOKEN}', 'User-Agent': 'DiscordBot (FullAudit, 1.0)', 'Content-Type': 'application/json'}

def fetch(endpoint):
    req = urllib.request.Request(f'https://discord.com/api/v10/{endpoint}', headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode('utf-8'))

print("================================================================")
print("             👑 RAI FAM 💗 • FULL SERVER HEALTH AUDIT           ")
print("================================================================")

# 1. Guild Overview
guild = fetch(f'guilds/{GUILD_ID}?with_counts=true')
print(f"🏰 Server Name:        {guild.get('name')}")
print(f"🆔 Guild ID:           {guild.get('id')}")
print(f"👑 Owner ID:           {guild.get('owner_id')}")
print(f"👥 Total Members:      {guild.get('approximate_member_count')}")
print(f"🟢 Online Members:     {guild.get('approximate_presence_count')}")
print(f"🚀 Boost Level:        Tier {guild.get('premium_tier')} ({guild.get('premium_subscription_count')} Boosts)")
print(f"🖼️ Icon Hash:          {guild.get('icon')}")
print(f"🎏 Banner Hash:        {guild.get('banner')}")
print(f"📝 Description:        {guild.get('description')}")
print(f"🔒 Verification Level: {guild.get('verification_level')}")
print(f"🛡️ Explicit Content:   {guild.get('explicit_content_filter')}")

# 2. Emojis
emojis = fetch(f'guilds/{GUILD_ID}/emojis')
print(f"\n🎨 Custom Emojis ({len(emojis)} Uploaded):")
for e in emojis:
    print(f"  • <:{e['name']}:{e['id']}> (Name: {e['name']})")

# 3. Roles Audit
roles = fetch(f'guilds/{GUILD_ID}/roles')
roles_sorted = sorted(roles, key=lambda r: r['position'], reverse=True)
print(f"\n🎭 Server Roles Hierarchy ({len(roles)} Total):")
for r in roles_sorted:
    color = f"#{r['color']:06x}" if r['color'] != 0 else "Default"
    hoist = "🌟 Hoisted" if r.get('hoist') else "Normal"
    admin = "⚡ Admin" if (int(r.get('permissions', 0)) & 0x8) else "Member"
    print(f"  [{r['position']:2d}] {r['name']:<35} | {color:<8} | {hoist:<10} | {admin}")

# 4. Channels & Categories Structure
channels = fetch(f'guilds/{GUILD_ID}/channels')
categories = [c for c in channels if c.get('type') == 4]
categories = sorted(categories, key=lambda x: x.get('position', 0))

print(f"\n📂 Categories & Channels ({len(channels)} Total Channels):")
for cat in categories:
    print(f"\n  📁 [{cat.get('position')}] {cat.get('name')}")
    cat_chans = [c for c in channels if c.get('parent_id') == cat['id']]
    cat_chans = sorted(cat_chans, key=lambda x: (x.get('type', 0), x.get('position', 0)))
    for ch in cat_chans:
        ctype = ch.get('type')
        t = '💬 Text ' if ctype == 0 else ('🔊 Voice' if ctype == 2 else '📢 Announce')
        limit = f"[Limit: {ch.get('user_limit')}]" if ch.get('user_limit') else ""
        bitrate = f"[{ch.get('bitrate')//1000}kbps]" if ch.get('bitrate') else ""
        print(f"     {t} | {ch.get('name'):<32} {limit} {bitrate}")

# Orphan channels
orphans = [c for c in channels if c.get('type') != 4 and not c.get('parent_id')]
if orphans:
    print("\n  📁 [NO CATEGORY]")
    for ch in sorted(orphans, key=lambda x: x.get('position', 0)):
        ctype = ch.get('type')
        t = '💬 Text ' if ctype == 0 else ('🔊 Voice' if ctype == 2 else '📢 Announce')
        print(f"     {t} | {ch.get('name'):<32}")

print("\n================================================================")
print("                  ✅ FULL AUDIT COMPLETE                        ")
print("================================================================")
