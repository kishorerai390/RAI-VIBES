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

ENTRY_SOUNDS = {
    "thalaivar": {
        "name": "👑 Rajini Thalaivar BGM",
        "url": "https://www.myinstants.com/media/sounds/jailer-hukum-bgm.mp3",
        "price": 1200,
        "emoji": "👑",
        "duration": 4.0,
        "description": "Mass Jailer Hukum BGM entrance theme"
    },
    "gunshot": {
        "name": "🔫 Anirudh Gunshot Swagger",
        "url": "https://www.myinstants.com/media/sounds/gunshot_sound.mp3",
        "price": 900,
        "emoji": "🔫",
        "duration": 2.5,
        "description": "Cinematic pistol trigger sound effect"
    },
    "airhorn": {
        "name": "🎺 MLG Hype Airhorn",
        "url": "https://www.myinstants.com/media/sounds/air-horn-club-sample_1.mp3",
        "price": 500,
        "emoji": "🎺",
        "duration": 2.5,
        "description": "High energy club airhorn blast (Free Starter)"
    },
    "victory": {
        "name": "🏆 Victory Fanfare Champion",
        "url": "https://www.myinstants.com/media/sounds/final-fantasy-vii-victory-fanfare-1.mp3",
        "price": 1000,
        "emoji": "🏆",
        "duration": 3.5,
        "description": "Classic gaming victory fanfare"
    },
    "crowd_cheer": {
        "name": "👏 Grand Stadium Applause",
        "url": "https://www.myinstants.com/media/sounds/cheering.mp3",
        "price": 750,
        "emoji": "👏",
        "duration": 3.0,
        "description": "Roaring stadium crowd cheer & applause"
    },
    "wow": {
        "name": "✨ Anime Wow Chime",
        "url": "https://www.myinstants.com/media/sounds/anime-wow-sound-effect.mp3",
        "price": 600,
        "emoji": "✨",
        "duration": 2.0,
        "description": "Cute aesthetic anime wow voice chime"
    },
    "bruh": {
        "name": "🗿 Legendary Bruh",
        "url": "https://www.myinstants.com/media/sounds/movie_1.mp3",
        "price": 500,
        "emoji": "🗿",
        "duration": 2.0,
        "description": "The immortal meme sound effect"
    },
    "emotional_damage": {
        "name": "💥 Emotional Damage",
        "url": "https://www.myinstants.com/media/sounds/emotional-damage-meme.mp3",
        "price": 800,
        "emoji": "💥",
        "duration": 2.5,
        "description": "Steven He iconic viral soundbite"
    },
    "directed_by": {
        "name": "🎬 Directed by Robert B. Weide",
        "url": "https://www.myinstants.com/media/sounds/curb-your-enthusiasm-theme_1.mp3",
        "price": 950,
        "emoji": "🎬",
        "duration": 4.0,
        "description": "Curb Your Enthusiasm comedy outro theme"
    },
    "drumroll": {
        "name": "🥁 Rimshot Ba-Dum-Tss",
        "url": "https://www.myinstants.com/media/sounds/ba-dum-tss.mp3",
        "price": 400,
        "emoji": "🥁",
        "duration": 2.0,
        "description": "Stand-up comedy punchline drumroll"
    },
    "vadivelu": {
        "name": "😂 Vadivelu Iconic Laugh",
        "url": "https://www.myinstants.com/media/sounds/vadivelu-laugh.mp3",
        "price": 1100,
        "emoji": "😂",
        "duration": 3.5,
        "description": "Hilarious legendary comedy laugh"
    },
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
            "unlocked": ["airhorn"]
        }
        save_entry_data(data)

    prof = data["users"][uid]
    # Owner gets all sounds unlocked
    if user_id == OWNER_ID:
        prof["unlocked"] = list(ALL_SOUND_KEYS)
        if not prof.get("equipped"):
            prof["equipped"] = "thalaivar"
    return prof


def unlock_user_sound(user_id: int, sound_key: str) -> bool:
    data = load_entry_data()
    uid = str(user_id)
    users = data.setdefault("users", {})
    if uid not in users:
        users[uid] = {"equipped": "airhorn", "enabled": True, "unlocked": ["airhorn"]}

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
        users[uid] = {"equipped": "thalaivar", "enabled": True, "unlocked": []}
    users[uid]["unlocked"] = list(ALL_SOUND_KEYS)
    save_entry_data(data)


# Cooldown cache: user_id -> last_played_timestamp
USER_ENTRY_COOLDOWNS: Dict[int, float] = {}


# =====================================================================
# INTERACTIVE ENTRY SOUND SELECT & CONTROLS
# =====================================================================
class EntrySoundSelect(Select):
    def __init__(self, user_id: int):
        prof = get_user_entry_profile(user_id)
        equipped = prof.get("equipped", "airhorn")
        unlocked = prof.get("unlocked", ["airhorn"])

        options = []
        for key, sfx in ENTRY_SOUNDS.items():
            is_unlocked = key in unlocked or user_id == OWNER_ID
            is_eq = key == equipped
            
            status = " [EQUIPPED]" if is_eq else (" [UNLOCKED]" if is_unlocked else f" [{sfx['price']:,} coins]")
            lbl = f"{sfx['name'][:25]}{status}"
            desc = sfx['description'][:95]
            options.append(discord.SelectOption(
                label=lbl,
                value=key,
                description=desc,
                emoji=sfx['emoji'],
                default=is_eq
            ))

        super().__init__(
            placeholder="🔊 Select a sound to Equip or Unlock...",
            min_values=1,
            max_values=1,
            options=options,
            custom_id=f"entry_select_{user_id}",
            row=0
        )
        self.target_user_id = user_id

    async def callback(self, interaction: discord.Interaction):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        if interaction.user.id != self.target_user_id and interaction.user.id != OWNER_ID:
            return await interaction.followup.send("❌ This menu belongs to another user. Use `/entrysound` to open yours!", ephemeral=True)

        selected_key = self.values[0]
        sfx = ENTRY_SOUNDS.get(selected_key)
        if not sfx:
            return await interaction.followup.send("❌ Unknown sound effect.", ephemeral=True)

        prof = get_user_entry_profile(interaction.user.id)
        unlocked = prof.get("unlocked", ["airhorn"])

        if selected_key in unlocked or interaction.user.id == OWNER_ID:
            # Equip it
            data = load_entry_data()
            data.setdefault("users", {}).setdefault(str(interaction.user.id), {})["equipped"] = selected_key
            data["users"][str(interaction.user.id)]["enabled"] = True
            save_entry_data(data)

            embed = discord.Embed(
                title="🔊 ENTRY SOUND EQUIPPED!",
                description=(
                    f"✦ ───────────────────────────── ✦\n\n"
                    f"You have equipped: **{sfx['emoji']} {sfx['name']}**!\n\n"
                    f"🎶 **Theme Effect:** {sfx['description']}\n"
                    f"📢 **Join Fanfare:** Plays whenever you enter an active voice room!\n\n"
                    f"✦ ───────────────────────────── ✦\n"
                    f"💡 *Click **Test Audio** below to preview in your current VC!*"
                ),
                color=0x2ECC71
            )
            embed.set_footer(text="RAI FAM 💗 • Entrance Themes", icon_url=config.RAI_ICON_URL)
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

        # Deduct coins & unlock
        new_coins = update_user_coins(interaction.user.id, -cost)
        unlock_user_sound(interaction.user.id, selected_key)
        
        # Auto-equip upon purchase
        data = load_entry_data()
        data.setdefault("users", {}).setdefault(str(interaction.user.id), {})["equipped"] = selected_key
        data["users"][str(interaction.user.id)]["enabled"] = True
        save_entry_data(data)

        bal_str = "∞ (Owner Vault)" if interaction.user.id == OWNER_ID else f"{new_coins:,} Coins"

        embed = discord.Embed(
            title="🎉 ENTRY SOUND UNLOCKED & EQUIPPED!",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"Successfully unlocked **{sfx['emoji']} {sfx['name']}** for `{cost:,} Coins`!\n\n"
                f"• **Remaining Balance:** `{bal_str}`\n"
                f"• **Equipped Status:** Active ✅\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"Whenever you join a voice room, your grand entrance theme will play!"
            ),
            color=0xF1C40F
        )
        embed.set_footer(text="RAI FAM 💗 • Entrance Themes", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)


class EntrySoundControlView(View):
    def __init__(self, user_id: int):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.add_item(EntrySoundSelect(user_id))

    @button(label="Test Audio in VC", style=discord.ButtonStyle.primary, emoji="🎧", row=1)
    async def test_btn(self, interaction: discord.Interaction, button: Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.followup.send("❌ You must join a voice channel first to test your sound!", ephemeral=True)

        prof = get_user_entry_profile(interaction.user.id)
        equipped = prof.get("equipped", "airhorn")
        sfx = ENTRY_SOUNDS.get(equipped, ENTRY_SOUNDS["airhorn"])

        cog = interaction.client.get_cog("EntrySound")
        if cog:
            success, msg = await cog.play_sound_in_channel(interaction.guild, interaction.user.voice.channel, sfx)
            if success:
                return await interaction.followup.send(f"🔊 Playing your entry theme **{sfx['name']}** in {interaction.user.voice.channel.mention}!", ephemeral=True)
            else:
                return await interaction.followup.send(f"⚠️ {msg}", ephemeral=True)
        await interaction.followup.send("❌ Voice engine currently unavailable.", ephemeral=True)

    @button(label="Toggle ON/OFF", style=discord.ButtonStyle.secondary, emoji="🔔", row=1)
    async def toggle_btn(self, interaction: discord.Interaction, button: Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        data = load_entry_data()
        user_entry = data.setdefault("users", {}).setdefault(str(interaction.user.id), {"equipped": "airhorn", "enabled": True, "unlocked": ["airhorn"]})
        curr = user_entry.get("enabled", True)
        user_entry["enabled"] = not curr
        save_entry_data(data)

        st = "ENABLED 🔔 (Will play on join)" if not curr else "MUTED 🔕 (Silent join)"
        await interaction.followup.send(f"Entrance Sound is now **{st}**!", ephemeral=True)

    @button(label="Full Catalog & Prices", style=discord.ButtonStyle.secondary, emoji="📜", row=1)
    async def catalog_btn(self, interaction: discord.Interaction, button: Button):
        try:
            if not interaction.response.is_done():
                await interaction.response.defer(ephemeral=True)
        except Exception:
            pass

        lines = []
        for k, s in ENTRY_SOUNDS.items():
            lines.append(f"• {s['emoji']} **{s['name']}** — `{s['price']:,} Coins`\n  *{s['description']}*")

        embed = discord.Embed(
            title="📜 VC ENTRANCE THEMES CATALOG",
            description="\n\n".join(lines),
            color=0x9B5DE5
        )
        embed.set_footer(text="RAI FAM 💗 • Select from the dropdown to unlock or equip!", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)


# Persistent View for the pinned Reward Exchange booth button
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
        enabled = prof.get("enabled", True)
        unlocked = prof.get("unlocked", ["airhorn"])
        sfx = ENTRY_SOUNDS.get(equipped, ENTRY_SOUNDS["airhorn"])

        status_str = "🟢 Active" if enabled else "🔴 Muted"
        total_unlocked = len(ALL_SOUND_KEYS) if interaction.user.id == OWNER_ID else len(unlocked)

        embed = discord.Embed(
            title="🔊 VC ENTRANCE SOUND STUDIO",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"Welcome to your **Voice Entrance Studio**, {interaction.user.mention}! 🌸\n"
                f"Whenever you join a voice room, make an unforgettable grand entrance with custom BGM!\n\n"
                f"📊 **Your Setup:**\n"
                f"• 🎵 **Current Sound:** **{sfx['emoji']} {sfx['name']}**\n"
                f"• 🔔 **Status:** `{status_str}`\n"
                f"• 🔓 **Unlocked Themes:** `{total_unlocked}/{len(ALL_SOUND_KEYS)}`\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Select any theme from the menu below to unlock or equip!*"
            ),
            color=0x00F5D4
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Voice Entrance Themes", icon_url=config.RAI_ICON_URL)

        view = EntrySoundControlView(interaction.user.id)
        await interaction.followup.send(embed=embed, view=view, ephemeral=True)


# =====================================================================
# COG IMPLEMENTATION
# =====================================================================
class EntrySound(commands.Cog):
    """Custom Voice Channel Entrance Themes and Audio Fanfares for RAI VIBES 💗."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    async def play_sound_in_channel(self, guild: discord.Guild, channel: discord.VoiceChannel, sfx_data: dict) -> tuple[bool, str]:
        """Plays sound in the specified channel without interrupting active music sessions."""
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
                before_options="-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5 -nostdin",
                options="-vn -bufsize 1024k"
            )
            transformed = discord.PCMVolumeTransformer(raw_source, volume=0.85)
            voice_client.play(transformed)

            # Wait for sound duration
            duration = sfx_data.get("duration", 3.0)
            await asyncio.sleep(duration + 0.5)

            # If we connected only to play the entry sound, cleanly disconnect
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

        # Trigger on joining or switching voice channels
        if not after.channel:
            return
        if before.channel and before.channel.id == after.channel.id:
            return

        channel = after.channel
        norm_name = unicodedata.normalize('NFKD', channel.name).lower()

        # Skip generator/hub channels
        if any(w in norm_name for w in ("join to create", "➕", "chamber", "generator")):
            return

        # Check user profile
        prof = get_user_entry_profile(member.id)
        if not prof.get("enabled", True):
            return

        # Cooldown check: 45 seconds per user
        now = time.time()
        last_played = USER_ENTRY_COOLDOWNS.get(member.id, 0)
        if now - last_played < 45.0 and member.id != OWNER_ID:
            return

        USER_ENTRY_COOLDOWNS[member.id] = now

        equipped_key = prof.get("equipped", "airhorn")
        sfx = ENTRY_SOUNDS.get(equipped_key)
        if not sfx:
            return

        # Small delay to ensure user audio connection is finalized
        await asyncio.sleep(0.8)

        # Confirm user is still in the voice channel
        if member not in channel.members:
            return

        # Fire and forget playback
        asyncio.create_task(self.play_sound_in_channel(member.guild, channel, sfx))

    @commands.hybrid_group(name="entrysound", aliases=["entrance", "joinsound"], description="Manage your voice channel entrance sound effect theme.")
    async def entrysound_group(self, ctx: commands.Context):
        if ctx.invoked_subcommand is None:
            await self.panel_cmd(ctx)

    @entrysound_group.command(name="panel", aliases=["menu"], description="Open the Voice Channel Entrance Sound Studio dashboard.")
    async def panel_cmd(self, ctx: commands.Context):
        prof = get_user_entry_profile(ctx.author.id)
        equipped = prof.get("equipped", "airhorn")
        enabled = prof.get("enabled", True)
        unlocked = prof.get("unlocked", ["airhorn"])
        sfx = ENTRY_SOUNDS.get(equipped, ENTRY_SOUNDS["airhorn"])

        status_str = "🟢 Active" if enabled else "🔴 Muted"
        total_unlocked = len(ALL_SOUND_KEYS) if ctx.author.id == OWNER_ID else len(unlocked)

        embed = discord.Embed(
            title="🔊 VC ENTRANCE SOUND STUDIO",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                f"Welcome to your **Voice Entrance Studio**, {ctx.author.mention}! 🌸\n"
                f"Whenever you join a voice channel, your entrance theme will play!\n\n"
                f"📊 **Your Setup:**\n"
                f"• 🎵 **Current Sound:** **{sfx['emoji']} {sfx['name']}**\n"
                f"• 🔔 **Status:** `{status_str}`\n"
                f"• 🔓 **Unlocked Themes:** `{total_unlocked}/{len(ALL_SOUND_KEYS)}`\n\n"
                f"✦ ───────────────────────────────────── ✦\n"
                f"👉 *Select any theme from the dropdown menu to equip or unlock!*"
            ),
            color=0x00F5D4
        )
        embed.set_thumbnail(url=ctx.author.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Voice Entrance Themes", icon_url=config.RAI_ICON_URL)

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

    @entrysound_group.command(name="toggle", description="Turn your entrance sound playback ON or OFF.")
    async def toggle_cmd(self, ctx: commands.Context):
        data = load_entry_data()
        user_entry = data.setdefault("users", {}).setdefault(str(ctx.author.id), {"equipped": "airhorn", "enabled": True, "unlocked": ["airhorn"]})
        curr = user_entry.get("enabled", True)
        user_entry["enabled"] = not curr
        save_entry_data(data)

        st = "ENABLED 🔔 (Will play on join)" if not curr else "MUTED 🔕 (Silent join)"
        await ctx.send(f"Entrance Sound is now **{st}**!", ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(EntrySound(bot))
