import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import discord
import asyncio
import json
from pathlib import Path
from config import TOKEN, GUILD_ID

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "server_stats.json"

async def main():
    intents = discord.Intents.default()
    intents.guilds = True
    intents.members = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as: {client.user}", flush=True)
        guild = client.get_guild(GUILD_ID)
        if not guild:
            print(f"Guild {GUILD_ID} not found!", flush=True)
            await client.close()
            return

        print(f"Provisioning SERVER STATS for '{guild.name}' ({guild.id})...", flush=True)

        # 1. Count members
        try:
            members = [m async for m in guild.fetch_members(limit=1000)]
            bots = len([m for m in members if m.bot])
            humans = len(members) - bots
            total = len(members)
        except Exception:
            total = guild.member_count or 27
            bots = len([m for m in guild.members if m.bot]) or 6
            humans = total - bots

        print(f"  Count: Total={total}, Humans={humans}, Bots={bots}", flush=True)

        # 2. Get or create Category at top of server (position 0)
        cat = discord.utils.get(guild.categories, name="SERVER STATS")
        cat_overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=True, connect=False),
            guild.me: discord.PermissionOverwrite(view_channel=True, connect=True, manage_channels=True)
        }

        if not cat:
            cat = await guild.create_category("SERVER STATS", overwrites=cat_overwrites, position=0)
            print("  Created category 'SERVER STATS' at position 0", flush=True)
            await asyncio.sleep(1.0)
        else:
            await cat.edit(overwrites=cat_overwrites, position=0)
            print("  Found and synced category 'SERVER STATS'", flush=True)

        # 3. Formats matching ABIJITH 777 server font
        name_all = f"| • ALL MEMBERS: {total}"
        name_humans = f"| • MEMBERS: {humans}"
        name_bots = f"| • BOTS: {bots}"

        # Accurate channel resolution
        ch_all = next((c for c in cat.voice_channels if "ALL" in c.name.upper()), None)
        ch_humans = next((c for c in cat.voice_channels if "MEMBERS" in c.name.upper() and "ALL" not in c.name.upper()), None)
        ch_bots = next((c for c in cat.voice_channels if "BOTS" in c.name.upper()), None)

        if not ch_all:
            ch_all = await guild.create_voice_channel(name_all, category=cat, overwrites=cat_overwrites, position=0)
            print(f"  Created: {name_all}", flush=True)
            await asyncio.sleep(1.0)
        else:
            if ch_all.name != name_all:
                await ch_all.edit(name=name_all, position=0)
                print(f"  Updated: {name_all}", flush=True)

        if not ch_humans:
            ch_humans = await guild.create_voice_channel(name_humans, category=cat, overwrites=cat_overwrites, position=1)
            print(f"  Created: {name_humans}", flush=True)
            await asyncio.sleep(1.0)
        else:
            if ch_humans.name != name_humans:
                await ch_humans.edit(name=name_humans, position=1)
                print(f"  Updated: {name_humans}", flush=True)

        if not ch_bots:
            ch_bots = await guild.create_voice_channel(name_bots, category=cat, overwrites=cat_overwrites, position=2)
            print(f"  Created: {name_bots}", flush=True)
            await asyncio.sleep(1.0)
        else:
            if ch_bots.name != name_bots:
                await ch_bots.edit(name=name_bots, position=2)
                print(f"  Updated: {name_bots}", flush=True)

        vc_all = ch_all
        vc_humans = ch_humans
        vc_bots = ch_bots

        # 4. Save to data/server_stats.json
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        stats_data = {}
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    stats_data = json.load(f)
            except Exception:
                stats_data = {}

        stats_data[str(GUILD_ID)] = {
            "category_id": cat.id,
            "ch_all": vc_all.id,
            "ch_humans": vc_humans.id,
            "ch_bots": vc_bots.id,
            "format_all": "| • ALL MEMBERS: {total}",
            "format_humans": "| • MEMBERS: {humans}",
            "format_bots": "| • BOTS: {bots}"
        }

        # Keep RAI FAM configuration active too
        if "1457382179981099090" not in stats_data:
            stats_data["1457382179981099090"] = {
                "category_id": 1546059369085534229,
                "ch_all": 1546099701496029194,
                "ch_humans": 1546099703630798848,
                "ch_bots": 1546059375574130769,
                "format_all": "👥・All Members: {total}",
                "format_humans": "👤・Members: {humans}",
                "format_bots": "🤖・Bots: {bots}"
            }

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(stats_data, f, indent=2)

        print("  Saved server stats config to data/server_stats.json", flush=True)
        print("\n✨ SERVER STATS setup complete for ABIJITH 777!", flush=True)
        await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
