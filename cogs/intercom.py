import asyncio
import os
import sys
import time
from typing import Optional, Dict, Any

import discord
from discord import app_commands
from discord.ext import commands

import config
from utils.ffmpeg_setup import get_ffmpeg_executable

class Intercom(commands.Cog):
    """Cross-Server Audio Intercom & Radio Portal between RAI FAM💗 and ABIJITH 777."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_links: Dict[int, int] = {}  # guild_id -> linked_guild_id
        self.mirrored_vcs: Dict[int, int] = {}  # guild_id -> target_vc_id

    @app_commands.command(name="intercom", description="🌐 Cross-Server Audio Portal: Bridge audio between RAI FAM💗 and ABIJITH 777!")
    @app_commands.describe(
        action="Action to perform",
        announcement="Message to broadcast across both servers simultaneously"
    )
    @app_commands.choices(
        action=[
            app_commands.Choice(name="🔗 Link Both Servers Audio (RAI FAM ↔ ABIJITH 777)", value="link"),
            app_commands.Choice(name="🔓 Unlink Cross-Server Bridge", value="unlink"),
            app_commands.Choice(name="📢 Broadcast Live Voice Announcement to Both Servers", value="broadcast"),
            app_commands.Choice(name="📊 View Portal Status", value="status")
        ]
    )
    async def intercom(
        self,
        interaction: discord.Interaction,
        action: app_commands.Choice[str],
        announcement: Optional[str] = None
    ):
        guild = interaction.guild
        if not guild:
            return await interaction.response.send_message("❌ This command must be used in a server.", ephemeral=True)

        other_guild = next((g for g in self.bot.guilds if g.id != guild.id), None)

        if action.value == "link":
            if not other_guild:
                return await interaction.response.send_message("❌ Cannot find target sister server to bridge.", ephemeral=True)

            # Find voice channel in other guild
            target_vc = next((vc for vc in other_guild.voice_channels if "COMMUNITY" in vc.name or "Music" in vc.name or "Lounge" in vc.name), None)
            if not target_vc and other_guild.voice_channels:
                target_vc = other_guild.voice_channels[0]

            self.active_links[guild.id] = other_guild.id
            self.active_links[other_guild.id] = guild.id
            if target_vc:
                self.mirrored_vcs[guild.id] = target_vc.id

            embed = discord.Embed(
                title="🌐 Cross-Server Audio Portal • ACTIVATED",
                description=(
                    f"**Audio Intercom Bridge Established!**\n\n"
                    f"🏰 **Primary Hub:** `{guild.name}`\n"
                    f"📡 **Linked Sister Server:** `{other_guild.name}` (Target VC: `{target_vc.name if target_vc else 'Default'}`)\n\n"
                    f"• Music played in this server will now mirror into `{other_guild.name}`!\n"
                    f"• Both communities are now connected on the same live radio frequency!"
                ),
                color=config.COLOR_PRIMARY
            )
            embed.set_footer(text="RAI VIBES 💗 • Cross-Server Radio Wave Network", icon_url=config.RAI_ICON_URL)
            return await interaction.response.send_message(embed=embed)

        elif action.value == "unlink":
            if guild.id in self.active_links:
                partner_id = self.active_links.pop(guild.id, None)
                if partner_id:
                    self.active_links.pop(partner_id, None)
                self.mirrored_vcs.pop(guild.id, None)

            embed = discord.Embed(
                title="🔓 Cross-Server Portal Disconnected",
                description="Audio bridge closed. Server voice channels returned to standalone mode.",
                color=config.COLOR_DARK
            )
            return await interaction.response.send_message(embed=embed)

        elif action.value == "broadcast":
            if not announcement:
                return await interaction.response.send_message("❌ Please provide an announcement text to broadcast!", ephemeral=True)

            await interaction.response.send_message(
                f"📡 **Transmitting Cross-Server Emergency Broadcast...**\n> *\"{announcement}\"*",
                ephemeral=False
            )

            # Synthesize voice announcement using edge-tts
            import edge_tts
            temp_path = f"data/temp_dj/broadcast_{int(time.time())}.mp3"
            os.makedirs("data/temp_dj", exist_ok=True)
            comm = edge_tts.Communicate(f"Attention all members in RAI FAM and Abijith 777! Broadcast from {interaction.user.display_name}: {announcement}", "en-US-ChristopherNeural")
            await comm.save(temp_path)

            ffmpeg_bin = get_ffmpeg_executable()
            connected_vcs = [vc for vc in self.bot.voice_clients if vc.is_connected()]

            for vc in connected_vcs:
                try:
                    was_p = vc.is_playing()
                    if was_p:
                        vc.pause()
                    src = discord.FFmpegPCMAudio(temp_path, executable=ffmpeg_bin)
                    vc.play(discord.PCMVolumeTransformer(src, volume=1.2))
                    await asyncio.sleep(4.0)
                    if was_p and vc.is_paused():
                        vc.resume()
                except Exception as e:
                    print(f"Broadcast error on {vc.guild.name}: {e}")

            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass

        elif action.value == "status":
            linked = guild.id in self.active_links
            partner_name = "None"
            if linked and other_guild:
                partner_name = other_guild.name

            embed = discord.Embed(
                title="🌐 Intercom Portal Status",
                color=config.COLOR_PRIMARY if linked else config.COLOR_DARK
            )
            embed.add_field(name="📡 Bridge State", value="🟢 **ONLINE**" if linked else "🔴 **OFFLINE**", inline=True)
            embed.add_field(name="🏰 Linked Partner", value=f"`{partner_name}`", inline=True)
            embed.add_field(name="⚡ Active Connected VCs", value=f"`{len(self.bot.voice_clients)} voice channel(s)`", inline=True)
            embed.set_footer(text="RAI VIBES 💗 • Multi-Server Audio Matrix", icon_url=config.RAI_ICON_URL)
            return await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Intercom(bot))
