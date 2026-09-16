import os
import sys
import asyncio
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GAMING_CHANNEL_ID = 1545803554550190212

from utils.persistent_views import GamingHubStationView

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"Logged in as {client.user} ({client.user.id})")
    channel = client.get_channel(GAMING_CHANNEL_ID)
    if not channel:
        print(f"Channel {GAMING_CHANNEL_ID} not found.")
        await client.close()
        return

    print(f"Target Channel: {channel.name} ({channel.id})")

    embed = discord.Embed(
        title="🎮 ✦ 𝐑𝐀𝐈 𝐕𝐈𝐁𝐄𝐒 ✦ 𝐆𝐀𝐌𝐈𝐍𝐆 𝐇𝐔𝐁 & 𝐀𝐑𝐄𝐍𝐀 ✦",
        description=(
            "Welcome to the **RAI VIBES Gaming Hub & Arena**! 🕹️\n"
            "Challenge your squadmates, play trivia, and build your fortune.\n\n"
            "### ⚔️ Live Game Commands\n"
            "• **`/tictactoe @member`** — Challenge a squadmate to an interactive 3x3 match!\n"
            "• **`/trivia [category]`** — Test your knowledge in Gaming, Anime, Movies & Tech (+50 Coins)!\n"
            "• **`/gamble <amount> <heads/tails>`** — Double your coins in the high-stakes coin toss!\n"
            "• **`/pay @member <amount>`** — Send coins directly to a friend.\n\n"
            "### 🕹️ Instant Arcade Station\n"
            "Click any button below to launch a quick match, flip a coin, or check your balance!"
        ),
        color=0x9B5DE5
    )
    embed.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/686/686589.png")
    embed.set_image(url="https://images.unsplash.com/photo-1542751371-adc38448a05e?auto=format&fit=crop&w=1200&q=80")
    embed.set_footer(text="RAI VIBES Gaming Arena • Instant Mini-Games")

    view = GamingHubStationView()
    sent_msg = await channel.send(embed=embed, view=view)
    print(f"Successfully posted Gaming Station message {sent_msg.id} in {channel.name}!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
