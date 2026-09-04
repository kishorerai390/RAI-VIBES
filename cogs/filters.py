import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional

import config
from utils.filters import FILTER_PRESETS

class Filters(commands.Cog):
    """Audio Equalizer & Sound Enhancement Effects for RAI VIBES 💗."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_player(self, ctx_or_interaction):
        guild = ctx_or_interaction.guild
        music_cog = self.bot.get_cog("Music")
        if not music_cog:
            return None
        return music_cog.get_player(guild.id)

    async def apply_player_filter(self, ctx: commands.Context, filter_name: str, display_name: str):
        player = self.get_player(ctx)
        if not player or not player.is_connected or not player.current:
            return await ctx.send("❌ RAI VIBES 💗 must be playing a song to apply audio effects.", ephemeral=True)

        if filter_name == "off":
            player.active_filters.clear()
            player.custom_speed = 1.0
            await player.restart_current_with_filters()
            return await ctx.send("✨ **All audio filters have been cleared / reset.**")

        # Toggle or set filter
        if filter_name in player.active_filters:
            player.active_filters.remove(filter_name)
            await player.restart_current_with_filters()
            return await ctx.send(f"➡️ **Audio filter disabled:** `{display_name}`")
        else:
            # If it's a bassboost variation, remove other bassboosts first
            if filter_name.startswith("bassboost_"):
                player.active_filters = [f for f in player.active_filters if not f.startswith("bassboost_")]
            player.active_filters.append(filter_name)
            await player.restart_current_with_filters()
            return await ctx.send(f"⚡ **Audio filter activated:** `{display_name}`")

    @commands.hybrid_command(name="bassboost", aliases=["bb", "bass"], description="Boost the sub-bass frequencies.")
    @app_commands.describe(level="Bass boost intensity level")
    @app_commands.choices(level=[
        app_commands.Choice(name="Off (Disable)", value="off"),
        app_commands.Choice(name="Low (Subtle Punch)", value="bassboost_low"),
        app_commands.Choice(name="Medium (Rich Thunder)", value="bassboost_medium"),
        app_commands.Choice(name="High (Heavy Rumble)", value="bassboost_high"),
        app_commands.Choice(name="Extreme (Asgard Quake)", value="bassboost_extreme"),
    ])
    async def bassboost(self, ctx: commands.Context, level: Optional[app_commands.Choice[str]] = None):
        target = level.value if level else "bassboost_medium"
        name = level.name if level else "Medium (Rich Thunder)"
        await self.apply_player_filter(ctx, target, f"Bass Boost [{name}]")

    @commands.hybrid_command(name="nightcore", aliases=["nc"], description="Toggle high-energy Nightcore pitch & speed filter.")
    async def nightcore(self, ctx: commands.Context):
        await self.apply_player_filter(ctx, "nightcore", "Nightcore")

    @commands.hybrid_command(name="slowed", aliases=["slow", "reverb"], description="Toggle aesthetic Slowed + Reverb audio filter.")
    async def slowed(self, ctx: commands.Context):
        await self.apply_player_filter(ctx, "slowed", "Slowed + Reverb")

    @commands.hybrid_command(name="spatial8d", aliases=["8d"], description="Toggle 8D 360-degree spatial headphone rotation.")
    async def spatial_8d(self, ctx: commands.Context):
        await self.apply_player_filter(ctx, "8d", "8D Spatial 360 Audio")

    @commands.hybrid_command(name="vaporwave", aliases=["vw"], description="Toggle nostalgic retro Vaporwave filter.")
    async def vaporwave(self, ctx: commands.Context):
        await self.apply_player_filter(ctx, "vaporwave", "Vaporwave")

    @commands.hybrid_command(name="karaoke", description="Attenuate vocals for karaoke singing.")
    async def karaoke(self, ctx: commands.Context):
        await self.apply_player_filter(ctx, "karaoke", "Karaoke (Vocal Attenuation)")

    @commands.hybrid_command(name="speed", description="Adjust playback speed (0.5x to 2.0x).")
    @app_commands.describe(value="Playback speed factor (e.g. 1.25 for 1.25x)")
    async def speed(self, ctx: commands.Context, value: float):
        player = self.get_player(ctx)
        if not player or not player.is_connected or not player.current:
            return await ctx.send("❌ RAI VIBES 💗 must be playing a song to adjust speed.", ephemeral=True)

        if not 0.5 <= value <= 2.0:
            return await ctx.send("❌ Speed must be between 0.5x and 2.0x.", ephemeral=True)

        player.custom_speed = value
        await player.restart_current_with_filters()
        await ctx.send(f"⏩ **Playback speed set to:** `{value}x`")

    @commands.hybrid_command(name="filter_reset", aliases=["clearfilters", "resetfilter"], description="Reset and remove all active audio filters.")
    async def filter_reset(self, ctx: commands.Context):
        await self.apply_player_filter(ctx, "off", "Off")


async def setup(bot: commands.Bot):
    await bot.add_cog(Filters(bot))
