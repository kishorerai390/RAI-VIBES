import time
import random
import logging
from typing import Optional, Dict
import discord
from discord import app_commands
from discord.ext import commands, tasks

import database
import config

logger = logging.getLogger("Leveling")

MILESTONE_ROLES = {
    5: "✦ 𝐑𝐢𝐬𝐢𝐧𝐠 𝐒𝐭𝐚𝐫",
    10: "✦ 𝐀𝐝𝐯𝐞𝐧𝐭𝐮𝐫𝐞𝐫",
    20: "✦ 𝐕𝐚𝐧𝐠𝐮𝐚𝐫𝐝",
    50: "✦ 𝐈𝐦𝐦𝐨𝐫𝐭𝐚𝐥"
}

def render_progress_bar(current: int, total: int, length: int = 10) -> str:
    if total <= 0:
        return "▱" * length
    fraction = max(0.0, min(1.0, current / total))
    filled = int(fraction * length)
    empty = length - filled
    return "▰" * filled + "▱" * empty

class Leveling(commands.Cog):
    """Leveling & XP Engine rewarding chat activity and voice participation."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # user_id: last_message_timestamp
        self.message_cooldowns: Dict[int, float] = {}
        self.voice_xp_task.start()

    def cog_unload(self):
        self.voice_xp_task.cancel()

    async def ensure_milestone_roles(self, guild: discord.Guild):
        """Ensure milestone roles exist in the guild."""
        for lvl, role_name in MILESTONE_ROLES.items():
            existing = discord.utils.get(guild.roles, name=role_name)
            if not existing:
                try:
                    colors = {5: 0x00FFCC, 10: 0x0099FF, 20: 0x9933FF, 50: 0xFF0066}
                    await guild.create_role(name=role_name, color=discord.Color(colors.get(lvl, 0xFF007F)), reason="Level milestone reward role")
                except Exception as e:
                    logger.debug(f"Could not create role {role_name}: {e}")

    # -------------------------------------------------------------
    # MESSAGE XP LISTENER
    # -------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        now = time.time()
        last_time = self.message_cooldowns.get(message.author.id, 0)
        # 60 second cooldown between XP rewards to prevent spamming
        if now - last_time < 60:
            return

        self.message_cooldowns[message.author.id] = now
        xp_gain = random.randint(15, 25)

        new_xp, new_lvl, leveled_up = await database.add_user_xp(message.guild.id, message.author.id, xp_gain)

        if leveled_up:
            await self.handle_level_up(message.guild, message.author, new_lvl, message.channel)

    async def handle_level_up(self, guild: discord.Guild, member: discord.Member, new_level: int, channel: discord.abc.Messageable):
        """Sends level-up celebration and awards milestone roles."""
        role_reward_text = ""
        # Check if a milestone role was unlocked
        if new_level in MILESTONE_ROLES:
            role_name = MILESTONE_ROLES[new_level]
            role = discord.utils.get(guild.roles, name=role_name)
            if not role:
                await self.ensure_milestone_roles(guild)
                role = discord.utils.get(guild.roles, name=role_name)
            if role and role < guild.me.top_role:
                try:
                    await member.add_roles(role, reason=f"Level milestone {new_level} reached")
                    role_reward_text = f"\n🎖️ **Unlocked Role Reward:** {role.mention}!"
                except Exception as e:
                    logger.debug(f"Failed to award role {role_name}: {e}")

        embed = discord.Embed(
            title="🎉 LEVEL UP! • ADVANCEMENT UNLOCKED",
            description=f"Congratulations {member.mention}! You just reached **Level {new_level}**! ✨{role_reward_text}",
            color=0x00FF88
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_footer(text="Keep chatting & participating to earn more XP!")
        try:
            await channel.send(embed=embed)
        except Exception:
            pass

    # -------------------------------------------------------------
    # VOICE XP LOOP (Runs every 2 minutes)
    # -------------------------------------------------------------
    @tasks.loop(minutes=2)
    async def voice_xp_task(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                # Skip AFK channel or empty channels
                if "afk" in vc.name.lower() or len(vc.members) < 1:
                    continue
                for member in vc.members:
                    if member.bot or member.voice.self_deaf or member.voice.deaf:
                        continue
                    # Award 10 XP for active voice participation
                    await database.add_user_xp(guild.id, member.id, 10)

    @voice_xp_task.before_loop
    async def before_voice_task(self):
        import asyncio
        while not self.bot.is_ready():
            await asyncio.sleep(1)

    # -------------------------------------------------------------
    # SLASH COMMANDS: /rank & /leaderboard
    # -------------------------------------------------------------
    @app_commands.command(name="rank", description="View your current level, XP, and server ranking card.")
    @app_commands.describe(member="Member whose rank card you want to inspect (defaults to you)")
    async def rank_command(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        data = await database.get_user_level_data(interaction.guild.id, target.id)

        current_xp = data["xp"]
        level = data["level"]
        rank = data["rank"]
        msg_count = data["messages_count"]
        base_xp = data["current_level_base_xp"]
        next_xp = data["next_level_xp"]

        xp_in_level = max(0, current_xp - base_xp)
        xp_needed = max(1, next_xp - base_xp)
        percent = int(min(100, (xp_in_level / xp_needed) * 100))
        progress_bar = render_progress_bar(xp_in_level, xp_needed, length=12)

        embed = discord.Embed(
            title=f"✦ RANK CARD • {target.display_name}",
            color=0xFF007F
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🏆 Server Rank", value=f"**#{rank}**", inline=True)
        embed.add_field(name="⭐ Level", value=f"**Level {level}**", inline=True)
        embed.add_field(name="💬 Messages", value=f"`{msg_count:,}`", inline=True)
        embed.add_field(
            name="📊 Level Progress",
            value=f"`{progress_bar}` **{percent}%**\n`{xp_in_level:,}` / `{xp_needed:,} XP` (Total: `{current_xp:,} XP`)",
            inline=False
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="leaderboard", description="View the Top 10 most active members on the server.")
    async def leaderboard_command(self, interaction: discord.Interaction):
        leaders = await database.get_leaderboard(interaction.guild.id, limit=10)
        if not leaders:
            return await interaction.response.send_message("ℹ️ No ranking data available yet. Start chatting to earn XP!", ephemeral=True)

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for row in leaders:
            uid = row["user_id"]
            user = interaction.guild.get_member(uid)
            user_name = user.display_name if user else f"User {uid}"
            rank_icon = medals.get(row["rank"], f"`#{row['rank']:02d}`")
            lines.append(f"{rank_icon} **{user_name}** — **Level {row['level']}** (`{row['xp']:,} XP` • `{row['messages_count']:,} msgs`)")

        embed = discord.Embed(
            title="🏆 SERVER XP LEADERBOARD • TOP 10",
            description="\n".join(lines),
            color=0xFFD700
        )
        embed.set_footer(text="Chat and participate in voice channels to climb the ranks!")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))
