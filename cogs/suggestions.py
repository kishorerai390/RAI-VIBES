import os
import json
import logging
from pathlib import Path
from typing import Optional, Dict

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, button

import config

logger = logging.getLogger("Suggestions")

DATA_DIR = Path("data")
SUGGESTIONS_FILE = DATA_DIR / "suggestions.json"

def load_suggestions() -> Dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SUGGESTIONS_FILE.exists():
        try:
            with open(SUGGESTIONS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Error reading suggestions: {e}")
    return {}

def save_suggestions(data: Dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(SUGGESTIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.warning(f"Error saving suggestions: {e}")


class SuggestionVoteView(View):
    """Persistent interactive upvote and downvote voting buttons for suggestions."""
    def __init__(self, suggestion_id: str = "default", upvotes: int = 0, downvotes: int = 0):
        super().__init__(timeout=None)
        self.suggestion_id = suggestion_id

        self.up_button.label = f"Upvote ({upvotes})"
        self.up_button.custom_id = f"sugg_up_{suggestion_id}"

        self.down_button.label = f"Downvote ({downvotes})"
        self.down_button.custom_id = f"sugg_down_{suggestion_id}"

    @button(label="Upvote (0)", emoji="👍", style=discord.ButtonStyle.success, row=0, custom_id="sugg_vote_up_btn")
    async def up_button(self, interaction: discord.Interaction, btn: Button):
        await self._handle_vote(interaction, vote_type="up")

    @button(label="Downvote (0)", emoji="👎", style=discord.ButtonStyle.danger, row=0, custom_id="sugg_vote_down_btn")
    async def down_button(self, interaction: discord.Interaction, btn: Button):
        await self._handle_vote(interaction, vote_type="down")

    async def _handle_vote(self, interaction: discord.Interaction, vote_type: str):
        await interaction.response.defer(ephemeral=True)
        user_id = str(interaction.user.id)
        msg_id = str(interaction.message.id)

        data = load_suggestions()
        sugg = data.get(msg_id)
        if not sugg:
            sugg = {
                "author_id": None,
                "text": interaction.message.embeds[0].description if interaction.message.embeds else "Suggestion",
                "upvoters": [],
                "downvoters": [],
                "status": "Pending"
            }
            data[msg_id] = sugg

        upvoters = sugg.setdefault("upvoters", [])
        downvoters = sugg.setdefault("downvoters", [])

        if vote_type == "up":
            if user_id in upvoters:
                upvoters.remove(user_id)
                action_text = "Removed your upvote."
            else:
                upvoters.append(user_id)
                if user_id in downvoters:
                    downvoters.remove(user_id)
                action_text = "Cast your 👍 **Upvote**!"
        else:
            if user_id in downvoters:
                downvoters.remove(user_id)
                action_text = "Removed your downvote."
            else:
                downvoters.append(user_id)
                if user_id in upvoters:
                    upvoters.remove(user_id)
                action_text = "Cast your 👎 **Downvote**!"

        save_suggestions(data)

        up_count = len(upvoters)
        down_count = len(downvoters)
        self.up_button.label = f"Upvote ({up_count})"
        self.down_button.label = f"Downvote ({down_count})"

        # Also update embed field
        if interaction.message.embeds:
            embed = interaction.message.embeds[0]
            embed.set_field_at(1, name="🗳️ Community Votes", value=f"👍 **{up_count} Upvotes** • 👎 **{down_count} Downvotes**", inline=True)
            try:
                await interaction.message.edit(embed=embed, view=self)
            except Exception:
                pass
        else:
            try:
                await interaction.message.edit(view=self)
            except Exception:
                pass

        await interaction.followup.send(f"✅ {action_text} (Current: +{up_count} / -{down_count})", ephemeral=True)


class Suggestions(commands.Cog):
    """Community Suggestions & Feature Voting System."""
    SUGGESTION_CHANNEL_ID = 1549489880776839248

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def get_suggestion_channel(self, guild: discord.Guild) -> Optional[discord.TextChannel]:
        return guild.get_channel(self.SUGGESTION_CHANNEL_ID) or next((c for c in guild.text_channels if "suggestion" in c.name.lower()), None)

    async def create_suggestion_card(self, channel: discord.TextChannel, author: discord.Member, content: str):
        """Builds and dispatches the high-fidelity cyber suggestion voting card."""
        embed = discord.Embed(
            title="💡 COMMUNITY SUGGESTION",
            description=content,
            color=0xFF69B4
        )
        embed.set_author(name=f"{author.display_name} ({author.name})", icon_url=author.display_avatar.url)
        embed.set_thumbnail(url=author.display_avatar.url)
        embed.add_field(name="📊 Status", value="🟡 **Pending Review**", inline=True)
        embed.add_field(name="🗳️ Community Votes", value="👍 **0 Upvotes** • 👎 **0 Downvotes**", inline=True)
        embed.set_footer(text="RAI FAM 💗 • Cast your vote using buttons below!", icon_url=config.RAI_ICON_URL)
        embed.timestamp = discord.utils.utcnow()

        msg = await channel.send(embed=embed)
        view = SuggestionVoteView(suggestion_id=str(msg.id), upvotes=0, downvotes=0)
        await msg.edit(view=view)

        # Save record
        data = load_suggestions()
        data[str(msg.id)] = {
            "author_id": author.id,
            "text": content,
            "upvoters": [],
            "downvoters": [],
            "status": "Pending",
            "created_at": discord.utils.utcnow().isoformat()
        }
        save_suggestions(data)
        return msg

    @app_commands.command(name="suggest", description="Submit an idea, improvement, or feature request for RAI FAM.")
    @app_commands.describe(idea="Your suggestion or idea for the server")
    async def suggest_command(self, interaction: discord.Interaction, idea: str):
        if not interaction.guild:
            return await interaction.response.send_message("❌ This command can only be used in a server.", ephemeral=True)

        chan = self.get_suggestion_channel(interaction.guild)
        if not chan:
            return await interaction.response.send_message("❌ Suggestions channel not found.", ephemeral=True)

        await interaction.response.defer(ephemeral=True)
        member = interaction.user if isinstance(interaction.user, discord.Member) else await interaction.guild.fetch_member(interaction.user.id)
        msg = await self.create_suggestion_card(chan, member, idea.strip())

        await interaction.followup.send(
            f"💡 **Suggestion Published!** Your idea has been posted to {chan.mention} for community voting:\n{msg.jump_url}",
            ephemeral=True
        )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return

        # Listen in suggestion channel
        if message.channel.id == self.SUGGESTION_CHANNEL_ID or "suggestion" in message.channel.name.lower():
            content = message.content.strip()
            if not content or content.startswith("/"):
                return

            try:
                await message.delete()
            except Exception:
                pass

            await self.create_suggestion_card(message.channel, message.author, content)


async def setup(bot: commands.Bot):
    await bot.add_cog(Suggestions(bot))
