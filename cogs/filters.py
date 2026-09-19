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

    @app_commands.command(name="filter", description="Apply studio audio FX filters to the current music playback.")
    @app_commands.describe(effect="Select an audio filter effect to toggle or activate")
    @app_commands.choices(effect=[
        app_commands.Choice(name="⚡ Bass Boost (Medium)", value="bassboost_medium"),
        app_commands.Choice(name="💥 Bass Boost (Extreme)", value="bassboost_extreme"),
        app_commands.Choice(name="🌙 Nightcore (Speed + Pitch)", value="nightcore"),
        app_commands.Choice(name="☕ Slowed + Reverb (Lo-fi)", value="slowed"),
        app_commands.Choice(name="🎧 8D Spatial Audio", value="8d"),
        app_commands.Choice(name="🌆 Retro Vaporwave", value="vaporwave"),
        app_commands.Choice(name="🎤 Karaoke (Vocal Cut)", value="karaoke"),
        app_commands.Choice(name="🔊 Loudness Normalization (ReplayGain)", value="loudnorm"),
        app_commands.Choice(name="🧹 Clear All Filters (Normal)", value="off"),
    ])
    async def filter_slash(self, interaction: discord.Interaction, effect: app_commands.Choice[str]):
        player = self.bot.get_cog("Music").get_player(interaction.guild) if self.bot.get_cog("Music") else None
        if not player or not player.is_connected or not player.current:
            return await interaction.response.send_message("❌ RAI VIBES must be streaming music in a voice channel to apply filters.", ephemeral=True)

        target = effect.value
        display = effect.name
        if target == "off":
            player.active_filters.clear()
            player.custom_speed = 1.0
            await player.restart_current_with_filters()
            return await interaction.response.send_message("🧹 **All audio filters deactivated:** Playback restored to studio normal.")

        if target in player.active_filters:
            player.active_filters.remove(target)
            await player.restart_current_with_filters()
            return await interaction.response.send_message(f"➡️ **Audio filter deactivated:** `{display}`")
        else:
            if target.startswith("bassboost_"):
                player.active_filters = [f for f in player.active_filters if not f.startswith("bassboost_")]
            player.active_filters.append(target)
            await player.restart_current_with_filters()
            return await interaction.response.send_message(f"⚡ **Audio filter activated:** `{display}`")

    @commands.command(name="bassboost", aliases=["bb", "bass"])
    async def bassboost(self, ctx: commands.Context, level: Optional[str] = "medium"):
        target_map = {
            "off": "off",
            "low": "bassboost_low",
            "medium": "bassboost_medium",
            "high": "bassboost_high",
            "extreme": "bassboost_extreme"
        }
        target = target_map.get(level.lower() if level else "medium", "bassboost_medium")
        display = level.capitalize() if level else "Medium"
        await self.apply_player_filter(ctx, target, f"Bass Boost [{display}]")

    @commands.command(name="nightcore", aliases=["nc"])
    async def nightcore(self, ctx: commands.Context):
        await self.apply_player_filter(ctx, "nightcore", "Nightcore")

    @commands.command(name="slowed", aliases=["slow", "reverb"])
    async def slowed(self, ctx: commands.Context):
        await self.apply_player_filter(ctx, "slowed", "Slowed + Reverb")

    @commands.command(name="spatial8d", aliases=["8d"])
    async def spatial_8d(self, ctx: commands.Context):
        await self.apply_player_filter(ctx, "8d", "8D Spatial 360 Audio")

    @commands.command(name="vaporwave", aliases=["vw"])
    async def vaporwave(self, ctx: commands.Context):
        await self.apply_player_filter(ctx, "vaporwave", "Vaporwave")

    @commands.hybrid_command(name="loudnorm", aliases=["replaygain", "norm"], description="Toggle automatic loudness normalization (EBU R128).")
    async def loudnorm_cmd(self, ctx: commands.Context):
        await self.apply_player_filter(ctx, "loudnorm", "Loudness Normalization (ReplayGain)")

    @commands.hybrid_command(name="karaoke", description="Toggle Karaoke mode (suppress center vocal frequencies for singing along).")
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
            await ctx.send("⚡ **Audio Filter Activated: Karaoke (Vocal Attenuation)**\n*Center vocal frequencies suppressed. Sing along with the music!*")

    @commands.hybrid_command(name="ambience", description="Stream calming ambient soundscapes (rain, fireplace, cafe, waves, lofi).")
    @app_commands.describe(preset="Select an ambient soundscape preset")
    @app_commands.choices(preset=[
        app_commands.Choice(name="🌧️ Heavy Rainstorm", value="rain"),
        app_commands.Choice(name="🔥 Cozy Fireplace", value="fireplace"),
        app_commands.Choice(name="☕ Cyberpunk Café", value="cafe"),
        app_commands.Choice(name="🌊 Ocean Waves", value="waves"),
        app_commands.Choice(name="🎧 24/7 Lo-Fi Chill", value="lofi"),
        app_commands.Choice(name="⏹️ Stop Ambience", value="stop")
    ])
    async def ambience_cmd(self, ctx: commands.Context, preset: str):
        music_cog = self.bot.get_cog("Music")
        if not music_cog:
            return await ctx.send("❌ Audio engine unavailable.", ephemeral=True)

        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must join a voice channel first to stream ambient audio.", ephemeral=True)

        if preset == "stop":
            player = music_cog.get_player(ctx.guild)
            if player and player.is_connected:
                await player.stop()
                return await ctx.send("⏹️ **Ambient soundscape stopped.**")
            return await ctx.send("ℹ️ No audio is currently playing.", ephemeral=True)

        ambient_urls = {
            "rain": "https://actions.google.com/sounds/v1/weather/rain_heavy.ogg",
            "fireplace": "https://actions.google.com/sounds/v1/household/fireplace_crackling.ogg",
            "cafe": "https://actions.google.com/sounds/v1/ambiences/coffee_shop.ogg",
            "waves": "https://actions.google.com/sounds/v1/water/ocean_waves.ogg",
            "lofi": "https://stream.zeno.fm/f3wvbbqmdg8uv"
        }

        url = ambient_urls.get(preset)
        if not url:
            return await ctx.send("❌ Unknown ambience preset. Try `rain`, `fireplace`, `cafe`, `waves`, or `lofi`.", ephemeral=True)

        names = {
            "rain": "🌧️ Heavy Rainstorm Ambience",
            "fireplace": "🔥 Cozy Fireplace Ambience",
            "cafe": "☕ Cyberpunk Café Ambience",
            "waves": "🌊 Ocean Waves Ambience",
            "lofi": "🎧 24/7 Lo-Fi Chill Stream"
        }

        # Play via music player
        player = music_cog.get_player(ctx.guild)
        if not player.is_connected:
            await player.connect(ctx.author.voice.channel)
        elif player.channel.id != ctx.author.voice.channel.id:
            await player.move_to(ctx.author.voice.channel)

        await ctx.send(f"🌿 **Now Streaming Ambience:** `{names.get(preset, preset)}` in {ctx.author.voice.channel.mention}")
        await music_cog.play_query(ctx, url, silent=True)

    @commands.command(name="speed")
    async def speed(self, ctx: commands.Context, value: float):
        player = self.get_player(ctx)
        if not player or not player.is_connected or not player.current:
            return await ctx.send("❌ RAI VIBES 💗 must be playing a song to adjust speed.")

        if not 0.5 <= value <= 2.0:
            return await ctx.send("❌ Speed must be between 0.5x and 2.0x.")

        player.custom_speed = value
        await player.restart_current_with_filters()
        await ctx.send(f"⏩ **Playback speed set to:** `{value}x`")

    @commands.hybrid_command(name="equalizer", aliases=["eq"], description="Open the live interactive Studio Audio Equalizer switchboard.")
    async def equalizer(self, ctx: commands.Context):
        player = self.get_player(ctx)
        if not player or not player.is_connected or not player.current:
            return await ctx.send("❌ RAI VIBES must be streaming in a voice channel to open the Equalizer.", ephemeral=True)

        active_list = ", ".join([f"`{f}`" for f in player.active_filters]) if player.active_filters else "`Flat / Clean`"
        embed = discord.Embed(
            title="🎛️ STUDIO AUDIO EQUALIZER",
            description=(
                f"Now Playing: **[{player.current.title}]({player.current.webpage_url})**\n\n"
                f"🎚️ **Active DSP Filters:** {active_list}\n\n"
                f"Click buttons below to toggle real-time audiophile DSP enhancements:"
            ),
            color=0x00FFCC
        )
        embed.set_footer(text="RAI VIBES Studio Sound Engine • High Fidelity Real-time DSP", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed, view=StudioEqualizerView(self, ctx.guild.id))


class StudioEqualizerView(discord.ui.View):
    def __init__(self, filters_cog: Filters, guild_id: int):
        super().__init__(timeout=120)
        self.filters_cog = filters_cog
        self.guild_id = guild_id

    async def toggle_filter(self, interaction: discord.Interaction, filter_key: str, name: str):
        music_cog = self.filters_cog.bot.get_cog("Music")
        if not music_cog:
            return await interaction.response.send_message("❌ Music engine not available.", ephemeral=True)
        player = music_cog.get_player(self.guild_id)
        if not player or not player.is_connected or not player.current:
            return await interaction.response.send_message("❌ Nothing is currently playing in voice.", ephemeral=True)

        if filter_key == "off":
            player.active_filters.clear()
            player.custom_speed = 1.0
            await player.restart_current_with_filters()
            status_text = "✨ Reset to Studio Flat reference master."
        else:
            if filter_key in player.active_filters:
                player.active_filters.remove(filter_key)
                status_text = f"⚪ Disabled `{name}`"
            else:
                player.active_filters.append(filter_key)
                status_text = f"⚡ Activated `{name}`"
            await player.restart_current_with_filters()

        active_list = ", ".join([f"`{f}`" for f in player.active_filters]) if player.active_filters else "`Flat / Clean`"
        embed = discord.Embed(
            title="🎛️ STUDIO AUDIO EQUALIZER",
            description=(
                f"Now Playing: **[{player.current.title}]({player.current.webpage_url})**\n\n"
                f"Status: {status_text}\n"
                f"🎚️ **Active DSP Filters:** {active_list}"
            ),
            color=0x00FFCC
        )
        embed.set_footer(text="RAI VIBES Studio Sound Engine • High Fidelity Real-time DSP", icon_url=config.RAI_ICON_URL)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Lo-Fi Mellow", emoji="☕", style=discord.ButtonStyle.primary, row=0)
    async def btn_lofi(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await self.toggle_filter(interaction, "lofi_mellow", "Lo-Fi Mellow")

    @discord.ui.button(label="Sub-Bass 3D", emoji="⚡", style=discord.ButtonStyle.primary, row=0)
    async def btn_bass(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await self.toggle_filter(interaction, "subbass_engine", "Sub-Bass 3D Engine")

    @discord.ui.button(label="Vocal Clarity", emoji="🎤", style=discord.ButtonStyle.primary, row=0)
    async def btn_vocal(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await self.toggle_filter(interaction, "vocal_clarity", "Vocal Clarity")

    @discord.ui.button(label="Cinema Surround", emoji="🍿", style=discord.ButtonStyle.secondary, row=1)
    async def btn_cinema(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await self.toggle_filter(interaction, "cinema", "Cinema Surround")

    @discord.ui.button(label="8D Spatial", emoji="🌌", style=discord.ButtonStyle.secondary, row=1)
    async def btn_8d(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await self.toggle_filter(interaction, "8d", "8D Spatial Audio")

    @discord.ui.button(label="Nightcore", emoji="⚡", style=discord.ButtonStyle.secondary, row=1)
    async def btn_nc(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await self.toggle_filter(interaction, "nightcore", "Nightcore")

    @discord.ui.button(label="Reset / Flat", emoji="🔄", style=discord.ButtonStyle.danger, row=2)
    async def btn_flat(self, interaction: discord.Interaction, btn: discord.ui.Button):
        await self.toggle_filter(interaction, "off", "Flat / Clean")


async def setup(bot: commands.Bot):
    await bot.add_cog(Filters(bot))
