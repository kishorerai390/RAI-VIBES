import discord
from discord import app_commands
from discord.ext import commands
import logging
import config

logger = logging.getLogger("Booster")

VIP_ELITE_ROLE_ID = 1545834931165335673
ANNOUNCEMENTS_CHANNEL_ID = 1545502718792175646
GENERAL_CHAT_CHANNEL_ID = 1545502730699808768

class Booster(commands.Cog):
    """Automated Server Booster Celebrations, Roles & Economy Perks."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        # Check if member just boosted the server
        if before.premium_since is None and after.premium_since is not None:
            logger.info(f"✨ [SERVER BOOST] {after.name}#{after.discriminator} just boosted {after.guild.name}!")

            # 1. Award +2,500 Coins
            try:
                from cogs.economy import update_user_coins
                new_bal = update_user_coins(after.id, 2500)
            except Exception as e:
                logger.warning(f"Could not award booster coins: {e}")
                new_bal = None

            # 2. Auto-grant VIP Elite Role
            vip_role = after.guild.get_role(VIP_ELITE_ROLE_ID)
            if vip_role and vip_role not in after.roles:
                try:
                    await after.add_roles(vip_role, reason="Automatic Server Booster VIP Perk")
                except Exception as e:
                    logger.warning(f"Could not grant booster role: {e}")

            # 3. Post celebration embed in announcements
            ch = after.guild.get_channel(ANNOUNCEMENTS_CHANNEL_ID) or after.guild.get_channel(GENERAL_CHAT_CHANNEL_ID)
            if ch:
                embed = discord.Embed(
                    title="🚀 SERVER BOOST CELEBRATION!",
                    description=(
                        f"✦ ───────────────────────────────────── ✦\n\n"
                        f"Huge thank you to {after.mention} for boosting **{after.guild.name}**! 💗\n\n"
                        f"✨ **Booster Perks Automatically Unlocked:**\n"
                        f"• 💎 **VIP Elite Role & Badge** (`{vip_role.name if vip_role else 'VIP Elite'}`)\n"
                        f"• 👛 **+2,500 Bonus Economy Coins**\n"
                        f"• 🥂 Access to exclusive VIP & Booster Voice Lounges\n"
                        f"• 👑 Enhanced chat permissions & custom nickname color\n\n"
                        f"✦ ───────────────────────────────────── ✦\n"
                        f"🌸 *We appreciate your generous support in taking RAI FAM higher!*"
                    ),
                    color=0xF47FFF
                )
                embed.set_thumbnail(url=after.display_avatar.url)
                embed.set_footer(text=f"Total Boost Level: Level {after.guild.premium_tier} ({after.guild.premium_subscription_count} Boosts)", icon_url=config.RAI_ICON_URL)
                
                card_file = None
                try:
                    from utils.canvas import generate_booster_card
                    av_bytes = await after.display_avatar.read()
                    buf = generate_booster_card(av_bytes, after.display_name, after.guild.premium_subscription_count, after.guild.premium_tier)
                    card_file = discord.File(fp=buf, filename="boost.png")
                    embed.set_image(url="attachment://boost.png")
                except Exception:
                    pass

                try:
                    if card_file:
                        await ch.send(content=f"🚀 **NEW BOOST!** Thank you {after.mention}!", embed=embed, file=card_file)
                    else:
                        await ch.send(content=f"🚀 **NEW BOOST!** Thank you {after.mention}!", embed=embed)
                except Exception as e:
                    logger.warning(f"Could not send boost celebration: {e}")

    @app_commands.command(name="boosterperks", description="View all exclusive perks unlocked by boosting RAI FAM.")
    async def booster_perks_command(self, interaction: discord.Interaction):
        guild = interaction.guild
        tier = guild.premium_tier if guild else 0
        boosts = guild.premium_subscription_count if guild else 0

        embed = discord.Embed(
            title="🚀 RAI FAM 💗 • EXCLUSIVE BOOSTER PERKS",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"Support the community and unlock legendary privileges:\n\n"
                f"• 💎 **`💎 ┊ 𝐑𝐀𝐈 𝐄𝐋𝐈𝐓𝐄` Prestige Role**\n"
                f"• 👛 **`+2,500 Coins` instant wallet bonus**\n"
                f"• 🥂 **Private Booster Voice Lounge** (`#🚀┃ ʙᴏᴏsᴛᴇʀ ʟᴏᴜɴɢᴇ`)\n"
                f"• 🎧 **Priority Audio Bitrate & DJ privileges**\n"
                f"• 📸 **Direct External Media & Embed Permissions**\n"
                f"• 🎨 **Custom Hex Color Role Selection**\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"📊 **Current Server Standing:** Level {tier} ({boosts} Boosts)"
            ),
            color=0xF47FFF
        )
        embed.set_thumbnail(url=guild.icon.url if guild and guild.icon else config.RAI_ICON_URL)
        embed.set_footer(text="Boost the server via Discord Nitro to claim your perks instantly!", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Booster(bot))
