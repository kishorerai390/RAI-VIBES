import logging
import discord
from discord import app_commands
from discord.ext import commands

import database

logger = logging.getLogger("Whitelist")

class Whitelist(commands.Cog):
    """Whitelist Management: Protect trusted staff & administrators from automatic Anti-Nuke restrictions."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def is_owner_or_security_admin(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == interaction.guild.owner_id:
            return True
        if interaction.user.guild_permissions.administrator:
            return True
        return False

    whitelist_group = app_commands.Group(name="whitelist", description="Manage trusted users and roles for Anti-Nuke bypass.")

    @whitelist_group.command(name="user", description="Add a trusted user to the Anti-Nuke whitelist.")
    @app_commands.describe(user="The member or user to whitelist")
    async def whitelist_user(self, interaction: discord.Interaction, user: discord.User):
        if not self.is_owner_or_security_admin(interaction):
            return await interaction.response.send_message("❌ Only the **Server Owner** or senior Administrators can modify the security whitelist.", ephemeral=True)

        await database.add_whitelisted_user(interaction.guild.id, user.id, interaction.user.id)
        embed = discord.Embed(
            title="🛡️ Security Whitelist Updated",
            description=f"✅ {user.mention} (`{user.name}` • `{user.id}`) is now **Whitelisted** and immune to automatic Anti-Nuke restrictions.",
            color=0x00FF88
        )
        embed.set_footer(text=f"Authorized by {interaction.user.name}")
        await interaction.response.send_message(embed=embed)

        await database.record_security_event(
            interaction.guild.id,
            "WHITELIST_USER_ADDED",
            f"User {user.name} ({user.id}) whitelisted by {interaction.user.name}",
            severity="LOW"
        )

    @whitelist_group.command(name="remove", description="Remove a user from the security whitelist.")
    @app_commands.describe(user="The user to remove from whitelist")
    async def remove_whitelist_user(self, interaction: discord.Interaction, user: discord.User):
        if not self.is_owner_or_security_admin(interaction):
            return await interaction.response.send_message("❌ Only the **Server Owner** or senior Administrators can modify the security whitelist.", ephemeral=True)

        removed = await database.remove_whitelisted_user(interaction.guild.id, user.id)
        if removed:
            embed = discord.Embed(
                title="🛡️ Security Whitelist Updated",
                description=f"⚠️ {user.mention} (`{user.name}`) has been **removed** from the security whitelist.",
                color=0xFFAA00
            )
            await interaction.response.send_message(embed=embed)
        else:
            await interaction.response.send_message(f"ℹ️ {user.mention} was not on the whitelist.", ephemeral=True)

    @whitelist_group.command(name="role", description="Add an entire role to the security whitelist.")
    @app_commands.describe(role="The role to whitelist")
    async def whitelist_role(self, interaction: discord.Interaction, role: discord.Role):
        if not self.is_owner_or_security_admin(interaction):
            return await interaction.response.send_message("❌ Only the **Server Owner** or senior Administrators can modify the security whitelist.", ephemeral=True)

        await database.add_whitelisted_role(interaction.guild.id, role.id, interaction.user.id)
        embed = discord.Embed(
            title="🛡️ Role Whitelist Updated",
            description=f"✅ Members with role {role.mention} are now **Whitelisted** from automatic Anti-Nuke restrictions.",
            color=0x00FF88
        )
        embed.set_footer(text=f"Authorized by {interaction.user.name}")
        await interaction.response.send_message(embed=embed)

    @whitelist_group.command(name="list", description="View all currently whitelisted users and roles.")
    async def list_whitelist(self, interaction: discord.Interaction):
        data = await database.get_whitelist(interaction.guild.id)
        users = data.get("users", [])
        roles = data.get("roles", [])

        user_lines = [f"• <@{uid}> (`{uid}`)" for uid in users[:15]] or ["*No individual users whitelisted*"]
        role_lines = [f"• <@&{rid}> (`{rid}`)" for rid in roles[:10]] or ["*No roles whitelisted*"]

        embed = discord.Embed(
            title=f"🛡️ Security Whitelist • {interaction.guild.name}",
            color=0x00EEFF
        )
        embed.add_field(name="👑 Server Owner (Permanent)", value=f"<@{interaction.guild.owner_id}>", inline=False)
        embed.add_field(name=f"👥 Whitelisted Users ({len(users)})", value="\n".join(user_lines), inline=False)
        embed.add_field(name=f"🎭 Whitelisted Roles ({len(roles)})", value="\n".join(role_lines), inline=False)
        embed.set_footer(text="Whitelisted members are exempt from automated Anti-Nuke actions.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Whitelist(bot))
