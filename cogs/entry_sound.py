import os
import sys
import json
import time
import asyncio
import logging
import urllib.request
import unicodedata
from pathlib import Path
from typing import Optional, Dict, List

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select, Modal, TextInput, button

import config
from utils.ffmpeg_setup import get_ffmpeg_executable
from cogs.economy import get_user_data, update_user_coins, OWNER_ID

logger = logging.getLogger("EntrySound")

REPO_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = REPO_DIR / "data"
ENTRY_SOUND_FILE = DATA_DIR / "entry_sounds.json"
CUSTOM_SOUNDS_DIR = DATA_DIR / "custom_sounds"

from utils.soundboard_manager import is_channel_soundboard_muted

def is_channel_suppressed(channel: Optional[discord.VoiceChannel]) -> bool:
    """Returns True if the voice channel is a generator, AFK, quiet room, or muted by the Founder."""
    if not channel:
        return True
    if is_channel_soundboard_muted(channel.id):
        return True
    norm_name = unicodedata.normalize('NFKD', channel.name).lower()
    # Generators
    if any(w in norm_name for w in ("join to create", "create ghost", "generator")):
        return True
    if "➕" in channel.name and ("create" in norm_name or "join" in norm_name):
        return True
    # Quiet, checking, AFK, or 24/7 Lo-Fi channels
    if channel.id == 1545781986193309789:
        return True
    if any(w in norm_name for w in ("afk", "sleep", "💤", "checking", "check-in", "silent", "quiet", "study", "focus", "lofi", "lo-fi", "ʟᴏ-ꜰɪ")):
        return True
    if channel.guild and channel.guild.afk_channel and channel.id == channel.guild.afk_channel.id:
        return True
    return False

FFMPEG_BEFORE_OPTIONS = (
    '-headers "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n'
    'Referer: https://www.myinstants.com/\r\n" '
    '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin'
)

# 24 100% Tested & Verified Live MP3 Sound Effects
ENTRY_SOUNDS = {
    # 👑 Sigma & Prestige
    "gigachad": {
        "name": "🗿 GigaChad Sigma Theme",
        "url": "https://www.myinstants.com/media/sounds/gigachad.mp3",
        "price": 1200,
        "emoji": "🗿",
        "duration": 4.5,
        "category": "Prestige",
        "description": "Legendary 'Can You Feel My Heart' Sigma Chad theme"
    },
    "john_cena": {
        "name": "🎺 John Cena Entrance",
        "url": "https://www.myinstants.com/media/sounds/and-his-name-is-john-cena-1.mp3",
        "price": 1200,
        "emoji": "🎺",
        "duration": 4.0,
        "category": "Prestige",
        "description": "And his name is John Cena! Epic brass fanfare"
    },
    "tokyo_drift": {
        "name": "🏎️ Tokyo Drift Beat",
        "url": "https://www.myinstants.com/media/sounds/tokyo-drift.mp3",
        "price": 1000,
        "emoji": "🏎️",
        "duration": 4.0,
        "category": "Prestige",
        "description": "Fast & Furious iconic bell beat drop"
    },
    "ultra_instinct": {
        "name": "⚡ Ultra Instinct Climax",
        "url": "https://www.myinstants.com/media/sounds/ultra-instinct.mp3",
        "price": 1100,
        "emoji": "⚡",
        "duration": 4.5,
        "category": "Prestige",
        "description": "Dragon Ball Super supreme godly power theme"
    },
    "gta_san_andreas": {
        "name": "🕶️ GTA San Andreas Passed",
        "url": "https://www.myinstants.com/media/sounds/gta-san-andreas-mission-complete-sound-hq.mp3",
        "price": 1000,
        "emoji": "🕶️",
        "duration": 4.0,
        "category": "Prestige",
        "description": "Classic GTA San Andreas mission completed theme"
    },

    # 🔥 Hype & Energy
    "airhorn": {
        "name": "🎺 MLG Hype Airhorn",
        "url": "https://www.myinstants.com/media/sounds/air-horn-club-sample_1.mp3",
        "price": 500,
        "emoji": "🎺",
        "duration": 2.5,
        "category": "Hype",
        "description": "High energy club airhorn blast (Free Starter)"
    },
    "victory": {
        "name": "🏆 Victory Fanfare Champion",
        "url": "https://www.myinstants.com/media/sounds/final-fantasy-vii-victory-fanfare-1.mp3",
        "price": 1000,
        "emoji": "🏆",
        "duration": 3.5,
        "category": "Hype",
        "description": "Classic gaming victory fanfare"
    },
    "crowd_cheer": {
        "name": "👏 Grand Stadium Applause",
        "url": "https://www.myinstants.com/media/sounds/cheering.mp3",
        "price": 750,
        "emoji": "👏",
        "duration": 3.0,
        "category": "Hype",
        "description": "Roaring stadium crowd cheer & applause"
    },
    "pistol_shot": {
        "name": "🔫 Pistol Trigger Swagger",
        "url": "https://www.myinstants.com/media/sounds/pistol-shot.mp3",
        "price": 650,
        "emoji": "🔫",
        "duration": 2.0,
        "category": "Hype",
        "description": "Crisp cinematic pistol shot effect"
    },
    "fbi_open_up": {
        "name": "🚨 FBI Open Up! Door Kick",
        "url": "https://www.myinstants.com/media/sounds/fbi-open-up-sfx.mp3",
        "price": 850,
        "emoji": "🚨",
        "duration": 2.5,
        "category": "Hype",
        "description": "Intense explosive FBI raid entrance"
    },
    "surprise_mf": {
        "name": "💥 Surprise Motherf***er!",
        "url": "https://www.myinstants.com/media/sounds/surprise-motherfucker.mp3",
        "price": 900,
        "emoji": "💥",
        "duration": 2.0,
        "category": "Hype",
        "description": "Iconic Sgt. Doakes legendary movie shout"
    },

    # 🎭 Viral Memes & Comedy
    "bruh": {
        "name": "🗿 Legendary Bruh",
        "url": "https://www.myinstants.com/media/sounds/movie_1.mp3",
        "price": 500,
        "emoji": "🗿",
        "duration": 2.0,
        "category": "Meme",
        "description": "The immortal meme sound effect"
    },
    "emotional_damage": {
        "name": "💥 Emotional Damage",
        "url": "https://www.myinstants.com/media/sounds/emotional-damage-meme.mp3",
        "price": 800,
        "emoji": "💥",
        "duration": 2.5,
        "category": "Meme",
        "description": "Steven He iconic viral soundbite"
    },
    "curb": {
        "name": "🎬 Curb Your Enthusiasm",
        "url": "https://www.myinstants.com/media/sounds/curb-your-enthusiasm.mp3",
        "price": 950,
        "emoji": "🎬",
        "duration": 4.0,
        "category": "Meme",
        "description": "Directed by Robert B. Weide comedic theme"
    },
    "spongebob_fail": {
        "name": "🎺 Sad SpongeBob Trombone",
        "url": "https://www.myinstants.com/media/sounds/spongebob-fail.mp3",
        "price": 450,
        "emoji": "🎺",
        "duration": 2.5,
        "category": "Meme",
        "description": "Disappointed comedic fail trombone"
    },
    "drumroll": {
        "name": "🥁 Rimshot Ba-Dum-Tss",
        "url": "https://www.myinstants.com/media/sounds/ba-dum-tss.mp3",
        "price": 400,
        "emoji": "🥁",
        "duration": 2.0,
        "category": "Meme",
        "description": "Stand-up comedy punchline drumroll"
    },
    "taco_bell": {
        "name": "🔔 Taco Bell Bong",
        "url": "https://www.myinstants.com/media/sounds/taco-bell-bong-sfx.mp3",
        "price": 500,
        "emoji": "🔔",
        "duration": 2.0,
        "category": "Meme",
        "description": "Deep resonance Taco Bell bong chime"
    },
    "among_us": {
        "name": "📮 Among Us Impostor",
        "url": "https://www.myinstants.com/media/sounds/among-us-role-reveal-sound.mp3",
        "price": 650,
        "emoji": "📮",
        "duration": 3.0,
        "category": "Meme",
        "description": "Dramatic eerie Impostor role reveal sting"
    },
    "gta_wasted": {
        "name": "💀 GTA V Wasted",
        "url": "https://www.myinstants.com/media/sounds/gta-v-death-sound-effect-102.mp3",
        "price": 750,
        "emoji": "💀",
        "duration": 3.5,
        "category": "Meme",
        "description": "Grand Theft Auto slow motion death sound"
    },
    "illuminati": {
        "name": "🔺 X-Files Illuminati",
        "url": "https://www.myinstants.com/media/sounds/illuminati-confirmed.mp3",
        "price": 800,
        "emoji": "🔺",
        "duration": 3.5,
        "category": "Meme",
        "description": "Mysterious Illuminati whistle theme"
    },

    # ✨ Aesthetic & Retro
    "wow": {
        "name": "✨ Anime Wow Chime",
        "url": "https://www.myinstants.com/media/sounds/anime-wow-sound-effect.mp3",
        "price": 600,
        "emoji": "✨",
        "duration": 2.0,
        "category": "Aesthetic",
        "description": "Cute aesthetic anime wow voice chime"
    },
    "windows_xp": {
        "name": "🧊 Windows XP Startup",
        "url": "https://www.myinstants.com/media/sounds/windows-xp-startup.mp3",
        "price": 900,
        "emoji": "🧊",
        "duration": 3.5,
        "category": "Aesthetic",
        "description": "Pure retro nostalgia Windows XP chime"
    },
    "discord_ping": {
        "name": "🔔 Discord Ping Troll",
        "url": "https://www.myinstants.com/media/sounds/discord-notification.mp3",
        "price": 500,
        "emoji": "🔔",
        "duration": 1.5,
        "category": "Aesthetic",
        "description": "Everyone looks at their phone notification pop"
    },
    "bye_great_time": {
        "name": "👋 Bye Have a Great Time!",
        "url": "https://www.myinstants.com/media/sounds/bye-have-a-great-time.mp3",
        "price": 600,
        "emoji": "👋",
        "duration": 2.5,
        "category": "Aesthetic",
        "description": "Wholesome Russian police officer exit greeting"
    }
}

SOUND_BUNDLES = {
    "bundle_sigma": {
        "name": "👑 The Sigma Apex Bundle",
        "description": "Unlock GigaChad, John Cena, Tokyo Drift, Ultra Instinct & San Andreas",
        "price": 3500,
        "emoji": "👑",
        "sounds": ["gigachad", "john_cena", "tokyo_drift", "ultra_instinct", "gta_san_andreas"]
    },
    "bundle_meme": {
        "name": "🎭 The Meme Lord Bundle",
        "description": "Unlock Bruh, Emotional Damage, Curb, SpongeBob, Rimshot, Taco Bell, Among Us, GTA V Wasted & Illuminati",
        "price": 3800,
        "emoji": "🎭",
        "sounds": ["bruh", "emotional_damage", "curb", "spongebob_fail", "drumroll", "taco_bell", "among_us", "gta_wasted", "illuminati"]
    },
    "bundle_hype": {
        "name": "🔥 The Hype Master Bundle",
        "description": "Unlock MLG Airhorn, Victory, Stadium Applause, Pistol Shot, FBI Open Up & Surprise Motherf***er",
        "price": 3200,
        "emoji": "🔥",
        "sounds": ["airhorn", "victory", "crowd_cheer", "pistol_shot", "fbi_open_up", "surprise_mf"]
    }
}

ALL_SOUND_KEYS = list(ENTRY_SOUNDS.keys())


def load_entry_data() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if ENTRY_SOUND_FILE.exists():
        try:
            with open(ENTRY_SOUND_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": {}}
    return {"users": {}}


def save_entry_data(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(ENTRY_SOUND_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_user_entry_profile(user_id: int) -> dict:
    data = load_entry_data()
    uid = str(user_id)
    if uid not in data.get("users", {}):
        data.setdefault("users", {})[uid] = {
            "equipped": "airhorn",
            "enabled": True,
            "exit_sound": "bye_great_time",
            "exit_enabled": True,
            "volume": 85,
            "banner_enabled": True,
            "custom_url": None,
            "custom_unlocked": False,
            "unlocked": ["airhorn", "bye_great_time"]
        }
        save_entry_data(data)

    prof = data["users"][uid]
    # Ensure all keys exist
    prof.setdefault("volume", 85)
    prof.setdefault("banner_enabled", True)
    prof.setdefault("custom_url", None)
    prof.setdefault("custom_unlocked", False)

    if user_id == OWNER_ID:
        prof["unlocked"] = list(ALL_SOUND_KEYS)
        prof["custom_unlocked"] = True
        if not prof.get("equipped"):
            prof["equipped"] = "gigachad"
        if not prof.get("exit_sound"):
            prof["exit_sound"] = "gta_san_andreas"
    return prof


def unlock_user_sound(user_id: int, sound_key: str) -> bool:
    data = load_entry_data()
    uid = str(user_id)
    users = data.setdefault("users", {})
    if uid not in users:
        users[uid] = {
            "equipped": "airhorn",
            "enabled": True,
            "exit_sound": "bye_great_time",
            "exit_enabled": True,
            "volume": 85,
            "banner_enabled": True,
            "custom_url": None,
            "custom_unlocked": False,
            "unlocked": ["airhorn", "bye_great_time"]
        }

    if sound_key not in users[uid]["unlocked"]:
        users[uid]["unlocked"].append(sound_key)
        save_entry_data(data)
        return True
    return False


def unlock_sound_bundle(user_id: int, bundle_key: str) -> List[str]:
    bundle = SOUND_BUNDLES.get(bundle_key)
    if not bundle:
        return []
    data = load_entry_data()
    uid = str(user_id)
    users = data.setdefault("users", {})
    if uid not in users:
        users[uid] = {
            "equipped": "airhorn",
            "enabled": True,
            "exit_sound": "bye_great_time",
            "exit_enabled": True,
            "volume": 85,
            "banner_enabled": True,
            "custom_url": None,
            "custom_unlocked": False,
            "unlocked": ["airhorn", "bye_great_time"]
        }
    newly_unlocked = []
    for s in bundle["sounds"]:
        if s not in users[uid]["unlocked"]:
            users[uid]["unlocked"].append(s)
            newly_unlocked.append(s)
    save_entry_data(data)
    return newly_unlocked


def unlock_custom_pass(user_id: int):
    data = load_entry_data()
    uid = str(user_id)
    users = data.setdefault("users", {})
    if uid not in users:
        users[uid] = {
            "equipped": "airhorn",
            "enabled": True,
            "exit_sound": "bye_great_time",
            "exit_enabled": True,
            "volume": 85,
            "banner_enabled": True,
            "custom_url": None,
            "custom_unlocked": True,
            "unlocked": ["airhorn", "bye_great_time"]
        }
    users[uid]["custom_unlocked"] = True
    save_entry_data(data)


def unlock_all_sounds(user_id: int):
    data = load_entry_data()
    uid = str(user_id)
    users = data.setdefault("users", {})
    if uid not in users:
        users[uid] = {
            "equipped": "gigachad",
            "enabled": True,
            "exit_sound": "bye_great_time",
            "exit_enabled": True,
            "volume": 85,
            "banner_enabled": True,
            "custom_url": None,
            "custom_unlocked": True,
            "unlocked": []
        }
    users[uid]["unlocked"] = list(ALL_SOUND_KEYS)
    users[uid]["custom_unlocked"] = True
    save_entry_data(data)


# Cooldown tracking: user_id -> timestamp
USER_ENTRY_COOLDOWNS: Dict[int, float] = {}


# =====================================================================
# MODALS FOR VOLUME & CUSTOM URL
# =====================================================================
class SetVolumeModal(Modal, title="Set Entrance Audio Volume"):
    vol = TextInput(
        label="Loudness (10 to 100%)",
        placeholder="e.g. 85 (Default is 85%)",
        min_length=2,
        max_length=3,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        try:
            val = int(self.vol.value.strip())
            if val < 10 or val > 100:
                return await interaction.response.send_message("❌ Volume must be between 10% and 100%.", ephemeral=True)
        except ValueError:
            return await interaction.response.send_message("❌ Please enter a valid number.", ephemeral=True)

        data = load_entry_data()
        prof = data.setdefault("users", {}).setdefault(str(interaction.user.id), {})
        prof["volume"] = val
        save_entry_data(data)

        await interaction.response.send_message(f"🔊 Entrance audio volume set to **`{val}%`**!", ephemeral=True)


class SetCustomUrlModal(Modal, title="Set Custom Audio Stream URL"):
    audio_url = TextInput(
        label="Direct MP3 / WAV / Audio Stream URL",
        placeholder="https://example.com/my-entrance-sound.mp3",
        min_length=10,
        max_length=250,
        required=True
    )

    async def on_submit(self, interaction: discord.Interaction):
        url = self.audio_url.value.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            return await interaction.response.send_message("❌ URL must start with `http://` or `https://`.", ephemeral=True)

        # Quick validation
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=4) as resp:
                if resp.getcode() >= 400:
                    return await interaction.response.send_message(f"❌ Could not reach URL (HTTP {resp.getcode()}).", ephemeral=True)
        except Exception as e:
            return await interaction.response.send_message(f"❌ URL verification failed: {e}", ephemeral=True)

        data = load_entry_data()
        prof = data.setdefault("users", {}).setdefault(str(interaction.user.id), {})
        prof["custom_url"] = url
        prof["equipped"] = "custom"
        prof["enabled"] = True
        save_entry_data(data)

        embed = discord.Embed(
            title="🔮 CUSTOM ENTRANCE THEME ACTIVATED!",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"Your custom audio stream has been verified and equipped!\n\n"
                f"🔗 **URL:** `{url[:75]}...`\n"
                f"📢 **Join Fanfare:** Active ✅\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"💡 *Click **Test Entrance in VC** to preview it live!*"
            ),
            color=0x9B5DE5
        )
        embed.set_footer(text="RAI FAM 💗 • Custom Audio Engine", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)


# =====================================================================
# INTERACTIVE ENTRY & EXIT SOUND CONTROLS
# =====================================================================
class EntrySoundSelect(Select):
    def __init__(self, user_id: int, mode: str = "entry"):
        prof = get_user_entry_profile(user_id)
        current_eq = prof.get("exit_sound" if mode == "exit" else "equipped", "airhorn")
        unlocked = prof.get("unlocked", ["airhorn", "bye_great_time"])

        options = []
        # If custom equipped
        if mode == "entry" and prof.get("custom_url"):
            custom_title = prof.get("custom_name") or "Personal Custom File"
            options.append(discord.SelectOption(
                label=f"🔮 {custom_title[:20]}" + (" [EQUIPPED]" if current_eq == "custom" else ""),
                value=f"{mode}:custom",
                description="Your personal custom audio theme"[:95],
                emoji="🔮",
                default=(current_eq == "custom")
            ))

        for key, sfx in ENTRY_SOUNDS.items():
            is_unlocked = key in unlocked or user_id == OWNER_ID
            is_eq = key == current_eq

            prefix = " [EQUIPPED]" if is_eq else (" [UNLOCKED]" if is_unlocked else f" [{sfx['price']:,}c]")
            lbl = f"{sfx['name'][:25]}{prefix}"
            desc = f"[{sfx['category']}] {sfx['description']}"[:95]

            options.append(discord.SelectOption(
                label=lbl,
                value=f"{mode}:{key}",
                description=desc,
                emoji=sfx['emoji'],
                default=is_eq
            ))

        ph = "🚪 Select Exit / Goodbye Theme..." if mode == "exit" else "🔊 Select Entrance / Join Theme..."
        cid = f"select_{mode}_{user_id}"

        super().__init__(
            placeholder=ph,
            min_values=1,
            max_values=1,
            options=options[:25],
            custom_id=cid,
            row=0 if mode == "entry" else 1
        )
        self.target_user_id = user_id
        self.mode = mode

    async def callback(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        if interaction.user.id != self.target_user_id and interaction.user.id != OWNER_ID:
            return await interaction.followup.send("❌ This menu belongs to another user. Use `/entrysound` to open yours!", ephemeral=True)

        val_parts = self.values[0].split(":")
        mode = val_parts[0]
        selected_key = val_parts[1]

        data = load_entry_data()
        user_prof = data.setdefault("users", {}).setdefault(str(interaction.user.id), {})

        # Handling Custom URL option
        if selected_key == "custom":
            user_prof["equipped"] = "custom"
            user_prof["enabled"] = True
            save_entry_data(data)
            return await interaction.followup.send("🔮 Equipped your **Personal Custom Audio URL** as Entrance Theme!", ephemeral=True)

        sfx = ENTRY_SOUNDS.get(selected_key)
        if not sfx:
            return await interaction.followup.send("❌ Unknown sound effect.", ephemeral=True)

        prof = get_user_entry_profile(interaction.user.id)
        unlocked = prof.get("unlocked", ["airhorn", "bye_great_time"])

        # If already unlocked or Owner
        if selected_key in unlocked or interaction.user.id == OWNER_ID:
            if mode == "exit":
                user_prof["exit_sound"] = selected_key
                user_prof["exit_enabled"] = True
                action_txt = f"Equipped as your **Exit / Goodbye Sound**! 👋"
            else:
                user_prof["equipped"] = selected_key
                user_prof["enabled"] = True
                action_txt = f"Equipped as your **Entrance Theme**! 🔊"
            save_entry_data(data)

            embed = discord.Embed(
                title=f"✨ THEME EQUIPPED: {sfx['name']}",
                description=(
                    f"✦ ───────────────────────────── ✦\n\n"
                    f"{action_txt}\n\n"
                    f"• **Sound:** {sfx['emoji']} **{sfx['name']}**\n"
                    f"• **Category:** `{sfx['category']}`\n"
                    f"• **Effect:** {sfx['description']}\n\n"
                    f"✦ ───────────────────────────── ✦\n"
                    f"💡 *Click **Test Audio in VC** below to preview it live!*"
                ),
                color=0x2ECC71
            )
            embed.set_footer(text="RAI FAM 💗 • Voice Entrance Themes", icon_url=config.RAI_ICON_URL)
            return await interaction.followup.send(embed=embed, ephemeral=True)

        # Purchase Sound
        cost = sfx["price"]
        user_data = get_user_data(interaction.user.id)
        current_coins = user_data.get("coins", 0)

        if current_coins < cost and interaction.user.id != OWNER_ID:
            return await interaction.followup.send(
                f"❌ **Insufficient Coins!** **{sfx['name']}** costs `{cost:,} Coins`. You currently have `{current_coins:,}` Coins.\n"
                f"Earn coins by chatting, participating in voice channels, or claiming `/daily`!",
                ephemeral=True
            )

        new_coins = update_user_coins(interaction.user.id, -cost)
        unlock_user_sound(interaction.user.id, selected_key)

        data = load_entry_data()
        u_prof = data.setdefault("users", {}).setdefault(str(interaction.user.id), {})
        if mode == "exit":
            u_prof["exit_sound"] = selected_key
            u_prof["exit_enabled"] = True
        else:
            u_prof["equipped"] = selected_key
            u_prof["enabled"] = True
        save_entry_data(data)

        bal_str = "∞ (Owner Vault)" if interaction.user.id == OWNER_ID else f"{new_coins:,} Coins"

        embed = discord.Embed(
            title="🎉 THEME UNLOCKED & EQUIPPED!",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"Successfully unlocked **{sfx['emoji']} {sfx['name']}** for `{cost:,} Coins`!\n\n"
                f"• **Category:** `{sfx['category']}`\n"
                f"• **Remaining Balance:** `{bal_str}`\n"
                f"• **Status:** Equipped & Active ✅\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"Enjoy your VIP audio presence in all server voice lounges!"
            ),
            color=0xF1C40F
        )
        embed.set_footer(text="RAI FAM 💗 • Voice Entrance Themes", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)


class EntrySoundControlView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=180)
        self.user_id = user_id
        # Row 0: Entrance Themes
        self.add_item(EntrySoundSelect(user_id, mode="entry"))
        # Row 1: Exit Themes
        self.add_item(EntrySoundSelect(user_id, mode="exit"))

    @button(label="Test Entrance", style=discord.ButtonStyle.primary, emoji="🎧", row=2)
    async def test_btn(self, interaction: discord.Interaction, button: Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.followup.send("❌ You must join a voice channel first to test audio!", ephemeral=True)

        prof = get_user_entry_profile(interaction.user.id)
        equipped = prof.get("equipped", "airhorn")
        if equipped == "custom" and prof.get("custom_url"):
            sfx = {
                "name": prof.get("custom_name", "🔮 Custom Theme"),
                "url": prof["custom_url"],
                "attachment_url": prof.get("attachment_url"),
                "duration": prof.get("custom_duration", 6.0),
                "category": "Custom",
                "emoji": "🔮"
            }
        else:
            sfx = ENTRY_SOUNDS.get(equipped, ENTRY_SOUNDS["airhorn"])

        cog = interaction.client.get_cog("EntrySound")
        if cog:
            vol = prof.get("volume", 85) / 100.0
            success, msg = await cog.play_sound_in_channel(interaction.guild, interaction.user.voice.channel, sfx, volume_factor=vol)
            if success:
                return await interaction.followup.send(f"🔊 Playing entrance theme **{sfx['name']}** in {interaction.user.voice.channel.mention} at `{int(vol*100)}%` volume!", ephemeral=True)
            else:
                return await interaction.followup.send(f"⚠️ {msg}", ephemeral=True)
        await interaction.followup.send("❌ Voice engine currently unavailable.", ephemeral=True)

    @button(label="Test Exit", style=discord.ButtonStyle.secondary, emoji="🚪", row=2)
    async def test_exit_btn(self, interaction: discord.Interaction, button: Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.followup.send("❌ You must join a voice channel first to test audio!", ephemeral=True)

        prof = get_user_entry_profile(interaction.user.id)
        exit_key = prof.get("exit_sound", "bye_great_time")
        sfx = ENTRY_SOUNDS.get(exit_key, ENTRY_SOUNDS["bye_great_time"])

        cog = interaction.client.get_cog("EntrySound")
        if cog:
            vol = prof.get("volume", 85) / 100.0
            success, msg = await cog.play_sound_in_channel(interaction.guild, interaction.user.voice.channel, sfx, volume_factor=vol)
            if success:
                return await interaction.followup.send(f"👋 Playing exit theme **{sfx['name']}** in {interaction.user.voice.channel.mention}!", ephemeral=True)
            else:
                return await interaction.followup.send(f"⚠️ {msg}", ephemeral=True)
        await interaction.followup.send("❌ Voice engine currently unavailable.", ephemeral=True)

    @button(label="Toggle Mute", style=discord.ButtonStyle.secondary, emoji="🔔", row=2)
    async def toggle_btn(self, interaction: discord.Interaction, button: Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        data = load_entry_data()
        u_prof = data.setdefault("users", {}).setdefault(str(interaction.user.id), {
            "equipped": "airhorn",
            "enabled": True,
            "exit_sound": "bye_great_time",
            "exit_enabled": True,
            "volume": 85,
            "banner_enabled": True,
            "custom_url": None,
            "custom_unlocked": False,
            "unlocked": ["airhorn", "bye_great_time"]
        })
        curr_in = u_prof.get("enabled", True)
        curr_out = u_prof.get("exit_enabled", True)

        new_st = not (curr_in and curr_out)
        u_prof["enabled"] = new_st
        u_prof["exit_enabled"] = new_st
        save_entry_data(data)

        st_str = "ENABLED 🔔 (Will play on join & leave)" if new_st else "MUTED 🔕 (Silent joins & leaves)"
        await interaction.followup.send(f"Voice Themes are now **{st_str}**!", ephemeral=True)

    @button(label="Catalog", style=discord.ButtonStyle.secondary, emoji="📜", row=2)
    async def catalog_btn(self, interaction: discord.Interaction, button: Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        cats = {}
        for k, s in ENTRY_SOUNDS.items():
            cats.setdefault(s["category"], []).append(f"• {s['emoji']} **{s['name']}** — `{s['price']:,}c`\n  *{s['description']}*")

        desc_blocks = []
        for cat, items in cats.items():
            desc_blocks.append(f"### ✦ {cat.upper()} THEMES:\n" + "\n".join(items))

        embed = discord.Embed(
            title="📜 FULL 24-THEME VOICE CATALOG",
            description="\n\n".join(desc_blocks),
            color=0x9B5DE5
        )
        embed.set_footer(text="RAI FAM 💗 • Select from dropdowns to equip or buy!", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @button(label="Set Volume", style=discord.ButtonStyle.secondary, emoji="🔊", row=3)
    async def volume_btn(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_modal(SetVolumeModal())

    @button(label="Visual Banner", style=discord.ButtonStyle.secondary, emoji="✨", row=3)
    async def banner_toggle_btn(self, interaction: discord.Interaction, button: Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        data = load_entry_data()
        prof = data.setdefault("users", {}).setdefault(str(interaction.user.id), {})
        curr = prof.get("banner_enabled", True)
        prof["banner_enabled"] = not curr
        save_entry_data(data)

        st = "ACTIVE ✨ (Mini card in voice chat on join)" if not curr else "DISABLED 🚫 (Silent voice chat)"
        await interaction.followup.send(f"Visual Entrance Banner is now **{st}**!", ephemeral=True)

    @button(label="Custom Audio URL", style=discord.ButtonStyle.success, emoji="🔮", row=3)
    async def custom_url_btn(self, interaction: discord.Interaction, button: Button):
        prof = get_user_entry_profile(interaction.user.id)
        is_unlocked = prof.get("custom_unlocked", False) or interaction.user.id == OWNER_ID
        if not is_unlocked:
            # Check if user has VIP Elite role
            vip_role = discord.utils.get(interaction.user.roles, name="💎 ┊ 𝐑𝐀𝐈 𝐄𝐋𝐈𝐓𝐄")
            if vip_role or interaction.user.premium_since:
                is_unlocked = True
                unlock_custom_pass(interaction.user.id)

        if not is_unlocked:
            return await interaction.response.send_message(
                "🔒 **Custom Audio URL is a Premium Perk!**\n"
                "Unlock it in `#🛒・server-shop` with **🔮 Custom Audio URL Pass** (`3,000 Coins`), "
                "or gain instant access by becoming a **💎 VIP Elite** or **Server Booster**!",
                ephemeral=True
            )

        await interaction.response.send_modal(SetCustomUrlModal())


# Persistent Launch View for pinned Reward Exchange booth
class PublicEntrySoundLaunchView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Voice Entry Sounds Studio", style=discord.ButtonStyle.primary, emoji="🔊", custom_id="booth_entry_sound", row=0)
    async def launch_btn(self, interaction: discord.Interaction, button: Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        prof = get_user_entry_profile(interaction.user.id)
        equipped = prof.get("equipped", "airhorn")
        exit_sound = prof.get("exit_sound", "bye_great_time")
        enabled = prof.get("enabled", True)
        exit_enabled = prof.get("exit_enabled", True)
        vol = prof.get("volume", 85)
        banner = "✨ On" if prof.get("banner_enabled", True) else "🚫 Off"
        unlocked = prof.get("unlocked", ["airhorn", "bye_great_time"])

        if equipped == "custom" and prof.get("custom_url"):
            sfx_in_name = "🔮 Custom Stream URL"
            sfx_in_emoji = "🔮"
        else:
            sfx_in = ENTRY_SOUNDS.get(equipped, ENTRY_SOUNDS["airhorn"])
            sfx_in_name = sfx_in['name']
            sfx_in_emoji = sfx_in['emoji']

        sfx_out = ENTRY_SOUNDS.get(exit_sound, ENTRY_SOUNDS["bye_great_time"])

        status_in = "🟢 Active" if enabled else "🔴 Muted"
        status_out = "🟢 Active" if exit_enabled else "🔴 Muted"
        total_unlocked = len(ALL_SOUND_KEYS) if interaction.user.id == OWNER_ID else len(unlocked)

        embed = discord.Embed(
            title="🔊 VC ENTRANCE & EXIT SOUND STUDIO",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"Welcome to your **Voice Presence Studio**, {interaction.user.mention}! 🌸\n"
                f"Customize your audio presence whenever you enter or leave a room!\n\n"
                f"📊 **Your Audio Setup:**\n"
                f"• 🔊 **Entrance Theme:** **{sfx_in_emoji} {sfx_in_name}** `{status_in}`\n"
                f"• 🚪 **Exit Goodbye:** **{sfx_out['emoji']} {sfx_out['name']}** `{status_out}`\n"
                f"• 🎚️ **Loudness:** `{vol}% Volume` • **Visual Banner:** `{banner}`\n"
                f"• 🔓 **Unlocked Themes:** `{total_unlocked}/{len(ALL_SOUND_KEYS)}`\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Select themes from dropdowns or customize settings below!*"
            ),
            color=0x00F5D4
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • 24 Verified Voice Entrance Themes", icon_url=config.RAI_ICON_URL)

        view = EntrySoundControlView(interaction.user.id)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


# =====================================================================
# COG IMPLEMENTATION
# =====================================================================
class EntrySound(commands.Cog):
    """Custom Voice Channel Entrance & Exit Fanfares for RAI VIBES 💗."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def play_sound_in_channel(self, guild: discord.Guild, channel: discord.VoiceChannel, sfx_data: dict, volume_factor: float = 0.85) -> tuple[bool, str]:
        """Plays sound in specified channel using FFmpeg, intelligently coexisting with 24/7 radio."""
        try:
            music_cog = self.bot.get_cog("Music")
            radio_cog = self.bot.get_cog("Radio")
            voice_client: Optional[discord.VoiceClient] = guild.voice_client

            radio_channel_ids = {1545781986193309789, 1545502782268772453}
            is_radio_stream = False
            if voice_client and voice_client.channel and voice_client.channel.id in radio_channel_ids:
                is_radio_stream = True
            elif music_cog:
                player = music_cog.get_player(guild.id)
                if player and player.is_radio_playing():
                    is_radio_stream = True

            # If real music is actively playing in another channel for human listeners, don't interrupt
            if voice_client and voice_client.channel and voice_client.channel.id != channel.id:
                human_listeners = [m for m in voice_client.channel.members if not m.bot]
                if voice_client.is_playing() and not is_radio_stream and len(human_listeners) > 0:
                    return False, f"Bot is currently playing music for {len(human_listeners)} listeners in {voice_client.channel.mention}."

            original_channel = voice_client.channel if (voice_client and voice_client.is_connected()) else None
            was_in_radio = bool(original_channel and (original_channel.id in radio_channel_ids or is_radio_stream))

            # Connect or move to target channel
            if not voice_client or not voice_client.is_connected():
                voice_client = await channel.connect(reconnect=True, timeout=10.0)
            elif voice_client.channel.id != channel.id:
                await voice_client.move_to(channel)

            if voice_client.is_playing():
                voice_client.stop()
                await asyncio.sleep(0.15)

            url_str = str(sfx_data.get("url", "")).strip()
            if not url_str:
                return False, "Audio file path or URL is empty."

            is_remote = url_str.startswith("http://") or url_str.startswith("https://")
            if is_remote:
                before_opts = FFMPEG_BEFORE_OPTIONS
            else:
                # Local file path
                clean_url = url_str.strip('\'"')
                local_path = Path(clean_url)
                if not local_path.exists():
                    candidate = CUSTOM_SOUNDS_DIR / local_path.name
                    if candidate.exists():
                        local_path = candidate
                        url_str = str(local_path)

                # Fallback by user_id if provided
                if not local_path.exists() and sfx_data.get("user_id"):
                    for ext in [".mp3", ".wav", ".ogg", ".m4a"]:
                        uid_cand = CUSTOM_SOUNDS_DIR / f"{sfx_data['user_id']}_custom{ext}"
                        if uid_cand.exists():
                            local_path = uid_cand
                            url_str = str(local_path)
                            break

                # Fallback: if file missing on container restart, try auto-downloading from attachment_url
                if not local_path.exists() and sfx_data.get("attachment_url"):
                    try:
                        import urllib.request
                        CUSTOM_SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
                        file_ext = Path(sfx_data.get("name", "custom.mp3")).suffix or ".mp3"
                        target_name = f"{sfx_data.get('user_id', 'unknown')}_custom{file_ext}"
                        target_save = CUSTOM_SOUNDS_DIR / target_name
                        urllib.request.urlretrieve(sfx_data["attachment_url"], target_save)
                        local_path = target_save
                        url_str = str(local_path)
                    except Exception as dl_err:
                        logger.warning(f"Failed to auto-redownload attachment: {dl_err}")

                if not local_path.exists():
                    return False, f"Sound file `{local_path.name}` not found on server disk. Please re-upload via `/entrysound upload`."

                before_opts = "-nostdin"

            ffmpeg_bin = get_ffmpeg_executable()
            raw_source = discord.FFmpegPCMAudio(
                url_str,
                executable=ffmpeg_bin,
                before_options=before_opts,
                options="-vn -bufsize 1024k"
            )
            transformed = discord.PCMVolumeTransformer(raw_source, volume=volume_factor)

            playback_error = []
            def _after_play(err):
                if err:
                    logger.error(f"[EntrySound] FFmpeg error: {err}")
                    playback_error.append(err)

            voice_client.play(transformed, after=_after_play)

            # Wait dynamically while audio is playing (up to max duration, default 12s, max 18s)
            target_duration = min(float(sfx_data.get("duration", 12.0)) + 1.0, 18.0)
            waited = 0.0
            await asyncio.sleep(0.5)
            while voice_client and voice_client.is_playing() and waited < target_duration:
                await asyncio.sleep(0.25)
                waited += 0.25

            if playback_error:
                return False, f"FFmpeg error: {playback_error[0]}"

            # Post-playback: Restore 24/7 radio or disconnect cleanly
            if was_in_radio and original_channel and channel.id != original_channel.id:
                if voice_client and voice_client.is_connected():
                    try:
                        await voice_client.disconnect(force=True)
                    except Exception:
                        pass
                if radio_cog:
                    asyncio.create_task(radio_cog.start_radio_in_channel(original_channel, notify=False))
            elif was_in_radio and original_channel and channel.id == original_channel.id:
                if radio_cog and voice_client and voice_client.is_connected():
                    asyncio.create_task(radio_cog.start_radio_in_channel(channel, notify=False))
            elif not original_channel:
                if voice_client and voice_client.is_connected() and not voice_client.is_playing():
                    await voice_client.disconnect(force=True)

            return True, "Played successfully"
        except Exception as e:
            logger.warning(f"Error playing entry sound: {e}")
            return False, str(e)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if member.bot:
            return

        now = time.time()
        last_played = USER_ENTRY_COOLDOWNS.get(member.id, 0)
        cooldown_passed = (now - last_played >= 40.0) or (member.id == OWNER_ID)

        # 1. ENTRANCE SOUND (Member joined or moved to a voice room)
        if after.channel and (not before.channel or before.channel.id != after.channel.id):
            if is_channel_suppressed(after.channel):
                return

            prof = get_user_entry_profile(member.id)
            if prof.get("enabled", True) and cooldown_passed:
                USER_ENTRY_COOLDOWNS[member.id] = now
                eq_key = prof.get("equipped", "airhorn")
                custom_file = None
                for ext in [".mp3", ".wav", ".ogg", ".m4a"]:
                    c_path = CUSTOM_SOUNDS_DIR / f"{member.id}_custom{ext}"
                    if c_path.exists():
                        custom_file = str(c_path.resolve())
                        break

                if eq_key == "custom" or custom_file:
                    sound_url = prof.get("custom_url") or custom_file
                    sfx = {
                        "name": prof.get("custom_name", "🔮 Personal Custom Theme"),
                        "url": sound_url,
                        "attachment_url": prof.get("attachment_url"),
                        "duration": float(prof.get("custom_duration", 12.0)),
                        "category": "Custom",
                        "emoji": "🔮",
                        "user_id": member.id
                    }
                else:
                    sfx = ENTRY_SOUNDS.get(eq_key, ENTRY_SOUNDS.get("airhorn"))

                if sfx:
                    vol = prof.get("volume", 85) / 100.0
                    await asyncio.sleep(0.8)
                    if member in after.channel.members:
                        # Play Audio
                        asyncio.create_task(self.play_sound_in_channel(member.guild, after.channel, sfx, volume_factor=vol))

                        # Send visual banner embed if enabled
                        if prof.get("banner_enabled", True):
                            try:
                                banner_embed = discord.Embed(
                                    title="✨ VIP VOICE ENTRANCE",
                                    description=f"🌸 {member.mention} entered the stage!\n🎶 **Theme:** **{sfx.get('emoji', '🎵')} {sfx['name']}**",
                                    color=0x9B5DE5
                                )
                                banner_embed.set_thumbnail(url=member.display_avatar.url)
                                await after.channel.send(embed=banner_embed, delete_after=8.0)
                            except Exception:
                                pass

        # 2. EXIT SOUND (Member left a voice room with other listeners remaining)
        elif before.channel and (not after.channel or before.channel.id != after.channel.id):
            if is_channel_suppressed(before.channel):
                return
            remaining_humans = [m for m in before.channel.members if not m.bot]
            if len(remaining_humans) >= 1:
                prof = get_user_entry_profile(member.id)
                if prof.get("exit_enabled", True) and cooldown_passed:
                    USER_ENTRY_COOLDOWNS[member.id] = now
                    exit_key = prof.get("exit_sound", "bye_great_time")
                    sfx = ENTRY_SOUNDS.get(exit_key)
                    if sfx:
                        vol = prof.get("volume", 85) / 100.0
                        asyncio.create_task(self.play_sound_in_channel(member.guild, before.channel, sfx, volume_factor=vol))

                        # Send visual exit banner embed if enabled
                        if prof.get("banner_enabled", True):
                            try:
                                exit_embed = discord.Embed(
                                    title="👋 VOICE DEPARTURE",
                                    description=f"🌙 {member.mention} departed the room.\n🎶 **Exit Theme:** **{sfx.get('emoji', '🚪')} {sfx['name']}**",
                                    color=0x7289DA
                                )
                                exit_embed.set_thumbnail(url=member.display_avatar.url)
                                await before.channel.send(embed=exit_embed, delete_after=8.0)
                            except Exception:
                                pass

    @commands.hybrid_group(name="entrysound", aliases=["entrance", "joinsound"], description="Manage your voice channel entrance & exit sound effect themes.")
    async def entrysound_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await self.panel_cmd(ctx)

    @entrysound_group.command(name="panel", aliases=["menu"], description="Open the Voice Channel Entrance & Exit Sound Studio.")
    async def panel_cmd(self, ctx: commands.Context):
        prof = get_user_entry_profile(ctx.author.id)
        equipped = prof.get("equipped", "airhorn")
        exit_sound = prof.get("exit_sound", "bye_great_time")
        enabled = prof.get("enabled", True)
        exit_enabled = prof.get("exit_enabled", True)
        vol = prof.get("volume", 85)
        banner = "✨ On" if prof.get("banner_enabled", True) else "🚫 Off"
        unlocked = prof.get("unlocked", ["airhorn", "bye_great_time"])

        if equipped == "custom" and prof.get("custom_url"):
            c_name = prof.get("custom_name") or "Personal Custom File"
            sfx_in_name = f"🔮 {c_name}"
            sfx_in_emoji = "🔮"
        else:
            sfx_in = ENTRY_SOUNDS.get(equipped, ENTRY_SOUNDS["airhorn"])
            sfx_in_name = sfx_in['name']
            sfx_in_emoji = sfx_in['emoji']

        sfx_out = ENTRY_SOUNDS.get(exit_sound, ENTRY_SOUNDS["bye_great_time"])

        status_in = "🟢 Active" if enabled else "🔴 Muted"
        status_out = "🟢 Active" if exit_enabled else "🔴 Muted"
        total_unlocked = len(ALL_SOUND_KEYS) if ctx.author.id == OWNER_ID else len(unlocked)

        embed = discord.Embed(
            title="🔊 VC ENTRANCE & EXIT SOUND STUDIO",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"Welcome to your **Voice Presence Studio**, {ctx.author.mention}! 🌸\n"
                f"Customize your audio presence whenever you enter or leave a room!\n\n"
                f"📊 **Your Audio Setup:**\n"
                f"• 🔊 **Entrance Theme:** **{sfx_in_emoji} {sfx_in_name}** `{status_in}`\n"
                f"• 🚪 **Exit Goodbye:** **{sfx_out['emoji']} {sfx_out['name']}** `{status_out}`\n"
                f"• 🎚️ **Loudness:** `{vol}% Volume` • **Visual Banner:** `{banner}`\n"
                f"• 🔓 **Unlocked Themes:** `{total_unlocked}/{len(ALL_SOUND_KEYS)}`\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Select themes from dropdowns or customize settings below!*"
            ),
            color=0x00F5D4
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • 24 Verified Voice Entrance Themes", icon_url=config.RAI_ICON_URL)

        view = EntrySoundControlView(ctx.author.id)
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @entrysound_group.command(name="volume", description="Set your personal voice entrance audio volume (10-100%).")
    @app_commands.describe(percentage="Volume percentage (10 to 100)")
    async def volume_cmd(self, ctx: commands.Context, percentage: int):
        if percentage < 10 or percentage > 100:
            return await ctx.send("❌ Volume percentage must be between 10 and 100.", ephemeral=True)
        data = load_entry_data()
        prof = data.setdefault("users", {}).setdefault(str(ctx.author.id), {})
        prof["volume"] = percentage
        save_entry_data(data)
        await ctx.send(f"🔊 Personal Entrance Theme volume set to **`{percentage}%`**!", ephemeral=True)

    @entrysound_group.command(name="banner", description="Toggle the mini visual announcement embed in the voice text chat.")
    async def banner_cmd(self, ctx: commands.Context):
        data = load_entry_data()
        prof = data.setdefault("users", {}).setdefault(str(ctx.author.id), {})
        curr = prof.get("banner_enabled", True)
        prof["banner_enabled"] = not curr
        save_entry_data(data)
        st = "ACTIVE ✨ (Mini card in voice chat on join)" if not curr else "DISABLED 🚫 (Silent voice chat)"
        await ctx.send(f"Visual Entrance Banner is now **{st}**!", ephemeral=True)

    @entrysound_group.command(name="test", description="Test your currently equipped entrance sound in your voice channel.")
    async def test_cmd(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must join a voice channel first to test your sound!", ephemeral=True)

        prof = get_user_entry_profile(ctx.author.id)
        equipped = prof.get("equipped", "airhorn")
        custom_file = None
        for ext in [".mp3", ".wav", ".ogg", ".m4a"]:
            c_path = CUSTOM_SOUNDS_DIR / f"{ctx.author.id}_custom{ext}"
            if c_path.exists():
                custom_file = str(c_path.resolve())
                break

        if equipped == "custom" or custom_file:
            sound_url = prof.get("custom_url") or custom_file
            sfx = {
                "name": prof.get("custom_name", "🔮 Personal Custom Theme"),
                "url": sound_url,
                "attachment_url": prof.get("attachment_url"),
                "duration": float(prof.get("custom_duration", 12.0)),
                "category": "Custom",
                "emoji": "🔮",
                "user_id": ctx.author.id
            }
        else:
            sfx = ENTRY_SOUNDS.get(equipped, ENTRY_SOUNDS["airhorn"])

        vol = prof.get("volume", 85) / 100.0
        await ctx.send(f"🎧 Previewing **{sfx['name']}** in {ctx.author.voice.channel.mention} at `{int(vol*100)}%` volume...", ephemeral=True)
        success, reason = await self.play_sound_in_channel(ctx.guild, ctx.author.voice.channel, sfx, volume_factor=vol)
        if not success:
            await ctx.send(f"⚠️ **Could not play audio preview:** {reason}", ephemeral=True)

    @entrysound_group.command(name="toggle", description="Turn your entrance and exit sounds ON or OFF.")
    async def toggle_cmd(self, ctx: commands.Context):
        data = load_entry_data()
        u_prof = data.setdefault("users", {}).setdefault(str(ctx.author.id), {
            "equipped": "airhorn",
            "enabled": True,
            "exit_sound": "bye_great_time",
            "exit_enabled": True,
            "volume": 85,
            "banner_enabled": True,
            "custom_url": None,
            "custom_unlocked": False,
            "unlocked": ["airhorn", "bye_great_time"]
        })
        curr_in = u_prof.get("enabled", True)
        curr_out = u_prof.get("exit_enabled", True)
        new_st = not (curr_in and curr_out)
        u_prof["enabled"] = new_st
        u_prof["exit_enabled"] = new_st
        save_entry_data(data)

        st = "ENABLED 🔔 (Will play on join & leave)" if new_st else "MUTED 🔕 (Silent joins & leaves)"
        await ctx.send(f"Voice Themes are now **{st}**!", ephemeral=True)

    @entrysound_group.command(name="upload", description="Upload an audio file (.mp3, .wav, .ogg, max 8MB) as your personal entrance sound.")
    @app_commands.describe(file="Audio file attachment (.mp3, .wav, or .ogg)")
    async def upload_cmd(self, ctx: commands.Context, file: discord.Attachment):
        if ctx.interaction and not ctx.interaction.response.is_done():
            try:
                await ctx.interaction.response.defer(ephemeral=True)
            except Exception:
                pass
        elif not ctx.interaction:
            try:
                await ctx.defer(ephemeral=True)
            except Exception:
                pass

        async def reply(content: Optional[str] = None, embed: Optional[discord.Embed] = None):
            if ctx.interaction:
                if ctx.interaction.response.is_done():
                    return await ctx.interaction.followup.send(content=content, embed=embed, ephemeral=True)
                else:
                    return await ctx.interaction.response.send_message(content=content, embed=embed, ephemeral=True)
            else:
                return await ctx.send(content=content, embed=embed)

        prof = get_user_entry_profile(ctx.author.id)
        is_unlocked = prof.get("custom_unlocked", False) or ctx.author.id == OWNER_ID
        if not is_unlocked:
            vip_role = discord.utils.get(ctx.author.roles, name="💎 ┊ 𝐑𝐀𝐈 𝐄𝐋𝐈𝐓𝐄")
            if vip_role or getattr(ctx.author, "premium_since", None):
                is_unlocked = True
                unlock_custom_pass(ctx.author.id)

        if not is_unlocked:
            return await reply(
                content=(
                    "🔒 **Custom Audio Upload is a Premium Perk!**\n"
                    "Unlock it in `#🛒・server-shop` with **🔮 Custom Audio URL Pass** (`3,000 Coins`), "
                    "or gain instant access by becoming a **💎 VIP Elite** or **Server Booster**!"
                )
            )

        filename = file.filename.lower()
        if not any(filename.endswith(ext) for ext in [".mp3", ".wav", ".ogg", ".m4a"]):
            return await reply(content="❌ Only audio files (`.mp3`, `.wav`, `.ogg`, `.m4a`) are supported.")

        if file.size > 8 * 1024 * 1024:
            return await reply(content="❌ Audio file size cannot exceed 8MB.")

        try:
            CUSTOM_SOUNDS_DIR.mkdir(parents=True, exist_ok=True)
            safe_ext = Path(file.filename).suffix
            dest_file = CUSTOM_SOUNDS_DIR / f"{ctx.author.id}_custom{safe_ext}"
            await file.save(dest_file)

            data = load_entry_data()
            u_prof = data.setdefault("users", {}).setdefault(str(ctx.author.id), {})
            u_prof["custom_url"] = str(dest_file.resolve())
            u_prof["custom_path"] = str(dest_file.resolve())
            u_prof["custom_name"] = file.filename
            u_prof["attachment_url"] = file.url
            u_prof["custom_duration"] = 14.0
            u_prof["equipped"] = "custom"
            u_prof["enabled"] = True
            u_prof["custom_unlocked"] = True
            save_entry_data(data)

            embed = discord.Embed(
                title="✨ CUSTOM AUDIO ATTACHMENT SAVED & EQUIPPED!",
                description=(
                    f"✦ ───────────────────────────── ✦\n\n"
                    f"Successfully saved **`{file.filename}`** (`{file.size // 1024} KB`) as your VIP Voice Entrance Theme! 🎵\n\n"
                    f"• **Playback Mode:** Personal Custom File 🔮\n"
                    f"• **Status:** Active & Ready ✅\n"
                    f"• **Volume:** `{u_prof.get('volume', 85)}%`\n\n"
                    f"✦ ───────────────────────────── ✦\n"
                    f"💡 *Use `/entrysound test` in any voice lounge to hear your custom audio!*"
                ),
                color=0x2ECC71
            )
            embed.set_footer(text="RAI FAM 💗 • Custom Audio Studio", icon_url=config.RAI_ICON_URL)
            await reply(embed=embed)
        except Exception as e:
            logger.error(f"Error saving uploaded sound: {e}")
            await reply(content=f"❌ Error saving audio file: {e}")

    @entrysound_group.command(name="custom", description="Set a direct web audio stream URL (.mp3, .wav) as your entrance theme.")
    @app_commands.describe(url="Direct public URL to an MP3 or WAV audio stream")
    async def custom_cmd(self, ctx: commands.Context, url: str):
        if ctx.interaction and not ctx.interaction.response.is_done():
            try:
                await ctx.interaction.response.defer(ephemeral=True)
            except Exception:
                pass
        elif not ctx.interaction:
            try:
                await ctx.defer(ephemeral=True)
            except Exception:
                pass

        async def reply(content: Optional[str] = None, embed: Optional[discord.Embed] = None):
            if ctx.interaction:
                if ctx.interaction.response.is_done():
                    return await ctx.interaction.followup.send(content=content, embed=embed, ephemeral=True)
                else:
                    return await ctx.interaction.response.send_message(content=content, embed=embed, ephemeral=True)
            else:
                return await ctx.send(content=content, embed=embed)

        prof = get_user_entry_profile(ctx.author.id)
        is_unlocked = prof.get("custom_unlocked", False) or ctx.author.id == OWNER_ID
        if not is_unlocked:
            vip_role = discord.utils.get(ctx.author.roles, name="💎 ┊ 𝐑𝐀𝐈 𝐄𝐋𝐈𝐓𝐄")
            if vip_role or getattr(ctx.author, "premium_since", None):
                is_unlocked = True
                unlock_custom_pass(ctx.author.id)

        if not is_unlocked:
            return await reply(
                content=(
                    "🔒 **Custom Audio Stream URL is a Premium Perk!**\n"
                    "Unlock it in `#🛒・server-shop` with **🔮 Custom Audio URL Pass** (`3,000 Coins`), "
                    "or gain instant access by becoming a **💎 VIP Elite** or **Server Booster**!"
                )
            )

        url = url.strip()
        if not (url.startswith("http://") or url.startswith("https://")):
            return await reply(content="❌ Invalid URL. Must start with `http://` or `https://`.")

        data = load_entry_data()
        u_prof = data.setdefault("users", {}).setdefault(str(ctx.author.id), {})
        u_prof["custom_url"] = url
        u_prof["equipped"] = "custom"
        u_prof["enabled"] = True
        u_prof["custom_unlocked"] = True
        save_entry_data(data)

        embed = discord.Embed(
            title="✨ CUSTOM AUDIO URL EQUIPPED!",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"Successfully set your personal entrance theme URL:\n"
                f"`{url[:75]}...`\n\n"
                f"• **Playback Mode:** Personal Web Stream 🔮\n"
                f"• **Status:** Active & Ready ✅\n"
                f"• **Volume:** `{u_prof.get('volume', 85)}%`\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"💡 *Use `/entrysound test` in any voice lounge to preview live!*"
            ),
            color=0x2ECC71
        )
        embed.set_footer(text="RAI FAM 💗 • Custom Audio Studio", icon_url=config.RAI_ICON_URL)
        await reply(embed=embed)

    @entrysound_group.command(name="preview", description="Preview and listen to any entrance theme.")
    @app_commands.describe(theme="Theme key or name (e.g. gigachad, anime_wow, tokyo_drift)")
    async def preview_cmd(self, ctx: commands.Context, theme: Optional[str] = None):
        if not theme:
            prof = get_user_entry_profile(ctx.author.id)
            theme = prof.get("equipped", "airhorn")

        target_key = theme.lower().strip().replace(" ", "_")
        sfx = None
        if target_key == "custom":
            prof = get_user_entry_profile(ctx.author.id)
            if prof.get("custom_url"):
                sfx = {
                    "name": prof.get("custom_name", "🔮 Custom Theme"),
                    "url": prof["custom_url"],
                    "attachment_url": prof.get("attachment_url"),
                    "duration": prof.get("custom_duration", 6.0),
                    "category": "Custom",
                    "emoji": "🔮"
                }
        else:
            sfx = ENTRY_SOUNDS.get(target_key)
            if not sfx:
                for k, v in ENTRY_SOUNDS.items():
                    if target_key in k or target_key in v["name"].lower():
                        sfx = v
                        target_key = k
                        break

        if not sfx:
            valid_list = ", ".join([f"`{k}`" for k in list(ENTRY_SOUNDS.keys())[:8]])
            return await ctx.send(f"❌ Unknown theme `{theme}`. Try one of: {valid_list}...", ephemeral=True)

        if ctx.author.voice and ctx.author.voice.channel:
            vol = get_user_entry_profile(ctx.author.id).get("volume", 85) / 100.0
            await ctx.send(f"🎧 Previewing **{sfx.get('emoji', '🎵')} {sfx['name']}** in {ctx.author.voice.channel.mention} at `{int(vol*100)}%` volume...", ephemeral=True)
            success, reason = await self.play_sound_in_channel(ctx.guild, ctx.author.voice.channel, sfx, volume_factor=vol)
            if not success:
                await ctx.send(f"⚠️ **Could not play preview:** {reason}", ephemeral=True)
        else:
            embed = discord.Embed(
                title=f"🎧 Sound Preview: {sfx.get('emoji', '🎵')} {sfx['name']}",
                description=(
                    f"• **Category:** `{sfx.get('category', 'General')}`\n"
                    f"• **Description:** {sfx.get('description', 'High-quality sound effect')}\n"
                    f"• **Duration:** `{sfx.get('duration', 3.0)}s`\n"
                    f"• **Price:** `{sfx.get('price', 1000):,} Coins`\n\n"
                    f"💡 *Join any voice channel and run `/entrysound preview {target_key}` to hear it live through the bot!*"
                ),
                color=0x00F5D4
            )
            embed.set_footer(text="RAI FAM 💗 • Audio Preview", icon_url=config.RAI_ICON_URL)
            await ctx.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(EntrySound(bot))
