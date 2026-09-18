import os
import sys
import json
import time
import urllib.request
import urllib.error
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

load_dotenv()

API_KEY = os.getenv("RENDER_API_KEY", "")
SVC_ID = os.getenv("RENDER_SERVICE_ID", "srv-dadipqn40ujc73bksugg")
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

def sync_render_environment():
    print("🚀 [Render Deployer] Preparing environment variable payload for 3-bot ecosystem...")
    
    vibes_token = os.getenv("DISCORD_BOT_TOKEN", "").strip()
    sentinel_token = os.getenv("SECURITY_BOT_TOKEN", "").strip()
    arcade_token = (os.getenv("COMMUNITY_BOT_TOKEN") or os.getenv("ARCADE_BOT_TOKEN") or "").strip()
    spotify_id = os.getenv("SPOTIFY_CLIENT_ID", "").strip()
    spotify_secret = os.getenv("SPOTIFY_CLIENT_SECRET", "").strip()
    
    if not vibes_token:
        print("❌ Error: DISCORD_BOT_TOKEN missing in .env")
        return False
    if not sentinel_token:
        print("❌ Error: SECURITY_BOT_TOKEN missing in .env")
        return False
    if not arcade_token:
        print("❌ Error: COMMUNITY_BOT_TOKEN / ARCADE_BOT_TOKEN missing in .env")
        return False
        
    payload = [
        {"key": "PORT", "value": "10000"},
        {"key": "RENDER_EXTERNAL_URL", "value": "https://rai-vibes.onrender.com"},
        {"key": "DISCORD_BOT_TOKEN", "value": vibes_token},
        {"key": "SECURITY_BOT_TOKEN", "value": sentinel_token},
        {"key": "COMMUNITY_BOT_TOKEN", "value": arcade_token},
        {"key": "ARCADE_BOT_TOKEN", "value": arcade_token},
        {"key": "ENABLE_CLOUD_MUSIC", "value": "true"},
        {"key": "BOT_PREFIX", "value": "!"},
        {"key": "DEFAULT_VOLUME", "value": "100"},
        {"key": "INACTIVITY_TIMEOUT", "value": "300"},
    ]
    
    if spotify_id:
        payload.append({"key": "SPOTIFY_CLIENT_ID", "value": spotify_id})
    if spotify_secret:
        payload.append({"key": "SPOTIFY_CLIENT_SECRET", "value": spotify_secret})
        
    print(f"📦 Uploading {len(payload)} environment variables to Render service {SVC_ID}...")
    print("   • DISCORD_BOT_TOKEN -> [RAI VIBES 💗]")
    print("   • SECURITY_BOT_TOKEN -> [RAI SENTINEL 🛡️]")
    print("   • COMMUNITY_BOT_TOKEN -> [RAI ARCADE 🎮]")
    print("   • ARCADE_BOT_TOKEN -> [RAI ARCADE 🎮]")
    print("   • PORT -> 10000")
    print("   • RENDER_EXTERNAL_URL -> https://rai-vibes.onrender.com")

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.render.com/v1/services/{SVC_ID}/env-vars",
        headers=HEADERS,
        data=data,
        method="PUT"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("✅ Successfully synchronized all bot tokens to Render!")
            return True
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to update env vars on Render: {e.code} - {e.read().decode('utf-8', errors='ignore')}")
        return False
    except Exception as e:
        print(f"❌ Network error updating env vars: {e}")
        return False

def trigger_render_deploy():
    print("\n🔄 [Render Deployer] Triggering immediate deployment on Render...")
    data = json.dumps({"clearCache": "do_not_clear"}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.render.com/v1/services/{SVC_ID}/deploys",
        headers=HEADERS,
        data=data,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            dep_id = res.get("id")
            commit_id = res.get("commit", {}).get("id", "latest")
            print(f"✅ Deployment queued! Deploy ID: {dep_id} (Commit: {commit_id[:7]})")
            return dep_id
    except urllib.error.HTTPError as e:
        print(f"❌ Deploy trigger error: {e.code} - {e.read().decode('utf-8', errors='ignore')}")
        return None
    except Exception as e:
        print(f"❌ Deploy trigger network error: {e}")
        return None

def monitor_render_deploy(dep_id: str, timeout_seconds: int = 300):
    print(f"⏳ [Render Deployer] Monitoring deployment `{dep_id}` (Timeout: {timeout_seconds}s)...")
    start_time = time.time()
    last_status = None
    
    while time.time() - start_time < timeout_seconds:
        req = urllib.request.Request(
            f"https://api.render.com/v1/services/{SVC_ID}/deploys/{dep_id}",
            headers=HEADERS
        )
        try:
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                status = res.get("status")
                if status != last_status:
                    elapsed = int(time.time() - start_time)
                    print(f"   [{elapsed}s] Deployment Status: {status.upper()}")
                    last_status = status
                if status == "live":
                    print("\n🎉 SUCCESS! All 3 bots (RAI VIBES, RAI SENTINEL, RAI ARCADE) are LIVE on Render 24/7!")
                    print("🌐 Public Dashboard: https://rai-vibes.onrender.com")
                    return True
                elif status in ["build_failed", "update_failed", "canceled"]:
                    print(f"\n❌ Deployment finished with status: {status}")
                    return False
        except Exception as e:
            print(f"   Notice checking deploy status: {e}")
        time.sleep(6)
        
    print("⚠️ Monitoring timed out. Deploy is still progressing in background.")
    return True

if __name__ == "__main__":
    if not sync_render_environment():
        sys.exit(1)
    dep_id = trigger_render_deploy()
    if dep_id:
        monitor_render_deploy(dep_id)
