import sys, os
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(1, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import discord
import asyncio
from config import TOKEN, GUILD_ID, COLOR_EMERALD, COLOR_GOLD, COLOR_CYAN
from cogs.verify import VerifyButtonView
from cogs.tickets import PersistentTicketLauncherView

async def main():
    intents = discord.Intents.default()
    intents.guilds = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready():
        print(f"Logged in as: {client.user}", flush=True)
        guild = client.get_guild(GUILD_ID)
        if not guild:
            print(f"Guild {GUILD_ID} not found!", flush=True)
            await client.close()
            return

        print(f"Refreshing Interactive Embeds on '{guild.name}' ({guild.id})...", flush=True)

        # 1. Verification Gate
        verify_ch = discord.utils.get(guild.text_channels, id=1550205959991992471) or discord.utils.get(guild.text_channels, name="✨｜ᴠᴇʀɪꜰʏ-ʜᴇʀᴇ")
        if verify_ch:
            async for m in verify_ch.history(limit=10):
                if m.author == client.user:
                    await m.delete()

            ver_embed = discord.Embed(
                title=f"🛡️ {guild.name.upper()} • MEMBER VERIFICATION",
                description=(
                    f"Welcome to **{guild.name}**! 🌟🎮🍿\n\n"
                    "To prevent automated spam and unlock the entire server, please click the "
                    "**`[✅ Verify & Enter Community]`** button below.\n\n"
                    "✨ **Instant Member Perks:**\n"
                    "• Full access to all text channels & voice lounges\n"
                    "• `+100 Coins` & `+50 XP` starter economy bonus\n"
                    "• Ability to chat, share media, and participate in events\n\n"
                    "*By verifying, you agree to respect our community members & server guidelines.*"
                ),
                color=COLOR_EMERALD
            )
            ver_embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            ver_embed.set_footer(text=f"{guild.name} • 1-Click Instant Verification", icon_url=guild.icon.url if guild.icon else None)
            await verify_ch.send(embed=ver_embed, view=VerifyButtonView())
            print("  Refreshed Verification Gate embed.", flush=True)

        # 2. Staff Operations Directives
        staff_ops_ch = discord.utils.get(guild.text_channels, name="｜・staff-operations")
        if staff_ops_ch:
            async for m in staff_ops_ch.history(limit=10):
                if m.author == client.user:
                    await m.delete()

            directives_embed = discord.Embed(
                title="🛡️ STAFF OPERATIONS & PROTOCOLS",
                description=(
                    f"Welcome to the **{guild.name}** Staff Operations command channel.\n"
                    "This channel is strictly reserved for moderation staff and server leadership.\n\n"
                    "⚡ **Key Staff Commands:**\n"
                    "• `/warn <user> <reason>` - Issue an official recorded strike\n"
                    "• `/mute <user> <duration> <reason>` - Timed communication timeout\n"
                    "• `/kick <user> <reason>` - Remove member from server\n"
                    "• `/ban <user> <reason>` - Ban member and purge messages\n"
                    "• `/modnotes <user>` - View member infraction history\n"
                    "• `/purge <amount>` - Clean up chat messages\n"
                    "• `/slowmode <seconds>` - Throttle chat traffic during raids\n\n"
                    "🛡️ **Security Telemetry:**\n"
                    "All security alerts, anti-raid activations, and audit events are broadcast to "
                    "`#｜・audit-logs`, `#｜・moderation-logs`, and `#｜・sentinel-logs`."
                ),
                color=COLOR_CYAN
            )
            directives_embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
            directives_embed.set_footer(text=f"{guild.name} • Staff Command Directives", icon_url=guild.icon.url if guild.icon else None)
            await staff_ops_ch.send(embed=directives_embed)
            print("  Refreshed Staff Operations Directives embed.", flush=True)

        print("\nEmbed refresh complete!", flush=True)
        await client.close()

    await client.start(TOKEN)

if __name__ == "__main__":
    asyncio.run(main())
