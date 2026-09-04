import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import os
import time
import math
import random
from typing import Optional

import config

DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "levels.json")

def load_data():
    if not os.path.exists(DATA_PATH):
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    try:
        with open(DATA_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_data(data):
    try:
        os.makedirs(os.path.dirname(DATA_PATH), exist_ok=True)
        with open(DATA_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

def xp_for_level(level: int) -> int:
    return int(100 * (level ** 1.5))

def make_progress_bar(current: int, total: int, length: int = 12) -> str:
    if total <= 0:
        return "▰" * length
    percent = max(0.0, min(1.0, current / total))
    filled = int(round(length * percent))
    return "▰" * filled + "▱" * (length - filled)


class Levels(commands.Cog):
    """Vibe XP, Activity Tracker, Leveling System & Leaderboards."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.data = load_data()
        self.cooldowns = {} # user_id: timestamp
        self.voice_xp_loop.start()

    def cog_unload(self):
        self.voice_xp_loop.cancel()
        save_data(self.data)

    def get_user_data(self, guild_id: str, user_id: str):
        if guild_id not in self.data:
            self.data[guild_id] = {}
        if user_id not in self.data[guild_id]:
            self.data[guild_id][user_id] = {
                "xp": 0,
                "level": 1,
                "messages": 0,
                "voice_minutes": 0
            }
        return self.data[guild_id][user_id]

    @tasks.loop(minutes=2.0)
    async def voice_xp_loop(self):
        """Grants 2x XP to users chilling in voice channels and updates live stats counters."""
        for guild in self.bot.guilds:
            g_id = str(guild.id)
            total_in_voice = 0
            
            for vc in guild.voice_channels:
                # Ignore stats channels and AFK
                if "afk" in vc.name.lower() or "sleeping" in vc.name.lower() or "・" in vc.name and ("members:" in vc.name.lower() or "in voice:" in vc.name.lower() or "boosts:" in vc.name.lower()):
                    continue
                
                non_bots = [m for m in vc.members if not m.bot and not m.voice.self_deaf and not m.voice.deaf]
                total_in_voice += len(non_bots)
                
                # Multi-person VC bonus
                multiplier = 1.5 if len(non_bots) >= 2 else 1.0
                xp_award = int(50 * multiplier) # Boosted Voice XP!

                for member in non_bots:
                    u_id = str(member.id)
                    u_data = self.get_user_data(g_id, u_id)
                    u_data["xp"] += xp_award
                    u_data["voice_minutes"] += 2
                    
                    # Check Level Up
                    needed = xp_for_level(u_data["level"])
                    if u_data["xp"] >= needed:
                        u_data["level"] += 1
                        new_lvl = u_data["level"]
                        # Check role reward
                        reward_role_name = None
                        if new_lvl >= 50: reward_role_name = "💎 ┊ Rai Legend"
                        elif new_lvl >= 30: reward_role_name = "🔥 ┊ Rai Champion"
                        elif new_lvl >= 15: reward_role_name = "✨ ┊ Rai Active"
                        elif new_lvl >= 5: reward_role_name = "🌱 ┊ Rai Novice"
                        if reward_role_name:
                            role = discord.utils.get(guild.roles, name=reward_role_name)
                            if role and role not in member.roles:
                                try: await member.add_roles(role)
                                except Exception: pass

            save_data(self.data)

            # Update top category name and bot presence lively
            try:
                for cat in guild.categories:
                    if "WELCOME" in cat.name.upper():
                        new_cat_name = f"🌸 | 𝙒𝙀𝙇𝘾𝙊𝙈𝙀 & 𝙄𝙉𝙁𝙊 ({guild.member_count} 💗)"
                        if cat.name != new_cat_name:
                            await cat.edit(name=new_cat_name)
                        break

                activity = discord.Activity(
                    type=discord.ActivityType.listening,
                    name=f"👥 {guild.member_count} Members • 🎙️ {total_in_voice} in VC | /play"
                )
                await self.bot.change_presence(status=discord.Status.online, activity=activity)
            except Exception:
                pass

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        user_id = message.author.id
        now = time.time()

        # 45-second message XP cooldown
        if user_id in self.cooldowns and now - self.cooldowns[user_id] < 45:
            return

        self.cooldowns[user_id] = now
        g_id = str(message.guild.id)
        u_id = str(user_id)
        
        u_data = self.get_user_data(g_id, u_id)
        xp_gain = random.randint(15, 25)
        u_data["xp"] += xp_gain
        u_data["messages"] += 1

        # Check Level Up
        old_lvl = u_data.get("level", 1)
        while u_data["xp"] >= xp_for_level(u_data["level"]):
            u_data["level"] += 1
        
        new_lvl = u_data["level"]
        save_data(self.data)

        if new_lvl > old_lvl and new_lvl >= 2:
            # Role reward check
            reward_role_name = None
            if new_lvl >= 50:
                reward_role_name = "💎 ┊ Rai Legend"
            elif new_lvl >= 30:
                reward_role_name = "🔥 ┊ Rai Champion"
            elif new_lvl >= 15:
                reward_role_name = "✨ ┊ Rai Active"
            elif new_lvl >= 5:
                reward_role_name = "🌱 ┊ Rai Novice"

            reward_text = ""
            if reward_role_name:
                role = discord.utils.get(message.guild.roles, name=reward_role_name)
                if role and role not in message.author.roles:
                    try:
                        await message.author.add_roles(role, reason=f"Reached Level {new_lvl}")
                        reward_text = f"\n🎖️ **Unlocked Role Reward:** {role.mention}!"
                    except Exception:
                        pass

            # Send level up embed (auto-deleted after 8 seconds to prevent chat clutter!)
            embed = discord.Embed(
                title="⚡ LEVEL UP • VIBE ELEVATED! ⚡",
                description=f"Congratulations {message.author.mention}! You reached **Level {new_lvl}**! 🎉{reward_text}",
                color=config.COLOR_PRIMARY
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.set_footer(text="Keep chatting and hanging out to unlock more rewards!", icon_url=config.RAI_ICON_URL)
            try:
                await message.channel.send(embed=embed, delete_after=8)
            except Exception:
                pass

    @commands.hybrid_command(name="rank", description="Check your current Vibe Level, XP progress, and server rank.")
    @app_commands.describe(member="Member to view (defaults to you)")
    async def rank(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        target = member or ctx.author
        g_id = str(ctx.guild.id)
        u_id = str(target.id)

        u_data = self.get_user_data(g_id, u_id)
        current_xp = u_data["xp"]
        level = u_data["level"]
        needed_xp = xp_for_level(level)
        prev_xp = xp_for_level(level - 1) if level > 1 else 0
        
        # Calculate rank leaderboard position
        guild_users = self.data.get(g_id, {})
        sorted_users = sorted(guild_users.items(), key=lambda x: x[1]["xp"], reverse=True)
        rank_pos = 1
        for idx, (uid, d) in enumerate(sorted_users, start=1):
            if uid == u_id:
                rank_pos = idx
                break

        progress_in_level = max(0, current_xp - prev_xp)
        level_span = max(1, needed_xp - prev_xp)
        bar = make_progress_bar(progress_in_level, level_span, length=12)
        percentage = int(min(100, (progress_in_level / level_span) * 100))

        embed = discord.Embed(
            title=f"⚡ Vibe Rank • {target.display_name}",
            description=(
                f"🏆 **Server Rank:** `#{rank_pos}`\n"
                f"⭐ **Level:** `{level}`\n"
                f"✨ **Total XP:** `{current_xp:,}` XP\n\n"
                f"**Progress to Level {level + 1}:**\n"
                f"`{bar}` **{percentage}%** ({progress_in_level:,}/{level_span:,} XP)\n\n"
                f"💬 Messages: `{u_data['messages']}` | 🎙️ Voice Time: `{u_data['voice_minutes']} mins`"
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="Apex Vibes Leveling System", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="leaderboard", description="View the top 10 most active vibers in the server.")
    async def leaderboard(self, ctx: commands.Context):
        g_id = str(ctx.guild.id)
        guild_users = self.data.get(g_id, {})
        if not guild_users:
            return await ctx.send("No activity recorded yet! Start chatting and hanging out in voice to gain XP.")

        sorted_users = sorted(guild_users.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        lines = []

        for idx, (uid, uinfo) in enumerate(sorted_users):
            member = ctx.guild.get_member(int(uid))
            name = member.display_name if member else f"User {uid}"
            medal = medals[idx] if idx < len(medals) else f"`#{idx+1}`"
            lines.append(f"{medal} **{name}** • Level `{uinfo['level']}` ({uinfo['xp']:,} XP)")

        embed = discord.Embed(
            title=f"🏆 {ctx.guild.name} • VIBE LEADERBOARD",
            description="\n".join(lines),
            color=config.COLOR_GOLD
        )
        embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else config.RAI_ICON_URL)
        embed.set_footer(text="Rank up by chatting and voice hanging out!", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Levels(bot))
