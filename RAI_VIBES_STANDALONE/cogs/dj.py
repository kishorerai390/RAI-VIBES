import json
import os
from pathlib import Path
from typing import Optional, Literal, Set

import discord
from discord.ext import commands
from discord import app_commands

import config

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DJ_FILE = DATA_DIR / "dj_settings.json"

class DJ(commands.Cog):
    """Dedicated DJ Role & Party Queue Controller for RAI VIBES 💗."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.settings = self.load_settings()
        self.skip_votes: dict[int, Set[int]] = {}  # guild_id: set of user_ids

    def load_settings(self) -> dict:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        if DJ_FILE.exists():
            try:
                with open(DJ_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def save_settings(self):
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        with open(DJ_FILE, "w", encoding="utf-8") as f:
            json.dump(self.settings, f, indent=2)

    def is_dj_or_admin(self, member: discord.Member) -> bool:
        """Returns True if member has DJ permissions or Administrator access."""
        if member.guild_permissions.administrator or member.guild_permissions.manage_guild or member.id == member.guild.owner_id:
            return True

        guild_id_str = str(member.guild.id)
        guild_dj = self.settings.get(guild_id_str, {})
        dj_role_id = guild_dj.get("role_id")

        if dj_role_id:
            role = member.guild.get_role(dj_role_id)
            if role and role in member.roles:
                return True

        # Fallback to any role named 'DJ' or '🎧 DJ'
        for r in member.roles:
            if "dj" in r.name.lower():
                return True

        return False

    def get_dj_mode(self, guild_id: int) -> str:
        """Returns 'off', 'on', or 'vote'."""
        return self.settings.get(str(guild_id), {}).get("mode", "off")

    @commands.hybrid_group(name="dj", description="Manage DJ role settings and queue playback permissions.")
    async def dj_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await self.status(ctx)

    @dj_group.command(name="setrole", description="Set or update the designated DJ role for the server.")
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(role="The role to assign as DJ")
    async def set_role(self, ctx: commands.Context, role: discord.Role):
        guild_id_str = str(ctx.guild.id)
        if guild_id_str not in self.settings:
            self.settings[guild_id_str] = {}

        self.settings[guild_id_str]["role_id"] = role.id
        self.save_settings()

        embed = discord.Embed(
            title="👑 DJ Role Configured",
            description=f"Assigned {role.mention} as the official **DJ Role** for {ctx.guild.name}!",
            color=config.COLOR_PRIMARY
        )
        embed.set_footer(text="RAI VIBES 💗 • Party Access Controls", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @dj_group.command(name="mode", description="Set DJ enforcement mode: off (open), on (DJ only), or vote (vote-skip).")
    @commands.has_permissions(manage_guild=True)
    @app_commands.describe(mode="Select DJ mode enforcement")
    @app_commands.choices(mode=[
        app_commands.Choice(name="🔓 Off (Everyone can control queue)", value="off"),
        app_commands.Choice(name="🔒 On (Only DJs & Admins can skip/stop)", value="on"),
        app_commands.Choice(name="🗳️ Vote (Requires majority listener votes to skip)", value="vote")
    ])
    async def set_mode(self, ctx: commands.Context, mode: app_commands.Choice[str]):
        guild_id_str = str(ctx.guild.id)
        if guild_id_str not in self.settings:
            self.settings[guild_id_str] = {}

        self.settings[guild_id_str]["mode"] = mode.value
        self.save_settings()

        mode_descs = {
            "off": "🔓 **DJ Mode: OFF** — All members in the voice channel can skip, stop, and manage the queue.",
            "on": "🔒 **DJ Mode: ON** — Only members with the DJ role or Administrator permissions can skip/stop songs.",
            "vote": "🗳️ **DJ Mode: VOTE** — Regular listeners can use `/voteskip` to cast a majority vote to skip tracks."
        }

        embed = discord.Embed(
            title="🎧 DJ Mode Updated",
            description=mode_descs.get(mode.value, mode.value),
            color=config.COLOR_SUCCESS
        )
        embed.set_footer(text="RAI VIBES 💗 • Queue Permissions", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @dj_group.command(name="status", description="Display the current DJ role configuration and mode.")
    async def status(self, ctx: commands.Context):
        guild_dj = self.settings.get(str(ctx.guild.id), {})
        dj_role_id = guild_dj.get("role_id")
        dj_mode = guild_dj.get("mode", "off").upper()

        role_str = f"<@&{dj_role_id}>" if dj_role_id else "*None set (use `/dj setrole`)*"

        embed = discord.Embed(
            title=f"👑 DJ System Configuration • {ctx.guild.name}",
            description=(
                f"• **Current DJ Role:** {role_str}\n"
                f"• **Enforcement Mode:** `{dj_mode}`\n\n"
                f"*Commands available:*\n"
                f"`/dj setrole <@role>` — Assign designated DJ role\n"
                f"`/dj mode <off/on/vote>` — Configure queue restrictions\n"
                f"`/voteskip` — Cast vote to skip active track (Vote mode)"
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="RAI VIBES 💗 • Sound Engine", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="voteskip", aliases=["vs"], description="Cast a vote to skip the current track (Active in Vote DJ mode).")
    async def voteskip(self, ctx: commands.Context):
        music_cog = self.bot.get_cog("Music")
        if not music_cog:
            return await ctx.send("❌ Music engine not available.", ephemeral=True)

        player = music_cog.get_player(ctx.guild.id)
        if not player or not player.current or not ctx.guild.voice_client:
            return await ctx.send("❌ No track currently playing.", ephemeral=True)

        vc = ctx.guild.voice_client
        if not ctx.author.voice or ctx.author.voice.channel != vc.channel:
            return await ctx.send(f"❌ You must join {vc.channel.mention} to vote!", ephemeral=True)

        # Non-bot listeners
        listeners = [m for m in vc.channel.members if not m.bot]
        required_votes = max(1, (len(listeners) + 1) // 2)

        if ctx.guild.id not in self.skip_votes:
            self.skip_votes[ctx.guild.id] = set()

        votes = self.skip_votes[ctx.guild.id]

        if ctx.author.id in votes:
            return await ctx.send("ℹ️ You have already voted to skip this song.", ephemeral=True)

        votes.add(ctx.author.id)
        current_votes = len(votes)

        if current_votes >= required_votes or self.is_dj_or_admin(ctx.author):
            self.skip_votes[ctx.guild.id] = set()
            skipped_title = player.current.title
            player.skip()
            await ctx.send(f"⏭️ **Vote Passed ({current_votes}/{required_votes})!** Skipped: `{skipped_title}`")
        else:
            await ctx.send(f"🗳️ **Vote added!** `{current_votes}/{required_votes}` listeners have voted to skip. *(Need {required_votes - current_votes} more)*")


async def setup(bot: commands.Bot):
    await bot.add_cog(DJ(bot))
