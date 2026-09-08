import re
import logging
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

import database

logger = logging.getLogger("AntiLink")

INVITE_REGEX = re.compile(r"(?:https?://)?(?:www\.)?(?:discord\.(?:gg|io|me|li|com/invite)/[a-zA-Z0-9]+)")
URL_REGEX = re.compile(r"https?://(?:www\.)?([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?:/[^\s]*)?")

import datetime

KNOWN_SCAM_PATTERNS = [
    "discorcl", "dlscord", "discrod", "discord-nitro", "free-nitro", "nitro-gift",
    "steamcommuniity", "steamcomminuty", "gift-discord", "discordapp.biz", "discord-app.me",
    "airdrop-nitro", "claim-nitro", "steam-gift", "discordgift", "t.me/airdrop",
    "discord-claim", "nitro-drop", "free-steam", "discord-boost", "get-nitro", "gift-nitro.click"
]

class AntiLink(commands.Cog):
    """Anti-Link Protection System: Filters unauthorized Discord invites, scam domains, and blacklisted URLs."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_log_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        chan = guild.get_channel(1546593526073135107) or guild.get_channel(1546540192343523399)
        if chan and isinstance(chan, discord.TextChannel):
            return chan
        settings = await database.get_guild_settings(guild.id)
        log_id = settings.get("log_channel_id")
        if log_id:
            channel = guild.get_channel(log_id)
            if channel and isinstance(channel, discord.TextChannel):
                return channel
        for name in ["・𝘀𝗲𝗰𝘂𝗿𝗶𝘁𝘆-𝗹𝗼𝗴𝘀・", "・𝗮𝘂𝗱𝗶𝘁-𝗹𝗼𝗴𝘀・", "security-logs", "mod-logs"]:
            channel = discord.utils.get(guild.text_channels, name=name)
            if channel:
                return channel
        return None

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        member = message.author
        if not isinstance(member, discord.Member):
            return

        # Bypass for Server Owner, Admins, & Whitelist
        if member.id == message.guild.owner_id or member.guild_permissions.administrator:
            return
        if await database.is_whitelisted(message.guild, member):
            return

        settings = await database.get_guild_settings(message.guild.id)
        if not settings.get("antilink_enabled", 1):
            return

        content_lower = message.content.lower()

        # 1. Check for Discord invites
        has_invite = bool(INVITE_REGEX.search(content_lower))
        
        # 2. Check for known scam domains
        has_scam = any(scam in content_lower for scam in KNOWN_SCAM_PATTERNS)

        # 3. Check for custom blocked domains from SQLite
        blocked_domains = await database.get_blocked_domains(message.guild.id)
        has_blocked_domain = any(domain in content_lower for domain in blocked_domains)

        if has_invite or has_scam or has_blocked_domain:
            try:
                await message.delete()
            except Exception:
                pass

            reason = "Unauthorized Discord Invite" if has_invite else ("Phishing / Scam Link" if has_scam else "Blacklisted Domain Link")
            timeout_note = ""

            # Automatic timeout protection for verified phishing / scam links
            if has_scam and not member.guild_permissions.manage_messages:
                try:
                    await member.timeout(datetime.timedelta(minutes=10), reason="Automated Shield: Phishing / Scam link detected")
                    timeout_note = " • Member placed on 10m Timeout"
                except Exception:
                    pass

            try:
                await message.channel.send(
                    f"🛡️ {member.mention}, links are restricted in this channel. *({reason}{timeout_note})*",
                    delete_after=6
                )
            except Exception:
                pass

            # Log incident
            log_channel = await self.get_log_channel(message.guild)
            if log_channel:
                embed = discord.Embed(
                    title="🛡️ Malicious Link Intercepted",
                    description=(
                        f"**User:** {member.mention} (`{member.name}` • ID: `{member.id}`)\n"
                        f"**Type:** `{reason}`\n"
                        f"**Action Taken:** Message Deleted & Warning Issued{timeout_note}\n"
                        f"**Origin Channel:** {message.channel.mention}"
                    ),
                    color=0xFF0033 if has_scam else 0xFF5500
                )
                embed.set_thumbnail(url=member.display_avatar.url)
                embed.set_footer(text="RAI SENTINEL 🛡️ Autonomous Defense", icon_url=self.bot.user.display_avatar.url)
                embed.timestamp = discord.utils.utcnow()
                try:
                    await log_channel.send(embed=embed)
                except Exception:
                    pass

    # -------------------------------------------------------------
    # LINK MANAGEMENT SLASH COMMANDS
    # -------------------------------------------------------------
    link_group = app_commands.Group(name="link", description="Manage anti-link filters and blocked domain lists.")

    @link_group.command(name="protection", description="Toggle Anti-Link filter ON or OFF.")
    @app_commands.describe(status="Choose whether Link Protection is ON or OFF")
    @app_commands.choices(status=[
        app_commands.Choice(name="ON", value="on"),
        app_commands.Choice(name="OFF", value="off")
    ])
    async def toggle_protection(self, interaction: discord.Interaction, status: str):
        if not interaction.user.guild_permissions.administrator and not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You require `Administrator` or `Manage Server` permission.", ephemeral=True)

        is_on = (status.lower() == "on")
        await database.update_guild_setting(interaction.guild.id, "antilink_enabled", 1 if is_on else 0)
        await interaction.response.send_message(
            f"✅ Anti-Link Protection is now **{'ENABLED' if is_on else 'DISABLED'}**.",
            ephemeral=True
        )

    @link_group.command(name="add", description="Add a domain to the server blacklist.")
    @app_commands.describe(domain="Domain to block (e.g. malicious-site.com)")
    async def add_domain(self, interaction: discord.Interaction, domain: str):
        if not interaction.user.guild_permissions.administrator and not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You require `Administrator` or `Manage Server` permission.", ephemeral=True)

        clean_domain = domain.strip().lower().replace("http://", "").replace("https://", "").replace("www.", "").split("/")[0]
        await database.add_blocked_domain(interaction.guild.id, clean_domain, interaction.user.id)
        await interaction.response.send_message(f"✅ Added `{clean_domain}` to the server link blacklist.", ephemeral=True)

    @link_group.command(name="remove", description="Remove a domain from the server blacklist.")
    @app_commands.describe(domain="Domain to unblock")
    async def remove_domain(self, interaction: discord.Interaction, domain: str):
        if not interaction.user.guild_permissions.administrator and not interaction.user.guild_permissions.manage_guild:
            return await interaction.response.send_message("❌ You require `Administrator` or `Manage Server` permission.", ephemeral=True)

        clean_domain = domain.strip().lower().replace("http://", "").replace("https://", "").replace("www.", "").split("/")[0]
        success = await database.remove_blocked_domain(interaction.guild.id, clean_domain)
        if success:
            await interaction.response.send_message(f"✅ Removed `{clean_domain}` from the server link blacklist.", ephemeral=True)
        else:
            await interaction.response.send_message(f"⚠️ `{clean_domain}` was not found in the blacklist.", ephemeral=True)

    @link_group.command(name="list", description="List all blacklisted domains in this server.")
    async def list_domains(self, interaction: discord.Interaction):
        domains = await database.get_blocked_domains(interaction.guild.id)
        if not domains:
            return await interaction.response.send_message("ℹ️ No custom blacklisted domains configured. Built-in scam patterns and unauthorized Discord invites remain active.", ephemeral=True)

        domain_list = "\n".join(f"• `{d}`" for d in domains[:25])
        embed = discord.Embed(
            title="🛡️ Blacklisted Server Domains",
            description=domain_list,
            color=0x00FFCC
        )
        embed.set_footer(text=f"Total: {len(domains)} custom blocked domain(s)")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(AntiLink(bot))
