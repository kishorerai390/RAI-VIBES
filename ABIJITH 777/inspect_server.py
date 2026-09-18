import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import discord
import asyncio
from config import TOKEN, GUILD_ID

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

        print(f"\n{'='*60}", flush=True)
        print(f"  GUILD AUDIT: {guild.name} ({guild.id})", flush=True)
        print(f"  Members: {guild.member_count} | Roles: {len(guild.roles)} | Channels: {len(guild.channels)}", flush=True)
        print(f"{'='*60}\n", flush=True)

        print("--- ROLES (Highest to Lowest) ---", flush=True)
        for r in reversed(guild.roles):
            if r != guild.default_role:
                print(f"  [{r.position:02d}] {r.name} (ID: {r.id}) - Color: {r.color}", flush=True)

        print("\n--- CATEGORIES & CHANNELS ---", flush=True)
        for cat in guild.categories:
            print(f"\n📂 [{cat.name}] (ID: {cat.id})", flush=True)
            for ch in cat.channels:
                icon = "💬" if isinstance(ch, discord.TextChannel) else "🔊"
                limit = f" [Limit: {ch.user_limit}]" if isinstance(ch, discord.VoiceChannel) and ch.user_limit else ""
                print(f"    {icon} {ch.name} (ID: {ch.id}){limit}", flush=True)

        uncat = [ch for ch in guild.channels if not ch.category and not isinstance(ch, discord.CategoryChannel)]
        if uncat:
            print("\n📂 [UNASSIGNED CHANNELS]", flush=True)
            for ch in uncat:
                print(f"    - {ch.name} ({ch.id})", flush=True)

        print(f"\n{'='*60}\nAudit complete.", flush=True)
        await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
