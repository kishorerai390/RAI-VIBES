import os
import json
import time
import math
import logging
from pathlib import Path
from typing import Optional, Dict, List, Literal

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button, button

import config
from cogs.economy import load_economy, save_economy

logger = logging.getLogger("Tournaments")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TOURNAMENTS_FILE = DATA_DIR / "tournaments.json"

SUPPORTED_GAMES = {
    "freefire": "💥 Free Fire Max",
    "bgmi": "⚡ BGMI (Battlegrounds)",
    "valorant": "🎯 Valorant Ranked",
    "gtarp": "🔫 GTA V / FiveM Heist",
    "roblox": "🧸 Roblox Championship",
    "rocketleague": "🚗 Rocket League 2v2",
    "chess": "♟️ Tactical Chess Tournament"
}


def load_tournaments() -> Dict[str, dict]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if TOURNAMENTS_FILE.exists():
        try:
            with open(TOURNAMENTS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_tournaments(data: Dict[str, dict]):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(TOURNAMENTS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def credit_coins(user_id: int, amount: int):
    try:
        data = load_economy()
        uid = str(user_id)
        if uid not in data:
            data[uid] = {"coins": 200, "last_daily": 0, "streak": 0, "rep": 0, "last_rep": 0}
        data[uid]["coins"] = data[uid].get("coins", 0) + amount
        save_economy(data)
    except Exception as e:
        logger.warning(f"Could not credit tournament prize: {e}")


class TournamentRegistrationView(View):
    """Interactive panel buttons for tournament registration."""
    def __init__(self, tourney_id: str):
        super().__init__(timeout=None)
        self.tourney_id = tourney_id

    @button(label="Register Squad / Solo ⚔️", style=discord.ButtonStyle.success, custom_id="tourney_register_btn")
    async def register_btn(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        tourneys = load_tournaments()
        t = tourneys.get(self.tourney_id)
        if not t or t.get("status") != "registration":
            return await interaction.followup.send("⚠️ Registration is closed or tournament no longer active.", ephemeral=True)

        uid = interaction.user.id
        # Check if already registered
        for team in t["teams"]:
            if uid == team["captain_id"] or uid in team.get("members", []):
                return await interaction.followup.send("ℹ️ You are already registered in this tournament!", ephemeral=True)

        if len(t["teams"]) >= t["max_teams"]:
            return await interaction.followup.send("⚠️ All slots are currently filled!", ephemeral=True)

        team_name = f"Team {interaction.user.display_name[:15]}"
        t["teams"].append({
            "name": team_name,
            "captain_id": uid,
            "members": [uid],
            "registered_at": time.time()
        })
        save_tournaments(tourneys)

        needed = t["max_teams"] - len(t["teams"])
        await interaction.followup.send(
            f"✅ **Registered!** You joined as `{team_name}`. ({len(t['teams'])}/{t['max_teams']} filled - `{needed}` slots left)",
            ephemeral=True
        )

    @button(label="Withdraw ❌", style=discord.ButtonStyle.secondary, custom_id="tourney_withdraw_btn")
    async def withdraw_btn(self, interaction: discord.Interaction, btn: Button):
        await interaction.response.defer(ephemeral=True)
        tourneys = load_tournaments()
        t = tourneys.get(self.tourney_id)
        if not t or t.get("status") != "registration":
            return await interaction.followup.send("⚠️ Tournament is not in registration stage.", ephemeral=True)

        uid = interaction.user.id
        prev_count = len(t["teams"])
        t["teams"] = [team for team in t["teams"] if team["captain_id"] != uid and uid not in team.get("members", [])]

        if len(t["teams"]) < prev_count:
            save_tournaments(tourneys)
            await interaction.followup.send("⚪ You have withdrawn from the tournament.", ephemeral=True)
        else:
            await interaction.followup.send("❌ You were not registered.", ephemeral=True)


class Tournaments(commands.Cog):
    """Competitive Scrims, Tournaments & Bracket Championship Engine."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot

    tournament_group = app_commands.Group(name="tournament", description="Competitive scrims, brackets, and tournament championships.")

    @tournament_group.command(name="create", description="Host a new competitive tournament championship.")
    @app_commands.describe(
        name="Name of the championship (e.g. Free Fire Scrims Night)",
        game="Select the tournament game",
        slots="Number of team slots (4, 8, or 16)",
        prize_pool="Total Rai Coins awarded to the Grand Champions (e.g. 10000)"
    )
    @app_commands.choices(game=[
        app_commands.Choice(name="💥 Free Fire Max", value="freefire"),
        app_commands.Choice(name="⚡ BGMI (Battlegrounds)", value="bgmi"),
        app_commands.Choice(name="🎯 Valorant Ranked", value="valorant"),
        app_commands.Choice(name="🔫 GTA V / FiveM Heist", value="gtarp"),
        app_commands.Choice(name="🧸 Roblox Championship", value="roblox"),
        app_commands.Choice(name="🚗 Rocket League", value="rocketleague"),
        app_commands.Choice(name="♟️ Tactical Chess", value="chess"),
    ])
    @app_commands.choices(slots=[
        app_commands.Choice(name="4 Teams (Semi-Finals & Finals)", value=4),
        app_commands.Choice(name="8 Teams (Quarter, Semi, Finals)", value=8),
        app_commands.Choice(name="16 Teams (Full Championship)", value=16),
    ])
    @app_commands.checks.has_permissions(manage_events=True)
    async def tournament_create_cmd(
        self,
        interaction: discord.Interaction,
        name: str,
        game: app_commands.Choice[str],
        slots: app_commands.Choice[int],
        prize_pool: int = 5000
    ):
        tourney_id = f"T-{int(time.time()) % 100000:05d}"
        game_title = SUPPORTED_GAMES.get(game.value, "Esports Championship")

        tourneys = load_tournaments()
        tourneys[tourney_id] = {
            "id": tourney_id,
            "guild_id": interaction.guild_id,
            "name": name,
            "game": game.value,
            "max_teams": slots.value,
            "prize_pool": prize_pool,
            "host_id": interaction.user.id,
            "status": "registration",
            "teams": [],
            "matches": [],
            "current_round": 1,
            "created_at": time.time()
        }
        save_tournaments(tourneys)

        embed = discord.Embed(
            title=f"🏆 ✦ TOURNAMENT ANNOUNCEMENT: {name.upper()} ✦ 🏆",
            description=(
                f"**Game:** `{game_title}`\n"
                f"**Bracket Size:** `{slots.value} Teams`\n"
                f"**Prize Pool:** `💰 {prize_pool:,} Rai Coins`\n"
                f"**Host:** {interaction.user.mention}\n"
                f"**Tournament ID:** `{tourney_id}`\n\n"
                f"⚡ **Registration is now OPEN!**\n"
                f"Click **`[Register Squad / Solo ⚔️]`** below to claim your spot in the bracket!"
            ),
            color=0xFFD700
        )
        embed.set_thumbnail(url=config.RAI_ICON_URL)
        embed.set_footer(text="RAI VIBES 💗 Competitive Gaming Hub • Scrims & Tournaments", icon_url=config.RAI_ICON_URL)

        view = TournamentRegistrationView(tourney_id)
        await interaction.response.send_message(embed=embed, view=view)

    @tournament_group.command(name="bracket", description="View the current visual single-elimination tournament bracket.")
    @app_commands.describe(tournament_id="Tournament ID (e.g. T-12345)")
    async def tournament_bracket_cmd(self, interaction: discord.Interaction, tournament_id: str):
        tourneys = load_tournaments()
        t = tourneys.get(tournament_id.strip().upper())
        if not t:
            return await interaction.response.send_message(f"❌ Tournament `{tournament_id}` was not found.", ephemeral=True)

        embed = discord.Embed(
            title=f"🏆 {t['name']} • Single Elimination Bracket",
            color=0x00FF88
        )
        embed.add_field(name="Status", value=f"`{t['status'].upper()}`", inline=True)
        embed.add_field(name="Teams Registered", value=f"`{len(t['teams'])}/{t['max_teams']}`", inline=True)
        embed.add_field(name="Prize Pool", value=f"`{t['prize_pool']:,} Rai Coins`", inline=True)

        if t["status"] == "registration":
            team_lines = [f"`#{i+1}` {tm['name']} (<@{tm['captain_id']}>)" for i, tm in enumerate(t["teams"])]
            embed.add_field(
                name="📋 Registered Competitors",
                value="\n".join(team_lines) if team_lines else "*No teams registered yet. Be the first!*",
                inline=False
            )
        else:
            match_lines = []
            for m in t.get("matches", []):
                t1 = m["team1"]
                t2 = m["team2"]
                w = m.get("winner")
                status = f"✅ **Winner:** `{w}`" if w else "⏳ *Pending match*"
                match_lines.append(f"**Match #{m['match_id']} (Round {m['round']}):**\n`{t1}` ⚔️ `{t2}`\n{status}")

            embed.add_field(
                name="⚔️ Match Pairings & Results",
                value="\n\n".join(match_lines) if match_lines else "*No matches generated.*",
                inline=False
            )

        embed.set_footer(text=f"Tournament ID: {t['id']} • RAI VIBES Esports", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    @tournament_group.command(name="start", description="Close registration and generate single-elimination match pairings.")
    @app_commands.describe(tournament_id="Tournament ID to launch")
    @app_commands.checks.has_permissions(manage_events=True)
    async def tournament_start_cmd(self, interaction: discord.Interaction, tournament_id: str):
        tourneys = load_tournaments()
        t = tourneys.get(tournament_id.strip().upper())
        if not t:
            return await interaction.response.send_message(f"❌ Tournament `{tournament_id}` not found.", ephemeral=True)

        if len(t["teams"]) < 2:
            return await interaction.response.send_message("❌ Need at least 2 teams registered to start the tournament bracket.", ephemeral=True)

        t["status"] = "in_progress"

        # Generate Round 1 pairings
        teams = [tm["name"] for tm in t["teams"]]
        # If odd number, add Bye
        if len(teams) % 2 != 0:
            teams.append("BYE (Free Win)")

        matches = []
        m_id = 1
        for i in range(0, len(teams), 2):
            matches.append({
                "match_id": m_id,
                "round": 1,
                "team1": teams[i],
                "team2": teams[i+1],
                "winner": None
            })
            m_id += 1

        t["matches"] = matches
        save_tournaments(tourneys)

        embed = discord.Embed(
            title=f"🚀 {t['name']} • BRACKET HAS COMMENCED!",
            description=(
                f"Registration is officially CLOSED!\n"
                f"**{len(t['teams'])} teams** are battling for `💰 {t['prize_pool']:,} Rai Coins`!\n\n"
                f"⚔️ **Round 1 Matchups:**\n" +
                "\n".join([f"• **Match {m['match_id']}:** `{m['team1']}` ⚔️ `{m['team2']}`" for m in matches]) +
                f"\n\nUse `/tournament setwinner` to record winners and advance the bracket!"
            ),
            color=0xFF007F
        )
        embed.set_footer(text=f"Tournament ID: {t['id']}", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    @tournament_group.command(name="setwinner", description="Record the winner of a tournament match and advance bracket.")
    @app_commands.describe(
        tournament_id="Tournament ID",
        match_id="Match number (e.g. 1)",
        winner="Name of the winning team exactly as listed in bracket"
    )
    @app_commands.checks.has_permissions(manage_events=True)
    async def tournament_setwinner_cmd(
        self,
        interaction: discord.Interaction,
        tournament_id: str,
        match_id: int,
        winner: str
    ):
        tourneys = load_tournaments()
        t = tourneys.get(tournament_id.strip().upper())
        if not t or t["status"] != "in_progress":
            return await interaction.response.send_message("❌ Tournament not in progress.", ephemeral=True)

        target_match = None
        for m in t.get("matches", []):
            if m["match_id"] == match_id:
                target_match = m
                break

        if not target_match:
            return await interaction.response.send_message(f"❌ Match #{match_id} not found.", ephemeral=True)

        target_match["winner"] = winner
        save_tournaments(tourneys)

        # Check if all matches in current round are resolved
        current_round = target_match["round"]
        round_matches = [m for m in t["matches"] if m["round"] == current_round]
        all_resolved = all(m.get("winner") is not None for m in round_matches)

        if all_resolved:
            winners = [m["winner"] for m in round_matches if m["winner"] != "BYE (Free Win)"]
            if len(winners) == 1:
                # Tournament Finished! We have a champion!
                champ_name = winners[0]
                t["status"] = "finished"
                t["champion"] = champ_name
                save_tournaments(tourneys)

                # Award Rai Coins prize pool to captain & team members
                payout_captain = None
                for tm in t["teams"]:
                    if tm["name"] == champ_name:
                        payout_captain = tm["captain_id"]
                        credit_coins(payout_captain, t["prize_pool"])
                        break

                embed = discord.Embed(
                    title="👑 ✦ TOURNAMENT GRAND CHAMPION DECLARED ✦ 👑",
                    description=(
                        f"🎉 Huge congratulations to **`{champ_name}`** for winning **{t['name']}**!\n\n"
                        f"💰 **Prize Pool Awarded:** `+{t['prize_pool']:,} Rai Coins`!\n"
                        f"🏆 **Champion Captain:** <@{payout_captain}>\n\n"
                        f"Thank you to all {len(t['teams'])} teams for competing with honor!"
                    ),
                    color=0xFFD700
                )
                embed.set_footer(text="RAI VIBES 💗 Esports League", icon_url=config.RAI_ICON_URL)
                return await interaction.response.send_message(embed=embed)
            else:
                # Generate next round matches
                next_round = current_round + 1
                next_matches = []
                new_mid = max(m["match_id"] for m in t["matches"]) + 1

                if len(winners) % 2 != 0:
                    winners.append("BYE (Free Win)")

                for i in range(0, len(winners), 2):
                    next_matches.append({
                        "match_id": new_mid,
                        "round": next_round,
                        "team1": winners[i],
                        "team2": winners[i+1],
                        "winner": None
                    })
                    new_mid += 1

                t["matches"].extend(next_matches)
                save_tournaments(tourneys)

                embed = discord.Embed(
                    title=f"⚔️ Round {current_round} Complete ➔ Round {next_round} Matches Ready!",
                    description="\n".join([f"• **Match {m['match_id']}:** `{m['team1']}` ⚔️ `{m['team2']}`" for m in next_matches]),
                    color=0x2ED573
                )
                return await interaction.response.send_message(embed=embed)

        await interaction.response.send_message(f"✅ Match #{match_id} recorded: **`{winner}`** won!", ephemeral=True)

    # -------------------------------------------------------------
    # ⚔️ SCRIM SPLIT & MERGE CONTROLS
    # -------------------------------------------------------------
    scrim_group = app_commands.Group(name="scrim", description="Tactical 5v5 scrim team split and merge controls.")

    @scrim_group.command(name="split", description="Split players in your voice channel into two team channels.")
    @app_commands.describe(team1_vc="Voice channel for Team 1", team2_vc="Voice channel for Team 2")
    async def scrim_split(self, interaction: discord.Interaction, team1_vc: discord.VoiceChannel, team2_vc: discord.VoiceChannel):
        if not interaction.user.voice or not interaction.user.voice.channel:
            return await interaction.response.send_message("❌ You must be in a voice channel with your squad to split teams!", ephemeral=True)

        members = [m for m in interaction.user.voice.channel.members if not m.bot]
        if len(members) < 2:
            return await interaction.response.send_message("❌ Need at least 2 players in the voice channel to split.", ephemeral=True)

        import random
        random.shuffle(members)
        mid = len(members) // 2
        team1 = members[:mid]
        team2 = members[mid:]

        for m in team1:
            try:
                await m.move_to(team1_vc, reason="Scrim Team 1 Split")
            except Exception:
                pass

        for m in team2:
            try:
                await m.move_to(team2_vc, reason="Scrim Team 2 Split")
            except Exception:
                pass

        embed = discord.Embed(
            title="⚔️ TACTICAL SCRIM SPLIT COMPLETE",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"**Team 1** ({len(team1)} players) ➔ {team1_vc.mention}\n"
                f"{', '.join([m.mention for m in team1])}\n\n"
                f"**Team 2** ({len(team2)} players) ➔ {team2_vc.mention}\n"
                f"{', '.join([m.mention for m in team2])}\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"💡 *Use `/scrim merge` after the match to bring everyone back together!*"
            ),
            color=0x00F5D4
        )
        embed.set_footer(text="RAI VIBES 💗 Scrim Engine", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

    @scrim_group.command(name="merge", description="Merge players from both team channels back into one debrief lounge.")
    @app_commands.describe(source_vc1="Team 1 Voice Channel", source_vc2="Team 2 Voice Channel", target_vc="Channel to merge into")
    async def scrim_merge(self, interaction: discord.Interaction, source_vc1: discord.VoiceChannel, source_vc2: discord.VoiceChannel, target_vc: Optional[discord.VoiceChannel] = None):
        dest = target_vc or (interaction.user.voice.channel if interaction.user.voice else source_vc1)
        moved_count = 0
        for vc in [source_vc1, source_vc2]:
            for m in vc.members:
                if not m.bot and m.voice and m.voice.channel and m.voice.channel.id != dest.id:
                    try:
                        await m.move_to(dest, reason="Scrim Merge Back")
                        moved_count += 1
                    except Exception:
                        pass

        await interaction.response.send_message(f"🤝 **Merged `{moved_count}` players** back into {dest.mention} for post-match debrief!", ephemeral=False)

    @app_commands.command(name="veto", description="Start an interactive competitive map ban/pick phase.")
    @app_commands.describe(game="Select game", team1="Team 1 Name", team2="Team 2 Name", captain1="Team 1 Captain", captain2="Team 2 Captain")
    @app_commands.choices(game=[
        app_commands.Choice(name="🎯 Valorant", value="valorant"),
        app_commands.Choice(name="⚡ CS2", value="cs2"),
        app_commands.Choice(name="💥 BGMI", value="bgmi"),
        app_commands.Choice(name="🚗 Rocket League", value="rocketleague"),
    ])
    async def veto_cmd(self, interaction: discord.Interaction, game: app_commands.Choice[str], team1: str, team2: str, captain1: discord.Member, captain2: discord.Member):
        view = MapVetoView(game.value, team1, team2, captain1, captain2)
        embed = discord.Embed(
            title=f"🗺️ MAP VETO: {game.name.upper()}",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"⚔️ **Matchup:** `{team1}` vs `{team2}`\n"
                f"👑 **Captains:** {captain1.mention} vs {captain2.mention}\n\n"
                f"👉 **First Ban:** {captain1.mention} (Click a button to ban a map)\n"
                f"Available maps: `{len(view.maps)}`"
            ),
            color=0xFF4757
        )
        embed.set_footer(text="RAI VIBES 💗 Competitive Veto System", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, view=view)


MAP_POOLS = {
    "valorant": ["Ascent", "Bind", "Breeze", "Haven", "Icebox", "Lotus", "Split", "Sunset"],
    "cs2": ["Mirage", "Inferno", "Nuke", "Dust II", "Ancient", "Anubis", "Vertigo"],
    "bgmi": ["Erangel", "Miramar", "Sanhok", "Vikendi"],
    "rocketleague": ["DFH Stadium", "Mannfield", "Champions Field", "Urban Central"]
}


class MapVetoView(discord.ui.View):
    def __init__(self, game: str, team1: str, team2: str, captain1: discord.Member, captain2: discord.Member):
        super().__init__(timeout=300)
        self.game = game
        self.team1 = team1
        self.team2 = team2
        self.captain1 = captain1
        self.captain2 = captain2
        self.turn = captain1
        self.maps = list(MAP_POOLS.get(game, MAP_POOLS["valorant"]))
        self.banned_maps = []
        self.decider = None
        self._build_buttons()

    def _build_buttons(self):
        self.clear_items()
        for idx, map_name in enumerate(self.maps):
            btn = discord.ui.Button(
                label=f"Ban {map_name}",
                style=discord.ButtonStyle.danger,
                custom_id=f"ban_{idx}"
            )
            btn.callback = self.make_ban_callback(map_name)
            self.add_item(btn)

    def make_ban_callback(self, map_name: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.turn.id:
                return await interaction.response.send_message(f"❌ It's {self.turn.mention}'s turn to ban a map!", ephemeral=True)

            if map_name in self.maps:
                self.maps.remove(map_name)
                self.banned_maps.append((map_name, self.turn.display_name))

            if len(self.maps) == 1:
                self.decider = self.maps[0]
                embed = discord.Embed(
                    title=f"🎯 MAP VETO COMPLETE: {self.decider.upper()}",
                    description=(
                        f"✦ ───────────────────────────── ✦\n\n"
                        f"⚔️ **Matchup:** `{self.team1}` vs `{self.team2}`\n"
                        f"🏆 **Decider Map:** **`{self.decider}`**\n\n"
                        f"**Banned Maps:**\n" + "\n".join([f"• 🚫 ~~{m}~~ *(banned by {c})*" for m, c in self.banned_maps])
                    ),
                    color=0x2ED573
                )
                embed.set_footer(text="RAI VIBES 💗 Competitive Veto System", icon_url=config.RAI_ICON_URL)
                return await interaction.response.edit_message(embed=embed, view=None)

            self.turn = self.captain2 if self.turn == self.captain1 else self.captain1
            self._build_buttons()

            embed = discord.Embed(
                title=f"🗺️ MAP VETO: {self.game.upper()}",
                description=(
                    f"⚔️ **Matchup:** `{self.team1}` vs `{self.team2}`\n"
                    f"👉 **Current Turn:** {self.turn.mention} (Choose a map to BAN)\n"
                    f"Remaining maps: `{len(self.maps)}`\n\n"
                    f"**Banned So Far:**\n" + "\n".join([f"• 🚫 ~~{m}~~ *(by {c})*" for m, c in self.banned_maps])
                ),
                color=0xFF4757
            )
            embed.set_footer(text="RAI VIBES 💗 Competitive Veto System", icon_url=config.RAI_ICON_URL)
            await interaction.response.edit_message(embed=embed, view=self)

        return callback


async def setup(bot: commands.Bot):
    await bot.add_cog(Tournaments(bot))
