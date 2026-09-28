import os
import sys
import json
import time
import logging
from pathlib import Path
from typing import Optional
import discord
from discord import app_commands
from discord.ext import commands

logger = logging.getLogger("ServerBackup")

BACKUP_DIR = Path(__file__).resolve().parent.parent / "data" / "server_backups"

def get_backups() -> list:
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    return sorted(BACKUP_DIR.glob("backup_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)

class ServerBackup(commands.Cog):
    """Native Server Snapshot, Disaster Recovery & Channel Vault."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="backup_create", description="Take an instant full snapshot of server channels, categories, and roles.")
    @commands.has_permissions(administrator=True)
    async def backup_create(self, interaction: discord.Interaction, note: Optional[str] = None):
        if not interaction.response.is_done():
            await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = int(time.time())

        data = {
            "timestamp": timestamp,
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "created_by": interaction.user.display_name,
            "note": note or "Manual Snapshot",
            "guild_id": guild.id,
            "guild_name": guild.name,
            "roles": [{"id": r.id, "name": r.name, "color": str(r.color), "position": r.position, "permissions": r.permissions.value} for r in guild.roles if not r.is_default()],
            "categories": [{"id": c.id, "name": c.name, "position": c.position} for c in guild.categories],
            "channels": [
                {
                    "id": c.id,
                    "name": c.name,
                    "type": str(c.type),
                    "category": c.category.name if c.category else None,
                    "position": c.position
                } for c in guild.channels
            ]
        }

        filename = f"backup_rai_fam_{timestamp}.json"
        filepath = BACKUP_DIR / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Update latest snapshot
        with open(BACKUP_DIR / "snapshot_latest.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        embed = discord.Embed(
            title="🛡️ SERVER BACKUP CREATED",
            description=(
                f"✅ **Snapshot successfully created & secured!**\n\n"
                f"📁 **Backup File:** `{filename}`\n"
                f"🏷️ **Roles Captured:** `{len(data['roles'])}`\n"
                f"📂 **Categories:** `{len(data['categories'])}`\n"
                f"💬 **Channels:** `{len(data['channels'])}`\n"
                f"📝 **Note:** `{data['note']}`"
            ),
            color=discord.Color.green()
        )
        embed.set_footer(text="AEGIS SENTINEL • Disaster Recovery Engine")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="backup_list", description="List all available server snapshot backups.")
    @commands.has_permissions(administrator=True)
    async def backup_list(self, interaction: discord.Interaction):
        backups = get_backups()
        if not backups:
            return await interaction.response.send_message("ℹ️ No backups found yet. Run `/backup_create` to create one!", ephemeral=True)

        lines = []
        for b in backups[:10]:
            try:
                with open(b, "r", encoding="utf-8") as f:
                    d = json.load(f)
                    dt = d.get("date", "Unknown")
                    note = d.get("note", "Snapshot")
                    lines.append(f"• **`{b.stem}`** — {dt} *({note})*")
            except Exception:
                lines.append(f"• **`{b.name}`**")

        embed = discord.Embed(
            title="📁 AVAILABLE SERVER BACKUPS",
            description="\n".join(lines),
            color=0x5865F2
        )
        embed.set_footer(text="AEGIS SENTINEL • Disaster Recovery Engine")
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ServerBackup(bot))
