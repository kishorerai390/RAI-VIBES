import discord
import logging

logger = logging.getLogger("ClanTagger")

async def apply_rf_tag(member: discord.Member):
    """No-op: Member tagging disabled as requested."""
    return
