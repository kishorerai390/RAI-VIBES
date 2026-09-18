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


SMALL_CAPS_MAP = str.maketrans("ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ", "abcdefghijklmnopqrstuvwxyz")

def clean_str(s: str) -> str:
    """Normalize unicode fonts, small-caps, replace non-breaking spaces, and convert to lowercase."""
    norm = unicodedata.normalize("NFKD", s)
    return norm.replace("\xa0", " ").translate(SMALL_CAPS_MAP).strip().lower()


class VerifiedNextStepsView(View):
    """Direct quick-action navigation buttons for verified members, dynamically resolved per guild."""
    def __init__(self, guild: discord.Guild):
        super().__init__(timeout=None)
        
        chat_ch = None
        roles_ch = None
        rules_ch = guild.rules_channel
        hub_ch = None

        for ch in guild.text_channels:
            c = clean_str(ch.name)
            if any(k in c for k in ["chats", "general", "main", "chat"]) and not chat_ch:
                if "ff-" not in c and "owo" not in c and "bot" not in c:
                    chat_ch = ch
            if any(k in c for k in ["role", "roles"]) and not roles_ch:
                roles_ch = ch
            if any(k in c for k in ["rule", "info"]) and not rules_ch:
                rules_ch = ch
            if any(k in c for k in ["lfg", "gaming", "bot-cmd", "music", "cinema"]) and not hub_ch:
                hub_ch = ch

        if chat_ch:
            self.add_item(Button(label="💬 Say Hello", url=chat_ch.jump_url, style=discord.ButtonStyle.link))
        if roles_ch:
            self.add_item(Button(label="🏷️ Role Info", url=roles_ch.jump_url, style=discord.ButtonStyle.link))
        if rules_ch:
            self.add_item(Button(label="📜 Server Rules", url=rules_ch.jump_url, style=discord.ButtonStyle.link))
        if hub_ch:
            self.add_item(Button(label="🎮 Community Hub", url=hub_ch.jump_url, style=discord.ButtonStyle.link))


class VerifyButtonView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Verify & Enter Community", emoji="✅", style=discord.ButtonStyle.success, custom_id="verify_member_btn")
    async def verify_button(self, interaction: discord.Interaction, btn: Button):
        # 1. Defer immediately to guarantee sub-50ms response to Discord
        if not interaction.response.is_done():
            try:
                await interaction.response.defer(ephemeral=True)
            except Exception:
                pass

        guild = interaction.guild
        if not guild:
            return await interaction.followup.send("❌ Server error.", ephemeral=True)

        role_ver = None
        role_mem = None
        
        # Dynamic search using small-caps normalizer
        for r in guild.roles:
            c = clean_str(r.name)
            if "verified" in c and not role_ver:
                role_ver = r
            if ("member" in c or "rai fam" in c) and not role_mem:
                role_mem = r

        # Fallback to known IDs if available
        if not role_ver:
            if guild.id == 1457382179981099090:  # RAI FAM
                role_ver = discord.utils.get(guild.roles, id=1549504522953695269)
            elif guild.id == 1428058914141900860:  # ABIJITH 777
                role_ver = discord.utils.get(guild.roles, id=1550205910218182696)
        if not role_mem:
            if guild.id == 1457382179981099090:  # RAI FAM
                role_mem = discord.utils.get(guild.roles, id=1545494584203673740)
            elif guild.id == 1428058914141900860:  # ABIJITH 777
                role_mem = discord.utils.get(guild.roles, id=1550205915398152364)

        role_unver = None

        member = interaction.user
        if isinstance(member, discord.User):
            member = await guild.fetch_member(interaction.user.id)

        roles_to_add = []
        if role_mem and role_mem not in member.roles:
            roles_to_add.append(role_mem)
        if role_ver and role_ver not in member.roles:
            roles_to_add.append(role_ver)

        # 3. Check if already verified
        if not roles_to_add and ((role_mem and role_mem in member.roles) or (role_ver and role_ver in member.roles)):
            view = VerifiedNextStepsView(guild)
            return await interaction.followup.send(
                "✨ **You are already verified!** All community channels & voice lounges are open to you. 🌸 Enjoy your stay!\n\n"
                "Use the quick buttons below to jump into the community:",
                view=view,
                ephemeral=True
            )

        if roles_to_add:
            try:
                await member.add_roles(*roles_to_add, reason="Passed Verification Gate")
                if role_unver and role_unver in member.roles:
                    try:
                        await member.remove_roles(role_unver, reason="Passed Verification Gate")
                    except Exception:
                        pass

                award_welcome_bonus(str(interaction.user.id))

                embed = discord.Embed(
                    title="🎉 VERIFICATION SUCCESSFUL!",
                    description=(
                        f"Welcome to **{guild.name}**, {interaction.user.mention}! 💗\n\n"
                        f"✅ **Roles Granted:** {', '.join(r.mention for r in roles_to_add)}\n"
                        f"🎁 **Starter Bonus:** `+100 Coins` & `+50 XP` credited to your profile!\n"
                        f"🔓 **All server channels & voice lounges are now unlocked!**\n\n"
                        f"👉 *Click the buttons below to pick your self-roles and join the conversation!*"
                    ),
                    color=0x2ECC71  # Bright Emerald Green
                )
                embed.set_thumbnail(url=guild.icon.url if guild.icon else None)
                embed.set_footer(text=f"{guild.name} • Verified Member Guide", icon_url=guild.icon.url if guild.icon else None)

                view = VerifiedNextStepsView(guild)
                await interaction.followup.send(embed=embed, view=view, ephemeral=True)
                logger.info(f"Verified {interaction.user.name} ({interaction.user.id}) in {guild.name} and granted {[r.name for r in roles_to_add]}")
            except Exception as e:
                logger.error(f"Error granting role to {interaction.user.id} in {guild.name}: {e}")
                await interaction.followup.send(f"❌ Failed to assign member role: {e}", ephemeral=True)
        else:
            await interaction.followup.send("❌ Verification role not configured on server. Please contact an admin.", ephemeral=True)


class Verification(commands.Cog):
    """Server Verification Gate with Persistent UI Views."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(name="setup_verify", description="Post the official Verification Gate embed in current channel.")
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
