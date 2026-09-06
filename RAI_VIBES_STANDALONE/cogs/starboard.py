import discord
from discord.ext import commands

import config

class Starboard(commands.Cog):
    """Community Starboard / Hall of Fame."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.starred_messages = set()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if str(payload.emoji) != "⭐":
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        channel = guild.get_channel(payload.channel_id)
        if not channel:
            return

        starboard_chan = (
            discord.utils.get(guild.text_channels, name="hall-of-fame") or
            discord.utils.get(guild.text_channels, name="starboard") or
            next((c for c in guild.text_channels if "hall" in c.name or "star" in c.name), None)
        )
        if not starboard_chan or channel.id == starboard_chan.id:
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except Exception:
            return

        reaction = discord.utils.get(message.reactions, emoji="⭐")
        if reaction and reaction.count >= 3 and message.id not in self.starred_messages:
            self.starred_messages.add(message.id)

            embed = discord.Embed(
                description=message.content or "",
                color=config.COLOR_GOLD,
                timestamp=message.created_at
            )
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.add_field(name="Source", value=f"[Jump to Message]({message.jump_url}) in {channel.mention}", inline=False)

            if message.attachments:
                embed.set_image(url=message.attachments[0].url)

            embed.set_footer(text=f"⭐ {reaction.count} | Hall of Fame", icon_url=config.RAI_ICON_URL)
            await starboard_chan.send(content=f"⭐ **{reaction.count}** {channel.mention}", embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Starboard(bot))
