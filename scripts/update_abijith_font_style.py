import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import discord
import asyncio
import config

GUILD_ID = 1428058914141900860

async def main():
    client = discord.Client(intents=discord.Intents.default())
    
    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}", flush=True)
        guild = client.get_guild(GUILD_ID)
        if not guild:
            print("Guild not found!", flush=True)
            await client.close()
            return
        
        # 1. Update Category
        cat = guild.get_channel(1550224008606126171)
        if cat and cat.name != "VIP & SENTINEL HQ":
            try:
                await cat.edit(name="VIP & SENTINEL HQ")
                print(f"Updated category name to 'VIP & SENTINEL HQ'", flush=True)
            except Exception as e:
                print(f"Error updating category: {e}", flush=True)
            await asyncio.sleep(1.0)
            
        # 2. Update Voice Channel
        vc = guild.get_channel(1550224047361757245)
        if vc and vc.name != "| • EXECUTIVE SUITE":
            try:
                await vc.edit(name="| • EXECUTIVE SUITE")
                print(f"Updated voice channel to '| • EXECUTIVE SUITE'", flush=True)
            except Exception as e:
                print(f"Error updating voice channel: {e}", flush=True)
            await asyncio.sleep(1.0)

        # 3. Update Text Channels
        text_updates = {
            1550224012905291886: "｜・executive-lounge",
            1550224016659316736: "｜・staff-operations",
            1550224028760019015: "｜・audit-logs",
            1550224034354958399: "｜・ticket-support",
            1550224039128203415: "｜・moderation-logs",
            1550224043678900286: "｜・sentinel-logs",
        }

        for ch_id, target_name in text_updates.items():
            ch = guild.get_channel(ch_id)
            if ch and ch.name != target_name:
                try:
                    await ch.edit(name=target_name)
                    print(f"Updated text channel {ch_id} -> '{target_name}'", flush=True)
                except Exception as e:
                    print(f"Error updating channel {ch_id}: {e}", flush=True)
                await asyncio.sleep(1.5)

        print("\nAll channels successfully updated to match SQUAD AREA style!", flush=True)
        await client.close()

    await client.start(config.DISCORD_TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
