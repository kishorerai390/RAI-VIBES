import unicodedata
import discord
from discord.ext import commands
from discord.ui import View, Button, button
import logging
from pathlib import Path
import json

import config

logger = logging.getLogger("Verification")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ECONOMY_FILE = DATA_DIR / "economy.json"
LEVELS_FILE = DATA_DIR / "levels.json"

def award_welcome_bonus(user_id: str):
    """Credit +100 Coins and +50 XP starter bonus to newly verified members."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        eco_data = {}
        if ECONOMY_FILE.exists():
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                eco_data = json.load(f)
        if user_id not in eco_data:
            eco_data[user_id] = {"coins": 200, "last_daily": 0, "wins": 0, "losses": 0}
        eco_data[user_id]["coins"] += 100
        with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
            json.dump(eco_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not award economy bonus to {user_id}: {e}")

    try:
        lvl_data = {}
        if LEVELS_FILE.exists():
            with open(LEVELS_FILE, "r", encoding="utf-8") as f:
                lvl_data = json.load(f)
        if user_id not in lvl_data:
            lvl_data[user_id] = {"xp": 0, "level": 1, "last_msg": 0}
        lvl_data[user_id]["xp"] += 50
        with open(LEVELS_FILE, "w", encoding="utf-8") as f:
            json.dump(lvl_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not award levels XP to {user_id}: {e}")


class VerifyButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Verify & Enter Community", emoji="✅", style=discord.ButtonStyle.success, custom_id="verify_member_btn")
    async def verify_button(self, interaction: discord.Interaction, btn: Button):
        # 1. Defer immediately to guarantee sub-50ms response to Discord
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        if not guild:
            return await interaction.followup.send("❌ Server error.", ephemeral=True)

        # 2. Find Verified Member / RAI FAMILY Role with NFKD Unicode normalization
        verified_role = None
        for r in guild.roles:
            norm_name = unicodedata.normalize('NFKD', r.name).upper()
            if "RAI FAMILY" in norm_name or "FAMILY" in norm_name or "VERIFIED" in norm_name:
                verified_role = r
                break

        if not verified_role:
            verified_role = discord.utils.get(guild.roles, id=1545494584203673740)

        # 3. Check if already verified
        if verified_role and verified_role in interaction.user.roles:
            return await interaction.followup.send(
                "✨ **You are already verified!** All community channels & voice lounges are open to you. 🌸 Enjoy your stay!",
                ephemeral=True
            )

        if verified_role:
            try:
                # Add role to user
                member = interaction.user
                if isinstance(member, discord.User):
                    member = await guild.fetch_member(interaction.user.id)

                await member.add_roles(verified_role, reason="Passed Verification Gate")
                award_welcome_bonus(str(interaction.user.id))

                embed = discord.Embed(
                    title="🎉 VERIFICATION SUCCESSFUL!",
                    description=(
                        f"Welcome to **{guild.name}**, {interaction.user.mention}! 💗\n\n"
                        f"✅ Role Granted: {verified_role.mention}\n"
                        f"🎁 Starter Bonus: **+100 Coins** & **+50 XP**\n"
                        f"🔓 **All server channels & voice lounges are now unlocked!**\n\n"
                        f"Head over to <#1545502730699808768> (General Chat) and say hello! 🌸"
                    ),
                    color=0x2ECC71 # Bright Emerald Green
                )
                embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
                embed.set_footer(text="RAI FAM 💗 • Verified Member", icon_url=guild.icon.url if guild.icon else None)

                await interaction.followup.send(embed=embed, ephemeral=True)
                logger.info(f"Verified {interaction.user.name} ({interaction.user.id}) and granted {verified_role.name}")
            except Exception as e:
                logger.error(f"Error granting role to {interaction.user.id}: {e}")
                await interaction.followup.send(f"❌ Failed to assign member role: {e}", ephemeral=True)
        else:
            await interaction.followup.send("❌ Verification role not configured on server. Please contact an admin.", ephemeral=True)


class Verification(commands.Cog):
    """Server Verification Gate with Persistent UI Views."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
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
        embed.set_footer(text="Instant 1-Click Verification • RAI FAM💗", icon_url=ctx.guild.icon.url if ctx.guild.icon else "https://cdn-icons-png.flaticon.com/512/9422/9422896.png")

        await ctx.send(embed=embed, view=VerifyButtonView())


async def setup(bot: commands.Bot):
    await bot.add_cog(Verification(bot))
