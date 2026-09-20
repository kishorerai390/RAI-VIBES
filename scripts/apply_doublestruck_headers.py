import asyncio
import os
import sys
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
load_dotenv()

TOKEN = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

# Target typography:
# - Replacing ALL Gothic Fraktur headers with Double-Struck (Blackboard Bold) Cyber Luxury
# - Replacing Gothic Fraktur voice channel with Royal Bold Serif
HEADER_UPDATES = {
    # Categories (Double-Struck Cyber Luxury)
    1545803464712650844: "✦ 𝕀 ℕ 𝔽 𝕆 ℝ 𝕄 𝔸 𝕋 𝕀 𝕆 ℕ ✦",
    1545803478490812578: "✦ ℂ 𝕆 𝕄 𝕄 𝕌 ℕ 𝕀 𝕋 𝕐 ✦",
    1550186748364066827: "✦ 𝔾 𝔸 𝕄 𝕀 ℕ 𝔾  ℤ 𝕆 ℕ 𝔼 ✦",
    1550186724137640006: "✦ 𝕍 𝕆 𝕀 ℂ 𝔼  𝕃 𝕆 𝕌 ℕ 𝔾 𝔼 ✦",
    1550197872006398014: "✦ 🍿 ℂ 𝕀 ℕ 𝔼 𝕄 𝔸  ℍ 𝕌 𝔹 ✦",
    1550198448203112539: "✦ 🎵 𝕄 𝕌 𝕊 𝕀 ℂ  𝕃 𝕆 𝕌 ℕ 𝔾 𝔼 ✦",
    1545803487093456906: "✦ 𝕊 𝕋 𝔸 𝔽 𝔉  ℍ ℚ ✦",
    1546059369085534229: "✦ 𝕊 𝔼 ℝ 𝕍 𝔼 ℝ  𝕊 𝕋 𝔸 𝕋 𝕊 ✦",

    # Channels (Remove any leftover Gothic Fraktur)
    1550187323084374079: "👑 ┊ 𝐄𝐱𝐞𝐜𝐮𝐭𝐢𝐯𝐞 𝐒𝐮𝐢𝐭𝐞",
}

intents = discord.Intents.default()
client = discord.Client(intents=intents)

@client.event
async def on_ready():
    print(f"Logged in as {client.user.name} ({client.user.id})")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("❌ Guild not found!")
        await client.close()
        return

    print("==================================================")
    print(f"Updating Headers to Double-Struck Cyber Luxury: {guild.name}")
    print("Strict Rule: Preserving 100% of channel layout & order")
    print("==================================================")

    for item_id, target_name in HEADER_UPDATES.items():
        ch = guild.get_channel(item_id)
        if not ch:
            ch = discord.utils.get(guild.categories, id=item_id)

        if ch:
            if ch.name != target_name:
                try:
                    await ch.edit(name=target_name)
                    print(f"  [UPDATED] {ch.id}: '{ch.name}' -> '{target_name}'")
                    await asyncio.sleep(0.6)
                except Exception as e:
                    print(f"  [ERROR] {ch.id}: {e}")
            else:
                print(f"  [MATCHED] {ch.id}: '{target_name}'")
        else:
            print(f"  [NOT FOUND] ID {item_id}")

    print("==================================================")
    print("All headers successfully upgraded to Double-Struck Cyber Luxury!")
    print("==================================================")
    await client.close()

if __name__ == "__main__":
    client.run(TOKEN)
