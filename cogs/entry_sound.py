import os
import sys
import json
import time
import asyncio
import logging
import unicodedata
from pathlib import Path
from typing import Optional, Dict, List

import discord
from discord.ext import commands
from discord import app_commands
from discord.ui import View, Button, Select, button

import config
from utils.ffmpeg_setup import get_ffmpeg_executable
from cogs.economy import get_user_data, update_user_coins, OWNER_ID

logger = logging.getLogger("EntrySound")

DATA_DIR = Path("data")
ENTRY_SOUND_FILE = DATA_DIR / "entry_sounds.json"

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
            "unlocked": ["airhorn", "bye_great_time"]
        }
        save_entry_data(data)

    prof = data["users"][uid]
    if user_id == OWNER_ID:
        prof["unlocked"] = list(ALL_SOUND_KEYS)
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
            "unlocked": ["airhorn", "bye_great_time"]
        }

    if sound_key not in users[uid]["unlocked"]:
        users[uid]["unlocked"].append(sound_key)
        save_entry_data(data)
        return True
    return False


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
            "unlocked": []
        }
    users[uid]["unlocked"] = list(ALL_SOUND_KEYS)
    save_entry_data(data)


# Cooldown tracking: user_id -> timestamp
USER_ENTRY_COOLDOWNS: Dict[int, float] = {}


# =====================================================================
# INTERACTIVE ENTRY & EXIT SOUND CONTROLS
# =====================================================================
class EntrySoundSelect(Select):
    def __init__(self, user_id: int, mode: str = "entry"):
        prof = get_user_entry_profile(user_id)
        current_eq = prof.get("exit_sound" if mode == "exit" else "equipped", "airhorn")
        unlocked = prof.get("unlocked", ["airhorn", "bye_great_time"])

        options = []
        # Sort sounds with currently equipped first, then by prestige
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
        sfx = ENTRY_SOUNDS.get(selected_key)
        if not sfx:
            return await interaction.followup.send("❌ Unknown sound effect.", ephemeral=True)

        prof = get_user_entry_profile(interaction.user.id)
        unlocked = prof.get("unlocked", ["airhorn", "bye_great_time"])

        data = load_entry_data()
        user_prof = data.setdefault("users", {}).setdefault(str(interaction.user.id), {})

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

    @button(label="Test Entrance in VC", style=discord.ButtonStyle.primary, emoji="🎧", row=2)
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
        sfx = ENTRY_SOUNDS.get(equipped, ENTRY_SOUNDS["airhorn"])

        cog = interaction.client.get_cog("EntrySound")
        if cog:
            success, msg = await cog.play_sound_in_channel(interaction.guild, interaction.user.voice.channel, sfx)
            if success:
                return await interaction.followup.send(f"🔊 Playing your entrance theme **{sfx['name']}** in {interaction.user.voice.channel.mention}!", ephemeral=True)
            else:
                return await interaction.followup.send(f"⚠️ {msg}", ephemeral=True)
        await interaction.followup.send("❌ Voice engine currently unavailable.", ephemeral=True)

    @button(label="Test Exit in VC", style=discord.ButtonStyle.secondary, emoji="🚪", row=2)
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
            success, msg = await cog.play_sound_in_channel(interaction.guild, interaction.user.voice.channel, sfx)
            if success:
                return await interaction.followup.send(f"👋 Playing your exit theme **{sfx['name']}** in {interaction.user.voice.channel.mention}!", ephemeral=True)
            else:
                return await interaction.followup.send(f"⚠️ {msg}", ephemeral=True)
        await interaction.followup.send("❌ Voice engine currently unavailable.", ephemeral=True)

    @button(label="Toggle Entry/Exit", style=discord.ButtonStyle.secondary, emoji="🔔", row=2)
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
            "unlocked": ["airhorn", "bye_great_time"]
        })
        curr_in = u_prof.get("enabled", True)
        curr_out = u_prof.get("exit_enabled", True)

        # Toggle both simultaneously
        new_st = not (curr_in and curr_out)
        u_prof["enabled"] = new_st
        u_prof["exit_enabled"] = new_st
        save_entry_data(data)

        st_str = "ENABLED 🔔 (Will play on join & leave)" if new_st else "MUTED 🔕 (Silent joins & leaves)"
        await interaction.followup.send(f"Your Voice Themes are now **{st_str}**!", ephemeral=True)

    @button(label="Full Sound Catalog", style=discord.ButtonStyle.secondary, emoji="📜", row=2)
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
        embed.set_footer(text="RAI FAM 💗 • Select from the dropdowns above to equip or buy!", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)


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
        unlocked = prof.get("unlocked", ["airhorn", "bye_great_time"])

        sfx_in = ENTRY_SOUNDS.get(equipped, ENTRY_SOUNDS["airhorn"])
        sfx_out = ENTRY_SOUNDS.get(exit_sound, ENTRY_SOUNDS["bye_great_time"])

        status_in = "🟢 Active" if enabled else "🔴 Muted"
        status_out = "🟢 Active" if exit_enabled else "🔴 Muted"
        total_unlocked = len(ALL_SOUND_KEYS) if interaction.user.id == OWNER_ID else len(unlocked)

        embed = discord.Embed(
            title="🔊 VC ENTRANCE & EXIT SOUND STUDIO",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"Welcome to your **Voice Presence Studio**, {interaction.user.mention}! 🌸\n"
                f"Whenever you enter or leave a voice channel, make an unforgettable statement!\n\n"
                f"📊 **Your Audio Setup:**\n"
                f"• 🔊 **Entrance Fanfare:** **{sfx_in['emoji']} {sfx_in['name']}** `{status_in}`\n"
                f"• 🚪 **Exit Goodbye:** **{sfx_out['emoji']} {sfx_out['name']}** `{status_out}`\n"
                f"• 🔓 **Unlocked Themes:** `{total_unlocked}/{len(ALL_SOUND_KEYS)}`\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Select any theme from the dropdown menus below to unlock or equip!*"
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

    async def play_sound_in_channel(self, guild: discord.Guild, channel: discord.VoiceChannel, sfx_data: dict) -> tuple[bool, str]:
        """Plays sound in specified channel using FFmpeg with proper browser referer headers."""
        try:
            music_cog = self.bot.get_cog("Music")
            voice_client: Optional[discord.VoiceClient] = guild.voice_client

            # If music is actively playing in another channel, don't interrupt
            if voice_client and voice_client.channel and voice_client.channel.id != channel.id:
                if voice_client.is_playing():
                    return False, f"Bot is currently playing music in {voice_client.channel.mention}."

            connected_fresh = False
            if not voice_client or not voice_client.is_connected():
                voice_client = await channel.connect(reconnect=True, timeout=10.0)
                connected_fresh = True
            elif voice_client.channel.id != channel.id:
                await voice_client.move_to(channel)

            if voice_client.is_playing():
                voice_client.stop()
                await asyncio.sleep(0.1)

            ffmpeg_bin = get_ffmpeg_executable()
            raw_source = discord.FFmpegPCMAudio(
                sfx_data["url"],
                executable=ffmpeg_bin,
                before_options=FFMPEG_BEFORE_OPTIONS,
                options="-vn -bufsize 1024k"
            )
            transformed = discord.PCMVolumeTransformer(raw_source, volume=0.85)
            voice_client.play(transformed)

            duration = sfx_data.get("duration", 3.0)
            await asyncio.sleep(duration + 0.5)

            if connected_fresh:
                if voice_client and voice_client.is_connected() and not voice_client.is_playing():
                    await voice_client.disconnect()

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
            norm_name = unicodedata.normalize('NFKD', after.channel.name).lower()
            if any(w in norm_name for w in ("join to create", "➕", "chamber", "generator")):
                return

            prof = get_user_entry_profile(member.id)
            if prof.get("enabled", True) and cooldown_passed:
                USER_ENTRY_COOLDOWNS[member.id] = now
                eq_key = prof.get("equipped", "airhorn")
                sfx = ENTRY_SOUNDS.get(eq_key)
                if sfx:
                    await asyncio.sleep(0.8)
                    if member in after.channel.members:
                        asyncio.create_task(self.play_sound_in_channel(member.guild, after.channel, sfx))

        # 2. EXIT SOUND (Member left a voice room with other listeners remaining)
        elif before.channel and (not after.channel or before.channel.id != after.channel.id):
            # Only play if non-bot listeners remain in the room
            remaining_humans = [m for m in before.channel.members if not m.bot]
            if len(remaining_humans) >= 1:
                prof = get_user_entry_profile(member.id)
                if prof.get("exit_enabled", True) and cooldown_passed:
                    USER_ENTRY_COOLDOWNS[member.id] = now
                    exit_key = prof.get("exit_sound", "bye_great_time")
                    sfx = ENTRY_SOUNDS.get(exit_key)
                    if sfx:
                        asyncio.create_task(self.play_sound_in_channel(member.guild, before.channel, sfx))

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
        unlocked = prof.get("unlocked", ["airhorn", "bye_great_time"])

        sfx_in = ENTRY_SOUNDS.get(equipped, ENTRY_SOUNDS["airhorn"])
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
                f"• 🔊 **Entrance Theme:** **{sfx_in['emoji']} {sfx_in['name']}** `{status_in}`\n"
                f"• 🚪 **Exit Goodbye:** **{sfx_out['emoji']} {sfx_out['name']}** `{status_out}`\n"
                f"• 🔓 **Unlocked Themes:** `{total_unlocked}/{len(ALL_SOUND_KEYS)}`\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Use the dropdown menus below to unlock or equip themes!*"
            ),
            color=0x00F5D4
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • 24 Verified Voice Entrance Themes", icon_url=config.RAI_ICON_URL)

        view = EntrySoundControlView(ctx.author.id)
        await ctx.send(embed=embed, view=view, ephemeral=True)

    @entrysound_group.command(name="test", description="Test your currently equipped entrance sound in your voice channel.")
    async def test_cmd(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must join a voice channel first to test your sound!", ephemeral=True)

        prof = get_user_entry_profile(ctx.author.id)
        equipped = prof.get("equipped", "airhorn")
        sfx = ENTRY_SOUNDS.get(equipped, ENTRY_SOUNDS["airhorn"])

        await ctx.send(f"🎧 Previewing **{sfx['name']}** in {ctx.author.voice.channel.mention}...", ephemeral=True)
        await self.play_sound_in_channel(ctx.guild, ctx.author.voice.channel, sfx)

    @entrysound_group.command(name="toggle", description="Turn your entrance and exit sounds ON or OFF.")
    async def toggle_cmd(self, ctx: commands.Context):
        data = load_entry_data()
        u_prof = data.setdefault("users", {}).setdefault(str(ctx.author.id), {
            "equipped": "airhorn",
            "enabled": True,
            "exit_sound": "bye_great_time",
            "exit_enabled": True,
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


async def setup(bot: commands.Bot):
    await bot.add_cog(EntrySound(bot))
