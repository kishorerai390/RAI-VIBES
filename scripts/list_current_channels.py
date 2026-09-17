import asyncio, os, sys, discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    guild = client.get_guild(1457382179981099090)
    print(f"=== GUILD: {guild.name} ({guild.id}) ===")
    print(f"afk_channel: {guild.afk_channel}")
    for cat in sorted(guild.categories, key=lambda c: c.position):
        print(f"\n📁 [CAT] {cat.name} (id={cat.id}, pos={cat.position})")
        for ch in sorted(cat.channels, key=lambda c: c.position):
            if isinstance(ch, discord.VoiceChannel):
                print(f"   🔊 (VC) {ch.name} (id={ch.id}, pos={ch.position}, limit={ch.user_limit})")
            elif isinstance(ch, discord.StageChannel):
                print(f"   🎙️ (Stage) {ch.name} (id={ch.id}, pos={ch.position})")
            else:
                print(f"   💬 (Text) {ch.name} (id={ch.id}, pos={ch.position})")
    
    uncat = [c for c in guild.channels if c.category is None]
    if uncat:
        print("\n📁 [UNCATEGORIZED]")
        for ch in sorted(uncat, key=lambda c: c.position):
            print(f"   {type(ch).__name__}: {ch.name} (id={ch.id}, pos={ch.position})")
    
    await client.close()

if __name__ == "__main__":
    client.run(os.getenv("DISCORD_BOT_TOKEN"))
