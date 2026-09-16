import os
import sys
import asyncio
import discord
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUIDE_CHANNEL_ID = 1546125872661012611

from utils.persistent_views import ServerGuideView

client = discord.Client(intents=discord.Intents.default())

@client.event
async def on_ready():
    print(f"Logged in as {client.user} ({client.user.id})")
    channel = client.get_channel(GUIDE_CHANNEL_ID)
    if not channel:
        print(f"Channel {GUIDE_CHANNEL_ID} not found.")
        await client.close()
        return

    print(f"Target Channel: {channel.name} ({channel.id})")

    # Purge old bot messages in guide channel to keep it pristine
    async for msg in channel.history(limit=10):
        if msg.author.id == client.user.id:
            try:
                await msg.delete()
                print(f"Deleted old guide message {msg.id}")
            except Exception as e:
                print(f"Could not delete message {msg.id}: {e}")

    embed = discord.Embed(
        title="🧭 ✦ 𝐑𝐀𝐈 𝐕𝐈𝐁𝐄𝐒 ✦ 𝐎𝐅𝐅𝐈𝐂𝐈𝐀𝐋 𝐒𝐄𝐑𝐕𝐄𝐑 𝐃𝐈𝐑𝐄𝐂𝐓𝐎𝐑𝐘 ✦",
        description=(
            "Welcome to **RAI VIBES** — the premier sanctuary for high-fidelity audio, "
            "competitive gaming squads, and immersive cyber community experiences!\n\n"
            "### 🌟 How To Use This Directory\n"
            "Use the **Interactive Dropdown** below to explore features, commands, and access systems. "
            "Everything is delivered privately so you can read at your own pace.\n\n"
            "╭────────────────────────────╮\n"
            "  🎙️ **Dynamic Voice Suites & Ghost VC**\n"
            "  🎵 **Zero-Prefix Audio & Lo-Fi Studio**\n"
            "  💡 **Interactive Suggestion Cards**\n"
            "  💰 **Economy, Daily Streaks & Server Shop**\n"
            "  🛡️ **Verification, Codex & Custom Colors**\n"
            "╰────────────────────────────╯\n\n"
            "📌 *Need immediate staff assistance? Visit `#🎫・ᴛɪᴄᴋᴇᴛ-ꜱᴜᴘᴘᴏʀᴛ`.*"
        ),
        color=0xFF69B4
    )
    embed.set_thumbnail(url=client.user.display_avatar.url)
    embed.set_image(url="https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?auto=format&fit=crop&w=1200&q=80")
    embed.set_footer(text="RAI VIBES Interactive Codex • Select an option below to begin")

    view = ServerGuideView()
    sent_msg = await channel.send(embed=embed, view=view)
    print(f"Successfully posted Server Guide message {sent_msg.id} in {channel.name}!")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
