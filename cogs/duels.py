import time
import random
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, button
from typing import Optional, Dict

import config
from cogs.economy import get_user_data, update_user_coins, OWNER_ID

# =====================================================================
# 1v1 QUICK DRAW DUEL
# =====================================================================
class QuickDrawFireButton(Button):
    def __init__(self, duel_view):
        super().__init__(
            label="💥 FIRE!",
            style=discord.ButtonStyle.danger,
            emoji="🔫",
            custom_id="duel_btn_fire"
        )
        self.duel_view = duel_view

    async def callback(self, interaction: discord.Interaction):
        view = self.duel_view
        if interaction.user.id not in (view.p1.id, view.p2.id):
            return await interaction.response.send_message("❌ You are not in this duel!", ephemeral=True)

        if view.winner:
            return await interaction.response.send_message("⏳ The duel has already concluded!", ephemeral=True)

        # Record winner
        view.winner = interaction.user
        loser = view.p2 if view.winner.id == view.p1.id else view.p1
        reaction_ms = int((time.time() - view.fire_time) * 1000)

        # Award pot
        pot = view.bet * 2
        update_user_coins(view.winner.id, pot)

        embed = discord.Embed(
            title="🤠 QUICK-DRAW DUEL • SHOT FIRED!",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"💥 **{view.winner.mention}** drew their weapon first in **`{reaction_ms}ms`**!\n\n"
                f"🏆 **Winner:** {view.winner.mention} *(+{pot:,} Coins pot)*\n"
                f"💀 **Defeated:** {loser.mention} *(-{view.bet:,} Coins)*\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"⚡ *Lightning-fast reflexes! Challenge another squadmate with `/duel`!*"
            ),
            color=0xF1C40F
        )
        embed.set_thumbnail(url=view.winner.display_avatar.url)
        embed.set_footer(text="RAI VIBES 💗 • Duel Arena", icon_url=config.RAI_ICON_URL)

        for item in self.view.children:
            item.disabled = True
        await interaction.response.edit_message(embed=embed, view=self.view)


class QuickDrawDuelView(View):
    def __init__(self, p1: discord.Member, p2: discord.Member, bet: int):
        super().__init__(timeout=60)
        self.p1 = p1
        self.p2 = p2
        self.bet = bet
        self.accepted = False
        self.winner = None
        self.fire_time = 0.0

    @button(label="Accept Duel", style=discord.ButtonStyle.success, emoji="⚔️", custom_id="duel_btn_accept")
    async def accept(self, interaction: discord.Interaction, btn: Button):
        if interaction.user.id != self.p2.id:
            return await interaction.response.send_message(f"❌ Only {self.p2.mention} can accept this duel.", ephemeral=True)

        # Validate wallet balances
        p1_bal = get_user_data(self.p1.id).get("coins", 0)
        p2_bal = get_user_data(self.p2.id).get("coins", 0)

        if self.bet > 0:
            if p1_bal < self.bet and self.p1.id != OWNER_ID:
                return await interaction.response.send_message(f"❌ {self.p1.mention} no longer has enough coins ({self.bet:,}c).", ephemeral=True)
            if p2_bal < self.bet and self.p2.id != OWNER_ID:
                return await interaction.response.send_message(f"❌ You do not have enough coins ({self.bet:,}c) to accept.", ephemeral=True)

            # Deduct bets into pot
            update_user_coins(self.p1.id, -self.bet)
            update_user_coins(self.p2.id, -self.bet)

        self.accepted = True
        self.clear_items()

        # Step 1: Countdown
        embed = discord.Embed(
            title="🤠 WILD WEST QUICK-DRAW DUEL",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"⚔️ **{self.p1.mention}** VS **{self.p2.mention}**\n"
                f"💰 **Total Pot:** `{self.bet * 2:,} Coins`\n\n"
                f"Get ready... Hands on holsters!\n"
                f"Click **FIRE** the instant it appears!\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"⏳ *Counting down...*"
            ),
            color=0xE67E22
        )
        await interaction.response.edit_message(embed=embed, view=self)

        # Random delay between 2.0 and 4.5 seconds
        await asyncio.sleep(random.uniform(2.0, 4.5))

        if self.winner:
            return

        self.fire_time = time.time()
        self.add_item(QuickDrawFireButton(self))

        draw_embed = discord.Embed(
            title="💥 DRAW! FIRE NOW!",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"🚨 **CLICK THE BUTTON BELOW NOW!** 🚨\n\n"
                f"✦ ───────────────────────────────────── ✦"
            ),
            color=0xE74C3C
        )
        await interaction.message.edit(embed=draw_embed, view=self)

    @button(label="Decline", style=discord.ButtonStyle.danger, emoji="🏳️", custom_id="duel_btn_decline")
    async def decline(self, interaction: discord.Interaction, btn: Button):
        if interaction.user.id != self.p2.id:
            return await interaction.response.send_message("❌ Only the challenged player can decline.", ephemeral=True)

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(
            content=f"🏳️ {self.p2.mention} declined the duel challenge.",
            embed=None,
            view=self
        )


# =====================================================================
# ROCK PAPER SCISSORS DUEL
# =====================================================================
class RPSChoiceButton(Button):
    def __init__(self, choice: str, emoji: str):
        super().__init__(label=choice.capitalize(), emoji=emoji, style=discord.ButtonStyle.secondary)
        self.choice = choice

    async def callback(self, interaction: discord.Interaction):
        view: RPSDuelView = self.view
        uid = interaction.user.id
        if uid not in (view.p1.id, view.p2.id):
            return await interaction.response.send_message("❌ You are not playing in this RPS match.", ephemeral=True)

        if uid in view.choices:
            return await interaction.response.send_message(f"⚠️ You already picked **{view.choices[uid].capitalize()}**! Waiting for opponent...", ephemeral=True)

        view.choices[uid] = self.choice
        await interaction.response.send_message(f"✅ You chose **{self.choice.capitalize()}**! Locked in.", ephemeral=True)

        if len(view.choices) == 2:
            await view.resolve_match()


class RPSDuelView(View):
    def __init__(self, p1: discord.Member, p2: discord.Member, bet: int, message: Optional[discord.Message] = None):
        super().__init__(timeout=60)
        self.p1 = p1
        self.p2 = p2
        self.bet = bet
        self.message = message
        self.choices: Dict[int, str] = {}

        self.add_item(RPSChoiceButton("rock", "🪨"))
        self.add_item(RPSChoiceButton("paper", "📄"))
        self.add_item(RPSChoiceButton("scissors", "✂️"))

    async def resolve_match(self):
        c1 = self.choices[self.p1.id]
        c2 = self.choices[self.p2.id]

        emojis = {"rock": "🪨", "paper": "📄", "scissors": "✂️"}

        if c1 == c2:
            # Tie: refund bets
            if self.bet > 0:
                update_user_coins(self.p1.id, self.bet)
                update_user_coins(self.p2.id, self.bet)
            result_txt = f"🤝 **It's a TIE!** Both players chose **{emojis[c1]} {c1.capitalize()}**.\nBets of `{self.bet:,}c` refunded!"
            winner = None
            color = 0x95A5A6
        elif (c1 == "rock" and c2 == "scissors") or (c1 == "paper" and c2 == "rock") or (c1 == "scissors" and c2 == "paper"):
            winner = self.p1
            loser = self.p2
            pot = self.bet * 2
            if self.bet > 0:
                update_user_coins(self.p1.id, pot)
            result_txt = (
                f"🏆 **{winner.mention} WINS!**\n\n"
                f"• {self.p1.mention}: **{emojis[c1]} {c1.capitalize()}**\n"
                f"• {self.p2.mention}: **{emojis[c2]} {c2.capitalize()}**\n\n"
                f"💰 **Prize Awarded:** `+{pot:,} Coins`"
            )
            color = 0x2ECC71
        else:
            winner = self.p2
            loser = self.p1
            pot = self.bet * 2
            if self.bet > 0:
                update_user_coins(self.p2.id, pot)
            result_txt = (
                f"🏆 **{winner.mention} WINS!**\n\n"
                f"• {self.p2.mention}: **{emojis[c2]} {c2.capitalize()}**\n"
                f"• {self.p1.mention}: **{emojis[c1]} {c1.capitalize()}**\n\n"
                f"💰 **Prize Awarded:** `+{pot:,} Coins`"
            )
            color = 0x2ECC71

        embed = discord.Embed(
            title="✂️ ROCK-PAPER-SCISSORS DUEL RESULT",
            description=f"✦ ───────────────────────────────────── ✦\n\n{result_txt}\n\n✦ ───────────────────────────────────── ✦",
            color=color
        )
        if winner:
            embed.set_thumbnail(url=winner.display_avatar.url)
        embed.set_footer(text="RAI VIBES 💗 • Duel Arena", icon_url=config.RAI_ICON_URL)

        for item in self.children:
            item.disabled = True

        if self.message:
            await self.message.edit(embed=embed, view=self)


class RPSLobbyView(View):
    def __init__(self, p1: discord.Member, p2: discord.Member, bet: int):
        super().__init__(timeout=60)
        self.p1 = p1
        self.p2 = p2
        self.bet = bet

    @button(label="Accept RPS Challenge", style=discord.ButtonStyle.success, emoji="✂️")
    async def accept_rps(self, interaction: discord.Interaction, btn: Button):
        if interaction.user.id != self.p2.id:
            return await interaction.response.send_message(f"❌ Only {self.p2.mention} can accept.", ephemeral=True)

        p1_bal = get_user_data(self.p1.id).get("coins", 0)
        p2_bal = get_user_data(self.p2.id).get("coins", 0)

        if self.bet > 0:
            if p1_bal < self.bet and self.p1.id != OWNER_ID:
                return await interaction.response.send_message(f"❌ {self.p1.mention} lacks `{self.bet:,}` Coins.", ephemeral=True)
            if p2_bal < self.bet and self.p2.id != OWNER_ID:
                return await interaction.response.send_message(f"❌ You lack `{self.bet:,}` Coins.", ephemeral=True)

            update_user_coins(self.p1.id, -self.bet)
            update_user_coins(self.p2.id, -self.bet)

        embed = discord.Embed(
            title="✂️ ROCK PAPER SCISSORS • MAKE YOUR CHOICE!",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"⚔️ **{self.p1.mention}** VS **{self.p2.mention}**\n"
                f"💰 **Total Pot:** `{self.bet * 2:,} Coins`\n\n"
                f"Click your choice below! Your selection is hidden until both players have picked.\n\n"
                f"✦ ───────────────────────────────────── ✦"
            ),
            color=0x3498DB
        )
        rps_view = RPSDuelView(self.p1, self.p2, self.bet, interaction.message)
        await interaction.response.edit_message(embed=embed, view=rps_view)

    @button(label="Decline", style=discord.ButtonStyle.danger, emoji="🏳️")
    async def decline(self, interaction: discord.Interaction, btn: Button):
        if interaction.user.id != self.p2.id:
            return await interaction.response.send_message("❌ Only the challenged player can decline.", ephemeral=True)

        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(content=f"🏳️ {self.p2.mention} declined the RPS challenge.", embed=None, view=self)


# =====================================================================
# DUELS COG
# =====================================================================
class Duels(commands.Cog):
    """Competitive 1v1 PvP Gaming & Reaction Duels."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.active_typeraces: Dict[int, str] = {}

    @app_commands.command(name="duel", description="Challenge another squadmate to a high-noon Quick-Draw reaction contest!")
    @app_commands.describe(opponent="The member you want to challenge", bet="Coins to wager on the duel (Default: 50)")
    async def duel_command(self, interaction: discord.Interaction, opponent: discord.Member, bet: Optional[int] = 50):
        if opponent.bot or opponent.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot duel bots or yourself!", ephemeral=True)

        wager = max(0, bet or 50)
        p1_bal = get_user_data(interaction.user.id).get("coins", 0)
        if p1_bal < wager and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(f"❌ You do not have `{wager:,}` Coins to wager.", ephemeral=True)

        embed = discord.Embed(
            title="⚔️ QUICK-DRAW DUEL CHALLENGE",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"{interaction.user.mention} challenged {opponent.mention} to a **Quick-Draw Duel**!\n\n"
                f"💰 **Wager per player:** `{wager:,} Coins`\n"
                f"🏆 **Winner takes:** `{wager * 2:,} Coins`\n\n"
                f"👉 *{opponent.mention}, click Accept below to draw weapons!*"
            ),
            color=0xE67E22
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI VIBES 💗 • Duel Arena", icon_url=config.RAI_ICON_URL)

        view = QuickDrawDuelView(interaction.user, opponent, wager)
        await interaction.response.send_message(content=f"{opponent.mention}", embed=embed, view=view)

    @app_commands.command(name="rps", description="Challenge a squadmate to a Rock-Paper-Scissors match with coins on the line!")
    @app_commands.describe(opponent="The member you want to challenge", bet="Coins to wager (Default: 50)")
    async def rps_command(self, interaction: discord.Interaction, opponent: discord.Member, bet: Optional[int] = 50):
        if opponent.bot or opponent.id == interaction.user.id:
            return await interaction.response.send_message("❌ You cannot challenge bots or yourself!", ephemeral=True)

        wager = max(0, bet or 50)
        p1_bal = get_user_data(interaction.user.id).get("coins", 0)
        if p1_bal < wager and interaction.user.id != OWNER_ID:
            return await interaction.response.send_message(f"❌ You do not have `{wager:,}` Coins to wager.", ephemeral=True)

        embed = discord.Embed(
            title="✂️ ROCK-PAPER-SCISSORS CHALLENGE",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"{interaction.user.mention} challenged {opponent.mention} to an **RPS Showdown**!\n\n"
                f"💰 **Wager:** `{wager:,} Coins` each (`{wager * 2:,}c` pot)\n\n"
                f"👉 *{opponent.mention}, click Accept below to play!*"
            ),
            color=0x3498DB
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI VIBES 💗 • Duel Arena", icon_url=config.RAI_ICON_URL)

        view = RPSLobbyView(interaction.user, opponent, wager)
        await interaction.response.send_message(content=f"{opponent.mention}", embed=embed, view=view)

    @app_commands.command(name="typerace", description="Start a lightning-fast typing race challenge in this channel!")
    async def typerace_command(self, interaction: discord.Interaction):
        sentences = [
            "the quick brown fox jumps over the lazy dog",
            "hyper speed audio vibes in the cyber lounge",
            "midnight melodies and aesthetic rain soundscapes",
            "legendary victory belongs to the swift and bold",
            "supreme energy beats in the official rai family",
            "tokyo drift bass drop shakes the entire arena"
        ]
        chosen = random.choice(sentences)
        self.active_typeraces[interaction.channel_id] = chosen

        embed = discord.Embed(
            title="⌨️ LIGHTNING TYPE RACE CHALLENGE!",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"First person to type the exact text below wins **`+100 Coins`**!\n\n"
                f"```text\n{chosen}\n```\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Type it directly in chat as fast as you can!*"
            ),
            color=0x00F5D4
        )
        embed.set_footer(text="RAI VIBES 💗 • Typing Arena", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        target_phrase = self.active_typeraces.get(message.channel.id)
        if target_phrase and message.content.strip().lower() == target_phrase.lower():
            del self.active_typeraces[message.channel.id]
            new_bal = update_user_coins(message.author.id, 100)
            bal_str = "∞ (Owner Vault)" if message.author.id == OWNER_ID else f"{new_bal:,} Coins"

            embed = discord.Embed(
                title="⚡ TYPE RACE CHAMPION!",
                description=(
                    f"🎉 {message.author.mention} was the fastest typist!\n\n"
                    f"💰 **Reward:** `+100 Coins`\n"
                    f"👛 **New Balance:** `{bal_str}`"
                ),
                color=0x2ECC71
            )
            embed.set_thumbnail(url=message.author.display_avatar.url)
            embed.set_footer(text="RAI VIBES 💗 • Typing Arena", icon_url=config.RAI_ICON_URL)
            await message.channel.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Duels(bot))
