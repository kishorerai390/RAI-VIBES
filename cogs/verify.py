import discord
from discord.ext import commands
from discord.ui import View, Button, button
import logging

import config

logger = logging.getLogger("Verification")

class VerifyButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Verify & Enter Community", emoji="✅", style=discord.ButtonStyle.success, custom_id="verify_member_btn")
    async def verify_button(self, interaction: discord.Interaction, btn: Button):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("❌ Server error.", ephemeral=True)

        verified_role = discord.utils.get(guild.roles, name="👥 Verified Member") or discord.utils.get(guild.roles, name="Verified Member")

        if not verified_role:
            # Attempt to create the verified role if not found
            try:
                verified_role = await guild.create_role(name="👥 Verified Member", color=discord.Color.from_rgb(149, 165, 166), reason="Auto-created for verification gate")
            except Exception as e:
                return await interaction.response.send_message("❌ Verified role not found and could not be auto-created.", ephemeral=True)

        if verified_role in interaction.user.roles:
            return await interaction.response.send_message("✨ **You are already verified!** Enjoy the community.", ephemeral=True)

        try:
            await interaction.user.add_roles(verified_role, reason="Passed Verification Gate")
            await interaction.response.send_message(f"🎉 **Verification successful!** Welcome to **{guild.name}** — all channels are now unlocked! 🍿🎵", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"❌ Failed to assign verified role: {e}", ephemeral=True)


class Verification(commands.Cog):
    """Server Verification Gate with Persistent UI Views."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Register persistent view so button works indefinitely even across restarts
        self.bot.add_view(VerifyButtonView())

    @commands.hybrid_command(name="setup_verify", description="Post the official Verification Gate embed in current channel.")
    @commands.has_permissions(administrator=True)
    async def setup_verify(self, ctx: commands.Context):
        embed = discord.Embed(
            title=f"🛡️ {ctx.guild.name.upper()} • MEMBER VERIFICATION",
            description=(
                f"Welcome to **{ctx.guild.name}**! 💗🍿🎵\n\n"
                "To prevent spam bots and keep our community friendly, safe, and neat, "
                "please click the **`[✅ Verify & Enter Community]`** button below to unlock all channels.\n\n"
                "By clicking verify, you agree to follow our server rules & code of conduct."
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else "https://cdn-icons-png.flaticon.com/512/9422/9422896.png")
        embed.set_footer(text="Instant 1-Click Verification • RAI FAM💗", icon_url="https://cdn-icons-png.flaticon.com/512/9422/9422896.png")

        await ctx.send(embed=embed, view=VerifyButtonView())


async def setup(bot: commands.Bot):
    await bot.add_cog(Verification(bot))
