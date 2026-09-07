import os
import aiosqlite
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
import discord

DATA_DIR = Path(__file__).resolve().parent / "data"
DB_PATH = DATA_DIR / "security.db"

def get_db():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    return aiosqlite.connect(DB_PATH)

async def init_db():
    """Create all required SQLite tables on bot boot."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    async with get_db() as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS guild_settings (
                guild_id INTEGER PRIMARY KEY,
                log_channel_id INTEGER,
                quarantine_role_id INTEGER,
                verified_role_id INTEGER,
                unverified_role_id INTEGER,
                raid_mode INTEGER DEFAULT 0,
                lockdown INTEGER DEFAULT 0,
                antinuke_enabled INTEGER DEFAULT 1,
                antiraid_enabled INTEGER DEFAULT 1,
                antispam_enabled INTEGER DEFAULT 1,
                antilink_enabled INTEGER DEFAULT 1,
                antimention_enabled INTEGER DEFAULT 1,
                channel_delete_limit INTEGER DEFAULT 3,
                role_delete_limit INTEGER DEFAULT 3,
                ban_limit INTEGER DEFAULT 4,
                kick_limit INTEGER DEFAULT 4,
                time_window INTEGER DEFAULT 10
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS whitelisted_users (
                guild_id INTEGER,
                user_id INTEGER,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, user_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS whitelisted_roles (
                guild_id INTEGER,
                role_id INTEGER,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, role_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS blocked_domains (
                guild_id INTEGER,
                domain TEXT,
                added_by INTEGER,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (guild_id, domain)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS infractions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                user_id INTEGER,
                action_type TEXT,
                reason TEXT,
                moderator_id INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS security_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                guild_id INTEGER,
                event_type TEXT,
                details TEXT,
                severity TEXT DEFAULT 'HIGH',
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS channel_snapshots (
                guild_id INTEGER,
                channel_id INTEGER,
                name TEXT,
                channel_type TEXT,
                category_id INTEGER,
                position INTEGER,
                topic TEXT,
                PRIMARY KEY (guild_id, channel_id)
            )
        """)

        await db.execute("""
            CREATE TABLE IF NOT EXISTS role_snapshots (
                guild_id INTEGER,
                role_id INTEGER,
                name TEXT,
                color INTEGER,
                permissions INTEGER,
                hoist INTEGER,
                position INTEGER,
                PRIMARY KEY (guild_id, role_id)
            )
        """)

        await db.commit()

async def save_channel_snapshot(guild_id: int, channel: discord.abc.GuildChannel):
    async with get_db() as db:
        c_type = "voice" if isinstance(channel, discord.VoiceChannel) else ("category" if isinstance(channel, discord.CategoryChannel) else "text")
        topic = getattr(channel, "topic", "") or ""
        cat_id = channel.category_id if hasattr(channel, "category_id") else None
        pos = channel.position if hasattr(channel, "position") else 0
        await db.execute("""
            INSERT OR REPLACE INTO channel_snapshots (guild_id, channel_id, name, channel_type, category_id, position, topic)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (guild_id, channel.id, channel.name, c_type, cat_id, pos, topic))
        await db.commit()

async def get_channel_snapshot(guild_id: int, channel_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM channel_snapshots WHERE guild_id = ? AND channel_id = ?", (guild_id, channel_id))
        row = await cur.fetchone()
        return dict(row) if row else None

async def save_role_snapshot(guild_id: int, role: discord.Role):
    async with get_db() as db:
        await db.execute("""
            INSERT OR REPLACE INTO role_snapshots (guild_id, role_id, name, color, permissions, hoist, position)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (guild_id, role.id, role.name, role.color.value, role.permissions.value, 1 if role.hoist else 0, role.position))
        await db.commit()

async def get_role_snapshot(guild_id: int, role_id: int) -> Optional[Dict[str, Any]]:
    async with get_db() as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute("SELECT * FROM role_snapshots WHERE guild_id = ? AND role_id = ?", (guild_id, role_id))
        row = await cur.fetchone()
        return dict(row) if row else None

async def get_guild_settings(guild_id: int) -> Dict[str, Any]:
    async with get_db() as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
        row = await cursor.fetchone()
        if not row:
            await db.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (guild_id,))
            await db.commit()
            cursor = await db.execute("SELECT * FROM guild_settings WHERE guild_id = ?", (guild_id,))
            row = await cursor.fetchone()
        return dict(row) if row else {}

async def update_guild_setting(guild_id: int, key: str, value: Any):
    allowed_keys = {
        "log_channel_id", "quarantine_role_id", "verified_role_id", "unverified_role_id",
        "raid_mode", "lockdown", "antinuke_enabled", "antiraid_enabled", "antispam_enabled",
        "antilink_enabled", "antimention_enabled", "channel_delete_limit", "role_delete_limit",
        "ban_limit", "kick_limit", "time_window"
    }
    if key not in allowed_keys:
        raise ValueError(f"Setting key '{key}' is not permitted.")

    async with get_db() as db:
        await db.execute("INSERT OR IGNORE INTO guild_settings (guild_id) VALUES (?)", (guild_id,))
        await db.execute(f"UPDATE guild_settings SET {key} = ? WHERE guild_id = ?", (value, guild_id))
        await db.commit()

async def is_whitelisted(guild: discord.Guild, member_or_user: Union[discord.Member, discord.User, int]) -> bool:
    """Check if member/user is Server Owner or explicitly whitelisted."""
    user_id = member_or_user.id if hasattr(member_or_user, "id") else member_or_user
    if user_id == guild.owner_id:
        return True

    if guild.me and user_id == guild.me.id:
        return True

    async with get_db() as db:
        # 1. User check
        cursor = await db.execute(
            "SELECT 1 FROM whitelisted_users WHERE guild_id = ? AND user_id = ?",
            (guild.id, user_id)
        )
        if await cursor.fetchone():
            return True

        # 2. Role check (if member object with roles)
        if isinstance(member_or_user, discord.Member):
            role_ids = [r.id for r in member_or_user.roles]
            if role_ids:
                placeholders = ",".join("?" for _ in role_ids)
                cursor = await db.execute(
                    f"SELECT 1 FROM whitelisted_roles WHERE guild_id = ? AND role_id IN ({placeholders})",
                    (guild.id, *role_ids)
                )
                if await cursor.fetchone():
                    return True

    return False

async def add_whitelisted_user(guild_id: int, user_id: int, added_by: int) -> bool:
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO whitelisted_users (guild_id, user_id, added_by) VALUES (?, ?, ?)",
            (guild_id, user_id, added_by)
        )
        await db.commit()
    return True

async def remove_whitelisted_user(guild_id: int, user_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM whitelisted_users WHERE guild_id = ? AND user_id = ?",
            (guild_id, user_id)
        )
        await db.commit()
        return cursor.rowcount > 0

async def add_whitelisted_role(guild_id: int, role_id: int, added_by: int) -> bool:
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO whitelisted_roles (guild_id, role_id, added_by) VALUES (?, ?, ?)",
            (guild_id, role_id, added_by)
        )
        await db.commit()
    return True

async def remove_whitelisted_role(guild_id: int, role_id: int) -> bool:
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM whitelisted_roles WHERE guild_id = ? AND role_id = ?",
            (guild_id, role_id)
        )
        await db.commit()
        return cursor.rowcount > 0

async def get_whitelist(guild_id: int) -> Dict[str, List[int]]:
    async with get_db() as db:
        user_cur = await db.execute("SELECT user_id FROM whitelisted_users WHERE guild_id = ?", (guild_id,))
        role_cur = await db.execute("SELECT role_id FROM whitelisted_roles WHERE guild_id = ?", (guild_id,))
        users = [row[0] for row in await user_cur.fetchall()]
        roles = [row[0] for row in await role_cur.fetchall()]
        return {"users": users, "roles": roles}

async def add_blocked_domain(guild_id: int, domain: str, added_by: int) -> bool:
    domain_clean = domain.strip().lower()
    async with get_db() as db:
        await db.execute(
            "INSERT OR REPLACE INTO blocked_domains (guild_id, domain, added_by) VALUES (?, ?, ?)",
            (guild_id, domain_clean, added_by)
        )
        await db.commit()
    return True

async def remove_blocked_domain(guild_id: int, domain: str) -> bool:
    domain_clean = domain.strip().lower()
    async with get_db() as db:
        cursor = await db.execute(
            "DELETE FROM blocked_domains WHERE guild_id = ? AND domain = ?",
            (guild_id, domain_clean)
        )
        await db.commit()
        return cursor.rowcount > 0

async def get_blocked_domains(guild_id: int) -> List[str]:
    async with get_db() as db:
        cur = await db.execute("SELECT domain FROM blocked_domains WHERE guild_id = ?", (guild_id,))
        return [row[0] for row in await cur.fetchall()]

async def record_infraction(guild_id: int, user_id: int, action_type: str, reason: str, moderator_id: int):
    async with get_db() as db:
        await db.execute(
            "INSERT INTO infractions (guild_id, user_id, action_type, reason, moderator_id) VALUES (?, ?, ?, ?, ?)",
            (guild_id, user_id, action_type, reason, moderator_id)
        )
        await db.commit()

async def record_security_event(guild_id: int, event_type: str, details: str, severity: str = "HIGH"):
    async with get_db() as db:
        await db.execute(
            "INSERT INTO security_events (guild_id, event_type, details, severity) VALUES (?, ?, ?, ?)",
            (guild_id, event_type, details, severity)
        )
        await db.commit()
