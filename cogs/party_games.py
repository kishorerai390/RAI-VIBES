import asyncio
import time
import logging
from typing import Optional, Literal

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button

import config

logger = logging.getLogger("PartyGames")

class PartyGamesView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Play Skribbl.io", url="https://skribbl.io/", emoji="🎨", style=discord.ButtonStyle.link))
        self.add_item(Button(label="Play Gartic Phone", url="https://garticphone.com/", emoji="📱", style=discord.ButtonStyle.link))
        self.add_item(Button(label="Play Codenames", url="https://horsepaste.com/", emoji="🕵️", style=discord.ButtonStyle.link))
        self.add_item(Button(label="Jackbox.tv", url="https://jackbox.tv/", emoji="📦", style=discord.ButtonStyle.link))
        self.add_item(Button(label="Play Lichess Chess", url="https://lichess.org/", emoji="♟️", style=discord.ButtonStyle.link))


class PartyGames(commands.Cog):
    """Community Party Games & Study Pomodoro Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="party", description="Launch instant 1-click casual party games for VC or chat squads!")
    @app_commands.describe(game="Optional specific game highlight")
    async def party_launcher(
        self,
        interaction: discord.Interaction,
        game: Optional[Literal["skribbl", "gartic", "codenames", "jackbox", "chess"]] = None
    ):
        GAME_INFO = {
            "skribbl": ("🎨 Skribbl.io", "Fast-paced drawing and guessing game! Zero download required.", "https://skribbl.io/"),
            "gartic": ("📱 Gartic Phone", "Hilarious game of telephone with drawings and chaotic sentences!", "https://garticphone.com/"),
            "codenames": ("🕵️ Codenames", "Top-secret spy word deduction game with two teams.", "https://horsepaste.com/"),
            "jackbox": ("📦 Jackbox Games", "Connect to a host's lobby directly using your phone or browser.", "https://jackbox.tv/"),
            "chess": ("♟️ Lichess Online", "Challenge your friends to a clean, rapid chess match.", "https://lichess.org/"),
        }

        if game and game in GAME_INFO:
            title, desc, url = GAME_INFO[game]
            view = View()
            view.add_item(Button(label=f"Launch {title}", url=url, style=discord.ButtonStyle.link, emoji="🚀"))
            embed = discord.Embed(
                title=f"🎮 ┊ {title.upper()}",
                description=f"{desc}\n\n👉 Click the button below to open the room in your browser!",
                color=0x00FFCC
            )
        else:
            view = PartyGamesView()
            embed = discord.Embed(
                title="🎉 ┊ 𝐑𝐀𝐈  𝐅𝐀𝐌  𝐏𝐀𝐑𝐓𝐘  𝐆𝐀𝐌𝐄𝐒  𝐇𝐔𝐁",
                description=(
                    "Looking for casual fun with everyone in voice or chat?\n"
                    "Select any of the zero-install web party games below to jump in immediately!\n\n"
                    "• **🎨 Skribbl.io** — Classic multiplayer drawing & guessing\n"
                    "• **📱 Gartic Phone** — The legendary voice-call telephone game\n"
                    "• **🕵️ Codenames** — Secret agent word deduction\n"
                    "• **📦 Jackbox.tv** — Enter any streamer or friend's room code\n"
                    "• **♟️ Chess** — 1v1 tactical battle"
                ),
                color=0xFF69B4
            )
            embed.set_footer(text="RAI FAM 💗 • Game Nights • Free & Browser-Based", icon_url=config.RAI_ICON_URL)

        await interaction.response.send_message(embed=embed, view=view)

    @app_commands.command(name="pomodoro", description="Start a productivity focus Pomodoro timer with coin completion rewards!")
    @app_commands.describe(minutes="Duration of study session in minutes (default 25 min)")
    async def pomodoro_timer(self, interaction: discord.Interaction, minutes: int = 25):
        if minutes < 5 or minutes > 120:
            return await interaction.response.send_message("❌ Pomodoro timer must be between 5 and 120 minutes.", ephemeral=True)

        user = interaction.user
        end_time = int(time.time()) + (minutes * 60)

        embed_start = discord.Embed(
            title="🍅 ┊ 𝐏𝐎𝐌𝐎𝐃𝐎𝐑𝐎  𝐅𝐎𝐂𝐔𝐒  𝐒𝐄𝐒𝐒𝐈𝐎𝐍",
            description=(
                f"Concentration session started for {user.mention}!\n\n"
                f"⏱️ **Duration:** `{minutes} Minutes`\n"
                f"🎯 **Target Finish:** <t:{end_time}:R> (<t:{end_time}:t>)\n"
                f"💡 **Tip:** Mute distractions and join <#1545781986193309789> (Lo-Fi Zone) for gentle background music!\n\n"
                f"✨ *Complete the full session to earn bonus Rai Coins!*"
            ),
            color=0xFF4757
        )
        embed_start.set_footer(text="Focus Mode Activated • Work hard, play hard")
        await interaction.response.send_message(embed=embed_start)

        # Background countdown and completion notification
        async def countdown_task():
            await asyncio.sleep(minutes * 60)
            from cogs.casino import add_coins
            coin_reward = minutes * 10
            add_coins(user.id, coin_reward)

            embed_done = discord.Embed(
                title="🔔 ✦ POMODORO SESSION COMPLETE! ✦ 🔔",
                description=(
                    f"Great job {user.mention}! Your **{minutes}-minute** study focus session has ended!\n\n"
                    f"☕ **Time to take a 5-minute break:** stretch, hydrate, or rest your eyes.\n"
                    f"🪙 **Productivity Reward:** `+{coin_reward:,} Rai Coins` credited to your wallet!"
                ),
                color=0x00FF88
            )
            embed_done.set_footer(text="RAI VIBES Productivity Engine", icon_url=config.RAI_ICON_URL)
            try:
                await interaction.channel.send(content=f"🔔 {user.mention}", embed=embed_done)
            except Exception:
                pass

        asyncio.create_task(countdown_task())

async def setup(bot: commands.Bot):
    await bot.add_cog(PartyGames(bot))
