import time
import logging
from collections import defaultdict
from typing import Dict, Tuple
import discord
from discord.ext import commands

logger = logging.getLogger("MentionNotifier")

class MentionNotifier(commands.Cog):
    """Sends DM notifications to users when they are tagged/mentioned in the server (Thor Apex style)."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Cooldown tracker to prevent DM spam: (sender_id, target_id) -> last_notification_timestamp
        self.cooldowns: Dict[Tuple[int, int], float] = defaultdict(float)
        # Users who opted out of mention DMs: user_id -> set
        self.opt_outs = set()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Check if any users were mentioned
        if not message.mentions:
            return

        now = time.time()
        guild = message.guild
        author = message.author

        # Build clean channel breadcrumb: Category > #Channel
        category_name = message.channel.category.name if getattr(message.channel, "category", None) else guild.name
        channel_name = getattr(message.channel, "name", str(message.channel))
        channel_type_icon = "🔊" if isinstance(message.channel, discord.VoiceChannel) else "#"
        channel_breadcrumb = f"{guild.name} > {channel_type_icon} {channel_name}"

        # Clean display text for message preview
        preview_content = message.clean_content.strip()
        if not preview_content:
            preview_content = "[Attachment or Media]"
        elif len(preview_content) > 1000:
            preview_content = preview_content[:997] + "..."

        # Quote formatting like Discord
        quoted_content = "\n".join(f"> {line}" for line in preview_content.splitlines())

        for target in message.mentions:
            # Skip self-mentions, bots, or users who opted out
            if target.bot or target.id == author.id or target.id in self.opt_outs:
                continue

            # 10-second cooldown per (sender, target) to avoid DM flood
            cd_key = (author.id, target.id)
            if now - self.cooldowns[cd_key] < 10.0:
                continue
            self.cooldowns[cd_key] = now

            # Build Thor Apex style DM embed matching the screenshot
            embed = discord.Embed(
                description=(
                    f"### 🔔 You were tagged in {guild.name}!\n\n"
                    f"**Sender:** {author.name} ( @{author.display_name} )\n"
                    f"**Server:** {guild.name}\n"
                    f"**Channel:** `{channel_breadcrumb}`\n\n"
                    f"**Message Content:**\n"
                    f"{quoted_content}\n\n"
                    f"**Jump to Message**\n"
                    f"[Click Here to View Message]({message.jump_url})"
                ),
                color=0x5865F2
            )
            embed.set_footer(text=f"Sent from {guild.name}")
            embed.timestamp = message.created_at or discord.utils.utcnow()

            # Attempt to send the DM
            try:
                await target.send(embed=embed)
            except discord.Forbidden:
                # User has DMs closed
                pass
            except Exception as e:
                logger.debug(f"Could not send mention notification DM to {target.id}: {e}")

    @commands.hybrid_command(
        name="mentiondms",
        description="Toggle receiving direct message (DM) notifications when tagged in chat."
    )
    async def toggle_mention_dms(self, ctx: commands.Context):
        """Toggle mention DMs on or off for yourself."""
        user_id = ctx.author.id
        if user_id in self.opt_outs:
            self.opt_outs.remove(user_id)
            await ctx.send("🔔 **Mention DMs enabled!** You will receive DMs when someone tags you.", ephemeral=True)
        else:
            self.opt_outs.add(user_id)
            await ctx.send("🔕 **Mention DMs disabled!** You will no longer receive DMs when tagged.", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(MentionNotifier(bot))
