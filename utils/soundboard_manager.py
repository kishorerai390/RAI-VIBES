import json
import logging
from pathlib import Path
from typing import Set, Optional, Tuple, Union

import discord

logger = logging.getLogger("SoundboardManager")

OWNER_ID = 1457380609641938981
FOUNDER_ROLE_IDS = {1545494610489643038, 1550205899069726810}

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
MUTED_SOUNDBOARDS_FILE = DATA_DIR / "muted_soundboards.json"


def is_founder(user: Union[discord.User, discord.Member], guild: Optional[discord.Guild] = None) -> bool:
    """Returns True only if the user is the Founder & Owner."""
    if user.id == OWNER_ID:
        return True
    if guild and user.id == guild.owner_id:
        return True
    if isinstance(user, discord.Member):
        for r in user.roles:
            if r.id in FOUNDER_ROLE_IDS:
                return True
            r_norm = r.name.lower()
            if "founder" in r_norm or "owner" in r_norm:
                return True
    return False


def get_muted_soundboard_channels() -> Set[int]:
    """Returns set of channel IDs where soundboard is muted."""
    if not MUTED_SOUNDBOARDS_FILE.exists():
        return set()
    try:
        with open(MUTED_SOUNDBOARDS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return set(data.get("muted_channels", []))
    except Exception as e:
        logger.error(f"Error reading muted soundboards file: {e}")
        return set()


def set_channel_soundboard_muted(channel_id: int, muted: bool) -> bool:
    """Sets the muted state for a voice channel in persistence."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        chans = get_muted_soundboard_channels()
        if muted:
            chans.add(channel_id)
        else:
            chans.discard(channel_id)
        with open(MUTED_SOUNDBOARDS_FILE, "w", encoding="utf-8") as f:
            json.dump({"muted_channels": sorted(list(chans))}, f, indent=2)
        return True
    except Exception as e:
        logger.error(f"Error saving muted soundboard channel: {e}")
        return False


def is_channel_soundboard_muted(channel_id: int) -> bool:
    """Returns True if soundboard is restricted in the given channel ID."""
    return channel_id in get_muted_soundboard_channels()


async def apply_discord_soundboard_permission(
    channel: Union[discord.VoiceChannel, discord.StageChannel],
    mute: bool,
    author: Union[discord.User, discord.Member]
) -> Tuple[bool, str]:
    """
    Updates the @everyone role and channel role permission overwrites on the voice channel.
    mute=True: use_soundboard=False, use_external_sounds=False
    mute=False: use_soundboard=None, use_external_sounds=None (resets to server default)
    """
    try:
        guild = channel.guild
        default_role = guild.default_role

        # Collect targets: @everyone plus all existing role overwrites that lack Administrator
        targets = [default_role]
        for target in list(channel.overwrites.keys()):
            if isinstance(target, discord.Role) and target != default_role:
                if not target.permissions.administrator:
                    targets.append(target)

        for target in targets:
            ow = channel.overwrites_for(target)
            if mute:
                ow.use_soundboard = False
                ow.use_external_sounds = False
                reason = f"Founder {author.display_name} muted soundboard in #{channel.name}"
            else:
                ow.use_soundboard = None
                ow.use_external_sounds = None
                reason = f"Founder {author.display_name} unmuted soundboard in #{channel.name}"
            await channel.set_permissions(target, overwrite=ow, reason=reason)

        return True, "Success"
    except discord.Forbidden:
        return False, "Bot is missing permission to edit channel permissions."
    except Exception as e:
        logger.error(f"Failed to update channel soundboard permission: {e}")
        return False, str(e)
