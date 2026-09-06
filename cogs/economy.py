import json
import random
import time
from pathlib import Path
import discord
from discord.ext import commands
from discord import app_commands
from typing import Dict, Any, Optional

import config

ECONOMY_FILE = Path(__file__).resolve().parent.parent / "data" / "economy.json"

SHOP_ITEMS = {
    "dj_pass": {
        "name": "🎧 DJ Priority Pass (24h)",
        "price": 500,
        "description": "Gain the @DJ role to control music queues and audio filters for 24 hours.",
        "role_id": 1545834928221069522
    },
    "vip_pink": {
        "name": "🌸 Sakura VIP Role (7 Days)",
        "price": 1000,
        "description": "Exclusive Sakura VIP status in chat and voice.",
        "role_id": 1545494584203673740
    },
    "booster_badge": {
        "name": "💎 Double XP Booster (24h)",
        "price": 750,
        "description": "Earn 2x XP from chatting and voice room activity.",
        "role_id": None
    },
    "custom_title": {
        "name": "🏷️ Custom Voice Title Ticket",
        "price": 300,
        "description": "Unlock infinite voice room status & title customizations.",
        "role_id": None
    }
}

WORK_JOBS = [
    ("🎧 Hosted a live Lo-Fi session on the DJ Stage", 150, 300),
    ("🍹 Mixed custom Sakura Cocktails at the RAI FAM Lounge", 120, 250),
    ("🛡️ Helped moderate the chat and kept the server safe", 180, 320),
    ("🍿 Hosted a movie watch party in Cinema Theater 1", 140, 280),
    ("🎮 Won a Free Fire custom room match with the squad", 200, 400),
    ("🎨 Created custom anime fanart for the community", 160, 310),
    ("🚀 Successfully bumped the server on Disboard", 150, 250),
]

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
            "last_work": 0,
            "wins": 0,
            "losses": 0,
            "inventory": []
        }
    # Backward compatibility
    if "inventory" not in data[user_id]:
        data[user_id]["inventory"] = []
    if "last_work" not in data[user_id]:
        data[user_id]["last_work"] = 0
    return data[user_id]


class Economy(commands.Cog):
    """RAI Sakura Economy, Daily Rewards, Casino Minigames & Arcade Store."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(name="daily", description="Claim your daily Sakura Coins reward (200-500 coins).")
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
            title="🌸 Daily Sakura Coins Claimed!",
            description=f"You received **+{reward} Sakura Coins** 🪙!\n**Current Balance:** `{user['coins']} Coins`",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="RAI VIBES 💗 Economy", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="work", description="Work a job in RAI FAM to earn extra Sakura Coins (1h cooldown).")
    async def work(self, ctx: commands.Context):
        user_id = str(ctx.author.id)
        data = load_economy()
        user = get_user_data(data, user_id)

        now = time.time()
        cooldown = 3600  # 1 hour
        if now - user.get("last_work", 0) < cooldown:
            remaining = int(cooldown - (now - user["last_work"]))
            mins, secs = divmod(remaining, 60)
            return await ctx.send(f"⏳ You are resting from your shift! Work again in **{mins}m {secs}s**.", ephemeral=True)

        job_desc, min_pay, max_pay = random.choice(WORK_JOBS)
        earned = random.randint(min_pay, max_pay)
        user["coins"] += earned
        user["last_work"] = now
        save_economy(data)

        embed = discord.Embed(
            title="💼 Shift Completed!",
            description=f"{job_desc}\n\n💵 **Earned:** `+{earned} Sakura Coins 🪙`\n💰 **New Balance:** `{user['coins']} Coins`",
            color=config.COLOR_SUCCESS
        )
        embed.set_footer(text="RAI VIBES 💗 Work Engine", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="balance", aliases=["bal", "coins"], description="Check your Sakura Coins wallet.")
    async def balance(self, ctx: commands.Context, member: Optional[discord.Member] = None):
        target = member or ctx.author
        data = load_economy()
        user = get_user_data(data, str(target.id))

        embed = discord.Embed(
            title=f"🌸 {target.display_name}'s Sakura Wallet",
            color=config.COLOR_PRIMARY
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="💰 Coins Balance", value=f"`{user['coins']} Sakura Coins 🪙`", inline=True)
        embed.add_field(name="🎒 Items Owned", value=f"`{len(user.get('inventory', []))} items`", inline=True)
        embed.add_field(name="🏆 Casino Stats", value=f"Wins: `{user['wins']}` | Losses: `{user['losses']}`", inline=False)
        embed.set_footer(text="Earn coins with /work, /daily and Disboard /bump!", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="slots", description="Play the Sakura Casino Slot Machine for a chance to win 5x your bet!")
    @app_commands.describe(bet="Amount of coins to bet")
    async def slots(self, ctx: commands.Context, bet: int):
        if bet <= 0:
            return await ctx.send("❌ Bet must be greater than 0.", ephemeral=True)

        user_id = str(ctx.author.id)
        data = load_economy()
        user = get_user_data(data, user_id)

        if user["coins"] < bet:
            return await ctx.send(f"❌ You only have **{user['coins']} coins** in your wallet.", ephemeral=True)

        emojis = ["🌸", "💎", "🍒", "🍋", "👑", "🔥", "7️⃣"]
        r1, r2, r3 = random.choice(emojis), random.choice(emojis), random.choice(emojis)

        if r1 == r2 == r3:
            multiplier = 5 if r1 == "7️⃣" else (4 if r1 == "👑" else 3)
            win_amount = bet * multiplier
            user["coins"] += win_amount
            user["wins"] += 1
            result_text = f"🎉 **JACKPOT! 3x {r1}**\nYou won **+{win_amount} Coins** ({multiplier}x multiplier)!"
            color = config.COLOR_GOLD
        elif r1 == r2 or r2 == r3 or r1 == r3:
            win_amount = int(bet * 1.5)
            user["coins"] += win_amount
            user["wins"] += 1
            result_text = f"✨ **MATCH! 2 Pairs!**\nYou won **+{win_amount} Coins** (1.5x)!"
            color = config.COLOR_SUCCESS
        else:
            user["coins"] -= bet
            user["losses"] += 1
            result_text = f"💥 **No match!** You lost **-{bet} Coins**."
            color = config.COLOR_ERROR

        save_economy(data)

        embed = discord.Embed(
            title="🎰 RAI SAKURA SLOTS 🎰",
            description=(
                f"```\n"
                f"╔═══════════════╗\n"
                f"║  {r1} │ {r2} │ {r3}  ║\n"
                f"╚═══════════════╝\n"
                f"```\n"
                f"{result_text}\n\n"
                f"💰 **New Balance:** `{user['coins']} Sakura Coins`"
            ),
            color=color
        )
        embed.set_footer(text="RAI VIBES 💗 Arcade Casino", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="coinflip", aliases=["cf"], description="Bet Sakura Coins on a coin toss (Heads or Tails).")
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

    @commands.hybrid_command(name="pay", aliases=["give"], description="Transfer Sakura Coins to a friend.")
    @app_commands.describe(member="The member to send coins to", amount="Amount of coins to transfer")
    async def pay(self, ctx: commands.Context, member: discord.Member, amount: int):
        if member.bot or member.id == ctx.author.id:
            return await ctx.send("❌ You cannot send coins to bots or yourself.", ephemeral=True)
        if amount <= 0:
            return await ctx.send("❌ Amount must be greater than 0.", ephemeral=True)

        data = load_economy()
        sender = get_user_data(data, str(ctx.author.id))
        if sender["coins"] < amount:
            return await ctx.send(f"❌ You only have **{sender['coins']} coins**.", ephemeral=True)

        receiver = get_user_data(data, str(member.id))
        sender["coins"] -= amount
        receiver["coins"] += amount
        save_economy(data)

        embed = discord.Embed(
            title="💸 Coins Transfer Complete!",
            description=f"✅ {ctx.author.mention} transferred **{amount} Sakura Coins 🪙** to {member.mention}!",
            color=config.COLOR_SUCCESS
        )
        embed.set_footer(text="RAI VIBES 💗 Economy", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="shop", description="Browse the RAI Arcade Shop and buy exclusive perks!")
    async def shop(self, ctx: commands.Context):
        embed = discord.Embed(
            title="🌸 RAI SAKURA ARCADE SHOP 🛍️",
            description="Use your **Sakura Coins 🪙** to purchase exclusive roles and community perks!\n*Type `/buy <item_id>` to purchase.*",
            color=config.COLOR_PRIMARY
        )
        for item_id, info in SHOP_ITEMS.items():
            embed.add_field(
                name=f"{info['name']} — 💰 `{info['price']} Coins`",
                value=f"• **ID:** `{item_id}`\n• **Perk:** {info['description']}",
                inline=False
            )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="Earn coins using /daily, /work, and Disboard /bump!", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="buy", description="Purchase an item from the RAI Sakura Arcade Shop.")
    @app_commands.describe(item_id="The item ID to purchase (e.g. dj_pass, custom_title)")
    async def buy(self, ctx: commands.Context, item_id: str):
        item_key = item_id.lower().strip()
        if item_key not in SHOP_ITEMS:
            return await ctx.send(f"❌ Invalid item ID. Type `/shop` to view available items.", ephemeral=True)

        item = SHOP_ITEMS[item_key]
        data = load_economy()
        user = get_user_data(data, str(ctx.author.id))

        if user["coins"] < item["price"]:
            return await ctx.send(f"❌ You need **{item['price']} coins** to buy this, but you only have **{user['coins']} coins**.", ephemeral=True)

        user["coins"] -= item["price"]
        user["inventory"].append(item_key)
        save_economy(data)

        # Grant role if applicable
        if item.get("role_id") and ctx.guild:
            role = ctx.guild.get_role(item["role_id"])
            if role:
                try:
                    await ctx.author.add_roles(role, reason=f"Purchased {item['name']} in Arcade Shop")
                except Exception as e:
                    pass

        embed = discord.Embed(
            title="🎉 Purchase Successful!",
            description=(
                f"You successfully bought **{item['name']}** for **{item['price']} Coins**!\n\n"
                f"• **Remaining Balance:** `{user['coins']} Sakura Coins 🪙`\n"
                f"• **Status:** Active in your `/inventory`"
            ),
            color=config.COLOR_SUCCESS
        )
        embed.set_footer(text="RAI VIBES 💗 Arcade Shop", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="inventory", aliases=["inv"], description="View your owned items and perks.")
    async def inventory(self, ctx: commands.Context):
        data = load_economy()
        user = get_user_data(data, str(ctx.author.id))
        inv = user.get("inventory", [])

        if not inv:
            return await ctx.send("🎒 Your inventory is empty! Type `/shop` to browse available items.", ephemeral=True)

        embed = discord.Embed(
            title=f"🎒 {ctx.author.display_name}'s Inventory",
            color=config.COLOR_PRIMARY
        )
        counts = {}
        for item_key in inv:
            counts[item_key] = counts.get(item_key, 0) + 1

        for item_key, count in counts.items():
            item_info = SHOP_ITEMS.get(item_key, {"name": item_key.title(), "description": "Community item"})
            embed.add_field(
                name=f"{item_info['name']} (x{count})",
                value=f"• {item_info['description']}",
                inline=False
            )
        embed.set_footer(text="RAI VIBES 💗 Inventory", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Economy(bot))
