import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict

import discord
from discord import app_commands
from discord.ext import commands

import config

logger = logging.getLogger("Invites")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
INVITES_FILE = DATA_DIR / "invites.json"
ECONOMY_FILE = DATA_DIR / "economy.json"
COIN_REWARD_PER_INVITE = 500

def load_invites() -> Dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if INVITES_FILE.exists():
        try:
            with open(INVITES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_invites(data: Dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(INVITES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"Error saving invites: {e}")

def award_coins(user_id: int, amount: int):
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
    except Exception:
        pass

class Invites(commands.Cog):
    """Server Invite Tracking & Rewards Engine."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # guild_id -> {code: uses}
        self.invite_cache: Dict[int, Dict[str, int]] = {}

    async def cog_load(self):
        import asyncio
        asyncio.create_task(self._init_cache())

    async def _init_cache(self):
        try:
            await self.bot.wait_until_ready()
            for guild in self.bot.guilds:
                try:
                    invs = await guild.invites()
                    self.invite_cache[guild.id] = {inv.code: inv.uses for inv in invs}
                except Exception as e:
                    logger.debug(f"Could not cache invites for {guild.name}: {e}")
        except Exception:
            pass

    @commands.Cog.listener()
    async def on_invite_create(self, invite: discord.Invite):
        if invite.guild:
            if invite.guild.id not in self.invite_cache:
                self.invite_cache[invite.guild.id] = {}
            self.invite_cache[invite.guild.id][invite.code] = invite.uses or 0

    @commands.Cog.listener()
    async def on_invite_delete(self, invite: discord.Invite):
        if invite.guild and invite.guild.id in self.invite_cache:
            self.invite_cache[invite.guild.id].pop(invite.code, None)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        old_invs = self.invite_cache.get(guild.id, {})
        new_invs = {}
        used_invite: Optional[discord.Invite] = None

        try:
            current_invites = await guild.invites()
            for inv in current_invites:
                new_invs[inv.code] = inv.uses
                if inv.code in old_invs and inv.uses > old_invs[inv.code]:
                    used_invite = inv
            self.invite_cache[guild.id] = new_invs
        except Exception:
            return

        if used_invite and used_invite.inviter and not used_invite.inviter.bot:
            inviter = used_invite.inviter
            data = load_invites()
            uid = str(inviter.id)

            if uid not in data:
                data[uid] = {"regular": 0, "fake": 0, "left": 0, "invited_users": []}

            # Check for self-invite or duplicate
            if member.id == inviter.id:
                data[uid]["fake"] = data[uid].get("fake", 0) + 1
            else:
                data[uid]["regular"] = data[uid].get("regular", 0) + 1
                data[uid].setdefault("invited_users", []).append(member.id)
                award_coins(inviter.id, COIN_REWARD_PER_INVITE)

                # Send direct notification or award log
                try:
                    embed = discord.Embed(
                        title="🎉 ✦ INVITE BOUNTY REWARD ✦ 🎉",
                        description=(
                            f"**{member.display_name}** just joined the server using your invite link `{used_invite.code}`!\n\n"
                            f"🪙 **Reward:** `+{COIN_REWARD_PER_INVITE:,} Rai Coins` added to your wallet!\n"
                            f"📊 **Total Real Invites:** `{data[uid]['regular']}`"
                        ),
                        color=0x00FF88
                    )
                    await inviter.send(embed=embed)
                except Exception:
                    pass

            save_invites(data)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        data = load_invites()
        for uid, stats in data.items():
            if member.id in stats.get("invited_users", []):
                stats["left"] = stats.get("left", 0) + 1
                save_invites(data)
                break

    @app_commands.command(name="invites", description="Check your server invite stats, coin rewards, and ranking.")
    @app_commands.describe(member="Member whose invites you want to check (defaults to you)")
    async def check_invites(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        data = load_invites()
        stats = data.get(str(target.id), {"regular": 0, "fake": 0, "left": 0})

        regular = stats.get("regular", 0)
        fake = stats.get("fake", 0)
        left = stats.get("left", 0)
        total = regular - left

        embed = discord.Embed(
            title=f"💌 ┊ 𝐈𝐍𝐕𝐈𝐓𝐄  𝐒𝐓𝐀𝐓𝐒  •  {target.display_name}",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"✨ **Net Active Invites:** `🌟 {max(0, total)} Members`\n"
                f"📈 **Total Joined:** `{regular}`\n"
                f"🚪 **Left Server:** `{left}`\n"
                f"⚠️ **Fake / Alt Accounts:** `{fake}`\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"🪙 **Earn 500 Rai Coins** for every real friend you invite to **RAI FAM 💗**!\n"
                f"👉 Create your permanent link with `Server Invite -> Edit Invite Link -> Never Expire`."
            ),
            color=0xFF69B4
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Growth Engine", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

async def setup(bot: commands.Bot):
    await bot.add_cog(Invites(bot))
