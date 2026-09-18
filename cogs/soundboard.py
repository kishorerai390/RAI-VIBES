import asyncio
import time
import datetime
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select
from typing import Optional, Dict


import config
from utils.ffmpeg_setup import get_ffmpeg_executable
from utils.soundboard_manager import (
    is_founder,
    is_channel_soundboard_muted,
    set_channel_soundboard_muted,
    apply_discord_soundboard_permission,
    OWNER_ID
)

SOUND_EFFECTS = {
    "airhorn": {
        "name": "🎺 Airhorn",
        "url": "https://www.myinstants.com/media/sounds/air-horn-club-sample_1.mp3",
        "category": "hype"
    },
    "crowd_cheer": {
        "name": "👏 Crowd Cheer",
        "url": "https://www.myinstants.com/media/sounds/cheering.mp3",
        "category": "hype"
    },
    "victory": {
        "name": "🏆 Victory Fanfare",
        "url": "https://www.myinstants.com/media/sounds/final-fantasy-vii-victory-fanfare-1.mp3",
        "category": "hype"
    },
    "drumroll": {
        "name": "🥁 Rimshot / Ba-Dum-Tss",
        "url": "https://www.myinstants.com/media/sounds/ba-dum-tss.mp3",
        "category": "hype"
    },
    "bruh": {
        "name": "🗿 Bruh",
        "url": "https://www.myinstants.com/media/sounds/movie_1.mp3",
        "category": "meme"
    },
    "sad_violin": {
        "name": "🎻 Sad Violin",
        "url": "https://www.myinstants.com/media/sounds/sad-violin.mp3",
        "category": "meme"
    },
    "emotional_damage": {
        "name": "💥 Emotional Damage",
        "url": "https://www.myinstants.com/media/sounds/emotional-damage-meme.mp3",
        "category": "meme"
    },
    "wow": {
        "name": "✨ Wow Anime",
        "url": "https://www.myinstants.com/media/sounds/anime-wow-sound-effect.mp3",
        "category": "meme"
    },
    "directed_by": {
        "name": "🎬 Directed by Robert B. Weide",
        "url": "https://www.myinstants.com/media/sounds/curb-your-enthusiasm-theme_1.mp3",
        "category": "meme"
    },
    "gunshot": {
        "name": "🔫 Anirudh Gunshot FX",
        "url": "https://www.myinstants.com/media/sounds/gunshot_sound.mp3",
        "category": "cinema"
    },
    "vadivelu": {
        "name": "😂 Vadivelu Haha",
        "url": "https://www.myinstants.com/media/sounds/vadivelu-laugh.mp3",
        "category": "cinema"
    },
    "thalaivar": {
        "name": "👑 Rajini Thalaivar BGM",
        "url": "https://www.myinstants.com/media/sounds/jailer-hukum-bgm.mp3",
        "category": "cinema"
    },
    "vineboom": {
        "name": "💥 Vine Boom Thud",
        "url": "https://www.myinstants.com/media/sounds/vine-boom.mp3",
        "category": "meme"
    },
    "nani": {
        "name": "⚡ Omae Wa Mou Shindeiru",
        "url": "https://www.myinstants.com/media/sounds/nani-meme-sound-effect.mp3",
        "category": "meme"
    },
    "discord_ping": {
        "name": "🔔 Discord Ghost Ping",
        "url": "https://www.myinstants.com/media/sounds/discord-notification.mp3",
        "category": "meme"
    },
    "sheesh": {
        "name": "🔥 Sheesh Hype",
        "url": "https://www.myinstants.com/media/sounds/sheesh.mp3",
        "category": "hype"
    }
}

# Soundboard spam & interruption tracker: user_id -> list of timestamps
USER_SOUNDBOARD_USAGE: Dict[int, list] = {}

class SoundboardButton(Button):
    def __init__(self, sfx_key: str, sfx_data: dict):
        super().__init__(
            label=sfx_data["name"][:30],
            style=discord.ButtonStyle.secondary,
            custom_id=f"sfx_btn_{sfx_key}"
        )
        self.sfx_key = sfx_key
        self.sfx_data = sfx_data

    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ You must join a voice channel to use the Soundboard!", ephemeral=True)

        member = interaction.user
        channel = member.voice.channel
        now = time.time()
        uid = member.id

        # Channel Soundboard Mute Check (Founder Override)
        if is_channel_soundboard_muted(channel.id) and not is_founder(member, interaction.guild):
            return await interaction.response.send_message(
                f"🔇 **Soundboard Restricted:** Soundboard audio is currently muted in {channel.mention} by the Founder.",
                ephemeral=True
            )

        # Soundboard Interruption & Spam Watchdog
        # If in VC with other members talking and member spams soundboard
        if not member.guild_permissions.moderate_members and not member.guild_permissions.administrator:
            if uid not in USER_SOUNDBOARD_USAGE:
                USER_SOUNDBOARD_USAGE[uid] = []
            
            # Keep timestamps within 15 seconds
            USER_SOUNDBOARD_USAGE[uid] = [t for t in USER_SOUNDBOARD_USAGE[uid] if now - t < 15.0]
            USER_SOUNDBOARD_USAGE[uid].append(now)

            # Trigger automatic 15-minute timeout if > 2 soundboard sounds in 15 seconds in multi-user VC
            non_bot_members = [m for m in channel.members if not m.bot]
            if len(non_bot_members) >= 2 and len(USER_SOUNDBOARD_USAGE[uid]) >= 3:
                USER_SOUNDBOARD_USAGE[uid].clear()
                
                # Apply 15-minute Discord timeout
                timeout_duration = datetime.timedelta(minutes=15)
                try:
                    await member.timeout(timeout_duration, reason="Automatic 15-minute Soundboard Interruption Timeout")
                except Exception:
                    pass
                
                # Server Mute in VC
                try:
                    await member.edit(mute=True, reason="Soundboard Spam in VC")
                except Exception:
                    pass

                # Announce in Channel
                alert_embed = discord.Embed(
                    title="🔇 Automated 15-Minute Soundboard Timeout",
                    description=(
                        f"⚠️ {member.mention} has been put on a **15-minute Voice & Soundboard Timeout** for interrupting and spamming sound effects during active conversation in {channel.mention}!\n\n"
                        f"⏳ **Duration:** `15 Minutes`\n"
                        f"🛡️ **Enforcement:** Automatic Soundboard Watchdog"
                    ),
                    color=config.COLOR_WARNING
                )
                alert_embed.set_footer(text="RAI SENTINEL 🛡️ Voice Protection", icon_url=config.RAI_ICON_URL)
                
                # Log to mod-logs
                log_chan = discord.utils.get(interaction.guild.text_channels, name="📋・mod-logs")
                if log_chan:
                    try:
                        await log_chan.send(embed=alert_embed)
                    except Exception:
                        pass

                return await interaction.response.send_message(
                    f"⛔ **Soundboard Timeout Applied!** You have been timed out for **15 minutes** for spamming sound effects during an active VC conversation.",
                    ephemeral=True
                )

        music_cog = interaction.client.get_cog("Music")
        if not music_cog:
            return await interaction.response.send_message("❌ Music engine unavailable.", ephemeral=True)

        vc = await music_cog.ensure_voice(interaction)
        if not vc:
            return await interaction.response.send_message("❌ Could not connect to your voice channel.", ephemeral=True)

        ffmpeg_bin = get_ffmpeg_executable()
        raw_source = discord.FFmpegPCMAudio(
            self.sfx_data["url"],
            executable=ffmpeg_bin,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin",
            options="-vn -bufsize 1024k"
        )
        player = music_cog.get_or_create_player(interaction.guild)
        transformed = discord.PCMVolumeTransformer(raw_source, volume=player.get_volume_factor())

        if vc.is_playing():
            vc.stop()
            await asyncio.sleep(0.15)

        vc.play(transformed)
        await interaction.response.send_message(f"🔊 Playing sound effect: **{self.sfx_data['name']}** in {vc.channel.mention}!", ephemeral=True)



class SoundboardView(View):
    """Interactive persistent soundboard button dashboard."""
    def __init__(self):
        super().__init__(timeout=None)
        
        # Add buttons in rows
        for key, data in SOUND_EFFECTS.items():
            self.add_item(SoundboardButton(key, data))


class Soundboard(commands.Cog):
    """Interactive Voice Channel Soundboard & DJ Sound Effects for RAI VIBES 💗."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="soundboard", aliases=["sfxpanel", "sounds", "djfx"], description="Display the interactive Voice Channel Soundboard control panel.")
    async def soundboard_cmd(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🎛️ RAI VIBES 💗 • LIVE SOUNDBOARD PANEL",
            description=(
                "Click any button below to instantly trigger live sound effects & meme audio in your voice channel!\n\n"
                "**🎺 Hype:** Airhorn, Crowd Cheer, Victory, Sheesh\n"
                "**🎭 Memes:** Bruh, Sad Violin, Emotional Damage, Wow, Nani, Vine Boom\n"
                "**🎬 Cinema:** Gunshot, Vadivelu Laugh, Thalaivar BGM"
            ),
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="RAI VIBES 💗 • High Fidelity SFX Sound Engine", icon_url=config.RAI_ICON_URL)

        view = SoundboardView()
        await ctx.send(embed=embed, view=view)

    @commands.command(name="fx")
    async def fx_cmd(self, ctx: commands.Context):
        """Direct prefix shortcut for the DJ FX Soundboard Pad."""
        await self.soundboard_cmd(ctx)

    @commands.hybrid_command(name="sfx", description="Play a specific sound effect directly in your voice room.")
    @app_commands.describe(effect="Select the sound effect to trigger")
    @app_commands.choices(effect=[
        app_commands.Choice(name="🎺 Airhorn", value="airhorn"),
        app_commands.Choice(name="👏 Crowd Cheer", value="crowd_cheer"),
        app_commands.Choice(name="🏆 Victory Fanfare", value="victory"),
        app_commands.Choice(name="🥁 Rimshot / Drumroll", value="drumroll"),
        app_commands.Choice(name="🗿 Bruh", value="bruh"),
        app_commands.Choice(name="🎻 Sad Violin", value="sad_violin"),
        app_commands.Choice(name="💥 Emotional Damage", value="emotional_damage"),
        app_commands.Choice(name="✨ Anime Wow", value="wow"),
        app_commands.Choice(name="🎬 Directed by Robert B. Weide", value="directed_by"),
        app_commands.Choice(name="🔫 Anirudh Gunshot FX", value="gunshot"),
        app_commands.Choice(name="😂 Vadivelu Comedy Laugh", value="vadivelu"),
        app_commands.Choice(name="👑 Rajini Thalaivar BGM", value="thalaivar")
    ])
    async def sfx_cmd(self, ctx: commands.Context, effect: app_commands.Choice[str]):
        sfx_key = effect.value
        sfx_data = SOUND_EFFECTS.get(sfx_key)
        if not sfx_data:
            return await ctx.send("❌ Unknown sound effect.", ephemeral=True)

        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("⚡ Please join a voice channel first!", ephemeral=True)

        target_vc = ctx.author.voice.channel
        if is_channel_soundboard_muted(target_vc.id) and not is_founder(ctx.author, ctx.guild):
            return await ctx.send(
                f"🔇 **Soundboard Restricted:** Soundboard audio is currently muted in {target_vc.mention} by the Founder.",
                ephemeral=True
            )

        music_cog = self.bot.get_cog("Music")
        if not music_cog:
            return await ctx.send("❌ Music engine unavailable.", ephemeral=True)

        vc = await music_cog.ensure_voice(ctx)
        if not vc:
            return await ctx.send("❌ Could not connect to voice channel.", ephemeral=True)

        ffmpeg_bin = get_ffmpeg_executable()
        raw_source = discord.FFmpegPCMAudio(
            sfx_data["url"],
            executable=ffmpeg_bin,
            before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin",
            options="-vn -bufsize 1024k"
        )
        player = music_cog.get_or_create_player(ctx.guild)
        transformed = discord.PCMVolumeTransformer(raw_source, volume=player.get_volume_factor())

        if vc.is_playing():
            vc.stop()
            await asyncio.sleep(0.15)

        vc.play(transformed)
        await ctx.send(f"🔊 Playing sound effect: **{sfx_data['name']}**!")

    @commands.hybrid_command(
        name="mutesoundboard",
        aliases=["soundboardmute", "silencesoundboard"],
        description="[👑 FOUNDER ONLY] Mute or unmute the soundboard in a specific voice channel."
    )
    @app_commands.describe(
        channel="Select the voice channel to mute/unmute (Defaults to your current voice channel)",
        action="Choose whether to Mute, Unmute, Toggle, or check Status"
    )
    @app_commands.choices(action=[
        app_commands.Choice(name="🔇 Mute Soundboard (Disable in room)", value="mute"),
        app_commands.Choice(name="🔊 Unmute Soundboard (Enable in room)", value="unmute"),
        app_commands.Choice(name="🔄 Toggle Soundboard", value="toggle"),
        app_commands.Choice(name="📊 View Status", value="status")
    ])
    async def mutesoundboard_cmd(
        self,
        ctx: commands.Context,
        channel: Optional[discord.VoiceChannel] = None,
        action: str = "toggle"
    ):
        """Mutes or unmutes Discord native soundboard & bot SFX in a specific voice channel. Founder only."""
        # 1. Founder security check
        if not is_founder(ctx.author, ctx.guild):
            embed = discord.Embed(
                title="⛔ ACCESS DENIED • FOUNDER RESTRICTED",
                description=(
                    "✦ ───────────────────────────────────── ✦\n\n"
                    "Only the **👑 Server Founder & Owner** can manage soundboard channel restrictions!\n\n"
                    "✦ ───────────────────────────────────── ✦"
                ),
                color=0xFF0055
            )
            embed.set_footer(text="RAI FAM 💗 • Founder Voice Authority", icon_url=config.RAI_ICON_URL)
            if ctx.interaction:
                return await ctx.interaction.response.send_message(embed=embed, ephemeral=True)
            else:
                return await ctx.send(embed=embed)

        # 2. Defer interaction if present
        if ctx.interaction and not ctx.interaction.response.is_done():
            await ctx.interaction.response.defer(ephemeral=False)

        async def reply_msg(content: Optional[str] = None, embed: Optional[discord.Embed] = None):
            if ctx.interaction:
                if ctx.interaction.response.is_done():
                    return await ctx.interaction.followup.send(content=content, embed=embed)
                else:
                    return await ctx.interaction.response.send_message(content=content, embed=embed)
            else:
                return await ctx.send(content=content, embed=embed)

        # 3. Determine target channel
        target_chan = channel
        if not target_chan:
            if isinstance(ctx.author, discord.Member) and ctx.author.voice and ctx.author.voice.channel:
                target_chan = ctx.author.voice.channel
            else:
                err_embed = discord.Embed(
                    title="❌ Voice Channel Required",
                    description=(
                        "Please specify a voice channel or join one first!\n\n"
                        "👉 **Usage:** `/mutesoundboard channel:#voice-room action:Mute`"
                    ),
                    color=config.COLOR_DANGER
                )
                return await reply_msg(embed=err_embed)

        # 4. Check current status
        currently_muted = is_channel_soundboard_muted(target_chan.id)

        if action == "status":
            state_str = "🔇 MUTED & LOCKED" if currently_muted else "🔊 UNMUTED & ACTIVE"
            color = 0xFF0055 if currently_muted else 0x00F5D4
            status_embed = discord.Embed(
                title="📊 VOICE SOUNDBOARD CHANNEL STATUS",
                description=(
                    f"✦ ───────────────────────────────────── ✦\n\n"
                    f"• **Channel:** {target_chan.mention} (`{target_chan.name}`)\n"
                    f"• **Soundboard Status:** **`{state_str}`**\n"
                    f"• **Discord Soundboard:** {'🚫 Disabled for @everyone' if currently_muted else '✅ Enabled for @everyone'}\n"
                    f"• **External Sounds:** {'🚫 Blocked' if currently_muted else '✅ Allowed'}\n"
                    f"• **Bot SFX & Fanfares:** {'🔕 Silenced in this room' if currently_muted else '🔔 Active'}\n\n"
                    f"✦ ───────────────────────────────────── ✦"
                ),
                color=color
            )
            status_embed.set_footer(text="RAI FAM 💗 • Founder Voice Authority", icon_url=config.RAI_ICON_URL)
            return await reply_msg(embed=status_embed)

        if action == "mute":
            new_state = True
        elif action == "unmute":
            new_state = False
        else:  # toggle
            new_state = not currently_muted

        # 5. Save persistence state
        set_channel_soundboard_muted(target_chan.id, new_state)

        # 6. Apply Discord channel permission overwrite for @everyone
        perm_ok, perm_msg = await apply_discord_soundboard_permission(target_chan, new_state, ctx.author)

        if new_state:
            res_embed = discord.Embed(
                title="🔇 SOUNDBOARD MUTED & RESTRICTED",
                description=(
                    f"✦ ───────────────────────────────────── ✦\n\n"
                    f"The soundboard has been **MUTED & LOCKED** in {target_chan.mention}!\n\n"
                    f"• **Target Room:** {target_chan.mention} (`{target_chan.name}`)\n"
                    f"• **Discord Soundboard:** 🚫 Disabled for `@everyone`\n"
                    f"• **External Sounds:** 🚫 Blocked\n"
                    f"• **Bot SFX & Entrance Sounds:** 🔕 Silenced in this room\n"
                    f"• **Enforced By:** 👑 Founder {ctx.author.mention}\n\n"
                    f"✦ ───────────────────────────────────── ✦\n"
                    f"💡 *To re-enable, run `/unmutesoundboard channel:{target_chan.mention}` or `/mutesoundboard action:Unmute`.*"
                ),
                color=0xFF0055
            )
        else:
            res_embed = discord.Embed(
                title="🔊 SOUNDBOARD RESTRICTION REMOVED",
                description=(
                    f"✦ ───────────────────────────────────── ✦\n\n"
                    f"The soundboard has been **UNMUTED & RESTORED** in {target_chan.mention}!\n\n"
                    f"• **Target Room:** {target_chan.mention} (`{target_chan.name}`)\n"
                    f"• **Discord Soundboard:** ✅ Enabled for `@everyone`\n"
                    f"• **External Sounds:** ✅ Restored\n"
                    f"• **Bot SFX & Entrance Sounds:** 🔔 Active\n"
                    f"• **Authorized By:** 👑 Founder {ctx.author.mention}\n\n"
                    f"✦ ───────────────────────────────────── ✦"
                ),
                color=0x00F5D4
            )

        if not perm_ok:
            res_embed.add_field(
                name="⚠️ Permission Notice",
                value=f"Database updated, but Discord channel permission warning: `{perm_msg}`",
                inline=False
            )

        res_embed.set_footer(text="RAI FAM 💗 • Founder Voice Authority", icon_url=config.RAI_ICON_URL)
        await reply_msg(embed=res_embed)

    @commands.hybrid_command(
        name="unmutesoundboard",
        aliases=["soundboardunmute"],
        description="[👑 FOUNDER ONLY] Unmute and restore soundboard in a specific voice channel."
    )
    @app_commands.describe(channel="Voice channel to restore soundboard in (Defaults to current VC)")
    async def unmutesoundboard_cmd(self, ctx: commands.Context, channel: Optional[discord.VoiceChannel] = None):
        """Quick shortcut to unmute the soundboard in a specific channel."""
        await self.mutesoundboard_cmd(ctx, channel=channel, action="unmute")


async def setup(bot: commands.Bot):
    await bot.add_cog(Soundboard(bot))
