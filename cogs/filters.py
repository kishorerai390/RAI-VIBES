import discord
from discord.ext import commands
from discord import app_commands
from typing import Optional, Literal

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
    async def bassboost(self, ctx: commands.Context, level: Optional[Literal["low", "medium", "high", "extreme", "off"]] = "medium"):
        target_map = {
            "off": "off",
            "low": "bassboost_low",
            "medium": "bassboost_medium",
            "high": "bassboost_high",
            "extreme": "bassboost_extreme"
        }
        target = target_map.get(level or "medium", "bassboost_medium")
        display = level.capitalize() if level else "Medium"
        await self.apply_player_filter(ctx, target, f"Bass Boost [{display}]")

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

    @commands.hybrid_command(name="karaoke", description="Toggle vocal attenuation filter & display song lyrics for sing-along!")
    async def karaoke(self, ctx: commands.Context):
        player = self.get_player(ctx)
        if not player or not player.is_connected or not player.current:
            return await ctx.send("❌ RAI VIBES 💗 must be playing a song to activate Karaoke mode.", ephemeral=True)

        if "karaoke" in player.active_filters:
            player.active_filters.remove("karaoke")
            await player.restart_current_with_filters()
            return await ctx.send("➡️ **Karaoke mode deactivated:** Restored full vocal audio track.")
        else:
            player.active_filters.append("karaoke")
            await player.restart_current_with_filters()

            # Automatically fetch and display lyrics for the song
            lyrics_cog = self.bot.get_cog("Lyrics")
            if lyrics_cog and player.current:
                data = await lyrics_cog.fetch_lyrics(player.current.title)
                if data and data.get("lyrics"):
                    lyrics_text = data["lyrics"]
                    if len(lyrics_text) > 3900:
                        lyrics_text = lyrics_text[:3885] + "...\n*(Lyrics truncated)*"

                    embed = discord.Embed(
                        title=f"🎤 Karaoke Sing-Along: {data.get('title', player.current.title)}",
                        description=f"```fix\n{lyrics_text}\n```" if len(lyrics_text) < 1800 else lyrics_text,
                        color=0xFF1493
                    )
                    embed.set_author(name=f"{data.get('author', 'Artist')} • Sing Along", icon_url=config.RAI_ICON_URL)
                    embed.set_thumbnail(url=player.current.thumbnail or config.RAI_ICON_URL)
                    embed.set_footer(text="RAI VIBES 💗 • Center Vocals Attenuated • Sing Loud & Proud!", icon_url=config.RAI_ICON_URL)
                    return await ctx.send(content="⚡ **Audio Filter Activated: Karaoke (Vocal Attenuation)**", embed=embed)

            await ctx.send("⚡ **Audio Filter Activated: Karaoke (Vocal Attenuation)**\n*Center vocal frequencies suppressed. Sing along with the music!*")

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
