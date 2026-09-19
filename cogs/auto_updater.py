import os
import sys
import time
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import Optional, Tuple, List

import discord
from discord.ext import commands, tasks
from discord import app_commands

import config

logger = logging.getLogger("AutoUpdater")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

class AutoUpdater(commands.Cog):
    """Autonomous Bot Self-Updating Engine (Continuous GitHub Sync, yt-dlp Upgrades & Zero-Downtime Hot-Reload)."""

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = time.time()
        self.last_update_check = 0.0
        self.last_ytdlp_check = 0.0
        self.is_updating = False

    async def cog_load(self):
        if not self.auto_git_sync_task.is_running():
            self.auto_git_sync_task.start()
        if not self.auto_ytdlp_upgrade_task.is_running():
            self.auto_ytdlp_upgrade_task.start()

    def cog_unload(self):
        if self.auto_git_sync_task.is_running():
            self.auto_git_sync_task.cancel()
        if self.auto_ytdlp_upgrade_task.is_running():
            self.auto_ytdlp_upgrade_task.cancel()

    # =========================================================================
    # PROCESS EXECUTION HELPER (Safe against shell escaping)
    # =========================================================================
    async def run_cmd(self, *args: str, timeout: int = 60) -> Tuple[int, str, str]:
        """Execute a command directly without shell interpretation to prevent quoting issues."""
        try:
            process = await asyncio.create_subprocess_exec(
                *args,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(PROJECT_ROOT)
            )
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=timeout)
            out_str = stdout.decode("utf-8", errors="replace").strip()
            err_str = stderr.decode("utf-8", errors="replace").strip()
            return process.returncode or 0, out_str, err_str
        except asyncio.TimeoutError:
            return -1, "", "Command timed out."
        except Exception as e:
            return -1, "", str(e)

    # =========================================================================
    # GIT STATUS & PULL OPERATIONS
    # =========================================================================
    async def get_current_commit(self) -> Tuple[str, str]:
        """Get the current commit hash and subject line."""
        code, out, _ = await self.run_cmd("git", "log", "-1", "--format=%h - %s (%cr)")
        if code == 0 and out:
            parts = out.split(" - ", 1)
            return parts[0].strip(), out.strip()
        return "unknown", "Unknown Commit"

    async def check_for_git_updates(self) -> Tuple[bool, str, str, str]:
        """Fetch origin/main and check if new commits exist.
        Returns: (has_updates, local_hash, remote_hash, changelog)
        """
        self.last_update_check = time.time()
        # 1. Fetch remote tracking branch
        code, _, err = await self.run_cmd("git", "fetch", "origin", "main")
        if code != 0:
            logger.warning(f"[AutoUpdater] git fetch failed: {err}")
            return False, "", "", f"Git fetch error: {err}"

        # 2. Get local and remote HEAD hashes
        _, local_hash, _ = await self.run_cmd("git", "rev-parse", "HEAD")
        _, remote_hash, _ = await self.run_cmd("git", "rev-parse", "origin/main")

        if not local_hash or not remote_hash:
            return False, "", "", "Could not resolve commit hashes."

        if local_hash.strip() == remote_hash.strip():
            return False, local_hash.strip()[:7], remote_hash.strip()[:7], "Up to date."

        # 3. Retrieve changelog of new commits
        _, log_out, _ = await self.run_cmd("git", "log", f"{local_hash.strip()}..{remote_hash.strip()}", "--oneline", "-n", "10")
        return True, local_hash.strip()[:7], remote_hash.strip()[:7], log_out or "New commits available."

    async def apply_git_updates(self) -> Tuple[bool, str, List[str]]:
        """Pull commits, check changed files, update dependencies, and hot-reload.
        Returns: (success, summary_message, changed_files)
        """
        if self.is_updating:
            return False, "An update is already in progress.", []

        self.is_updating = True
        try:
            _, old_hash, _ = await self.run_cmd("git", "rev-parse", "HEAD")

            # 1. Pull origin main
            code, pull_out, pull_err = await self.run_cmd("git", "pull", "origin", "main")
            if code != 0:
                logger.error(f"[AutoUpdater] git pull failed: {pull_err}")
                return False, f"Git pull failed: {pull_err or pull_out}", []

            _, new_hash, _ = await self.run_cmd("git", "rev-parse", "HEAD")

            # 2. Inspect changed files
            code, diff_out, _ = await self.run_cmd("git", "diff", "--name-only", old_hash.strip(), new_hash.strip())
            changed_files = [f.strip() for f in diff_out.splitlines() if f.strip()]

            # 3. If requirements.txt changed, update pip dependencies
            if "requirements.txt" in changed_files:
                logger.info("[AutoUpdater] requirements.txt changed. Installing updated dependencies...")
                await self.run_cmd(sys.executable, "-m", "pip", "install", "-r", "requirements.txt")

            # 4. Determine if reload or restart is needed
            core_files = ["main.py", "run_24_7.py", "security_bot.py", "config.py", "database.py"]
            core_changed = any(f in changed_files for f in core_files)

            reloaded_cogs = []
            reload_errors = []

            # Hot-reload modified cogs
            for f in changed_files:
                if f.startswith("cogs/") and f.endswith(".py"):
                    cog_name = f.replace("/", ".").replace(".py", "")
                    try:
                        if cog_name in self.bot.extensions:
                            await self.bot.reload_extension(cog_name)
                            reloaded_cogs.append(cog_name)
                            logger.info(f"[AutoUpdater] Successfully hot-reloaded: {cog_name}")
                    except Exception as e:
                        reload_errors.append(f"{cog_name}: {e}")
                        logger.error(f"[AutoUpdater] Error reloading {cog_name}: {e}")

            # Resync command tree if any cogs were hot-reloaded
            if reloaded_cogs:
                try:
                    for guild in self.bot.guilds:
                        try:
                            self.bot.tree.clear_commands(guild=guild)
                            await self.bot.tree.sync(guild=guild)
                        except Exception:
                            pass
                    await self.bot.tree.sync()
                    logger.info("[AutoUpdater] Resynchronized slash commands across guilds and globally.")
                except Exception as se:
                    logger.error(f"[AutoUpdater] Error resyncing tree after reload: {se}")

            summary = f"Pulled `{old_hash.strip()[:7]}` ➔ `{new_hash.strip()[:7]}`.\n"
            if reloaded_cogs:
                summary += f"🔄 **Hot-Reloaded Extensions:** {', '.join(reloaded_cogs)}\n"
            if reload_errors:
                summary += f"⚠️ **Reload Errors:** {'; '.join(reload_errors)}\n"
            if core_changed:
                summary += "⚡ **Core File Changed:** Full process restart recommended or scheduled.\n"

            return True, summary, changed_files
        finally:
            self.is_updating = False

    async def upgrade_ytdlp(self) -> Tuple[bool, str]:
        """Upgrade yt-dlp to the latest release to keep YouTube extraction working."""
        import yt_dlp
        old_ver = getattr(yt_dlp, "version", None)
        old_ver_str = old_ver.__version__ if old_ver else "unknown"

        code, out, err = await self.run_cmd(sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp")
        self.last_ytdlp_check = time.time()
        if code == 0:
            # Re-read version
            code2, new_ver_str, _ = await self.run_cmd(sys.executable, "-c", "import yt_dlp; print(yt_dlp.version.__version__)")
            new_ver = new_ver_str.strip() or "updated"
            if old_ver_str != new_ver:
                msg = f"yt-dlp upgraded from `{old_ver_str}` to `{new_ver}`."
                logger.info(f"[AutoUpdater] {msg}")
                return True, msg
            else:
                return True, f"yt-dlp is already at the latest release (`{old_ver_str}`)."
        else:
            return False, f"yt-dlp upgrade error: {err or out}"

    # =========================================================================
    # NOTIFICATION DISPATCHER
    # =========================================================================
    async def send_staff_notification(self, embed: discord.Embed):
        """Send automated update reports to staff operations / mod-logs channels."""
        for guild in self.bot.guilds:
            staff_chan = (
                discord.utils.get(guild.text_channels, name="｜・𝗌𝗍𝖺𝖿𝖿-𝗈𝗉𝖾𝗋𝖺𝗍𝗂𝗈𝗇𝗌") or
                discord.utils.get(guild.text_channels, name="🛡️｜ꜱᴛᴀꜰꜰ-ᴏᴘᴇʀᴀᴛɪᴏɴꜱ") or
                discord.utils.get(guild.text_channels, name="staff-operations") or
                discord.utils.get(guild.text_channels, name="🚨｜ꜱᴇɴᴛɪɴᴇʟ-ʟᴏɢꜱ") or
                discord.utils.get(guild.text_channels, name="bot-commands")
            )
            if staff_chan:
                try:
                    await staff_chan.send(embed=embed)
                except Exception:
                    pass

    # =========================================================================
    # PERIODIC BACKGROUND TASKS
    # =========================================================================
    @tasks.loop(minutes=15)
    async def auto_git_sync_task(self):
        """Periodically checks GitHub for updates, pulls changes, and hot-reloads cogs."""
        try:
            has_updates, old_h, new_h, changelog = await self.check_for_git_updates()
            if has_updates:
                logger.info(f"[AutoUpdater] New commits detected on GitHub ({old_h} -> {new_h}). Auto-applying update...")
                success, summary, files = await self.apply_git_updates()

                embed = discord.Embed(
                    title="🚀 Autonomous Update Deployed",
                    description=(
                        f"**GitHub Commits Pulled:** `{old_h}` ➔ `{new_h}`\n\n"
                        f"**Changelog:**\n```\n{changelog[:800]}\n```\n"
                        f"{summary}"
                    ),
                    color=config.COLOR_SUCCESS if success else config.COLOR_DANGER
                )
                embed.set_footer(text="RAI Auto-Updater Engine • 24/7 Continuous Deployment", icon_url=config.RAI_ICON_URL)
                await self.send_staff_notification(embed)
        except Exception as e:
            logger.error(f"[AutoUpdater] Error in auto_git_sync_task: {e}")

    @auto_git_sync_task.before_loop
    async def before_git_sync(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(60)  # Wait 1 minute after boot before starting checks

    @tasks.loop(hours=24)
    async def auto_ytdlp_upgrade_task(self):
        """Periodically ensures yt-dlp is updated to avoid YouTube cipher & player breakages."""
        try:
            success, msg = await self.upgrade_ytdlp()
            logger.info(f"[AutoUpdater] Daily yt-dlp maintenance: {msg}")
        except Exception as e:
            logger.warning(f"[AutoUpdater] yt-dlp daily check notice: {e}")

    @auto_ytdlp_upgrade_task.before_loop
    async def before_ytdlp_upgrade(self):
        await self.bot.wait_until_ready()
        await asyncio.sleep(180)

    # =========================================================================
    # SLASH COMMANDS: /botupdate
    # =========================================================================
    update_group = app_commands.Group(name="botupdate", description="Autonomous self-updating engine controls.")

    @update_group.command(name="check", description="Check GitHub for pending bot updates without applying them.")
    async def update_check_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        has_updates, local_h, remote_h, changelog = await self.check_for_git_updates()

        if has_updates:
            embed = discord.Embed(
                title="📥 New Updates Available on GitHub!",
                description=(
                    f"**Current Local Commit:** `{local_h}`\n"
                    f"**Latest Remote Commit:** `{remote_h}`\n\n"
                    f"**Pending Changes:**\n```\n{changelog[:900]}\n```\n"
                    f"Use `/botupdate apply` to pull and hot-reload these changes immediately!"
                ),
                color=config.COLOR_PRIMARY
            )
        else:
            embed = discord.Embed(
                title="✅ Bot is 100% Up to Date",
                description=f"Running commit **`{local_h}`** on branch `main`.\nNo new commits found on GitHub.",
                color=config.COLOR_SUCCESS
            )
        embed.set_footer(text="RAI Auto-Updater • Continuous Sync", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @update_group.command(name="apply", description="Pull latest commits from GitHub and hot-reload cogs with 0 downtime.")
    @app_commands.checks.has_permissions(administrator=True)
    async def update_apply_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        has_updates, old_h, new_h, changelog = await self.check_for_git_updates()

        if not has_updates:
            return await interaction.followup.send("✅ **Bot is already on the latest commit!** No updates to apply.", ephemeral=True)

        status_msg = await interaction.followup.send("⏳ **Pulling latest commits and hot-reloading extensions...**", ephemeral=True)
        success, summary, files = await self.apply_git_updates()

        embed = discord.Embed(
            title="🚀 Update Applied Successfully!" if success else "❌ Update Failed",
            description=(
                f"**Commits:** `{old_h}` ➔ `{new_h}`\n\n"
                f"**Changes Applied:**\n```\n{changelog[:600]}\n```\n"
                f"{summary}"
            ),
            color=config.COLOR_SUCCESS if success else config.COLOR_DANGER
        )
        embed.set_footer(text="RAI Auto-Updater Engine", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)

    @update_group.command(name="status", description="Display current bot version, uptime, commit hash and update telemetry.")
    async def update_status_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        commit_h, commit_title = await self.get_current_commit()

        import yt_dlp
        ytdlp_ver = getattr(yt_dlp, "version", None)
        ytdlp_ver_str = ytdlp_ver.__version__ if ytdlp_ver else "unknown"

        uptime_sec = int(time.time() - self.start_time)
        hours, remainder = divmod(uptime_sec, 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime_str = f"{hours}h {minutes}m {seconds}s"

        last_check_str = f"<t:{int(self.last_update_check)}:R>" if self.last_update_check else "Never"

        embed = discord.Embed(
            title="🤖 Bot System & Auto-Updater Status",
            color=config.COLOR_PRIMARY
        )
        embed.add_field(name="📌 Current Commit", value=f"`{commit_h}`\n*{commit_title[:60]}*", inline=False)
        embed.add_field(name="⏱️ Continuous Uptime", value=f"`{uptime_str}`", inline=True)
        embed.add_field(name="📻 yt-dlp Engine", value=f"`v{ytdlp_ver_str}`", inline=True)
        embed.add_field(name="🔄 Last GitHub Check", value=last_check_str, inline=True)
        embed.add_field(name="🌿 Git Upstream", value="`origin/main`", inline=True)
        embed.add_field(name="⚡ Auto-Sync Interval", value="`Every 15 Minutes`", inline=True)
        embed.add_field(name="🛠️ Daily Maintenance", value="`Every 24 Hours`", inline=True)
        embed.set_footer(text="RAI Auto-Updater Engine • Continuous Integration", icon_url=config.RAI_ICON_URL)

        await interaction.followup.send(embed=embed, ephemeral=True)

    @update_group.command(name="ytdlp", description="Check and force update yt-dlp to the latest audio release.")
    @app_commands.checks.has_permissions(administrator=True)
    async def update_ytdlp_cmd(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True)
        success, msg = await self.upgrade_ytdlp()
        embed = discord.Embed(
            title="📻 yt-dlp Audio Engine Update",
            description=msg,
            color=config.COLOR_SUCCESS if success else config.COLOR_DANGER
        )
        embed.set_footer(text="RAI Auto-Updater Engine", icon_url=config.RAI_ICON_URL)
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(AutoUpdater(bot))
