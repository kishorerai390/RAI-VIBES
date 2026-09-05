import os
import sys
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

GUILD_ID = "1457382179981099090"
VIBES_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
SENTINEL_TOKEN = os.getenv("SECURITY_BOT_TOKEN")

MODERATION_COMMAND_NAMES = {
    "automod", "ban", "kick", "unban", "warn", "strikes",
    "clearstrikes", "clear", "purge", "lockdown", "unlock",
    "servermute", "serverunmute", "setup_verify"
}

def clean_vibes():
    print("=" * 60)
    print("🧹 CLEANING COMMANDS FOR RAI VIBES")
    print("=" * 60)
    headers = {"Authorization": f"Bot {VIBES_TOKEN}"}
    app_id = requests.get("https://discord.com/api/v10/oauth2/applications/@me", headers=headers).json()["id"]
    print(f"RAI VIBES App ID: {app_id}")

    # 1. Guild commands
    guild_cmds = requests.get(f"https://discord.com/api/v10/applications/{app_id}/guilds/{GUILD_ID}/commands", headers=headers).json()
    print(f"Guild commands count on {GUILD_ID}: {len(guild_cmds)}")
    for cmd in guild_cmds:
        cmd_name = cmd["name"]
        cmd_id = cmd["id"]
        if cmd_name in MODERATION_COMMAND_NAMES:
            del_resp = requests.delete(f"https://discord.com/api/v10/applications/{app_id}/guilds/{GUILD_ID}/commands/{cmd_id}", headers=headers)
            print(f"  ❌ Deleted Guild command: /{cmd_name} ({del_resp.status_code})")

    # If guild commands were registered that shadow global commands, let's clear all guild commands so global commands take effect cleanly
    if guild_cmds:
        print("Clearing all guild-level command overrides for RAI VIBES so global tree is clean...")
        requests.put(f"https://discord.com/api/v10/applications/{app_id}/guilds/{GUILD_ID}/commands", json=[], headers=headers)
        print("✅ Cleared all guild-specific command overrides.")

    # 2. Global commands
    global_cmds = requests.get(f"https://discord.com/api/v10/applications/{app_id}/commands", headers=headers).json()
    print(f"Global commands count: {len(global_cmds)}")
    for cmd in global_cmds:
        cmd_name = cmd["name"]
        cmd_id = cmd["id"]
        if cmd_name in MODERATION_COMMAND_NAMES:
            del_resp = requests.delete(f"https://discord.com/api/v10/applications/{app_id}/commands/{cmd_id}", headers=headers)
            print(f"  ❌ Deleted Global moderation command from RAI VIBES: /{cmd_name} ({del_resp.status_code})")
        else:
            print(f"  🎵 Kept Music command: /{cmd_name}")

def sync_sentinel():
    print("\n" + "=" * 60)
    print("🛡️ VERIFYING COMMANDS FOR RAI SENTINEL")
    print("=" * 60)
    if not SENTINEL_TOKEN:
        print("No SENTINEL_TOKEN found!")
        return

    headers = {"Authorization": f"Bot {SENTINEL_TOKEN}"}
    app_id = requests.get("https://discord.com/api/v10/oauth2/applications/@me", headers=headers).json()["id"]
    print(f"RAI SENTINEL App ID: {app_id}")

    # Check global commands
    global_cmds = requests.get(f"https://discord.com/api/v10/applications/{app_id}/commands", headers=headers).json()
    print(f"RAI SENTINEL Global commands: {[c['name'] for c in global_cmds]}")

    # Check guild commands
    guild_cmds = requests.get(f"https://discord.com/api/v10/applications/{app_id}/guilds/{GUILD_ID}/commands", headers=headers).json()
    print(f"RAI SENTINEL Guild commands: {[c['name'] for c in guild_cmds]}")

if __name__ == "__main__":
    clean_vibes()
    sync_sentinel()
