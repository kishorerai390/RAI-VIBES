import os
import json
import time
import random
import logging
import datetime
from pathlib import Path
from typing import Optional, Dict

import discord
from discord import app_commands
from discord.ext import commands, tasks

import config

logger = logging.getLogger("Lottery")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LOTTERY_FILE = DATA_DIR / "lottery.json"
ECONOMY_FILE = DATA_DIR / "economy.json"
HALL_OF_FAME_CH_ID = 1549407114861215815
GENERAL_CHAT_ID = 1545502730699808768

TICKET_PRICE = 100
DEFAULT_SEED = 2500

def load_lottery() -> Dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if LOTTERY_FILE.exists():
        try:
            with open(LOTTERY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error loading lottery: {e}")
    now = int(time.time())
    return {
        "jackpot": DEFAULT_SEED,
        "ticket_price": TICKET_PRICE,
        "tickets": {},
        "draw_time": now + 86400,
        "last_winner": None
    }

def save_lottery(data: Dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(LOTTERY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"Error saving lottery: {e}")

def get_coins(user_id: int) -> int:
    if ECONOMY_FILE.exists():
        try:
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                eco = json.load(f)
                return eco.get(str(user_id), {}).get("coins", 0)
        except Exception:
            pass
    return 0

def add_coins(user_id: int, amount: int):
    try:
        eco = {}
        if ECONOMY_FILE.exists():
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                eco = json.load(f)
        uid = str(user_id)
        if uid not in eco:
            eco[uid] = {"coins": 200, "last_daily": 0, "wins": 0, "losses": 0}
        eco[uid]["coins"] = max(0, eco[uid].get("coins", 0) + amount)
        with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
            json.dump(eco, f, indent=2)
    except Exception as e:
        logger.warning(f"Error modifying coins: {e}")

class Lottery(commands.GroupCog, group_name="lottery"):
    """Server-Wide Progressive Jackpot Lottery Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.lottery_loop.start()

    def cog_unload(self):
        self.lottery_loop.cancel()

    @tasks.loop(minutes=5)
    async def lottery_loop(self):
        await self.bot.wait_until_ready()
        data = load_lottery()
        now = int(time.time())
        if now >= data.get("draw_time", 0):
            await self._execute_draw(data)

    async def _execute_draw(self, data: Dict):
        tickets = data.get("tickets", {})
        jackpot = data.get("jackpot", DEFAULT_SEED)

        if not tickets:
            # No tickets bought, extend draw by 24h
            data["draw_time"] = int(time.time()) + 86400
            save_lottery(data)
            return

        # Weighted selection by tickets
        ticket_pool = []
        for uid_str, count in tickets.items():
            ticket_pool.extend([int(uid_str)] * count)

        winner_id = random.choice(ticket_pool)
        winner_payout = int(jackpot * 0.90)
        seed_remainder = jackpot - winner_payout

        add_coins(winner_id, winner_payout)

        data["last_winner"] = {
            "user_id": winner_id,
            "payout": winner_payout,
            "tickets": tickets.get(str(winner_id), 0),
            "date": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        }
        data["jackpot"] = max(DEFAULT_SEED, seed_remainder)
        data["tickets"] = {}
        data["draw_time"] = int(time.time()) + 86400
        save_lottery(data)

        # Broadcast grand victory announcement
        channel = self.bot.get_channel(HALL_OF_FAME_CH_ID) or self.bot.get_channel(GENERAL_CHAT_ID)
        if channel:
            embed = discord.Embed(
                title="🎰 ✦ SERVER JACKPOT DRAW RESULTS ✦ 🎰",
                description=(
                    f"🎉 **WE HAVE A WINNER!** 🎉\n\n"
                    f"👑 **Jackpot Champion:** <@{winner_id}>\n"
                    f"💰 **Total Prize Awarded:** `+{winner_payout:,} Rai Coins`!\n\n"
                    f"✦ ───────────────────────────────────── ✦\n"
                    f"🌱 **Next Round Seed:** `{data['jackpot']:,} Coins`\n"
                    f"🎟️ Get your tickets now for the next draw using **`/lottery buy`**!"
                ),
                color=0xFFD700
            )
            embed.set_footer(text="RAI VIBES Lottery Suite • 90% Player Payout Guarantee", icon_url=config.RAI_ICON_URL)
            try:
                await channel.send(content=f"🎊 Congratulations <@{winner_id}>!", embed=embed)
            except Exception as e:
                logger.warning(f"Could not announce lottery winner: {e}")

    @app_commands.command(name="pool", description="View the current progressive lottery jackpot, tickets, and timer.")
    async def pool_status(self, interaction: discord.Interaction):
        data = load_lottery()
        jackpot = data.get("jackpot", DEFAULT_SEED)
        tickets = data.get("tickets", {})
        total_tickets = sum(tickets.values())
        user_tickets = tickets.get(str(interaction.user.id), 0)
        draw_time = data.get("draw_time", int(time.time()) + 86400)

        chance = (user_tickets / total_tickets * 100) if total_tickets > 0 else 0.0

        embed = discord.Embed(
            title="🎰 ┊ 𝐑𝐀𝐈  𝐅𝐀𝐌  𝐉𝐀𝐂𝐊𝐏𝐎𝐓  𝐋𝐎𝐓𝐓𝐄𝐑𝐘",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"💰 **Current Progressive Jackpot:** `🪙 {jackpot:,} Coins`\n"
                f"🎟️ **Total Tickets in Pool:** `{total_tickets:,} tickets`\n"
                f"🏷️ **Ticket Price:** `{TICKET_PRICE:,} Coins / ticket`\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👤 **Your Tickets:** `{user_tickets}` ({chance:.1f}% chance)\n"
                f"⏳ **Next Draw:** <t:{draw_time}:R> (<t:{draw_time}:F>)\n\n"
                f"👉 Use **`/lottery buy <amount>`** to enter the draw!"
            ),
            color=0xFFD700
        )

        last = data.get("last_winner")
        if last:
            embed.add_field(
                name="🏆 Previous Jackpot Winner",
                value=f"<@{last['user_id']}> won **+{last['payout']:,} Coins** ({last['date']})",
                inline=False
            )

        embed.set_footer(text="RAI VIBES Casino • High-Roller Progressive Pot", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="buy", description="Purchase tickets for the progressive server lottery jackpot.")
    @app_commands.describe(amount="Number of tickets to buy (100 coins each)")
    async def buy_tickets(self, interaction: discord.Interaction, amount: int = 1):
        if amount < 1:
            return await interaction.response.send_message("❌ You must buy at least 1 ticket!", ephemeral=True)
        if amount > 500:
            return await interaction.response.send_message("❌ Maximum 500 tickets per purchase!", ephemeral=True)

        total_cost = amount * TICKET_PRICE
        user_coins = get_coins(interaction.user.id)

        if user_coins < total_cost:
            return await interaction.response.send_message(
                f"❌ Insufficient funds! You need **{total_cost:,} Coins** for `{amount}` tickets, but you have **{user_coins:,} Coins**.",
                ephemeral=True
            )

        # Deduct coins
        add_coins(interaction.user.id, -total_cost)

        # Update lottery state
        data = load_lottery()
        tickets = data.setdefault("tickets", {})
        uid_str = str(interaction.user.id)
        tickets[uid_str] = tickets.get(uid_str, 0) + amount
        data["jackpot"] = data.get("jackpot", DEFAULT_SEED) + total_cost
        save_lottery(data)

        user_total = tickets[uid_str]
        pot_total = data["jackpot"]

        embed = discord.Embed(
            title="🎟️ ┊ 𝐋𝐎𝐓𝐓𝐄𝐑𝐘  𝐓𝐈𝐂𝐊𝐄𝐓𝐒  𝐏𝐔𝐑𝐂𝐇𝐀𝐒𝐄𝐃",
            description=(
                f"Successfully bought **{amount} Ticket(s)** for **🪙 {total_cost:,} Coins**!\n\n"
                f"📊 **Your Total Tickets:** `{user_total}`\n"
                f"💰 **New Jackpot Pool:** `🪙 {pot_total:,} Coins`\n"
                f"⏳ **Draw Time:** <t:{data.get('draw_time')}:R>"
            ),
            color=0x00FF88
        )
        embed.set_footer(text="Good luck! The winner receives 90% of the entire jackpot.")
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="draw", description="Force an immediate lottery draw (Admin / Server Owner only).")
    async def force_draw(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator and interaction.user.id != 1457380609641938981:
            return await interaction.response.send_message("❌ You lack permissions to force a lottery draw.", ephemeral=True)

        data = load_lottery()
        if not data.get("tickets"):
            return await interaction.response.send_message("❌ Cannot draw lottery: No tickets have been purchased yet!", ephemeral=True)

        await interaction.response.send_message("⏳ Executing immediate lottery draw...", ephemeral=True)
        await self._execute_draw(data)

async def setup(bot: commands.Bot):
    await bot.add_cog(Lottery(bot))
