import sys
import os
import requests
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()
token = os.getenv("DISCORD_BOT_TOKEN")
headers = {
    "Authorization": f"Bot {token}",
    "Content-Type": "application/json"
}

# 1. Get Application ID
app_res = requests.get("https://discord.com/api/v10/oauth2/applications/@me", headers=headers)
app_data = app_res.json()
app_id = app_data["id"]
app_name = app_data["name"]

print(f"🤖 Bot Name: {app_name} (App ID: {app_id})")

# 2. Get Global Commands
global_cmds_res = requests.get(f"https://discord.com/api/v10/applications/{app_id}/commands", headers=headers)
global_cmds = global_cmds_res.json()

print(f"\n🌐 Total Global Slash Commands: {len(global_cmds)}")
for idx, cmd in enumerate(global_cmds, 1):
    options_str = ""
    if cmd.get("options"):
        opts = [f"{o['name']}{' (req)' if o.get('required') else ''}" for o in cmd['options']]
        options_str = f" [{', '.join(opts)}]"
    print(f"  {idx:2d}. /{cmd['name']}{options_str} - {cmd.get('description', 'No description')}")

# 3. Get Guild Commands for RAI FAM (1457382179981099090)
guild_id = "1457382179981099090"
guild_cmds_res = requests.get(f"https://discord.com/api/v10/applications/{app_id}/guilds/{guild_id}/commands", headers=headers)
guild_cmds = guild_cmds_res.json()

print(f"\n🏰 Total Guild Slash Commands (RAI FAM): {len(guild_cmds) if isinstance(guild_cmds, list) else 0}")
if isinstance(guild_cmds, list):
    for idx, cmd in enumerate(guild_cmds, 1):
        options_str = ""
        if cmd.get("options"):
            opts = [f"{o['name']}{' (req)' if o.get('required') else ''}" for o in cmd['options']]
            options_str = f" [{', '.join(opts)}]"
        print(f"  {idx:2d}. /{cmd['name']}{options_str} - {cmd.get('description', 'No description')}")
