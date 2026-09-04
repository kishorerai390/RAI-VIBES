import json
import random
import time
from pathlib import Path
import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, Any

import config

ECONOMY_FILE = Path(__file__).resolve().parent.parent / "data" / "economy.json"

def load_economy() -> Dict[str, Dict[str, Any]]:
    if not ECONOMY_FILE.exists():
        ECONOMY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)
        return {}
    try:
        with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_economy(data: dict):
    ECONOMY_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def get_user_data(data: dict, user_id: str) -> dict:
    if user_id not in data:
        data[user_id] = {
            "coins": 200,
            "last_daily": 0,
            "wins": 0,
            "losses": 0
        }
    return data[user_id]


class Economy(commands.Cog):
    """Apex Economy, Daily Rewards & Chat Minigames."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="daily", description="Claim your daily Apex Coins reward (200-500 coins).")
    async def daily(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        data = load_economy()
        user = get_user_data(data, user_id)

        now = time.time()
        cooldown = 86400  # 24 hours
        if now - user["last_daily"] < cooldown:
            remaining = int(cooldown - (now - user["last_daily"]))
            hours, rem = divmod(remaining, 3600)
            mins, _ = divmod(rem, 60)
            return await ctx.send(f"⏳ You already claimed your daily reward! Come back in **{hours}h {mins}m**.", ephemeral=True)

        reward = random.randint(200, 500)
        user["coins"] += reward
        user["last_daily"] = now
        save_economy(data)

        embed = discord.Embed(
            title="⚡ Daily Apex Reward Claimed!",
            description=f"You received **+{reward} Apex Coins** 🪙!\n**Current Balance:** `{user['coins']} Coins`",
            color=config.COLOR_GOLD
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="RAI VIBES 💗 Economy", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="balance", aliases=["bal", "coins"], description="Check your Apex Coins wallet.")
    async def balance(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        data = load_economy()
        user = get_user_data(data, str(target.id))

        embed = discord.Embed(
            title=f"🪙 {target.display_name}'s Apex Wallet",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="💰 Coins Balance", value=f"`{user['coins']} Coins`", inline=True)
        embed.add_field(name="🏆 Minigame Stats", value=f"Wins: `{user['wins']}` | Losses: `{user['losses']}`", inline=True)
        embed.set_footer(text="Play minigames with /coinflip and /dice", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="coinflip", aliases=["cf"], description="Bet Apex Coins on a coin toss (Heads or Tails).")
    @app_commands.describe(choice="Choose heads or tails", bet="Amount of coins to bet")
    @app_commands.choices(choice=[
        app_commands.Choice(name="Heads", value="heads"),
        app_commands.Choice(name="Tails", value="tails")
    ])
    async def coinflip(self, ctx: commands.Context, choice: app_commands.Choice[str], bet: int):
        if bet <= 0:
            return await ctx.send("❌ Bet must be greater than 0.", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_economy()
        user = get_user_data(data, user_id)

        if user["coins"] < bet:
            return await ctx.send(f"❌ You only have **{user['coins']} coins** in your wallet.", ephemeral=True)

        result = random.choice(["heads", "tails"])
        won = (result == choice.value)

        if won:
            user["coins"] += bet
            user["wins"] += 1
            msg = f"🎉 **It landed on {result.upper()}!** You won **+{bet} Coins** 🪙!\nNew Balance: `{user['coins']} Coins`"
            col = config.COLOR_SUCCESS
        else:
            user["coins"] -= bet
            user["losses"] += 1
            msg = f"💥 **It landed on {result.upper()}!** You lost **-{bet} Coins**.\nNew Balance: `{user['coins']} Coins`"
            col = config.COLOR_ERROR

        save_economy(data)
        embed = discord.Embed(title="🪙 Coinflip Result", description=msg, color=col)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="dice", description="Roll against the bot for a chance to double your bet!")
    @app_commands.describe(bet="Amount of coins to bet")
    async def dice(self, ctx: commands.Context, bet: int):
        if bet <= 0:
            return await ctx.send("❌ Bet must be greater than 0.", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_economy()
        user = get_user_data(data, user_id)

        if user["coins"] < bet:
            return await ctx.send(f"❌ You only have **{user['coins']} coins**.", ephemeral=True)

        user_roll = random.randint(1, 6) + random.randint(1, 6)
        bot_roll = random.randint(1, 6) + random.randint(1, 6)

        if user_roll > bot_roll:
            user["coins"] += bet
            user["wins"] += 1
            embed = discord.Embed(
                title="🎲 Dice Battle: You Won!",
                description=f"🎲 **Your Roll:** `{user_roll}`\n🤖 **Bot Roll:** `{bot_roll}`\n\n🎉 You won **+{bet} Coins**! Balance: `{user['coins']}`",
                color=config.COLOR_SUCCESS
            )
        elif user_roll < bot_roll:
            user["coins"] -= bet
            user["losses"] += 1
            embed = discord.Embed(
                title="🎲 Dice Battle: You Lost!",
                description=f"🎲 **Your Roll:** `{user_roll}`\n🤖 **Bot Roll:** `{bot_roll}`\n\n💥 You lost **-{bet} Coins**. Balance: `{user['coins']}`",
                color=config.COLOR_ERROR
            )
        else:
            embed = discord.Embed(
                title="🎲 Dice Battle: Draw!",
                description=f"🎲 Both rolled `{user_roll}`! Your bet was returned.",
                color=config.COLOR_GOLD
            )

        save_economy(data)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
