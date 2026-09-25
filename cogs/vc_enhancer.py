import asyncio
import time
import logging
from typing import Optional, Dict, Set
import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button

import config

logger = logging.getLogger("VCEnhancer")

RECORDING_STUDIO_ID = 1552354617415962785

class ClutchControlView(View):
    """Interactive view to cancel/end Clutch Mode early."""
    def __init__(self, host_id: int, muted_members: Set[discord.Member]):
        super().__init__(timeout=180)
        self.host_id = host_id
        self.muted_members = muted_members
        self.ended = False

    @discord.ui.button(label="🔊 End Clutch (Unmute All)", style=discord.ButtonStyle.success, emoji="🔊", custom_id="end_clutch_btn")
    async def end_clutch(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.host_id and not interaction.user.guild_permissions.mute_members:
            return await interaction.response.send_message("❌ Only the clutching player or a moderator can end Clutch Mode early.", ephemeral=True)

        if self.ended:
            return await interaction.response.send_message("ℹ️ Clutch Mode has already ended.", ephemeral=True)

        self.ended = True
        button.disabled = True
        button.label = "✅ Clutch Finished"
        await interaction.response.edit_message(view=self)

        # Unmute all muted members
        unmuted_count = 0
        for m in list(self.muted_members):
            try:
                if m.voice and m.voice.mute:
                    await m.edit(mute=False, reason="Clutch Mode ended by player")
                    unmuted_count += 1
            except Exception:
                pass

        await interaction.followup.send(f"🎉 **Clutch Mode Finished!** `{unmuted_count}` squadmates unmuted. GG! 🔥")


class VoteSkipView(View):
    """Interactive voting buttons to skip music tracks democratically."""
    def __init__(self, required_votes: int, vc: discord.VoiceChannel, bot_instance: commands.Bot):
        super().__init__(timeout=45)
        self.required_votes = required_votes
        self.vc = vc
        self.bot = bot_instance
        self.voters: Set[int] = set()
        self.skipped = False

    @discord.ui.button(label="Vote Skip (0)", style=discord.ButtonStyle.primary, emoji="⏭️", custom_id="vote_skip_btn")
    async def vote(self, interaction: discord.Interaction, button: Button):
        if not interaction.user.voice or interaction.user.voice.channel.id != self.vc.id:
            return await interaction.response.send_message("❌ You must be listening in this voice channel to vote.", ephemeral=True)

        if interaction.user.id in self.voters:
            return await interaction.response.send_message("⚠️ You have already voted to skip this track.", ephemeral=True)

        self.voters.add(interaction.user.id)
        current = len(self.voters)
        button.label = f"Vote Skip ({current}/{self.required_votes})"

        if current >= self.required_votes and not self.skipped:
            self.skipped = True
            button.disabled = True
            button.style = discord.ButtonStyle.success
            await interaction.response.edit_message(view=self)

            # Trigger skip on voice client
            vc_client = discord.utils.get(self.bot.voice_clients, guild=interaction.guild)
            if vc_client and (vc_client.is_playing() or vc_client.is_paused()):
                vc_client.stop()
                await interaction.followup.send("⏭️ **Vote Passed!** Skipping to the next track... 🎵")
            else:
                await interaction.followup.send("ℹ️ No active audio to skip.")
        else:
            await interaction.response.edit_message(view=self)


class ScrimsControlView(View):
    """Host controls for Custom Scrims & Tournament matches."""
    def __init__(self, host_id: int, vc: discord.VoiceChannel):
        super().__init__(timeout=None)
        self.host_id = host_id
        self.vc = vc

    @discord.ui.button(label="Silence Match (Mute All)", style=discord.ButtonStyle.danger, emoji="🔇", custom_id="scrims_mute_all")
    async def mute_all(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.host_id and not interaction.user.guild_permissions.mute_members:
            return await interaction.response.send_message("❌ Only tournament hosts or staff can control match audio.", ephemeral=True)

        count = 0
        for m in self.vc.members:
            if not m.bot and m.id != interaction.user.id and not m.voice.mute:
                try:
                    await m.edit(mute=True, reason="Tournament host silenced room for match start")
                    count += 1
                except Exception:
                    pass
        await interaction.response.send_message(f"🔇 **Match Audio Silenced!** Muted `{count}` players for match start/rules.", ephemeral=False)

    @discord.ui.button(label="Unmute All Players", style=discord.ButtonStyle.success, emoji="🔊", custom_id="scrims_unmute_all")
    async def unmute_all(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.host_id and not interaction.user.guild_permissions.mute_members:
            return await interaction.response.send_message("❌ Only tournament hosts or staff can control match audio.", ephemeral=True)

        count = 0
        for m in self.vc.members:
            if not m.bot and m.voice.mute:
                try:
                    await m.edit(mute=False, reason="Tournament match ended or pause over")
                    count += 1
                except Exception:
                    pass
        await interaction.response.send_message(f"🔊 **Match Finished!** Unmuted `{count}` players. GG! 🏆", ephemeral=False)


class VCEnhancer(commands.Cog):
    """Advanced Voice Channel Utilities: Clutch Mode, Team Codes, Vote-to-Skip, Recording Studio Sentinel."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.recent_studio_notices: Dict[int, float] = {}

    @app_commands.command(name="clutch", description="Silence squadmates in your voice channel so you can clutch the round in peace.")
    @app_commands.describe(seconds="Duration in seconds to silence the room (Default: 60s, Max: 180s)")
    async def clutch_command(self, interaction: discord.Interaction, seconds: Optional[int] = 60):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ You must be inside a voice channel to engage Clutch Mode.", ephemeral=True)

        vc = interaction.user.voice.channel
        dur = max(15, min(seconds or 60, 180))

        # Check permissions
        if not interaction.guild.me.guild_permissions.mute_members:
            return await interaction.response.send_message("⚠️ Bot requires `Mute Members` permission to activate Clutch Mode.", ephemeral=True)

        muted_members: Set[discord.Member] = set()
        for m in vc.members:
            if not m.bot and m.id != interaction.user.id and not m.voice.mute:
                try:
                    await m.edit(mute=True, reason=f"Clutch Mode engaged by {interaction.user.display_name}")
                    muted_members.add(m)
                except Exception:
                    pass

        embed = discord.Embed(
            title="🤫 ┊ 𝐂𝐋𝐔𝐓𝐂𝐇  𝐌𝐎𝐃𝐄  𝐄𝐍𝐆𝐀𝐆𝐄𝐃",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"### 🔥 **SILENCE IN THE ROOM! LET THEM COOK!** 🔥\n\n"
                f"**Clutcher:** {interaction.user.mention}\n"
                f"**Duration:** `{dur} seconds` *(or tap button when finished)*\n"
                f"**Muted Squadmates:** `{len(muted_members)}` players silenced.\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *All teammates will automatically unmute when the timer expires!*"
            ),
            color=0xFF0055
        )
        embed.set_footer(text="RAI VIBES 💗 • Competitive Gaming Engine", icon_url=config.RAI_ICON_URL)

        view = ClutchControlView(interaction.user.id, muted_members)
        await interaction.response.send_message(embed=embed, view=view)

        # Background auto-unmute task
        async def _auto_unmute():
            await asyncio.sleep(dur)
            if not view.ended:
                view.ended = True
                for m in list(muted_members):
                    try:
                        if m.voice and m.voice.mute:
                            await m.edit(mute=False, reason="Clutch Mode timer expired")
                    except Exception:
                        pass
                try:
                    await interaction.channel.send(f"⏰ **Clutch Time Expired!** Everyone in `{vc.name}` has been unmuted. GG! 🏆")
                except Exception:
                    pass

        asyncio.create_task(_auto_unmute())

    @app_commands.command(name="code", description="Drop your Free Fire, BGMI, or Custom Room code for squadmates to copy instantly.")
    @app_commands.describe(
        code="The team code or room ID (e.g. 7482910)",
        game="Select the game title",
        password="Optional room password for private custom matches"
    )
    async def code_command(
        self,
        interaction: discord.Interaction,
        code: str,
        game: Optional[str] = "Free Fire",
        password: Optional[str] = None
    ):
        clean_code = code.strip().upper()
        vc_name = interaction.user.voice.channel.name if interaction.user.voice else "Voice Lounge"
        
        embed = discord.Embed(
            title=f"⚡ ┊ {game.upper()}  𝐒𝐐𝐔𝐀𝐃  𝐈𝐍𝐕𝐈𝐓𝐄",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"### 🎮 **JOIN THE SQUAD NOW!**\n\n"
                f"🔑 **TEAM CODE / ROOM ID:**\n"
                f"```fix\n{clean_code}\n```\n"
                + (f"🔒 **PASSWORD:** ` {password} `\n\n" if password else "\n") +
                f"🎙️ **VOICE CHANNEL:** `{vc_name}`\n"
                f"👑 **HOSTED BY:** {interaction.user.mention}\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Copy the code above and paste it into your game lobby!*"
            ),
            color=0x00FF88
        )
        embed.set_footer(text="RAI VIBES 💗 • Fast Team Matchmaking", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="scrims", description="Open tournament host controls for Custom Scrims & Tournament voice channels.")
    async def scrims_command(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.mute_members and not interaction.user.guild_permissions.manage_channels:
            return await interaction.response.send_message("❌ Only tournament hosts or staff can open scrims audio controls.", ephemeral=True)

        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ You must be connected to the Scrims or Tournament voice channel.", ephemeral=True)

        vc = interaction.user.voice.channel
        view = ScrimsControlView(interaction.user.id, vc)

        embed = discord.Embed(
            title="🏆 ┊ 𝐓𝐎𝐔𝐑𝐍𝐀𝐌𝐄𝐍𝐓  𝐀𝐔𝐃𝐈𝐎  𝐃𝐄𝐂𝐊",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"### 🎙️ **Custom Scrims & Tournament Caster Controls**\n\n"
                f"📍 **Target Channel:** `{vc.name}`\n"
                f"👑 **Host / Caster:** {interaction.user.mention}\n\n"
                f"🔇 **Mute All Players:** Silence background chatter before drop/start\n"
                f"🔊 **Unmute All Players:** Open voice lines back up after GG\n\n"
                f"✦ ───────────────────────────────────── ✦"
            ),
            color=0xFFD700
        )
        embed.set_footer(text="RAI VIBES 💗 • Competitive Tournament Engine", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        """Monitors special voice channels like Recording Studio."""
        if member.bot:
            return

        # 1. Recording Studio Privacy Notification
        if after.channel and after.channel.id == RECORDING_STUDIO_ID and before.channel != after.channel:
            now = time.time()
            last_notice = self.recent_studio_notices.get(RECORDING_STUDIO_ID, 0)
            if now - last_notice > 300:  # Only post once every 5 minutes to avoid spam
                self.recent_studio_notices[RECORDING_STUDIO_ID] = now
                try:
                    embed = discord.Embed(
                        title="🔴 ┊ 𝐑𝐄𝐂𝐎𝐑𝐃𝐈𝐍𝐆  𝐒𝐓𝐔𝐃𝐈𝐎  𝐀𝐂𝐓𝐈𝐕𝐄",
                        description=(
                            f"🎬 **Welcome to the Creator Studio, {member.mention}!**\n\n"
                            f"🎥 *This channel is designated for high-quality video recording, clips, and screen captures.*\n\n"
                            f"• Keep background noise low when mics are open\n"
                            f"• Audio is running at **96 kbps Studio Bitrate** for ultra-crisp sound\n"
                            f"• Use the in-VC chat to share raw clip links and assets\n\n"
                            f"Have a great recording session! ✨"
                        ),
                        color=0xFF0000
                    )
                    embed.set_footer(text="RAI CREATIVE HUB ◈ Content Creation Engine")
                    await after.channel.send(embed=embed)
                except Exception:
                    pass

async def setup(bot: commands.Bot):
    await bot.add_cog(VCEnhancer(bot))
