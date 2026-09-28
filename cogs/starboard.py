import os
import json
import logging
from pathlib import Path
from typing import Optional
import discord
from discord.ext import commands

logger = logging.getLogger("Starboard")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
STAR_FILE = DATA_DIR / "starboard.json"
DEFAULT_STAR_CHANNEL_ID = 1554174876749791342  # 🏆｜ʜᴀʟʟ-ᴏꜰ-ꜰᴀᴍᴇ
REQUIRED_STARS = 3

def load_star_data() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if STAR_FILE.exists():
        try:
            with open(STAR_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_star_data(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(STAR_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Failed to save starboard data: {e}")

class Starboard(commands.Cog):
    """Automatic Community Clip Showcase & Hall of Fame."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.starred_posts = load_star_data()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) not in ("⭐", "🌟", "✨"):
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        star_channel = guild.get_channel(DEFAULT_STAR_CHANNEL_ID)
        if not star_channel or payload.channel_id == star_channel.id:
            return

        source_channel = guild.get_channel(payload.channel_id)
        if not source_channel:
            return

        try:
            message = await source_channel.fetch_message(payload.message_id)
        except Exception:
            return

        if message.author.bot:
            return

        # Count star reactions
        star_count = 0
        for reaction in message.reactions:
            if str(reaction.emoji) in ("⭐", "🌟", "✨"):
                star_count += reaction.count

        if star_count < REQUIRED_STARS:
            return

        str_msg_id = str(message.id)
        existing_star_id = self.starred_posts.get(str_msg_id)

        # Build Hall of Fame Embed
        embed = discord.Embed(
            description=message.content or "",
            color=0xFFA500,
            timestamp=message.created_at
        )
        embed.set_author(
            name=f"{message.author.display_name} in #{source_channel.name}",
            icon_url=message.author.display_avatar.url
        )
        embed.add_field(
            name="🔗 Original Clip / Message",
            value=f"[Jump to Message]({message.jump_url})",
            inline=False
        )

        # Handle images / media attachments
        image_set = False
        for att in message.attachments:
            if any(att.filename.lower().endswith(ext) for ext in (".png", ".jpg", ".jpeg", ".gif", ".webp")):
                embed.set_image(url=att.url)
                image_set = True
                break

        embed.set_footer(text=f"⭐ {star_count} | RAI FAM Hall of Fame")

        content = f"⭐ **{star_count}** | {source_channel.mention}"

        if existing_star_id:
            try:
                star_msg = await star_channel.fetch_message(existing_star_id)
                await star_msg.edit(content=content, embed=embed)
                return
            except Exception:
                pass

        # Post new Hall of Fame entry
        try:
            star_msg = await star_channel.send(content=content, embed=embed)
            self.starred_posts[str_msg_id] = star_msg.id
            save_star_data(self.starred_posts)

            # Award bonus coins to clip author
            try:
                from cogs.economy import update_user_coins
                update_user_coins(message.author.id, 250)
                await source_channel.send(
                    f"🌟 **Hall of Fame Feature!** {message.author.mention}'s clip just hit **{star_count} stars** and was featured in {star_channel.mention}! (`+250 Coins` awarded)",
                    delete_after=15
                )
            except Exception:
                pass

        except Exception as e:
            logger.error(f"Failed to post to starboard: {e}")

async def setup(bot: commands.Bot):
    await bot.add_cog(Starboard(bot))
