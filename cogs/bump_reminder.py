import os
import sys
import json
import time
import logging
from pathlib import Path
import discord
from discord import app_commands
from discord.ext import commands, tasks

logger = logging.getLogger("BumpReminder")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STATE_FILE = DATA_DIR / "bump_state.json"
GENERAL_CHAN_ID = 1545502730699808768
DISBOARD_BOT_ID = 302050872383242240
COOLDOWN_SECONDS = 7200  # 2 Hours

DIVIDER = "<a:w_welc1:1547271923891707915><:w_dash:1547271874981920868><:w_dash:1547271874981920868><:w_dash:1547271874981920868><:w_dash:1547271874981920868><a:w_welc2:1547271930699190424>"

def load_state() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"last_bump": 0, "reminder_sent": True}

def save_state(state: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving bump state: {e}")

class BumpReminder(commands.Cog):
    """Auto-Bump Monitor and 2-Hour Disboard Reminder Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.state = load_state()

    async def cog_load(self):
        if not self.bump_check_loop.is_running():
            self.bump_check_loop.start()

    def cog_unload(self):
        self.bump_check_loop.cancel()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        # Detect DISBOARD response
        if message.author.id == DISBOARD_BOT_ID:
            is_bump_success = False
            for embed in message.embeds:
                desc = embed.description or ""
                if "Bump done" in desc or "bump done" in desc.lower():
                    is_bump_success = True
                    break
            
            if is_bump_success:
                now = time.time()
                self.state["last_bump"] = now
                self.state["reminder_sent"] = False
                save_state(self.state)
                logger.info(f"Disboard bump registered at {now}. 2h timer active.")
                
                try:
                    await message.channel.send(
                        "✨ **Bump Registered!** I will remind you in **2 hours** when the next bump is ready! ⏰"
                    )
                except Exception:
                    pass

    @tasks.loop(seconds=60)
    async def bump_check_loop(self):
        now = time.time()
        last_bump = self.state.get("last_bump", 0)
        reminder_sent = self.state.get("reminder_sent", False)

        if last_bump > 0 and not reminder_sent:
            elapsed = now - last_bump
            if elapsed >= COOLDOWN_SECONDS:
                gen_chan = self.bot.get_channel(GENERAL_CHAN_ID)
                if gen_chan:
                    embed = discord.Embed(
                        title="<a:pinkflame:1547271954841731193> ✦ DISBOARD BUMP IS READY! ✦ <a:pinkflame:1547271954841731193>",
                        description=(
                            f"{DIVIDER}\n\n"
                            "It has been **2 hours** since our last server bump!\n\n"
                            "👉 Type **`/bump`** in this channel right now to boost **RAI FAM 💗** to the #1 spot on Disboard! 🚀\n\n"
                            f"{DIVIDER}\n"
                            "💡 *Bumping keeps our community discoverable to hundreds of players!*"
                        ),
                        color=0xFF2A85
                    )
                    embed.set_footer(text="RAI VIBES • Auto Growth Engine 📈")
                    try:
                        await gen_chan.send(embed=embed)
                        self.state["reminder_sent"] = True
                        save_state(self.state)
                        logger.info("Sent 2-hour bump reminder to #general!")
                    except Exception as e:
                        logger.error(f"Failed to send bump reminder: {e}")

    @bump_check_loop.before_loop
    async def before_loop(self):
        await self.bot.wait_until_ready()

    @app_commands.command(name="nextbump", description="Check when the next Disboard bump is ready.")
    async def next_bump_cmd(self, interaction: discord.Interaction):
        now = time.time()
        last_bump = self.state.get("last_bump", 0)
        elapsed = now - last_bump
        
        if last_bump == 0 or elapsed >= COOLDOWN_SECONDS:
            await interaction.response.send_message(
                "🟢 **Disboard is ready to bump right now!** Type `/bump` in <#1545502730699808768>! 🚀"
            )
        else:
            remaining = int(COOLDOWN_SECONDS - elapsed)
            minutes, seconds = divmod(remaining, 60)
            hours, minutes = divmod(minutes, 60)
            time_str = f"{hours}h {minutes}m" if hours > 0 else f"{minutes}m {seconds}s"
            await interaction.response.send_message(
                f"⏳ **Disboard is on cooldown.** The next bump is ready in **{time_str}**! (Bumping pushes RAI FAM to #1)."
            )

async def setup(bot: commands.Bot):
    await bot.add_cog(BumpReminder(bot))
