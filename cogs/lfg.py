import os
import json
import time
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict, List, Literal

import discord
from discord import app_commands
from discord.ext import commands, tasks
from discord.ui import View, Button, button

import config

logger = logging.getLogger("LFG")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LFG_FILE = DATA_DIR / "active_lfg.json"

GAME_EMOJIS = {
    "bgmi": "⚡ BGMI (Battlegrounds)",
    "freefire": "💥 Free Fire Max",
    "roblox": "🧸 Roblox Squad",
    "gtarp": "🔫 GTA V / FiveM RP",
    "valorant": "🎯 Valorant Ranked",
    "pc": "🖥️ PC Gaming / Steam",
    "other": "🎮 Squad Session"
}


def load_lfg() -> Dict[str, dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if LFG_FILE.exists():
        try:
            with open(LFG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_lfg(data: Dict[str, dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(LFG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class LFGView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Join Squad 🎮", style=discord.ButtonStyle.success, custom_id="lfg_join_squad_btn")
    async def join_squad(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        lfg_data = load_lfg()
        msg_id = str(interaction.message.id)

        if msg_id not in lfg_data:
            return await interaction.followup.send("❌ This LFG squad is no longer active.", ephemeral=True)

        squad = lfg_data[msg_id]
        if squad.get("completed"):
            return await interaction.followup.send("⚠️ This squad has already filled up!", ephemeral=True)

        uid = interaction.user.id
        if uid in squad["members"]:
            return await interaction.followup.send("ℹ️ You are already registered in this squad!", ephemeral=True)

        if len(squad["members"]) >= squad["max_slots"]:
            return await interaction.followup.send("⚠️ Squad is currently full!", ephemeral=True)

        squad["members"].append(uid)
        save_lfg(lfg_data)

        # Check if squad is now full
        is_full = len(squad["members"]) >= squad["max_slots"]
        created_vc = None

        if is_full:
            squad["completed"] = True
            save_lfg(lfg_data)

            # Auto-create temporary private voice room
            guild = interaction.guild
            cat = (
                discord.utils.get(guild.categories, name="🥂 ＰＲＩＶＡＴＥ  ＳＵＩＴＥＳ")
                or discord.utils.get(guild.categories, name="🎮 ＧＡＭＩＮＧ  ＺＯＮＥ")
                or interaction.channel.category
            )

            game_label = GAME_EMOJIS.get(squad["game"], "Gaming").split(" ")[1]
            vc_name = f"🎮 ┊ {game_label} Squad"

            try:
                created_vc = await guild.create_voice_channel(
                    name=vc_name,
                    category=cat,
                    user_limit=squad["max_slots"],
                    reason="LFG Squad Full auto-provision"
                )
                squad["voice_channel_id"] = created_vc.id
                save_lfg(lfg_data)

                # Move connected members into VC if in any voice channel
                for m_id in squad["members"]:
                    mem = guild.get_member(m_id)
                    if mem and mem.voice and mem.voice.channel:
                        try:
                            await mem.move_to(created_vc, reason="LFG Squad formed")
                        except Exception:
                            pass
            except Exception as e:
                logger.warning(f"Could not provision LFG VC: {e}")

        # Update embed
        embed = interaction.message.embeds[0]
        member_mentions = [f"<@{m_id}>" for m_id in squad["members"]]
        needed = squad["max_slots"] - len(squad["members"])

        embed.set_field_at(
            0,
            name=f"👥 Squad Members ({len(squad['members'])}/{squad['max_slots']})",
            value=" • ".join(member_mentions),
            inline=False
        )

        if is_full:
            vc_text = f" 🎉 **Squad formed!** Join your voice room: {created_vc.mention if created_vc else 'Voice Lounge'}"
            embed.color = 0x00FF88
            embed.set_field_at(
                1,
                name="Status",
                value=f"🟢 **Ready to Drop!**{vc_text}",
                inline=False
            )
            await interaction.message.edit(embed=embed, view=None)
            await interaction.followup.send(f"✅ Squad is FULL! Head over to {created_vc.mention if created_vc else 'voice'} now!", ephemeral=True)
        else:
            embed.set_field_at(
                1,
                name="Status",
                value=f"🟡 **Recruiting** (`{needed}` more needed)",
                inline=False
            )
            await interaction.message.edit(embed=embed, view=self)
            await interaction.followup.send("✅ You joined the squad!", ephemeral=True)

    @button(label="Leave Squad", style=discord.ButtonStyle.secondary, custom_id="lfg_leave_squad_btn")
    async def leave_squad(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        lfg_data = load_lfg()
        msg_id = str(interaction.message.id)

        if msg_id not in lfg_data:
            return await interaction.followup.send("❌ This squad is no longer active.", ephemeral=True)

        squad = lfg_data[msg_id]
        if squad.get("completed"):
            return await interaction.followup.send("⚠️ The squad match has already started.", ephemeral=True)

        uid = interaction.user.id
        if uid == squad["host_id"]:
            return await interaction.followup.send("❌ The host cannot leave the squad! If you want to cancel, delete the message.", ephemeral=True)

        if uid not in squad["members"]:
            return await interaction.followup.send("❌ You are not in this squad.", ephemeral=True)

        squad["members"].remove(uid)
        save_lfg(lfg_data)

        # Update embed
        embed = interaction.message.embeds[0]
        member_mentions = [f"<@{m_id}>" for m_id in squad["members"]]
        needed = squad["max_slots"] - len(squad["members"])

        embed.set_field_at(
            0,
            name=f"👥 Squad Members ({len(squad['members'])}/{squad['max_slots']})",
            value=" • ".join(member_mentions) if member_mentions else "None",
            inline=False
        )
        embed.set_field_at(
            1,
            name="Status",
            value=f"🟡 **Recruiting** (`{needed}` more needed)",
            inline=False
        )
        await interaction.message.edit(embed=embed, view=self)
        await interaction.followup.send("⚪ You left the squad.", ephemeral=True)


class LFGHubLauncherView(View):
    """1-Click Squad Matchmaker Panel with Persistent Buttons."""
    def __init__(self):
        super().__init__(timeout=None)

    @button(label="Valorant (4P)", style=discord.ButtonStyle.primary, emoji="🎯", custom_id="lfg_quick_valorant")
    async def valo_btn(self, interaction: discord.Interaction, btn: Button):
        await self._launch(interaction, "valorant", 4, "Ranked / Competitive Grind")

    @button(label="BGMI Squad (4P)", style=discord.ButtonStyle.success, emoji="⚡", custom_id="lfg_quick_bgmi")
    async def bgmi_btn(self, interaction: discord.Interaction, btn: Button):
        await self._launch(interaction, "bgmi", 4, "Classic / Rank Push")

    @button(label="Free Fire (4P)", style=discord.ButtonStyle.danger, emoji="💥", custom_id="lfg_quick_freefire")
    async def ff_btn(self, interaction: discord.Interaction, btn: Button):
        await self._launch(interaction, "freefire", 4, "BR Ranked / Clash Squad")

    @button(label="Roblox (3P)", style=discord.ButtonStyle.secondary, emoji="🧸", custom_id="lfg_quick_roblox")
    async def roblox_btn(self, interaction: discord.Interaction, btn: Button):
        await self._launch(interaction, "roblox", 3, "Minigames & Chill Hangout")

    @button(label="GTA RP (2P)", style=discord.ButtonStyle.secondary, emoji="🔫", custom_id="lfg_quick_gtarp")
    async def gtarp_btn(self, interaction: discord.Interaction, btn: Button):
        await self._launch(interaction, "gtarp", 2, "FiveM / Heists / Patrol")

    async def _launch(self, interaction: discord.Interaction, game: str, slots: int, default_note: str):
        await interaction.response.defer(ephemeral=True)
        lfg_data = load_lfg()
        for msg_id, sq in lfg_data.items():
            if sq.get("host_id") == interaction.user.id and not sq.get("completed"):
                return await interaction.followup.send("⚠️ You already have an active recruiting squad! Please wait for it or finish before opening another.", ephemeral=True)

        hub = (
            discord.utils.get(interaction.guild.text_channels, name="🎮・ɢᴀᴍɪɴɢ-ʜᴜʙ")
            or discord.utils.get(interaction.guild.text_channels, name="gaming-hub")
            or interaction.channel
        )

        game_title = GAME_EMOJIS.get(game, "Squad Session")
        needed = slots - 1

        role_mention = ""
        role_keywords = {
            "bgmi": ["bgmi", "battlegrounds"],
            "freefire": ["free fire", "freefire"],
            "roblox": ["roblox"],
            "gtarp": ["gta", "fivem"],
            "valorant": ["valorant"]
        }
        kws = role_keywords.get(game, [])
        for r in interaction.guild.roles:
            if any(kw in r.name.lower() for kw in kws):
                role_mention = f" {r.mention}"
                break

        embed = discord.Embed(
            title=f"🎮 LOOKING FOR SQUAD • {game_title}",
            description=(
                f"**Host:** {interaction.user.mention}\n"
                f"**Objective:** *{default_note}*\n\n"
                f"⚡ *Click **`[Join Squad 🎮]`** below! When full, a private squad voice room auto-provisions!*"
            ),
            color=0xFF007F
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(
            name=f"👥 Squad Members (1/{slots})",
            value=f"{interaction.user.mention}",
            inline=False
        )
        embed.add_field(
            name="Status",
            value=f"🟡 **Recruiting** (`{needed}` more needed)",
            inline=False
        )
        embed.set_footer(text="RAI VIBES Gaming Hub • 1-Click Matchmaker", icon_url=config.RAI_ICON_URL)

        view = LFGView()
        announcement = f"🚀 **{interaction.user.mention} opened a 1-click squad for {game_title}!** Need **{needed}** more!{role_mention}"
        msg = await hub.send(content=announcement, embed=embed, view=view)

        lfg_data[str(msg.id)] = {
            "host_id": interaction.user.id,
            "game": game,
            "max_slots": slots,
            "members": [interaction.user.id],
            "completed": False,
            "created_at": time.time()
        }
        save_lfg(lfg_data)

        await interaction.followup.send(f"✅ **{game_title}** squad created in {hub.mention}! [Jump to Card]({msg.jump_url})", ephemeral=True)


class LFG(commands.Cog):
    """Clean Looking For Group Squad Matchmaker."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.vc_cleanup_task.start()

    def cog_unload(self):
        self.vc_cleanup_task.cancel()

    @tasks.loop(minutes=2)
    async def vc_cleanup_task(self):
        """Automatically deletes empty temporary LFG squad channels."""
        await self.bot.wait_until_ready()
        lfg_data = load_lfg()
        to_remove = []

        for msg_id, sq in lfg_data.items():
            vc_id = sq.get("voice_channel_id")
            if vc_id:
                chan = self.bot.get_channel(vc_id)
                if chan and isinstance(chan, discord.VoiceChannel):
                    # If older than 5 min and empty, clean up
                    if len(chan.members) == 0:
                        try:
                            await chan.delete(reason="LFG Squad channel empty auto-cleanup")
                            to_remove.append(msg_id)
                        except Exception:
                            pass
                else:
                    to_remove.append(msg_id)

        for m_id in to_remove:
            if m_id in lfg_data:
                del lfg_data[m_id]
        if to_remove:
            save_lfg(lfg_data)

    @app_commands.command(name="lfgpanel", description="Deploy the 1-Click LFG Squad Launcher Panel to #gaming-hub.")
    @app_commands.checks.has_permissions(manage_messages=True)
    async def lfg_panel_command(self, interaction: discord.Interaction):
        embed = discord.Embed(
            title="🎮 ✦ RAI GAMING SQUAD LAUNCHER ✦ 🎮",
            description=(
                "Need teammates right now? **Click any game button below** to instantly deploy an LFG squad recruit card!\n\n"
                "• **Instant Matchmaking:** Members click `[Join Squad 🎮]` to join your party.\n"
                "• **Auto-Voice Provisioning:** When full, an exclusive private voice room is auto-created!\n"
                "• **Game Ping:** Automatically notifies members with matching gamer roles."
            ),
            color=0x2ED573
        )
        embed.add_field(
            name="Available Quick-Queues",
            value=(
                "🎯 **Valorant** — 4-player tactical squad\n"
                "⚡ **BGMI** — 4-player battle royale crew\n"
                "💥 **Free Fire** — 4-player clash squad\n"
                "🧸 **Roblox** — 3-player minigames & party\n"
                "🔫 **GTA V RP** — 2-player duo heists & patrol"
            ),
            inline=False
        )
        embed.set_footer(text="RAI VIBES 💗 • Fast-Drop Matchmaker", icon_url=config.RAI_ICON_URL)
        view = LFGHubLauncherView()
        await interaction.channel.send(embed=embed, view=view)
        await interaction.response.send_message("✅ 1-Click LFG Squad Launcher panel deployed!", ephemeral=True)

    @app_commands.command(name="lfg", description="Find squadmates and auto-create a private squad voice room!")
    @app_commands.describe(
        game="Choose the game you are queueing for",
        slots="Total squad size required (2 to 5)",
        note="Brief objective (e.g. Push Rank, Casual, Tournament Practice)",
        ping_role="Auto-ping the corresponding game role so squadmates get notified"
    )
    async def lfg_create(
        self,
        interaction: discord.Interaction,
        game: Literal["bgmi", "freefire", "roblox", "gtarp", "valorant", "pc", "other"],
        slots: Literal[2, 3, 4, 5],
        note: Optional[str] = None,
        ping_role: Optional[bool] = True
    ):
        game_title = GAME_EMOJIS.get(game, "Squad Session")
        needed = slots - 1

        embed = discord.Embed(
            title=f"🎮 LOOKING FOR SQUAD • {game_title}",
            description=(
                f"**Host:** {interaction.user.mention}\n"
                f"**Mission / Note:** *{note or 'Pushing rank & vibing! Join up.'}*\n\n"
                f"⚡ *Click **`[Join Squad]`** below! When full, a private squad voice room will be created automatically.*"
            ),
            color=0xFF007F
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.add_field(
            name=f"👥 Squad Members (1/{slots})",
            value=f"{interaction.user.mention}",
            inline=False
        )
        embed.add_field(
            name="Status",
            value=f"🟡 **Recruiting** (`{needed}` more needed)",
            inline=False
        )
        embed.set_footer(text="RAI VIBES Gaming Hub • LFG Matchmaker", icon_url=config.RAI_ICON_URL)

        view = LFGView()

        # Target channel: #🎮・ɢᴀᴍɪɴɢ-ʜᴜʙ or current channel
        hub = (
            discord.utils.get(interaction.guild.text_channels, name="🎮・ɢᴀᴍɪɴɢ-ʜᴜʙ")
            or discord.utils.get(interaction.guild.text_channels, name="gaming-hub")
            or interaction.channel
        )

        role_mention = ""
        if ping_role:
            role_keywords = {
                "bgmi": ["bgmi", "battlegrounds"],
                "freefire": ["free fire", "freefire"],
                "roblox": ["roblox"],
                "gtarp": ["gta", "fivem"],
                "valorant": ["valorant"],
                "pc": ["pc", "steam"]
            }
            kws = role_keywords.get(game, [])
            for r in interaction.guild.roles:
                if any(kw in r.name.lower() for kw in kws):
                    role_mention = f" {r.mention}"
                    break

        announcement = f"📢 **New LFG Squad Created for {game_title}!** Need **{needed}** more players!{role_mention}"
        msg = await hub.send(
            content=announcement,
            embed=embed,
            view=view
        )

        lfg_data = load_lfg()
        lfg_data[str(msg.id)] = {
            "host_id": interaction.user.id,
            "game": game,
            "max_slots": slots,
            "members": [interaction.user.id],
            "completed": False,
            "created_at": time.time()
        }
        save_lfg(lfg_data)

        if hub.id != interaction.channel.id:
            await interaction.response.send_message(f"✅ LFG Squad card posted in {hub.mention}!", ephemeral=True)
        else:
            await interaction.response.send_message("✅ LFG Squad card created!", ephemeral=True)


async def setup(bot: commands.Bot):
    cog = LFG(bot)
    await bot.add_cog(cog)
    bot.add_view(LFGView())
    bot.add_view(LFGHubLauncherView())
