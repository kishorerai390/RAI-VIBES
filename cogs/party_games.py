import asyncio
import time
import random
import logging
from typing import Optional, Literal

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button

import config
from cogs.economy import load_economy, save_economy

logger = logging.getLogger("PartyGames")

# Official Discord Embedded Voice Activity Application IDs
DISCORD_ACTIVITIES = {
    "youtube": {
        "name": "YouTube Watch Together",
        "id": 880218394199220274,
        "emoji": "📺",
        "desc": "Watch YouTube videos together in sync inside your voice channel!"
    },
    "gartic": {
        "name": "Gartic Phone",
        "id": 1007373713693438004,
        "emoji": "📱",
        "desc": "The chaotic game of telephone with drawings and voice-call hilarity!"
    },
    "chess": {
        "name": "Chess in the Park",
        "id": 832012774040141824,
        "emoji": "♟️",
        "desc": "Challenge voice channel members to competitive 1v1 chess."
    },
    "poker": {
        "name": "Poker Night",
        "id": 755827207812677713,
        "emoji": "🃏",
        "desc": "Texas Hold'em Poker with friends directly in voice."
    },
    "golf": {
        "name": "Putt Party (Mini Golf)",
        "id": 945737672455782480,
        "emoji": "⛳",
        "desc": "Fun multiplayer mini-golf courses inside Discord."
    },
    "sketch": {
        "name": "Sketch Heads",
        "id": 902271654783242291,
        "emoji": "🎨",
        "desc": "Fast-paced Pictionary doodle and guess challenge."
    },
    "letter": {
        "name": "Letter League",
        "id": 879863686562779156,
        "emoji": "🔤",
        "desc": "Scrabble-style anagram and word-building competition."
    },
    "checkers": {
        "name": "Checkers in the Park",
        "id": 832013003968348200,
        "emoji": "⚪",
        "desc": "Classic checkers strategy matches in voice."
    },
    "bobble": {
        "name": "Bobble League",
        "id": 947957217959759964,
        "emoji": "⚽",
        "desc": "Turn-based mini soccer / table-football party match."
    }
}

SCRAMBLE_WORDS = [
    ("CYBERPUNK", "High-tech dystopian RPG or futuristic aesthetic"),
    ("VALORANT", "Tactical 5v5 hero shooter game"),
    ("MINECRAFT", "Block building and survival sandbox"),
    ("DISCORD", "The home of our server and community"),
    ("PLAYSTATION", "Popular gaming console platform"),
    ("HEADPHONES", "Essential audio hardware for gaming and music"),
    ("ALGORITHM", "Step-by-step logic in computer science"),
    ("BLUETOOTH", "Wireless short-range audio protocol"),
    ("FIREWALL", "Network security protection layer"),
    ("EQUALIZER", "Audio DSP tool to adjust sound frequencies"),
    ("TELEMETRY", "Real-time automated data and health metrics"),
    ("RADIOACTIVE", "Nuclear glow or hit rock track"),
    ("KEYBOARD", "Mechanical hardware for typists and gamers"),
    ("BROADCAST", "Transmitting audio or video to an audience"),
    ("CHAMPION", "The winner of a competitive tournament"),
    ("NIGHTCORE", "High-speed high-pitch audio remix genre"),
    ("SUBWOOFER", "Speaker driver dedicated to deep bass frequencies"),
    ("MICROPHONE", "Audio capture device for voice chat and streaming")
]


class PartyGamesView(View):
    """Persistent 1-click links for zero-install web party games."""
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="Play Skribbl.io", url="https://skribbl.io/", emoji="🎨", style=discord.ButtonStyle.link))
        self.add_item(Button(label="Play Gartic Phone", url="https://garticphone.com/", emoji="📱", style=discord.ButtonStyle.link))
        self.add_item(Button(label="Play Codenames", url="https://horsepaste.com/", emoji="🕵️", style=discord.ButtonStyle.link))
        self.add_item(Button(label="Jackbox.tv", url="https://jackbox.tv/", emoji="📦", style=discord.ButtonStyle.link))
        self.add_item(Button(label="Play Lichess Chess", url="https://lichess.org/", emoji="♟️", style=discord.ButtonStyle.link))


class ActivityLinkView(View):
    """View with a direct Discord embedded activity launcher button."""
    def __init__(self, invite_url: str, app_name: str, emoji: str = "🚀"):
        super().__init__(timeout=300)
        self.add_item(Button(label=f"Join {app_name}", url=invite_url, emoji=emoji, style=discord.ButtonStyle.link))


def award_minigame_reward(user_id: int, coins: int):
    """Credits economy coins directly to minigame winners."""
    try:
        data = load_economy()
        uid = str(user_id)
        if uid not in data:
            data[uid] = {"coins": 200, "last_daily": 0, "streak": 0, "rep": 0, "last_rep": 0}
        data[uid]["coins"] = data[uid].get("coins", 0) + coins
        save_economy(data)
    except Exception as e:
        logger.warning(f"Could not award minigame reward: {e}")


class PartyGames(commands.Cog):
    """Community Party Games, Discord Voice Activities & Interactive Chat Minigames."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Active minigame locks per channel to prevent overlapping races
        self.active_channels = set()

    # =========================================================================
    # SLASH COMMAND GROUP: /party
    # =========================================================================
    party_group = app_commands.Group(name="party", description="Casual party games, voice activities, and chat minigames.")

    @party_group.command(name="hub", description="Open the 1-click casual web party games launcher station.")
    async def party_hub_cmd(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎉 ┊ 𝐑𝐀𝐈  𝐅𝐀Ｍ  𝐏𝐀𝐑𝐓𝐘  𝐆𝐀Ｍ𝐄𝐒  𝐇𝐔𝐁",
            description=(
                "Looking for quick casual fun with everyone in voice or chat?\n"
                "Select any of the zero-install web party games below to jump in immediately!\n\n"
                "• **🎨 Skribbl.io** — Classic multiplayer drawing & guessing\n"
                "• **📱 Gartic Phone** — The legendary voice-call telephone game\n"
                "• **🕵️ Codenames** — Secret agent word deduction\n"
                "• **📦 Jackbox.tv** — Enter any streamer or friend's room code\n"
                "• **♟️ Chess** — 1v1 tactical battle\n\n"
                "💡 *Want games directly inside Discord Voice? Use `/party activity`!*"
            ),
            color=0xFF69B4
        )
        embed.set_footer(text="RAI FAM 💗 • Game Nights • Free & Browser-Based", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, view=PartyGamesView())

    @party_group.command(name="activity", description="Launch an official Discord embedded activity inside your voice channel!")
    @app_commands.describe(game="Select the Discord Voice Activity to start")
    @app_commands.choices(game=[
        app_commands.Choice(name="📺 YouTube Watch Together", value="youtube"),
        app_commands.Choice(name="📱 Gartic Phone (In-Voice)", value="gartic"),
        app_commands.Choice(name="♟️ Chess in the Park", value="chess"),
        app_commands.Choice(name="🃏 Poker Night (Texas Hold'em)", value="poker"),
        app_commands.Choice(name="⛳ Putt Party (Mini Golf)", value="golf"),
        app_commands.Choice(name="🎨 Sketch Heads (Pictionary)", value="sketch"),
        app_commands.Choice(name="🔤 Letter League (Scrabble)", value="letter"),
        app_commands.Choice(name="⚪ Checkers in the Park", value="checkers"),
        app_commands.Choice(name="⚽ Bobble League (Table Soccer)", value="bobble"),
    ])
    async def party_activity_cmd(self, interaction: discord.Interaction, game: app_commands.Choice[str]):
        member = interaction.user
        if not isinstance(member, discord.Member) or not member.voice or not member.voice.channel:
            return await interaction.response.send_message(
                "❌ **You must be in a Voice Channel** to launch a Discord Activity! Join a voice lounge first.",
                ephemeral=True
            )

        vc = member.voice.channel
        act_info = DISCORD_ACTIVITIES.get(game.value)
        if not act_info:
            return await interaction.response.send_message("❌ Invalid activity selected.", ephemeral=True)

        await interaction.response.defer()

        try:
            # Create embedded application invite linking directly into the voice channel
            invite = await vc.create_invite(
                target_type=discord.InviteTarget.embedded_application,
                target_application_id=act_info["id"],
                max_age=3600,
                reason=f"[Party Games] Launched {act_info['name']} by {member.name}"
            )

            embed = discord.Embed(
                title=f"{act_info['emoji']} {act_info['name']} • Voice Activity",
                description=(
                    f"**Room:** {vc.mention}\n"
                    f"**Host:** {member.mention}\n\n"
                    f"{act_info['desc']}\n\n"
                    f"👉 **Click the button below to start or join the activity!**"
                ),
                color=0x2ED573
            )
            embed.set_footer(text="Discord Embedded Activities • Powered by RAI VIBES 💗", icon_url=config.RAI_ICON_URL)
            view = ActivityLinkView(invite.url, act_info["name"], emoji=act_info["emoji"])

            await interaction.followup.send(embed=embed, view=view)
        except Exception as e:
            logger.error(f"Error creating Discord Activity invite: {e}")
            await interaction.followup.send(
                f"⚠️ Could not launch activity in {vc.mention}. Please ensure the bot has **Create Invite** permissions in that channel.",
                ephemeral=True
            )

    @party_group.command(name="math", description="Start a fast mental arithmetic race in chat with Rai Coin rewards!")
    async def party_math_cmd(self, interaction: discord.Interaction):
        chan_id = interaction.channel_id
        if chan_id in self.active_channels:
            return await interaction.response.send_message("⏳ A party minigame is already running in this channel!", ephemeral=True)

        self.active_channels.add(chan_id)

        # Generate a clean arithmetic challenge
        ops = ["+", "-", "*"]
        op = random.choice(ops)
        if op == "+":
            a = random.randint(25, 450)
            b = random.randint(25, 450)
            ans = a + b
        elif op == "-":
            a = random.randint(100, 600)
            b = random.randint(20, a)
            ans = a - b
        else:
            a = random.randint(6, 25)
            b = random.randint(4, 18)
            ans = a * b

        bounty = 250
        embed = discord.Embed(
            title="⚡ ┊ 𝐅𝐀𝐒𝐓  𝐌𝐀𝐓𝐇  𝐑𝐀𝐂𝐄",
            description=(
                "First member to type the correct answer in chat wins!\n\n"
                f"### 🧮 `{a} {op} {b} = ?`\n\n"
                f"💰 **Reward:** `+{bounty:,} Rai Coins`\n"
                f"⏱️ **Time Limit:** `25 Seconds`"
            ),
            color=0xFFA502
        )
        embed.set_footer(text="Type your answer directly into this channel!", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

        def check(m: discord.Message):
            if m.channel.id != chan_id or m.author.bot:
                return False
            cleaned = m.content.strip()
            return cleaned.isdigit() and int(cleaned) == ans

        try:
            winner_msg = await self.bot.wait_for("message", check=check, timeout=25.0)
            winner = winner_msg.author
            award_minigame_reward(winner.id, bounty)

            win_embed = discord.Embed(
                title="🏆 FAST MATH CHAMPION!",
                description=(
                    f"🎉 Congratulations {winner.mention}!\n\n"
                    f"• **Correct Answer:** `{ans}`\n"
                    f"• **Prize:** `+{bounty:,} Rai Coins` credited to your balance!"
                ),
                color=0x2ED573
            )
            win_embed.set_thumbnail(url=winner.display_avatar.url)
            await interaction.channel.send(embed=win_embed)
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⌛ Time's Up!",
                description=f"No one solved the equation in time!\n• The answer was: **`{ans}`**",
                color=config.COLOR_DANGER
            )
            await interaction.channel.send(embed=timeout_embed)
        finally:
            self.active_channels.discard(chan_id)

    @party_group.command(name="scramble", description="Unscramble the mystery gaming/tech word for Rai Coins!")
    async def party_scramble_cmd(self, interaction: discord.Interaction):
        chan_id = interaction.channel_id
        if chan_id in self.active_channels:
            return await interaction.response.send_message("⏳ A party minigame is already running in this channel!", ephemeral=True)

        self.active_channels.add(chan_id)

        target_word, hint = random.choice(SCRAMBLE_WORDS)
        letters = list(target_word)
        scrambled = letters.copy()
        while "".join(scrambled) == target_word and len(target_word) > 2:
            random.shuffle(scrambled)
        scrambled_str = " ".join(scrambled)

        bounty = 300
        embed = discord.Embed(
            title="🧩 ┊ 𝐖𝐎𝐑𝐃  𝐒𝐂𝐑𝐀𝐌𝐁𝐋𝐄",
            description=(
                "Unscramble the letters to reveal the mystery word!\n\n"
                f"### 🔠 `{scrambled_str}`\n\n"
                f"💡 **Hint:** *{hint}*\n"
                f"💰 **Reward:** `+{bounty:,} Rai Coins`\n"
                f"⏱️ **Time Limit:** `30 Seconds`"
            ),
            color=0x00D2D3
        )
        embed.set_footer(text="Type the unscrambled word directly into this channel!", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

        def check(m: discord.Message):
            if m.channel.id != chan_id or m.author.bot:
                return False
            return m.content.strip().upper() == target_word

        try:
            winner_msg = await self.bot.wait_for("message", check=check, timeout=30.0)
            winner = winner_msg.author
            award_minigame_reward(winner.id, bounty)

            win_embed = discord.Embed(
                title="🧩 PUZZLE SOLVED!",
                description=(
                    f"🎉 Great job {winner.mention}!\n\n"
                    f"• **Mystery Word:** **`{target_word}`**\n"
                    f"• **Prize:** `+{bounty:,} Rai Coins` added to your vault!"
                ),
                color=0x2ED573
            )
            win_embed.set_thumbnail(url=winner.display_avatar.url)
            await interaction.channel.send(embed=win_embed)
        except asyncio.TimeoutError:
            timeout_embed = discord.Embed(
                title="⌛ Time's Up!",
                description=f"Nobody solved the word puzzle!\n• The mystery word was: **`{target_word}`**",
                color=config.COLOR_DANGER
            )
            await interaction.channel.send(embed=timeout_embed)
        finally:
            self.active_channels.discard(chan_id)

    # Prefix command fallback
    @commands.command(name="party")
    async def party_prefix_cmd(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🎉 ┊ 𝐑𝐀𝐈  𝐅𝐀Ｍ  𝐏𝐀𝐑𝐓Ｙ  𝐆𝐀𝐌𝐄𝐒  𝐇𝐔𝐁",
            description=(
                "Looking for quick casual fun with everyone in voice or chat?\n"
                "Select any of the zero-install web party games below to jump in immediately!\n\n"
                "• **🎨 Skribbl.io** — Classic multiplayer drawing & guessing\n"
                "• **📱 Gartic Phone** — The legendary voice-call telephone game\n"
                "• **🕵️ Codenames** — Secret agent word deduction\n"
                "• **📦 Jackbox.tv** — Enter any streamer or friend's room code\n"
                "• **♟️ Chess** — 1v1 tactical battle\n\n"
                "💡 *Use `/party activity`, `/party math`, or `/party scramble` for interactive games!*"
            ),
            color=0xFF69B4
        )
        embed.set_footer(text="RAI FAM 💗 • Game Nights • Free & Browser-Based", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed, view=PartyGamesView())


async def setup(bot: commands.Bot):
    await bot.add_cog(PartyGames(bot))
