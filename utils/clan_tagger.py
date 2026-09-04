import discord
import logging

logger = logging.getLogger("ClanTagger")

async def apply_rf_tag(member: discord.Member):
    """Automatically adds 'RF | ' before a member's display name if not already present."""
    if not member or member.bot:
        return

    guild = member.guild
    if not guild:
        return

    # Discord strictly blocks bots from changing Server Owner nickname
    if member.id == guild.owner_id:
        return

    # Bot cannot edit users with higher or equal role hierarchy
    bot_member = guild.me
    if bot_member and member.top_role >= bot_member.top_role:
        return

    name = member.display_name.strip()

    # Check if already tagged
    upper_name = name.upper()
    if upper_name.startswith("RF ") or upper_name.startswith("RF |") or upper_name.startswith("RF・") or upper_name.startswith("RF|"):
        return

    # Discord max nickname length is 32 chars
    prefix = "RF | "
    max_len = 32 - len(prefix)
    clean_name = name[:max_len]
    new_nick = f"{prefix}{clean_name}"

    try:
        await member.edit(nick=new_nick, reason="Automatic RF clan tag on chat/VC")
        logger.info(f"✅ Applied RF tag: {name} -> {new_nick}")
    except Exception as e:
        logger.debug(f"Could not update nickname for {member.name}: {e}")
