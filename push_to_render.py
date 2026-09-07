import os
import sys
import json
import time
import argparse
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

def update_render_env_vars(vibes_token: str, sentinel_token: str):
    print("🚀 Pushing new bot credentials to Render...")
    payload = [
        {"key": "PORT", "value": "10000"},
        {"key": "DISCORD_BOT_TOKEN", "value": vibes_token.strip()},
        {"key": "SECURITY_BOT_TOKEN", "value": sentinel_token.strip()},
    ]
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.render.com/v1/services/{SVC_ID}/env-vars",
        headers=HEADERS,
        data=data,
        method="PUT",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            print("✅ Successfully updated Render Environment Variables!")
    except urllib.error.HTTPError as e:
        print(f"❌ Failed to update env vars on Render: {e.code} - {e.read().decode('utf-8', errors='ignore')}")
        return False
    return True

def trigger_deploy():
    print("🔄 Triggering immediate deploy on Render...")
    data = json.dumps({"clearCache": "do_not_clear"}).encode("utf-8")
    req = urllib.request.Request(
        f"https://api.render.com/v1/services/{SVC_ID}/deploys",
        headers=HEADERS,
        data=data,
        method="POST",
    )
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            dep_id = res.get("id")
            print(f"✅ Deploy triggered! Deploy ID: {dep_id}")
            return dep_id
    except urllib.error.HTTPError as e:
        print(f"❌ Deploy trigger error: {e.code} - {e.read().decode('utf-8', errors='ignore')}")
        return None

def monitor_deploy(dep_id: str):
    print("⏳ Monitoring 24/7 Render deployment status...")
    last_status = None
    for _ in range(30):
        req = urllib.request.Request(
            f"https://api.render.com/v1/services/{SVC_ID}/deploys/{dep_id}",
            headers=HEADERS,
        )
        try:
            with urllib.request.urlopen(req) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                status = res.get("status")
                if status != last_status:
                    print(f"   Status: {status}")
                    last_status = status
                if status == "live":
                    print("\n🎉 SUCCESS! Your bot is LIVE on Render 24/7!")
                    print("🌐 Live URL: https://rai-vibes.onrender.com")
                    return True
                elif "fail" in status or "cancel" in status:
                    print(f"\n❌ Deploy finished with status: {status}")
                    return False
        except Exception as e:
            print(f"   Notice: {e}")
        time.sleep(5)
    print("Deployment is still processing in background.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Deploy bot credentials and code to Render 24/7.")
    parser.add_argument("--vibes", help="New DISCORD_BOT_TOKEN for RAI VIBES", default=None)
    parser.add_argument("--sentinel", help="New SECURITY_BOT_TOKEN for RAI SENTINEL", default=None)
    args = parser.parse_args()

    load_dotenv(override=True)
    vibes_tok = args.vibes or os.getenv("DISCORD_BOT_TOKEN", "")
    sentinel_tok = args.sentinel or os.getenv("SECURITY_BOT_TOKEN", "")

    if not vibes_tok or not sentinel_tok:
        print("❌ Error: Missing bot tokens.")
        print("Please provide --vibes <token> --sentinel <token> or set them in .env")
        sys.exit(1)

    # Save to .env if passed as arguments
    if args.vibes or args.sentinel:
        env_lines = []
        if os.path.exists(".env"):
            with open(".env", "r", encoding="utf-8", errors="ignore") as f:
                env_lines = f.readlines()
        
        found_vibes = False
        found_sentinel = False
        new_lines = []
        for line in env_lines:
            if line.startswith("DISCORD_BOT_TOKEN="):
                new_lines.append(f"DISCORD_BOT_TOKEN={vibes_tok}\n")
                found_vibes = True
            elif line.startswith("SECURITY_BOT_TOKEN="):
                new_lines.append(f"SECURITY_BOT_TOKEN={sentinel_tok}\n")
                found_sentinel = True
            else:
                new_lines.append(line)
        if not found_vibes:
            new_lines.append(f"DISCORD_BOT_TOKEN={vibes_tok}\n")
        if not found_sentinel:
            new_lines.append(f"SECURITY_BOT_TOKEN={sentinel_tok}\n")
        
        with open(".env", "w", encoding="utf-8") as f:
            f.writelines(new_lines)
        print("💾 Updated local .env file.")

    if update_render_env_vars(vibes_tok, sentinel_tok):
        dep_id = trigger_deploy()
        if dep_id:
            monitor_deploy(dep_id)

if __name__ == "__main__":
    main()
