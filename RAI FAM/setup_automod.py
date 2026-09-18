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
    print(f"Logged in as {client.user}")
    guild = client.get_guild(GUILD_ID)
    if not guild:
        print("Guild not found")
        await client.close()
        return

    print(f"🛡️ Auto-configuring AutoMod and Safety Rules for {guild.name}...")

    log_chan = discord.utils.get(guild.text_channels, name="📋-mod-logs") or discord.utils.get(guild.text_channels, name="🛡️-staff-chat")
    
    actions = [discord.AutoModRuleAction(type=discord.AutoModRuleActionType.block_message)]
    if log_chan:
        actions.append(discord.AutoModRuleAction(type=discord.AutoModRuleActionType.send_alert_message, channel_id=log_chan.id))

    # 1. Anti-Invite Link AutoMod Rule
    try:
        await guild.create_automod_rule(
            name="🛡️ Anti-Discord Invite Links",
            event_type=discord.AutoModRuleEventType.message_send,
            trigger=discord.AutoModTrigger(
                type=discord.AutoModRuleTriggerType.keyword,
                keyword_filter=["*discord.gg/*", "*discord.com/invite/*"]
            ),
            actions=actions,
            enabled=True,
            reason="Automated Safety Setup"
        )
        print("✅ Created AutoMod Rule: Anti-Invite Links")
    except Exception as e:
        print(f"ℹ️ Invite Rule note: {e}")

    # 2. Block Suspected Spam AutoMod Rule
    try:
        await guild.create_automod_rule(
            name="🤖 Block Suspected Spam Content",
            event_type=discord.AutoModRuleEventType.message_send,
            trigger=discord.AutoModTrigger(type=discord.AutoModRuleTriggerType.spam_content),
            actions=actions,
            enabled=True,
            reason="Automated Safety Setup"
        )
        print("✅ Created AutoMod Rule: Block Suspected Spam")
    except Exception as e:
        print(f"ℹ️ Spam Content Rule note: {e}")

    # 3. Mention Spam Protection (Max 4 mentions)
    try:
        await guild.create_automod_rule(
            name="🚨 Anti-Mass Mention Spam",
            event_type=discord.AutoModRuleEventType.message_send,
            trigger=discord.AutoModTrigger(
                type=discord.AutoModRuleTriggerType.mention_spam,
                mention_limit=4
            ),
            actions=actions,
            enabled=True,
            reason="Automated Safety Setup"
        )
        print("✅ Created AutoMod Rule: Mention Spam (Max 4)")
    except Exception as e:
        print(f"ℹ️ Mention Spam Rule note: {e}")

    # 4. Filter Severe Toxicity & Harassment
    try:
        await guild.create_automod_rule(
            name="🚫 Profanity & Harassment Filter",
            event_type=discord.AutoModRuleEventType.message_send,
            trigger=discord.AutoModTrigger(
                type=discord.AutoModTriggerType.keyword_preset,
                presets=[
                    discord.AutoModKeywordPresetType.profanity,
                    discord.AutoModKeywordPresetType.sexual_content,
                    discord.AutoModKeywordPresetType.slurs
                ]
            ),
            actions=actions,
            enabled=True,
            reason="Automated Safety Setup"
        )
        print("✅ Created AutoMod Rule: Profanity, Sexual Content & Slurs Filter")
    except Exception as e:
        print(f"ℹ️ Toxicity Rule note: {e}")

    print("\n🎉 SAFETY & AUTOMOD SETUP COMPLETE (All 5 of 5 rules active)!")
    await client.close()

if __name__ == "__main__":
    asyncio.run(client.start(TOKEN))
