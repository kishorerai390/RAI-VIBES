import os
import json
import time
import asyncio
import logging
from pathlib import Path
from typing import Optional, Dict

import discord
from discord import app_commands
from discord.ext import commands

import config

logger = logging.getLogger("Productivity")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
TODO_FILE = DATA_DIR / "todos.json"
VOICE_STATS_FILE = DATA_DIR / "voice_stats.json"
TELEMETRY_FILE = DATA_DIR / "telemetry.json"


def load_todos() -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if TODO_FILE.exists():
        try:
            with open(TODO_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_todos(data: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(TODO_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


class Productivity(commands.Cog):
    """Productivity Suite: Pomodoro Focus Timer, Personal Todo Tracker & Voice Activity Leaderboard."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Active pomodoro sessions: user_id -> {"end_time": int, "task": asyncio.Task, "minutes": int, "goal": str}
        self.active_pomodoros: Dict[int, dict] = {}

    # -------------------------------------------------------------
    # 🍅 1. POMODORO STUDY & FOCUS LOUNGE
    # -------------------------------------------------------------
    pomodoro_group = app_commands.Group(name="pomodoro", description="Productivity Pomodoro focus timers and study rewards")

    @pomodoro_group.command(name="start", description="Start a focused study/work Pomodoro session with coin rewards.")
    @app_commands.describe(
        minutes="Duration of study focus in minutes (5 - 120, default 25)",
        break_minutes="Duration of break in minutes (default 5)",
        goal="Optional study or coding goal for this session"
    )
    async def pomodoro_start(
        self,
        interaction: discord.Interaction,
        minutes: int = 25,
        break_minutes: int = 5,
        goal: Optional[str] = None
    ):
        if minutes < 5 or minutes > 120:
            return await interaction.response.send_message("❌ Focus session must be between 5 and 120 minutes.", ephemeral=True)
        if break_minutes < 1 or break_minutes > 30:
            return await interaction.response.send_message("❌ Break must be between 1 and 30 minutes.", ephemeral=True)

        user = interaction.user
        uid = user.id

        if uid in self.active_pomodoros:
            return await interaction.response.send_message(
                "⏳ You already have an active Pomodoro timer running! Use `/pomodoro cancel` if you need to abort it.",
                ephemeral=True
            )

        now = int(time.time())
        end_time = now + (minutes * 60)
        goal_text = f"\n🎯 **Goal:** {goal}" if goal else ""

        embed_start = discord.Embed(
            title="🍅 ┊ 𝐏𝐎𝐌𝐎𝐃𝐎𝐑𝐎  𝐅𝐎𝐂𝐔𝐒  𝐒𝐄𝐒𝐒𝐈𝐎𝐍",
            description=(
                f"Concentration mode engaged for {user.mention}! 📚✨\n\n"
                f"⏱️ **Focus Duration:** `{minutes} Minutes`\n"
                f"☕ **Scheduled Break:** `{break_minutes} Minutes`\n"
                f"🎯 **Target Finish:** <t:{end_time}:R> (<t:{end_time}:t>){goal_text}\n\n"
                f"💡 **Pro-Tip:** Mute notifications and join our Lo-Fi Lounge for calming study beats!\n"
                f"🪙 *Complete this session to earn `+{minutes * 10:,}` Rai Coins!*"
            ),
            color=0xFF4757
        )
        embed_start.set_thumbnail(url=user.display_avatar.url)
        embed_start.set_footer(text="RAI FAM 💗 • Focus & Productivity Lounge", icon_url=config.RAI_ICON_URL)
        embed_start.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed_start)

        # Background runner task
        async def session_runner():
            try:
                await asyncio.sleep(minutes * 60)

                # Award economy coins and level XP
                coin_reward = minutes * 10
                try:
                    from cogs.casino import add_coins
                    add_coins(uid, coin_reward)
                except Exception as err:
                    logger.warning(f"Could not award coins: {err}")

                embed_finish = discord.Embed(
                    title="🔔 ┊ 𝐏𝐎𝐌𝐎𝐃𝐎𝐑𝐎  𝐒𝐄𝐒𝐒𝐈𝐎𝐍  𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄!",
                    description=(
                        f"🎉 Outstanding focus, {user.mention}! Your **{minutes}-minute** study sprint is complete!\n\n"
                        f"☕ **Time for a {break_minutes}-minute break:** Stand up, stretch, grab a glass of water or coffee!\n"
                        f"🪙 **Reward Credited:** `+{coin_reward:,} Rai Coins`\n"
                        f"🏆 *Stay consistent to conquer your daily goals!*"
                    ),
                    color=0x2ED573
                )
                embed_finish.set_footer(text="RAI FAM 💗 • Focus Completed", icon_url=config.RAI_ICON_URL)

                if uid in self.active_pomodoros:
                    del self.active_pomodoros[uid]

                try:
                    await interaction.channel.send(content=f"🔔 {user.mention}", embed=embed_finish)
                except Exception:
                    pass

            except asyncio.CancelledError:
                pass

        task = asyncio.create_task(session_runner())
        self.active_pomodoros[uid] = {
            "end_time": end_time,
            "task": task,
            "minutes": minutes,
            "goal": goal or "General Study"
        }

    @pomodoro_group.command(name="cancel", description="Cancel your currently running Pomodoro timer.")
    async def pomodoro_cancel(self, interaction: discord.Interaction):
        uid = interaction.user.id
        if uid not in self.active_pomodoros:
            return await interaction.response.send_message("❌ You have no active Pomodoro timer to cancel.", ephemeral=True)

        session = self.active_pomodoros.pop(uid)
        session["task"].cancel()
        await interaction.response.send_message("🛑 Your Pomodoro focus timer has been cancelled. Take care!", ephemeral=True)

    @pomodoro_group.command(name="status", description="Check how much time remains on your active Pomodoro timer.")
    async def pomodoro_status(self, interaction: discord.Interaction):
        uid = interaction.user.id
        if uid not in self.active_pomodoros:
            return await interaction.response.send_message("💤 You do not have an active Pomodoro timer. Start one with `/pomodoro start`!", ephemeral=True)

        session = self.active_pomodoros[uid]
        rem = max(0, session["end_time"] - int(time.time()))
        mins = rem // 60
        secs = rem % 60

        embed = discord.Embed(
            title="🍅 ┊ 𝐀𝐂𝐓𝐈𝐕𝐄  𝐏𝐎𝐌𝐎𝐃𝐎𝐑𝐎  𝐒𝐓𝐀𝐓𝐔𝐒",
            description=(
                f"👤 **User:** {interaction.user.mention}\n"
                f"🎯 **Goal:** `{session['goal']}`\n"
                f"⏳ **Time Remaining:** `{mins}m {secs}s` (<t:{session['end_time']}:R>)\n"
                f"🪙 **Completion Reward:** `+{session['minutes'] * 10:,} Rai Coins`"
            ),
            color=0xFFA502
        )
        embed.set_footer(text="Keep going, you've got this! 📚", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # -------------------------------------------------------------
    # 📝 2. TASK TODO LIST ENGINE
    # -------------------------------------------------------------
    todo_group = app_commands.Group(name="todo", description="Personal productivity tasks & daily goal tracker")

    @todo_group.command(name="add", description="Add a task or homework assignment to your personal todo list.")
    @app_commands.describe(task="The task description or goal")
    async def todo_add(self, interaction: discord.Interaction, task: str):
        if len(task) > 200:
            return await interaction.response.send_message("❌ Task description must be under 200 characters.", ephemeral=True)

        data = load_todos()
        uid = str(interaction.user.id)
        user_tasks = data.setdefault(uid, [])

        if len(user_tasks) >= 25:
            return await interaction.response.send_message("❌ You reached the limit of 25 active tasks! Complete or clear older ones first.", ephemeral=True)

        task_id = len(user_tasks) + 1
        created_at = int(time.time())
        user_tasks.append({
            "id": task_id,
            "text": task.strip(),
            "done": False,
            "created_at": created_at
        })
        save_todos(data)

        embed = discord.Embed(
            title="📝 ┊ 𝐓𝐀𝐒𝐊  𝐀𝐃𝐃𝐄𝐃!",
            description=(
                f"✅ Added to your list: **#{task_id}**\n"
                f"📌 `{task.strip()}`\n\n"
                f"Use `/todo list` to view all tasks or `/todo done {task_id}` when finished!"
            ),
            color=0x00F2FE
        )
        embed.set_footer(text=f"Total active tasks: {len(user_tasks)}", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @todo_group.command(name="list", description="View your personal todo list and task completion progress.")
    async def todo_list(self, interaction: discord.Interaction):
        data = load_todos()
        uid = str(interaction.user.id)
        tasks = data.get(uid, [])

        if not tasks:
            return await interaction.response.send_message(
                "📋 Your todo list is empty! Add your first task with `/todo add <task>`.",
                ephemeral=True
            )

        completed_count = sum(1 for t in tasks if t.get("done"))
        total_count = len(tasks)
        pct = int((completed_count / total_count) * 100) if total_count > 0 else 0

        bar = "█" * (pct // 10) + "░" * (10 - (pct // 10))

        lines = []
        for t in tasks:
            status = "✅ ~~" if t.get("done") else "⏳ **"
            end_tag = "~~" if t.get("done") else "**"
            lines.append(f"`#{t['id']}` {status}{t['text']}{end_tag}")

        embed = discord.Embed(
            title=f"📋 ┊ {interaction.user.display_name}'𝐬  𝐓𝐎𝐃𝐎  𝐋𝐈𝐒𝐓",
            description=(
                f"**Progress:** `{pct}%` `[{bar}]` ({completed_count}/{total_count} done)\n"
                f"✦ ───────────────────────────── ✦\n"
                + "\n".join(lines) +
                f"\n✦ ───────────────────────────── ✦\n"
                f"💡 *Mark tasks complete with `/todo done <id>` • Clear with `/todo clear`*"
            ),
            color=0x70A1FF
        )
        embed.set_thumbnail(url=interaction.user.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Personal Productivity Tracker", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @todo_group.command(name="done", description="Mark a task as completed.")
    @app_commands.describe(task_id="The # number of the task from /todo list")
    async def todo_done(self, interaction: discord.Interaction, task_id: int):
        data = load_todos()
        uid = str(interaction.user.id)
        tasks = data.get(uid, [])

        matched = next((t for t in tasks if t["id"] == task_id), None)
        if not matched:
            return await interaction.response.send_message(f"❌ Task `#{task_id}` not found on your list.", ephemeral=True)

        if matched.get("done"):
            return await interaction.response.send_message(f"💡 Task `#{task_id}` is already completed!", ephemeral=True)

        matched["done"] = True
        save_todos(data)

        embed = discord.Embed(
            title="🎉 ┊ 𝐓𝐀𝐒𝐊  𝐂𝐎𝐌𝐏𝐋𝐄𝐓𝐄𝐃!",
            description=f"Great job knocking out task `#{task_id}`:\n✅ ~~{matched['text']}~~",
            color=0x2ED573
        )
        embed.set_footer(text="Check your list with /todo list", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @todo_group.command(name="clear", description="Remove all completed tasks from your list.")
    async def todo_clear(self, interaction: discord.Interaction):
        data = load_todos()
        uid = str(interaction.user.id)
        tasks = data.get(uid, [])

        initial_len = len(tasks)
        remaining = [t for t in tasks if not t.get("done")]

        # Re-index remaining
        for i, t in enumerate(remaining):
            t["id"] = i + 1

        cleared_count = initial_len - len(remaining)
        data[uid] = remaining
        save_todos(data)

        await interaction.response.send_message(
            f"🧹 Cleared **{cleared_count}** completed tasks! You have **{len(remaining)}** pending tasks remaining.",
            ephemeral=True
        )

    # -------------------------------------------------------------
    # 🎙️ 3. LIVE VOICE ACTIVITY & LEADERBOARD
    # -------------------------------------------------------------
    @app_commands.command(name="voicetop", description="Display the top 10 voice lounge champions and listening activity.")
    async def voicetop(self, interaction: discord.Interaction):
        leaderboard_data = []

        # Check primary voice_stats.json
        if VOICE_STATS_FILE.exists():
            try:
                with open(VOICE_STATS_FILE, "r", encoding="utf-8") as f:
                    vs = json.load(f)
                    for uid, vdata in vs.items():
                        secs = vdata.get("total_seconds", 0)
                        leaderboard_data.append((uid, secs, vdata.get("username", "Member")))
            except Exception:
                pass

        # Check telemetry.json if voice_stats had few entries
        if len(leaderboard_data) < 3 and TELEMETRY_FILE.exists():
            try:
                with open(TELEMETRY_FILE, "r", encoding="utf-8") as f:
                    tdata = json.load(f)
                    users = tdata.get("users", {})
                    for uid, uinfo in users.items():
                        mins = uinfo.get("total_minutes", 0)
                        leaderboard_data.append((uid, mins * 60, f"<@{uid}>"))
            except Exception:
                pass

        # Deduplicate by user ID
        merged = {}
        for uid, secs, name in leaderboard_data:
            merged[uid] = max(merged.get(uid, (0, name))[0], secs), name

        sorted_users = sorted(merged.items(), key=lambda x: x[1][0], reverse=True)[:10]

        if not sorted_users:
            return await interaction.response.send_message("🎙️ No voice activity has been recorded yet. Join any voice lounge to start logging time!", ephemeral=True)

        medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"]
        lines = []

        for i, (uid, (total_sec, name)) in enumerate(sorted_users):
            hours = total_sec // 3600
            mins = (total_sec % 3600) // 60
            medal = medals[i] if i < len(medals) else f"`#{i+1}`"
            lines.append(f"{medal} <@{uid}> — **{hours}h {mins}m** `{total_sec:,}s`")

        embed = discord.Embed(
            title="🎙️ ┊ 𝐕𝐎𝐈𝐂𝐄  𝐋𝐎𝐔𝐍𝐆𝐄  𝐋𝐄𝐀𝐃𝐄𝐑𝐁𝐎𝐀𝐑𝐃",
            description=(
                f"✦ ───────────────────────────────────── ✦\n\n"
                + "\n".join(lines) +
                f"\n\n✦ ───────────────────────────────────── ✦\n"
                f"💡 *Earn voice XP and coins passively by hanging out in voice channels!*"
            ),
            color=0x00FFCC
        )
        embed.set_thumbnail(url="https://cdn.discordapp.com/emojis/1149363065603702834.webp?size=96&quality=lossless")
        embed.set_footer(text="RAI FAM 💗 • Voice Lounge Telemetry", icon_url=config.RAI_ICON_URL)
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

    # -------------------------------------------------------------
    # 🔒 4. DEEP FOCUS DISTRACTION-FREE VOICE ROOM
    # -------------------------------------------------------------
    @app_commands.command(name="deepfocus", description="Create a temporary silent, distraction-free voice room (auto-mutes & deafens).")
    @app_commands.describe(
        minutes="Duration of the deep work session in minutes (10 to 180, default 45)",
        name="Optional custom name for your focus sanctuary"
    )
    async def deepfocus_cmd(self, interaction: discord.Interaction, minutes: int = 45, name: Optional[str] = None):
        if minutes < 10 or minutes > 180:
            return await interaction.response.send_message("❌ Deep Focus duration must be between 10 and 180 minutes.", ephemeral=True)

        guild = interaction.guild
        cat = (
            discord.utils.get(guild.categories, name="🍅 ＳＴＵＤＹ  ＆  ＦＯＣＵＳ")
            or discord.utils.get(guild.categories, name="🥂 ＰＲＩＶＡＴＥ  ＳＵＩＴＥＳ")
            or interaction.channel.category
        )

        room_title = f"🔒 ┊ {name[:20] if name else 'Deep Focus'} ({minutes}m)"
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(
                connect=True,
                speak=False,
                stream=False,
                use_soundboard=False,
                use_voice_activation=False
            ),
            interaction.user: discord.PermissionOverwrite(
                connect=True,
                speak=False,
                deafen_members=False
            )
        }

        try:
            vc = await guild.create_voice_channel(
                name=room_title,
                category=cat,
                overwrites=overwrites,
                reason=f"Deep Focus session initiated by {interaction.user.name}"
            )
        except Exception as e:
            return await interaction.response.send_message(f"❌ Failed to create focus room: {e}", ephemeral=True)

        if interaction.user.voice and interaction.user.voice.channel:
            try:
                await interaction.user.move_to(vc, reason="Joined Deep Focus")
            except Exception:
                pass

        embed = discord.Embed(
            title="🔒 ┊ 𝐃𝐄𝐄Ｐ  𝐅𝐎ＣＵＳ  ＳＡＮＣＴＵＡＲＹ  ＣＲＥＡＴＥＤ",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"Welcome to your distraction-free workspace, {interaction.user.mention}!\n\n"
                f"• 🎙️ **Channel:** {vc.mention}\n"
                f"• ⏱️ **Timer:** `{minutes} Minutes`\n"
                f"• 🔇 **Protocol:** Microphones are locked. Pure silent focus.\n\n"
                f"✦ ───────────────────────────── ✦\n"
                f"💡 *This room will automatically close once the session completes or everyone leaves.*"
            ),
            color=0x2ED573
        )
        embed.set_footer(text="RAI FAM 💗 • Deep Work & Flow State", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)

        # Scheduled auto-delete task
        async def cleanup_room():
            await asyncio.sleep(minutes * 60)
            try:
                if vc in guild.voice_channels:
                    await vc.delete(reason="Deep Focus session time expired")
            except Exception:
                pass

        asyncio.create_task(cleanup_room())

    # -------------------------------------------------------------
    # 📊 5. FOCUS STATS & MILESTONE BADGES
    # -------------------------------------------------------------
    @app_commands.command(name="focusstats", description="View your cumulative focus and study hours with milestone badges.")
    @app_commands.describe(member="Member to view focus stats for (defaults to you)")
    async def focusstats_cmd(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        uid = str(target.id)

        # Retrieve voice stats
        total_sec = 0
        if VOICE_STATS_FILE.exists():
            try:
                with open(VOICE_STATS_FILE, "r", encoding="utf-8") as f:
                    vs = json.load(f)
                    total_sec = vs.get(uid, {}).get("total_seconds", 0)
            except Exception:
                pass

        total_hours = total_sec / 3600.0

        # Calculate milestone badges
        badges = []
        if total_hours >= 1.0:
            badges.append("🌱 **Focus Novice** (1+ Hours Logged)")
        if total_hours >= 10.0:
            badges.append("📖 **Dedicated Scholar** (10+ Hours Logged)")
        if total_hours >= 25.0:
            badges.append("⚡ **Deep Work Virtuoso** (25+ Hours Logged)")
        if total_hours >= 50.0:
            badges.append("🏆 **Flow State Champion** (50+ Hours Logged)")
        if total_hours >= 100.0:
            badges.append("👑 **Master of Flow** (100+ Hours Logged)")

        if not badges:
            badges.append("⚪ *No badges unlocked yet. Join study voice channels or start `/pomodoro` to log time!*")

        embed = discord.Embed(
            title=f"📊 ┊ {target.display_name}'𝐬  𝐅𝐎ＣＵＳ  ＳＴＡＴＳ",
            description=(
                f"✦ ───────────────────────────── ✦\n\n"
                f"⏱️ **Total Focus Time:** `{total_hours:.1f} Hours` (`{int(total_sec // 60)} mins`)\n\n"
                f"🎖️ **Milestone Achievements:**\n"
                + "\n".join(badges) +
                f"\n\n✦ ───────────────────────────── ✦\n"
                f"💡 *Use `/pomodoro start` or join our study lounges to level up your focus!*"
            ),
            color=0x70A1FF
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Focus & Productivity Mastery", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Productivity(bot))
