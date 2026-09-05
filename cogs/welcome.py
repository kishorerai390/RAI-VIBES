import discord
from discord.ext import commands
import logging

import config

logger = logging.getLogger("Welcome")

class Welcome(commands.Cog):
    """Aesthetic Welcome Cards, Dynamic Member Count & Onboarding."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        member_count = len(guild.members)

        # 1. Automatic Role Assignment on Join
        try:
            if member.bot:
                bot_role = discord.utils.get(guild.roles, name="🤖 ┊ 𝐀𝐔𝐃𝐈𝐎 𝐁𝐎𝐓𝐒") or discord.utils.get(guild.roles, name="Bots")
                if bot_role:
                    await member.add_roles(bot_role, reason="Auto-role for bot")
            else:
                family_role = discord.utils.get(guild.roles, name="🌸 ┊ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘")
                if not family_role:
                    for r in guild.roles:
                        if "RAI FAMILY" in r.name.upper() or "FAMILY" in r.name.upper():
                            family_role = r
                            break
                if family_role:
                    await member.add_roles(family_role, reason="Auto-role on join: RAI FAMILY")
                    logger.info(f"Granted {family_role.name} to {member.display_name}")
        except Exception as e:
            logger.error(f"Failed to auto-assign role to {member.display_name}: {e}")

        # 2. Update Server Stats Channel if present
        for vc in guild.voice_channels:
            if "members:" in vc.name.lower() or "member count" in vc.name.lower():
                try:
                    await vc.edit(name=f"👥・Members: {member_count}")
                except Exception:
                    pass

        # 3. Find Welcome Channel
        welcome_chan = (
            discord.utils.get(guild.text_channels, name="welcome") or
            discord.utils.get(guild.text_channels, name="👋・welcome") or
            discord.utils.get(guild.text_channels, name="╭・「👋」welcome") or
            discord.utils.get(guild.text_channels, name="general-chat")
        )

        if welcome_chan:
            rules_chan = discord.utils.get(guild.text_channels, name="rules") or discord.utils.get(guild.text_channels, name="├・「📜」rules-and-guidelines")
            roles_chan = discord.utils.get(guild.text_channels, name="self-roles") or discord.utils.get(guild.text_channels, name="├・「⭐」self-roles")

            rules_mention = rules_chan.mention if rules_chan else "#rules"
            roles_mention = roles_chan.mention if roles_chan else "#self-roles"

            embed = discord.Embed(
                title=f"🌸 WELCOME TO {guild.name.upper()}! 🌸",
                description=(
                    f"Hey {member.mention}, welcome to the family! You've been granted the **`🌸 ┊ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘`** role! 🎉\n\n"
                    f"✨ **You are Member #{member_count}**\n\n"
                    f"**🚀 Quick Start:**\n"
                    f"1️⃣ Read server guidelines in {rules_mention}\n"
                    f"2️⃣ Pick optional movie/music pings in {roles_mention}\n"
                    f"3️⃣ Hang out in voice lounges or chat in **`#general-chat`**!\n"
                ),
                color=config.COLOR_PRIMARY
            )
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id} • Have fun in RAI FAM!", icon_url=config.RAI_ICON_URL)

            try:
                await welcome_chan.send(content=f"👋 Welcome to RAI FAM, {member.mention}!", embed=embed)
            except Exception as e:
                logger.error(f"Failed to send welcome message: {e}")

        # 4. Anti-Alt Account Check
        now_dt = discord.utils.utcnow()
        account_age = (now_dt - member.created_at).days
        if account_age < 3:
            log_chan = discord.utils.get(guild.text_channels, name="📋・mod-logs")
            if log_chan:
                alt_embed = discord.Embed(
                    title="⚠️ [SECURITY ALERT] New / Alt Account Joined",
                    description=(
                        f"**User:** {member.mention} (`{member.id}`)\n"
                        f"**Account Age:** `{account_age} day(s) old` (Created <t:{int(member.created_at.timestamp())}:R>)\n"
                        f"**Notice:** Monitored for suspicious raid activity."
                    ),
                    color=config.COLOR_WARNING
                )
                try:
                    await log_chan.send(embed=alt_embed)
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Server Booster Celebration Announcer."""
        # Check if member just boosted the server
        if before.premium_since is None and after.premium_since is not None:
            guild = after.guild
            elite_role = discord.utils.get(guild.roles, name="💎 ┊ 𝐑𝐀𝐈 𝐄𝐋𝐈𝐓𝐄")
            if elite_role:
                try:
                    await after.add_roles(elite_role, reason="Server Booster Reward")
                except Exception:
                    pass

            gen_chan = discord.utils.get(guild.text_channels, name="💬・general-chat")
            if gen_chan:
                embed = discord.Embed(
                    title="🚀 NEW SERVER BOOSTER • ROYAL RESPECT! 💎",
                    description=(
                        f"A huge thank you to {after.mention} for boosting **{guild.name}**! 💖✨\n\n"
                        f"You have unlocked the prestigious **`💎 ┊ 𝐑𝐀𝐈 𝐄𝐋𝐈𝐓𝐄`** role & VIP perks!\n"
                        f"Server Boost Level is now **Level {guild.premium_tier}** ({guild.premium_subscription_count} Boosts)."
                    ),
                    color=discord.Color.nitro_pink()
                )
                embed.set_thumbnail(url=after.display_avatar.url)
                embed.set_image(url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1000&auto=format&fit=crop")
                embed.set_footer(text="Thank you for supporting RAI FAM!", icon_url=config.RAI_ICON_URL)
                try:
                    await gen_chan.send(content=f"🎉 **NEW BOOST!** {after.mention}", embed=embed)
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        member_count = len(guild.members)

        # Log goodbye to mod-logs
        log_chan = discord.utils.get(guild.text_channels, name="📋・mod-logs")
        if log_chan:
            embed = discord.Embed(
                title="👋 Member Left",
                description=f"**{member.name}** (`{member.id}`) has left the server. Member count is now **{member_count}**.",
                color=config.COLOR_SECONDARY
            )
            try:
                await log_chan.send(embed=embed)
            except Exception:
                pass


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
