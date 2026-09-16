import os
import json
import time
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Literal
import discord
from discord import app_commands
from discord.ext import commands, tasks

import config
from utils.canvas import generate_bracket_card

logger = logging.getLogger("Squads")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SQUADS_FILE = DATA_DIR / "squads.json"


def load_squads() -> Dict[str, dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if SQUADS_FILE.exists():
        try:
            with open(SQUADS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_squads(data: Dict[str, dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(SQUADS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def get_user_squad(user_id: int, squads: Dict[str, dict]) -> tuple[Optional[str], Optional[dict]]:
    uid = user_id
    for sq_id, data in squads.items():
        if uid in data.get("members", []) or uid == data.get("leader_id"):
            return sq_id, data
    return None, None


class Squads(commands.Cog):
    """Voice Clans & Community Squad Wars."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.voice_squad_xp_task.start()

    def cog_unload(self):
        self.voice_squad_xp_task.cancel()

    @tasks.loop(minutes=3)
    async def voice_squad_xp_task(self):
        """Awards Clan XP when squadmates hang out in voice together."""
        await self.bot.wait_until_ready()
        squads = load_squads()
        if not squads:
            return

        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                if "afk" in vc.name.lower() or len(vc.members) < 2:
                    continue

                # Group members by squad
                squad_members_in_vc: Dict[str, list] = {}
                for m in vc.members:
                    if m.bot or m.voice.self_deaf:
                        continue
                    sq_id, sq = get_user_squad(m.id, squads)
                    if sq_id:
                        squad_members_in_vc.setdefault(sq_id, []).append(m)

                # If 2 or more squad members in same VC, award squad bonus XP
                for sq_id, members in squad_members_in_vc.items():
                    if len(members) >= 2:
                        squads[sq_id]["xp"] = squads[sq_id].get("xp", 0) + (len(members) * 10)
                        # Level up squad (every 500 XP)
                        sq_lvl = squads[sq_id].get("level", 1)
                        if squads[sq_id]["xp"] >= sq_lvl * 500:
                            squads[sq_id]["level"] += 1

        save_squads(squads)

    @voice_squad_xp_task.before_loop
    async def before_voice_squad_task(self):
        import asyncio
        while not self.bot.is_ready():
            await asyncio.sleep(1)

    # -------------------------------------------------------------
    # SQUAD SLASH COMMANDS
    # -------------------------------------------------------------
    @app_commands.command(name="squad", description="Create, join, and manage your voice clan squad!")
    @app_commands.describe(
        action="Action to perform (create, join, leave, info, tag, leaderboard)",
        name="Name of the squad",
        tag="Short squad tag (e.g. AURA, PHANTOM) max 5 chars"
    )
    async def squad_command(
        self,
        interaction: discord.Interaction,
        action: Literal["create", "join", "leave", "info", "tag", "leaderboard"],
        name: Optional[str] = None,
        tag: Optional[str] = None
    ):
        squads = load_squads()
        user_sq_id, user_sq = get_user_squad(interaction.user.id, squads)

        # 1. CREATE SQUAD
        if action == "create":
            if user_sq:
                return await interaction.response.send_message(
                    f"⚠️ You are already in squad **{user_sq['name']}** `[{user_sq['tag']}]`!\n"
                    f"Leave your current squad first with `/squad action:leave`.",
                    ephemeral=True
                )
            if not name or not tag:
                return await interaction.response.send_message(
                    "❌ Please specify both a squad name and tag! Example: `/squad action:create name:Phantom tag:PHTM`",
                    ephemeral=True
                )

            sq_name = name.strip()[:24]
            sq_tag = tag.strip().upper()[:5]

            # Check if name or tag taken
            for sq in squads.values():
                if sq["name"].lower() == sq_name.lower():
                    return await interaction.response.send_message("❌ A squad with that name already exists!", ephemeral=True)
                if sq["tag"].upper() == sq_tag:
                    return await interaction.response.send_message("❌ A squad with that tag already exists!", ephemeral=True)

            sq_id = f"squad_{int(time.time())}"
            squads[sq_id] = {
                "name": sq_name,
                "tag": sq_tag,
                "leader_id": interaction.user.id,
                "members": [interaction.user.id],
                "level": 1,
                "xp": 0,
                "created_at": time.time()
            }
            save_squads(squads)

            embed = discord.Embed(
                title=f"🛡️ CLAN SQUAD FOUNDED • [{sq_tag}] {sq_name}",
                description=(
                    f"Leader: {interaction.user.mention}\n\n"
                    f"🌟 Your squad has been officially registered! Invite friends using `/squad action:join name:{sq_name}`.\n"
                    f"💡 Hang out together in voice rooms to earn collective Squad XP and climb the weekly leaderboard!"
                ),
                color=0xFF007F
            )
            embed.set_footer(text="RAI VIBES Clan Wars", icon_url=config.RAI_ICON_URL)
            return await interaction.response.send_message(embed=embed)

        # 2. JOIN SQUAD
        if action == "join":
            if user_sq:
                return await interaction.response.send_message(f"⚠️ You are already in squad **{user_sq['name']}**!", ephemeral=True)
            if not name:
                return await interaction.response.send_message("❌ Specify the squad name you want to join!", ephemeral=True)

            target_id, target_sq = None, None
            for s_id, s_data in squads.items():
                if s_data["name"].lower() == name.strip().lower() or s_data["tag"].upper() == name.strip().upper():
                    target_id, target_sq = s_id, s_data
                    break

            if not target_sq:
                return await interaction.response.send_message("❌ Squad not found. Check `/squad action:leaderboard` for existing squads.", ephemeral=True)

            if len(target_sq["members"]) >= 15:
                return await interaction.response.send_message("❌ This squad is at maximum capacity (15 members)!", ephemeral=True)

            target_sq["members"].append(interaction.user.id)
            save_squads(squads)

            return await interaction.response.send_message(
                f"✅ You joined squad **[{target_sq['tag']}] {target_sq['name']}**! Welcome to the clan!",
                ephemeral=False
            )

        # 3. LEAVE SQUAD
        if action == "leave":
            if not user_sq:
                return await interaction.response.send_message("❌ You are not currently in any squad!", ephemeral=True)

            if interaction.user.id == user_sq["leader_id"]:
                # If leader leaves and members exist, transfer
                remaining = [m for m in user_sq["members"] if m != interaction.user.id]
                if remaining:
                    user_sq["leader_id"] = remaining[0]
                    user_sq["members"] = remaining
                    save_squads(squads)
                    return await interaction.response.send_message(f"👑 You left the squad. Leadership transferred to <@{remaining[0]}>.", ephemeral=True)
                else:
                    del squads[user_sq_id]
                    save_squads(squads)
                    return await interaction.response.send_message(f"🗑️ Squad **{user_sq['name']}** was disbanded because all members left.", ephemeral=True)
            else:
                user_sq["members"].remove(interaction.user.id)
                save_squads(squads)
                return await interaction.response.send_message(f"👋 You have left squad **{user_sq['name']}**.", ephemeral=True)

        # 4. SQUAD INFO
        if action == "info":
            target_sq = user_sq
            if name:
                for s_data in squads.values():
                    if s_data["name"].lower() == name.strip().lower() or s_data["tag"].upper() == name.strip().upper():
                        target_sq = s_data
                        break

            if not target_sq:
                return await interaction.response.send_message("❌ Squad not found or you are not in a squad!", ephemeral=True)

            lvl = target_sq.get("level", 1)
            xp = target_sq.get("xp", 0)
            needed_xp = lvl * 500
            m_count = len(target_sq.get("members", []))
            leader = interaction.guild.get_member(target_sq["leader_id"])
            leader_str = leader.mention if leader else f"`ID: {target_sq['leader_id']}`"

            embed = discord.Embed(
                title=f"🛡️ SQUAD PROFILE • [{target_sq['tag']}] {target_sq['name']}",
                color=0x00FFCC
            )
            embed.add_field(name="👑 Leader", value=leader_str, inline=True)
            embed.add_field(name="⭐ Squad Level", value=f"**Level {lvl}**", inline=True)
            embed.add_field(name="👥 Members", value=f"**{m_count}/15**", inline=True)
            embed.add_field(name="✨ Clan XP", value=f"`{xp}/{needed_xp}`", inline=True)
            embed.set_footer(text="RAI VIBES Clan Wars", icon_url=config.RAI_ICON_URL)
            return await interaction.response.send_message(embed=embed)

        # 5. TOGGLE SQUAD TAG IN NICKNAME
        if action == "tag":
            if not user_sq:
                return await interaction.response.send_message("❌ You must be in a squad to equip its tag!", ephemeral=True)

            tag_str = f"[{user_sq['tag']}]"
            member = interaction.user
            current_nick = member.nick or member.name

            if tag_str in current_nick:
                new_nick = current_nick.replace(tag_str, "").strip()
                action_text = f"Removed `{tag_str}` from your nickname."
            else:
                new_nick = f"{tag_str} {current_nick}".strip()[:32]
                action_text = f"Equipped `{tag_str}` to your nickname!"

            if member.id == interaction.guild.owner_id or member.top_role >= interaction.guild.me.top_role:
                return await interaction.response.send_message(
                    f"⚠️ Discord restricts bots from changing nicknames for Server Owners or roles higher than the bot.\n"
                    f"You can manually set your nickname to: **{new_nick}**!",
                    ephemeral=True
                )

            try:
                await member.edit(nick=new_nick, reason="Squad Clan Tag toggle")
                return await interaction.response.send_message(f"✅ {action_text} New name: **{new_nick}**", ephemeral=True)
            except Exception as e:
                return await interaction.response.send_message(f"❌ Could not update nickname: {e}", ephemeral=True)

        # 6. SQUAD LEADERBOARD
        if action == "leaderboard":
            if not squads:
                return await interaction.response.send_message("ℹ️ No squads registered yet! Create the first one with `/squad action:create`.", ephemeral=True)

            sorted_squads = sorted(squads.values(), key=lambda x: (x.get("level", 1), x.get("xp", 0)), reverse=True)[:10]

            embed = discord.Embed(
                title="🏆 SQUAD CLAN WARS • TOP LEADERBOARD",
                description="The most dominant squads on **RAI VIBES** ranked by Level and Voice XP:\n",
                color=0xFFD700
            )

            medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
            for i, sq in enumerate(sorted_squads):
                medal = medals[i] if i < len(medals) else f"#{i+1}"
                embed.add_field(
                    name=f"{medal} [{sq['tag']}] {sq['name']} (Lvl {sq.get('level', 1)})",
                    value=f"👥 {len(sq.get('members', []))} Members | ✨ `{sq.get('xp', 0):,}` Clan XP",
                    inline=False
                )

            embed.set_footer(text="Earn squad XP by hanging out in voice rooms together!", icon_url=config.RAI_ICON_URL)
            return await interaction.response.send_message(embed=embed)

    @commands.hybrid_command(name="teams", description="Randomly split members in your voice room into two balanced squads with captains.")
    async def teams(self, ctx: commands.Context):
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send("❌ You must be in a voice channel with other players to randomize teams!", ephemeral=True)

        members = [m for m in ctx.author.voice.channel.members if not m.bot]
        if len(members) < 2:
            return await ctx.send("⚠️ You need at least 2 people in your voice channel to split into teams!", ephemeral=True)

        shuffled = members.copy()
        random.shuffle(shuffled)
        mid = len(shuffled) // 2

        team_a = shuffled[:mid]
        team_b = shuffled[mid:]

        captain_a = team_a[0]
        captain_b = team_b[0]

        team_a_str = "\n".join([f"• {m.mention} {'👑 *(Captain)*' if m == captain_a else ''}" for m in team_a])
        team_b_str = "\n".join([f"• {m.mention} {'👑 *(Captain)*' if m == captain_b else ''}" for m in team_b])

        embed = discord.Embed(
            title="⚖️ BALANCED SQUAD RANDOMIZER",
            description=f"Divided **{len(members)} players** from {ctx.author.voice.channel.mention} into 2 balanced squads:",
            color=config.COLOR_PRIMARY
        )
        embed.add_field(name=f"🔵 TEAM ALPHA ({len(team_a)})", value=team_a_str, inline=True)
        embed.add_field(name=f"🔴 TEAM BRAVO ({len(team_b)})", value=team_b_str, inline=True)
        embed.set_footer(text="RAI VIBES 💗 • Matchmaking Engine", icon_url=config.RAI_ICON_URL)
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="bracket", description="Generate a single-elimination tournament match bracket for custom games.")
    @app_commands.describe(teams="Comma-separated squad names (4, 8, or 16 teams)")
    async def bracket(self, ctx: commands.Context, teams: Optional[str] = None):
        if teams:
            team_list = [t.strip() for t in teams.split(",") if t.strip()]
        else:
            team_list = [f"Squad #{i+1}" for i in range(8)]

        count = len(team_list)
        if count < 4:
            return await ctx.send("❌ Tournament brackets require at least 4 teams! Provide comma-separated names, e.g. `/bracket teams: Alpha, Bravo, Charlie, Delta`.", ephemeral=True)

        random.shuffle(team_list)

        embed = discord.Embed(
            title="🏆 TOURNAMENT SINGLE-ELIMINATION BRACKET",
            description=f"Generated balanced match schedule for **{count} participating squads**:",
            color=0xFFD700
        )

        matches = []
        for i in range(0, len(team_list) - 1, 2):
            matches.append(f"**Match #{len(matches)+1}:** `{team_list[i]}` ⚔️ `{team_list[i+1]}`")

        if len(team_list) % 2 != 0:
            matches.append(f"**Match #{len(matches)+1}:** `{team_list[-1]}` *(Bye to next round)*")

        embed.add_field(name="⚔️ ROUND 1 / QUARTERFINALS", value="\n".join(matches), inline=False)
        embed.add_field(
            name="🏁 ADVANCEMENT PATH",
            value="```fix\n[Round 1 / Quarterfinals] ➔ [Semifinals] ➔ [Grand Championship Final]\n```",
            inline=False
        )
        embed.set_footer(text="RAI VIBES 💗 • Community Tournament System", icon_url=config.RAI_ICON_URL)

        match_tuples = []
        for i in range(0, len(team_list) - 1, 2):
            match_tuples.append((team_list[i], team_list[i+1]))
        if len(team_list) % 2 != 0:
            match_tuples.append((team_list[-1], "BYE (Advance)"))

        card_buf = generate_bracket_card(match_tuples, round_name="Quarterfinals" if count >= 8 else "Semifinals")
        file = discord.File(fp=card_buf, filename="bracket.png")
        embed.set_image(url="attachment://bracket.png")

        await ctx.send(embed=embed, file=file)


async def setup(bot: commands.Bot):
    await bot.add_cog(Squads(bot))
