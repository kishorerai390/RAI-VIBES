import os
import sys
import time
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = "1457382179981099090"

HEADERS = {
    "Authorization": f"Bot {TOKEN}",
    "Content-Type": "application/json"
}

# Channels that should be normal (UNLOCKED) for all server members:
# Lounge, Music/Vibe, Gaming, Fun
COMMUNITY_CHANNEL_IDS = [
    # The Lounge
    "1545834933417672744",  # vip-lounge (text)
    "1545518531192553603",  # vip-voice-lounge (voice)
    "1545834935678537738",  # booster-lounge (voice)
    "1545518528126394400",  # rai-fam-lounge (voice)

    # Vibe Studio
    "1545781986193309789",  # lo-fi (voice)
    "1545518701414195281",  # karaoke (voice)

    # Gaming Zone
    "1545502794868457574",  # gaming-lounge (voice)
    "1545502823699980408",  # free-fire (voice)
    "1545502832822591539",  # roblox (voice)

    # Fun Zone
    "1545803549559099502",  # open-voice (voice)
    "1545502813889499136",  # afk (voice)
    "1545502790888198215",  # create-vc (voice)
]

# Categories that should be normal / unlocked
COMMUNITY_CATEGORY_IDS = [
    "1545803478490812578",  # THE LOUNGE
    "1545803473528815807",  # VIBE STUDIO
    "1545803471289057300",  # GAMING ZONE
    "1545803469196230686",  # FUN ZONE
]

def unlock_channels():
    print("🔓 Removing lock symbols from community channels (Normal Server Mode)...")
    
    # 1. Fetch current channels
    r = requests.get(f"https://discord.com/api/v10/guilds/{GUILD_ID}/channels", headers=HEADERS)
    if r.status_code != 200:
        print(f"❌ Failed to fetch channels: {r.status_code} {r.text}")
        return

    channels = r.json()
    ch_dict = {c["id"]: c for c in channels}

    all_targets = COMMUNITY_CATEGORY_IDS + COMMUNITY_CHANNEL_IDS

    for cid in all_targets:
        ch = ch_dict.get(cid)
        if not ch:
            continue
        
        name = ch.get("name", cid)
        ch_type = ch.get("type")
        
        # Delete the @everyone deny overwrite so it becomes normal/open
        del_url = f"https://discord.com/api/v10/channels/{cid}/permissions/{GUILD_ID}"
        res = requests.delete(del_url, headers=HEADERS)
        
        if res.status_code in (200, 204):
            print(f"  ✅ Unlocked (Removed lock icon): {name}")
        elif res.status_code == 404:
            # Overwrite was already absent
            print(f"  ✨ Already open/unlocked: {name}")
        elif res.status_code == 429:
            retry = res.json().get("retry_after", 1.0)
            time.sleep(retry)
            requests.delete(del_url, headers=HEADERS)
            print(f"  ✅ Unlocked after retry: {name}")
        else:
            print(f"  ⚠️ Response {res.status_code} on {name}: {res.text}")
            
        time.sleep(0.3)

    print("\n🎉 Normal Server layout applied! All community channels are now open without lock symbols.")

if __name__ == "__main__":
    unlock_channels()
