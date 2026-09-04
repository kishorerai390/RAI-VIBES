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
    log_chan = discord.utils.get(guild.text_channels, name="📋-mod-logs")
    actions = [discord.AutoModRuleAction(type=discord.AutoModRuleActionType.block_message)]
    if log_chan:
        actions.append(discord.AutoModRuleAction(type=discord.AutoModRuleActionType.send_alert_message, channel_id=log_chan.id))

    try:
        presets = discord.AutoModPresets(profanity=True, sexual_content=True, slurs=True)
        await guild.create_automod_rule(
            name="🚫 Block Profanity, Sexual Content & Slurs",
            event_type=discord.AutoModRuleEventType.message_send,
            trigger=discord.AutoModTrigger(
                type=discord.AutoModRuleTriggerType.keyword_preset,
                presets=presets
            ),
            actions=actions,
            enabled=True,
            reason="Automated Safety Setup"
        )
        print("✅ Created AutoMod Rule: Profanity, Sexual Content & Slurs Filter")
    except Exception as e:
        print(f"ℹ️ Presets: {e}")

    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
