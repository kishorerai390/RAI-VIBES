import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
import asyncio
import discord
from dotenv import load_dotenv
from pathlib import Path

load_dotenv(Path(__file__).parent.parent / ".env")
load_dotenv()
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    guild = client.get_guild(GUILD_ID)
    cat = discord.utils.get(guild.categories, name="🛡️ | 𝙎𝙏𝘼𝙁𝙁 𝙕𝙊𝙉𝙀")
    
    existing = discord.utils.get(guild.text_channels, name="ticket-support")
    if not existing:
        t_chan = await guild.create_text_channel(name="ticket-support", category=cat)
        from deploy_clean_embeds import TicketCreateView, COLOR_PINK
        t_embed = discord.Embed(
            title=f"🎫 {guild.name.upper()} • SUPPORT DESK",
            description="Need help from server moderators? Click **`[📩 Open Support Ticket]`** below!",
            color=COLOR_PINK
        )
        await t_chan.send(embed=t_embed, view=TicketCreateView())
        print("Recreated #ticket-support channel with embed!")
    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
