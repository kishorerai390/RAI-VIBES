import os
import json
import time
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Literal

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, button

import config

logger = logging.getLogger("Pets")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PETS_FILE = DATA_DIR / "pets.json"
ECONOMY_FILE = DATA_DIR / "economy.json"

PET_SPECIES = {
    "cat": {
        "title": "Cyber Kitty",
        "emoji": "🐱",
        "badge": "🐾",
        "desc": "Agile, affectionate, and purrs in sync with lo-fi beats.",
        "perk": "+5% Voice Coin Multiplier"
    },
    "fox": {
        "title": "Neon Fox",
        "emoji": "🦊",
        "badge": "🦊",
        "desc": "Cunning, energetic, and loves late-night gaming sessions.",
        "perk": "+5% Daily Streak Bonus"
    },
    "dragon": {
        "title": "Baby Dragon",
        "emoji": "🐉",
        "badge": "🐲",
        "desc": "Fierce, loyal, and breathes glowing cyber-pink embers.",
        "perk": "+10% Mini-game Luck"
    },
    "panda": {
        "title": "Chill Panda",
        "emoji": "🐼",
        "badge": "🎋",
        "desc": "Zen master, loves munching bamboo in quiet voice lounges.",
        "perk": "+5% Chat XP Gain"
    },
    "wolf": {
        "title": "Lunar Wolf",
        "emoji": "🐺",
        "badge": "🐺",
        "desc": "Proud squad leader, howls along with hype music drops.",
        "perk": "+5% Voice XP Gain"
    },
    "phoenix": {
        "title": "Astral Phoenix",
        "emoji": "🦅",
        "badge": "🔥",
        "desc": "Reborn from the cosmic energy of RAI VIBES.",
        "perk": "+10% Coin Bonus on Level Up"
    },
    "bunny": {
        "title": "Starlight Bunny",
        "emoji": "🐰",
        "badge": "✨",
        "desc": "Swift, adorable, and brings lucky sparkle multipliers.",
        "perk": "+5% Daily Allowance"
    },
    "frog": {
        "title": "Vibe Frog",
        "emoji": "🐸",
        "badge": "👑",
        "desc": "The ultimate chill companion, headbanging to 24/7 bass.",
        "perk": "+5% Passive Coin Gain"
    }
}


def load_pets() -> Dict[str, dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if PETS_FILE.exists():
        try:
            with open(PETS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_pets(data: Dict[str, dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(PETS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_user_coins(user_id: int) -> int:
    if ECONOMY_FILE.exists():
        try:
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                eco = json.load(f)
                return eco.get(str(user_id), {}).get("coins", 0)
        except Exception:
            pass
    return 0


def deduct_user_coins(user_id: int, amount: int) -> bool:
    try:
        eco = {}
        if ECONOMY_FILE.exists():
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                eco = json.load(f)
        uid = str(user_id)
        if uid not in eco:
            return False
        if eco[uid].get("coins", 0) < amount:
            return False
        eco[uid]["coins"] -= amount
        with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
            json.dump(eco, f, indent=2)
        return True
    except Exception:
        return False


def get_pet_stage(level: int) -> str:
    if level < 5:
        return "🌱 Baby Hatchling"
    elif level < 15:
        return "⚡ Playful Juvenile"
    elif level < 30:
        return "🌟 Loyal Companion"
    else:
        return "👑 Mythic Ascended"


async def apply_nickname_badge(member: discord.Member, pet_data: dict) -> tuple[bool, str]:
    """Applies or removes the member's companion pet badge from their nickname."""
    guild = member.guild
    species_info = PET_SPECIES.get(pet_data.get("species", "cat"), PET_SPECIES["cat"])
    badge = species_info["badge"]
    style = pet_data.get("badge_style", "suffix")

    current_nick = member.nick or member.name
    # Strip all existing pet badges
    all_badges = [info["badge"] for info in PET_SPECIES.values()]
    clean_nick = current_nick
    for b in all_badges:
        clean_nick = clean_nick.replace(f"[{b}]", "").replace(f" {b}", "").replace(b, "").strip()

    if not clean_nick:
        clean_nick = member.name

    if style == "suffix":
        target_nick = f"{clean_nick} {badge}"
    elif style == "prefix":
        target_nick = f"[{badge}] {clean_nick}"
    else:
        target_nick = clean_nick

    if len(target_nick) > 32:
        target_nick = target_nick[:32]

    # Check hierarchy
    if member.id == guild.owner_id:
        return False, "Discord does not permit bots to change the Server Owner's nickname. Your pet badge is active on your profile!"
    if member.top_role >= guild.me.top_role:
        return False, "Your role is equal to or higher than the bot in Discord hierarchy. Your pet badge is active on your profile!"

    try:
        await member.edit(nick=target_nick, reason="Companion Pet Badge synchronization")
        return True, f"Nickname updated to **{target_nick}**!"
    except Exception as e:
        return False, f"Could not update nickname: {e}"


class PetCareView(View):
    def __init__(self, owner_id: int):
        super().__init__(timeout=None)
        self.owner_id = owner_id

    @button(label="Feed (50 Coins)", emoji="🍗", style=discord.ButtonStyle.success, custom_id="pet_feed_btn")
    async def feed_button(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer()
        if interaction.user.id != self.owner_id:
            return await interaction.followup.send("❌ This is not your pet companion!", ephemeral=True)

        pets = load_pets()
        uid = str(interaction.user.id)
        if uid not in pets:
            return await interaction.followup.send("❌ You don't have an adopted pet! Use `/pet adopt`.", ephemeral=True)

        user_coins = get_user_coins(interaction.user.id)
        if user_coins < 50:
            return await interaction.followup.send(f"❌ You need **50 Coins** to feed your pet! (You have {user_coins:,} Coins)", ephemeral=True)

        deduct_user_coins(interaction.user.id, 50)
        p = pets[uid]
        p["hunger"] = min(100, p.get("hunger", 50) + 35)
        p["happiness"] = min(100, p.get("happiness", 50) + 15)
        p["xp"] = p.get("xp", 0) + 20
        p["last_fed"] = time.time()

        # Level up check (every 100 XP)
        current_lvl = p.get("level", 1)
        needed_xp = current_lvl * 100
        lvl_up = False
        if p["xp"] >= needed_xp:
            p["level"] += 1
            p["xp"] -= needed_xp
            lvl_up = True

        save_pets(pets)

        spec = PET_SPECIES.get(p["species"], PET_SPECIES["cat"])
        desc = f"✨ You fed **{p['name']}** the {spec['title']}! Yummy! (+35 Hunger, +15 Happiness, +20 XP)"
        if lvl_up:
            desc += f"\n🎉 **LEVEL UP!** {p['name']} reached **Level {p['level']}**! Stage: **{get_pet_stage(p['level'])}**"

        await interaction.followup.send(desc, ephemeral=True)

    @button(label="Play (Free)", emoji="🎾", style=discord.ButtonStyle.primary, custom_id="pet_play_btn")
    async def play_button(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer()
        if interaction.user.id != self.owner_id:
            return await interaction.followup.send("❌ This is not your pet companion!", ephemeral=True)

        pets = load_pets()
        uid = str(interaction.user.id)
        if uid not in pets:
            return await interaction.followup.send("❌ You don't have an adopted pet!", ephemeral=True)

        p = pets[uid]
        now = time.time()
        if now - p.get("last_played", 0) < 60:
            rem = int(60 - (now - p.get("last_played", 0)))
            return await interaction.followup.send(f"⏳ **{p['name']}** is resting! Play again in **{rem}s**.", ephemeral=True)

        p["last_played"] = now
        p["happiness"] = min(100, p.get("happiness", 50) + 25)
        p["xp"] = p.get("xp", 0) + 15
        p["hunger"] = max(0, p.get("hunger", 50) - 10)

        current_lvl = p.get("level", 1)
        needed_xp = current_lvl * 100
        lvl_up = False
        if p["xp"] >= needed_xp:
            p["level"] += 1
            p["xp"] -= needed_xp
            lvl_up = True

        save_pets(pets)
        spec = PET_SPECIES.get(p["species"], PET_SPECIES["cat"])
        activities = [
            f"threw a neon frisbee for **{p['name']}**! They caught it mid-air!",
            f"scratched **{p['name']}** behind the ears. They made happy chirp sounds!",
            f"danced to the music beat with **{p['name']}**!",
            f"played laser tag in the voice lounge with **{p['name']}**!"
        ]
        msg = f"🎾 You {random.choice(activities)}\n*(+25 Happiness, +15 XP, -10 Hunger)*"
        if lvl_up:
            msg += f"\n🎉 **LEVEL UP!** {p['name']} reached **Level {p['level']}**!"

        await interaction.followup.send(msg, ephemeral=True)

    @button(label="Cycle Name Badge", emoji="🏷️", style=discord.ButtonStyle.secondary, custom_id="pet_badge_cycle_btn")
    async def badge_cycle_button(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer()
        if interaction.user.id != self.owner_id:
            return await interaction.followup.send("❌ This is not your pet companion!", ephemeral=True)

        pets = load_pets()
        uid = str(interaction.user.id)
        if uid not in pets:
            return await interaction.followup.send("❌ You don't have an adopted pet!", ephemeral=True)

        p = pets[uid]
        current_style = p.get("badge_style", "suffix")
        styles = ["suffix", "prefix", "off"]
        next_style = styles[(styles.index(current_style) + 1) % len(styles)]
        p["badge_style"] = next_style
        save_pets(pets)

        success, note = await apply_nickname_badge(interaction.user, p)
        await interaction.followup.send(f"🏷️ **Badge Style:** `{next_style.upper()}`\n{note}", ephemeral=True)


class Pets(commands.Cog):
    """Virtual Companion Pets with Evolution and Nickname Badges."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="pet", description="Interact with your virtual server companion pet!")
    @app_commands.describe(
        action="Choose an action (adopt, profile, badge, feed, play, list)",
        species="Species to adopt (cat, fox, dragon, panda, wolf, phoenix, bunny, frog)",
        name="Custom name for your pet companion"
    )
    async def pet_command(
        self,
        interaction: discord.Interaction,
        action: Literal["adopt", "profile", "badge", "feed", "play", "list"],
        species: Optional[Literal["cat", "fox", "dragon", "panda", "wolf", "phoenix", "bunny", "frog"]] = None,
        name: Optional[str] = None
    ):
        pets = load_pets()
        uid = str(interaction.user.id)

        # 1. LIST SPECIES
        if action == "list":
            embed = discord.Embed(
                title="🐾 RAI VIBES COMPANION PET DIRECTORY",
                description="Adopt a pet to accompany you across the server! Your pet badge appears right beside your name in chat.\n",
                color=0xFF69B4
            )
            for key, info in PET_SPECIES.items():
                embed.add_field(
                    name=f"{info['emoji']} {info['title']} (Badge: `{info['badge']}`)",
                    value=f"*{info['desc']}*\n💎 **Perk:** `{info['perk']}`\nAdopt: `/pet adopt species:{key} name:<name>`",
                    inline=False
                )
            embed.set_footer(text="RAI VIBES 💗 Companion Pet Sanctuary", icon_url=config.RAI_ICON_URL)
            return await interaction.response.send_message(embed=embed)

        # 2. ADOPT
        if action == "adopt":
            if uid in pets:
                existing = pets[uid]
                spec = PET_SPECIES.get(existing["species"], PET_SPECIES["cat"])
                return await interaction.response.send_message(
                    f"⚠️ You already have an adopted pet: **{existing['name']}** the {spec['title']} ({spec['emoji']})!\n"
                    f"Use `/pet profile` to inspect them or `/pet badge` to toggle your name badge.",
                    ephemeral=True
                )

            if not species:
                return await interaction.response.send_message(
                    "❌ Please specify a pet species to adopt! Example: `/pet adopt species:fox name:Kitsune`\n"
                    "Use `/pet list` to view all available species.",
                    ephemeral=True
                )

            pet_name = (name or "Companion").strip()[:20]
            pets[uid] = {
                "species": species,
                "name": pet_name,
                "level": 1,
                "xp": 0,
                "hunger": 100,
                "happiness": 100,
                "last_fed": time.time(),
                "last_played": time.time(),
                "badge_style": "suffix",
                "adopted_at": time.time()
            }
            save_pets(pets)

            # Auto-apply nickname badge
            success, note = await apply_nickname_badge(interaction.user, pets[uid])
            spec = PET_SPECIES[species]

            embed = discord.Embed(
                title=f"🎉 COMPANION ADOPTED • {pet_name}!",
                description=(
                    f"Congratulations {interaction.user.mention}! You have bonded with **{pet_name}** the {spec['title']}!\n\n"
                    f"🐾 **Badge:** `{spec['badge']}`\n"
                    f"✨ **Special Perk:** `{spec['perk']}`\n\n"
                    f"🏷️ **Nickname Status:** {note}\n\n"
                    f"💡 *Feed your pet with `/pet feed` and play with `/pet play` to level up and evolve!*"
                ),
                color=0x00FFCC
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.set_footer(text="RAI VIBES Pet Sanctuary", icon_url=config.RAI_ICON_URL)
            return await interaction.response.send_message(embed=embed, view=PetCareView(interaction.user.id))

        # Check existing pet for profile / care
        if uid not in pets:
            return await interaction.response.send_message(
                "❌ You don't have an adopted pet companion yet!\n"
                "Adopt one today with `/pet adopt [species] [name]` or view species with `/pet list`.",
                ephemeral=True
            )

        p = pets[uid]
        spec = PET_SPECIES.get(p["species"], PET_SPECIES["cat"])

        # 3. BADGE TOGGLE
        if action == "badge":
            current_style = p.get("badge_style", "suffix")
            styles = ["suffix", "prefix", "off"]
            next_style = styles[(styles.index(current_style) + 1) % len(styles)]
            p["badge_style"] = next_style
            save_pets(pets)
            success, note = await apply_nickname_badge(interaction.user, p)
            return await interaction.response.send_message(
                f"🏷️ **Pet Name Badge:** `{next_style.upper()}`\n{note}",
                ephemeral=True
            )

        # 4. FEED
        if action == "feed":
            user_coins = get_user_coins(interaction.user.id)
            if user_coins < 50:
                return await interaction.response.send_message(
                    f"❌ Feeding costs **50 Coins**! You currently have **{user_coins:,} Coins**.\n"
                    f"Earn more coins by chatting or claiming `/daily`!",
                    ephemeral=True
                )
            deduct_user_coins(interaction.user.id, 50)
            p["hunger"] = min(100, p.get("hunger", 50) + 35)
            p["happiness"] = min(100, p.get("happiness", 50) + 15)
            p["xp"] = p.get("xp", 0) + 20
            p["last_fed"] = time.time()

            current_lvl = p.get("level", 1)
            needed_xp = current_lvl * 100
            lvl_up = False
            if p["xp"] >= needed_xp:
                p["level"] += 1
                p["xp"] -= needed_xp
                lvl_up = True
            save_pets(pets)

            msg = f"🍗 You fed **{p['name']}** delicious treats! (+35 Hunger, +15 Happiness, +20 XP)"
            if lvl_up:
                msg += f"\n🎉 **LEVEL UP!** {p['name']} reached **Level {p['level']}**!"
            return await interaction.response.send_message(msg, ephemeral=True)

        # 5. PLAY
        if action == "play":
            now = time.time()
            if now - p.get("last_played", 0) < 60:
                rem = int(60 - (now - p.get("last_played", 0)))
                return await interaction.response.send_message(
                    f"⏳ **{p['name']}** is resting! Play again in **{rem}s**.",
                    ephemeral=True
                )
            p["last_played"] = now
            p["happiness"] = min(100, p.get("happiness", 50) + 25)
            p["xp"] = p.get("xp", 0) + 15
            p["hunger"] = max(0, p.get("hunger", 50) - 10)

            current_lvl = p.get("level", 1)
            needed_xp = current_lvl * 100
            lvl_up = False
            if p["xp"] >= needed_xp:
                p["level"] += 1
                p["xp"] -= needed_xp
                lvl_up = True
            save_pets(pets)

            msg = f"🎾 You spent quality time playing with **{p['name']}**!\n*(+25 Happiness, +15 XP, -10 Hunger)*"
            if lvl_up:
                msg += f"\n🎉 **LEVEL UP!** {p['name']} reached **Level {p['level']}**!"
            return await interaction.response.send_message(msg, ephemeral=True)

        # 6. PROFILE
        if action == "profile":
            lvl = p.get("level", 1)
            xp = p.get("xp", 0)
            needed_xp = lvl * 100
            stage = get_pet_stage(lvl)
            hunger = p.get("hunger", 100)
            happiness = p.get("happiness", 100)
            badge_style = p.get("badge_style", "suffix").upper()

            def bar(val: int) -> str:
                filled = int(val / 10)
                return "▰" * filled + "▱" * (10 - filled)

            embed = discord.Embed(
                title=f"{spec['emoji']} {p['name']} • {spec['title']}",
                description=f"Companion to **{interaction.user.display_name}**\n*{spec['desc']}*",
                color=0xFF007F
            )
            embed.set_thumbnail(url=interaction.user.display_avatar.url)
            embed.add_field(name="⭐ Evolution Stage", value=f"**{stage}** (Lvl {lvl})", inline=True)
            embed.add_field(name="🏷️ Nickname Badge", value=f"`{spec['badge']}` ({badge_style})", inline=True)
            embed.add_field(name="💎 Active Perk", value=f"`{spec['perk']}`", inline=False)
            embed.add_field(name=f"🍖 Hunger ({hunger}%)", value=bar(hunger), inline=True)
            embed.add_field(name=f"💖 Happiness ({happiness}%)", value=bar(happiness), inline=True)
            embed.add_field(name=f"✨ XP Progress ({xp}/{needed_xp})", value=bar(int((xp / needed_xp) * 100)), inline=False)
            embed.set_footer(text="Use buttons below to feed, play, or toggle name badge!")

            return await interaction.response.send_message(embed=embed, view=PetCareView(interaction.user.id))


async def setup(bot: commands.Bot):
    await bot.add_cog(Pets(bot))
