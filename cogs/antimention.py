import logging
from datetime import timedelta
from typing import Optional
import discord
from discord.ext import commands

import database

logger = logging.getLogger("AntiMention")

class AntiMention(commands.Cog):
    """Protects server against mass mentions, unauthorized @everyone / @here, and ghost pings."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def get_log_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        settings = await database.get_guild_settings(guild.id)
        log_id = settings.get("log_channel_id")
        if log_id:
            channel = guild.get_channel(log_id)
            if channel and isinstance(channel, discord.TextChannel):
                return channel
        for name in ["security-logs", "mod-logs"]:
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
        if not settings.get("antimention_enabled", 1):
            return

        is_violating = False
        reason = ""

        # 1. Check for unauthorized @everyone or @here
        if (message.mention_everyone or "@everyone" in message.content or "@here" in message.content):
            if not member.guild_permissions.mention_everyone:
                is_violating = True
                reason = "Unauthorized @everyone / @here Ping"

        # 2. Check for excessive user mentions (>5 pings)
        if len(message.mentions) >= 5:
            is_violating = True
            reason = f"Mass User Mention ({len(message.mentions)} users tagged)"

        # 3. Check for excessive role mentions (>3 roles)
        if len(message.role_mentions) >= 3:
            is_violating = True
            reason = f"Mass Role Mention ({len(message.role_mentions)} roles tagged)"

        if is_violating:
            try:
                await message.delete()
            except Exception:
                pass

            # Timeout offender for 10 minutes
            try:
                await member.timeout(timedelta(minutes=10), reason=f"[Anti-Mention] {reason}")
                await message.channel.send(
                    f"🔇 {member.mention} has been timed out for 10 minutes for mass ping abuse.",
                    delete_after=8
                )
            except Exception as e:
                logger.debug(f"Anti-mention timeout error: {e}")

            # Record in SQLite
            await database.record_infraction(
                message.guild.id,
                member.id,
                "MASS_MENTION_TIMEOUT",
                reason,
                moderator_id=self.bot.user.id
            )

            # Log event
            log_channel = await self.get_log_channel(message.guild)
            if log_channel:
                embed = discord.Embed(
                    title="🛡️ Anti-Mass Mention Interception",
                    description=f"**Offender:** {member.mention} (`{member.name}` • ID: `{member.id}`)\n**Reason:** {reason}\n**Action Taken:** Message Deleted & 10-Minute Timeout Applied",
                    color=0xFF3300
                )
                embed.set_footer(text=f"Channel: #{message.channel.name}")
                embed.timestamp = discord.utils.utcnow()
                try:
                    await log_channel.send(embed=embed)
                except Exception:
                    pass

async def setup(bot: commands.Bot):
    await bot.add_cog(AntiMention(bot))
