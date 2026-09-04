import discord
from discord.ext import commands

class Counting(commands.Cog):
    """Interactive Counting Minigame."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.current_count = {}
        self.last_counter = {}

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        if "counting" in message.channel.name.lower():
            guild_id = message.guild.id
            if guild_id not in self.current_count:
                self.current_count[guild_id] = 0
                self.last_counter[guild_id] = None

            content = message.content.strip().split()[0]
            if content.isdigit():
                num = int(content)
                expected = self.current_count[guild_id] + 1

                # Check if same user counted twice in a row
                if self.last_counter[guild_id] == message.author.id:
                    self.current_count[guild_id] = 0
                    self.last_counter[guild_id] = None
                    await message.add_reaction("❌")
                    return await message.channel.send(f"⚠️ {message.author.mention} ruined the count! You cannot count twice in a row. Starting back at **1**.")

                # Correct count
                if num == expected:
                    self.current_count[guild_id] = expected
                    self.last_counter[guild_id] = message.author.id
                    await message.add_reaction("✅")
                    if expected % 50 == 0:
                        await message.channel.send(f"🎉 **Milestone Reached!** Current streak: **{expected}**!")
                else:
                    self.current_count[guild_id] = 0
                    self.last_counter[guild_id] = None
                    await message.add_reaction("❌")
                    await message.channel.send(f"💥 {message.author.mention} entered `{num}` instead of `{expected}`! The count resets to **1**.")


async def setup(bot: commands.Bot):
    await bot.add_cog(Counting(bot))
