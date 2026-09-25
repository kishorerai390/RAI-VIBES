import io
import json
from pathlib import Path
import time
import datetime
import random
import logging
from typing import Optional, Dict
import discord
from discord import app_commands
from discord.ext import commands, tasks

import database
import config
from utils.canvas import generate_rank_card, generate_profile_codex

logger = logging.getLogger("Leveling")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ECONOMY_FILE = DATA_DIR / "economy.json"

def award_vc_coins(member_id: int, amount: int = 5):
    """Award economy coins to active voice participants."""
    try:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        eco_data = {}
        if ECONOMY_FILE.exists():
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                eco_data = json.load(f)
        uid = str(member_id)
        if uid not in eco_data:
            eco_data[uid] = {"coins": 200, "last_daily": 0, "wins": 0, "losses": 0}
        eco_data[uid]["coins"] = eco_data[uid].get("coins", 0) + amount
        with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
            json.dump(eco_data, f, indent=2)
    except Exception as e:
        logger.debug(f"Could not award VC coins: {e}")

def get_user_coins(member_id: int) -> int:
    """Retrieve user coin balance."""
    if ECONOMY_FILE.exists():
        try:
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                eco = json.load(f)
                return eco.get(str(member_id), {}).get("coins", 0)
        except Exception:
            pass
    return 0

def get_user_rep(member_id: int) -> int:
    """Retrieve user reputation points."""
    if ECONOMY_FILE.exists():
        try:
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                eco = json.load(f)
                return eco.get(str(member_id), {}).get("rep", 0)
        except Exception:
            pass
    return 0

def sanitize_for_canvas(text: str, max_len: int = 16) -> str:
    import unicodedata
    norm = unicodedata.normalize('NFKD', text)
    clean = "".join([c for c in norm if ord(c) < 128 or c.isalnum() or c in " -_!."]).strip()
    if not clean:
        clean = "RAI Member"
    return clean[:max_len] if len(clean) <= max_len else f"{clean[:max_len-2]}.."

def create_grand_levelup_image(avatar_bytes: bytes, username: str, old_level: int, new_level: int, coin_bonus: int) -> io.BytesIO:
    """Generates a luxury 900x350 Cyber-Pink & Emerald level-up card with user avatar."""
    from PIL import Image, ImageDraw, ImageFont, ImageOps
    WIDTH, HEIGHT = 900, 350
    
    # 1. Base Image with Deep Gradient Dark Background
    img = Image.new("RGBA", (WIDTH, HEIGHT), color=(11, 9, 18, 255))
    draw = ImageDraw.Draw(img)

    # 2. Ambient Cyber-Pink & Emerald Radiant Glow
    for r in range(160, 0, -12):
        alpha = int(28 * (1 - r / 160))
        draw.ellipse([60 - r, 60 - r, 60 + r, 60 + r], fill=(0, 255, 136, alpha))
        draw.ellipse([WIDTH - 60 - r, HEIGHT - 60 - r, WIDTH - 60 + r, HEIGHT - 60 + r], fill=(255, 105, 180, alpha))
        draw.ellipse([WIDTH // 2 - r, 20 - r, WIDTH // 2 + r, 20 + r], fill=(255, 215, 0, int(alpha * 0.6)))

    # Outer Cyber Frame (Gold + Pink Accents)
    draw.rounded_rectangle([12, 12, WIDTH - 12, HEIGHT - 12], radius=28, outline=(0, 255, 136, 200), width=3)
    draw.rounded_rectangle([18, 18, WIDTH - 18, HEIGHT - 18], radius=24, outline=(255, 215, 0, 140), width=2)
    draw.rounded_rectangle([22, 22, WIDTH - 22, HEIGHT - 22], radius=20, outline=(28, 22, 42, 255), width=2)

    # Top Crown Ribbon Accent
    draw.rectangle([140, 12, WIDTH - 140, 18], fill=(0, 255, 136, 240))
    draw.rectangle([200, 18, WIDTH - 200, 22], fill=(255, 215, 0, 255))

    # Corner Decorative Sparkles
    bracket_color = (255, 215, 0, 220)
    draw.line([(30, 45), (45, 30)], fill=bracket_color, width=3)
    draw.line([(WIDTH - 45, 30), (WIDTH - 30, 45)], fill=bracket_color, width=3)
    draw.line([(30, HEIGHT - 45), (45, HEIGHT - 30)], fill=bracket_color, width=3)
    draw.line([(WIDTH - 45, HEIGHT - 30), (WIDTH - 30, HEIGHT - 45)], fill=bracket_color, width=3)

    # 3. Avatar Processing (Circular Crop with Concentric Glowing Rings)
    try:
        raw_avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        raw_avatar = raw_avatar.resize((180, 180), Image.Resampling.LANCZOS)
        
        mask = Image.new("L", (180, 180), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 180, 180), fill=255)
        
        avatar_circle = ImageOps.fit(raw_avatar, mask.size, centering=(0.5, 0.5))
        avatar_circle.putalpha(mask)

        # Concentric Outer Glow Rings (Emerald -> Gold -> Pink)
        draw.ellipse([58, 80, 252, 274], outline=(0, 255, 136, 220), width=6)
        draw.ellipse([62, 84, 248, 270], outline=(255, 215, 0, 200), width=4)
        draw.ellipse([65, 87, 245, 267], outline=(255, 105, 180, 255), width=3)
        img.paste(avatar_circle, (65, 87), avatar_circle)
    except Exception as e:
        logger.warning(f"Could not render avatar image: {e}")
        draw.ellipse([65, 87, 245, 267], fill=(0, 255, 136, 255))

    # 4. Text Content Rendering
    try:
        font_sub = ImageFont.truetype("arialbd.ttf", 22)
        font_name = ImageFont.truetype("arialbd.ttf", 38)
        font_lvl = ImageFont.truetype("arialbd.ttf", 26)
        font_tags = ImageFont.truetype("arialbd.ttf", 16)
    except Exception:
        font_sub = ImageFont.load_default()
        font_name = font_sub
        font_lvl = font_sub
        font_tags = font_sub

    # Header: "⭐ LEVEL UP ADVANCEMENT ⭐"
    draw.text((280, 72), "⭐ LEVEL UP ADVANCEMENT ⭐", fill=(0, 255, 136, 255), font=font_sub)
    
    # Username with Glow/Shadow Effect
    clean_name = sanitize_for_canvas(username, max_len=18)
    draw.text((282, 110), clean_name, fill=(20, 10, 30, 255), font=font_name)
    draw.text((280, 108), clean_name, fill=(255, 255, 255, 255), font=font_name)
    
    # Level Progress Badge with Emerald Border
    badge_bg = [280, 172, 600, 222]
    draw.rounded_rectangle(badge_bg, radius=14, fill=(24, 38, 28, 255), outline=(0, 255, 136, 240), width=2)
    draw.text((298, 182), f"🚀 LEVEL {old_level} ➔ LEVEL {new_level}", fill=(0, 255, 136, 255), font=font_lvl)

    # Feature Highlights Badges
    pills = [
        (f"💰 +{coin_bonus} COINS BONUS", (255, 215, 0)),
        ("⚡ XP BOOSTED", (0, 240, 255)),
        ("🌸 RAI FAMILY", (255, 105, 180))
    ]
    px = 280
    for pill, color in pills:
        pill_len = len(pill) * 9 + 20
        draw.rounded_rectangle([px, 246, px + pill_len, 282], radius=10, fill=(25, 35, 30, 230), outline=(color[0], color[1], color[2], 180), width=1)
        draw.text((px + 10, 254), pill, fill=color, font=font_tags)
        px += pill_len + 12

    # 5. Export to BytesIO
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output

def render_progress_bar(current: int, total: int, length: int = 10) -> str:
    if total <= 0:
        return "▱" * length
    fraction = max(0.0, min(1.0, current / total))
    filled = int(fraction * length)
    empty = length - filled
    return "▰" * filled + "▱" * empty

class Leveling(commands.Cog):
    """Leveling & XP Engine rewarding chat activity and voice participation."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # user_id: last_message_timestamp
        self.message_cooldowns: Dict[int, float] = {}
        self.voice_xp_task.start()

    def cog_unload(self):
        self.voice_xp_task.cancel()

    # -------------------------------------------------------------
    # MESSAGE XP LISTENER
    # -------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return

        now = time.time()
        last_time = self.message_cooldowns.get(message.author.id, 0)
        # 60 second cooldown between XP rewards to prevent spamming
        if now - last_time < 60:
            return

        self.message_cooldowns[message.author.id] = now
        xp_gain = random.randint(15, 25)

        # Weekend 2x XP Multiplier (Saturday & Sunday UTC)
        if datetime.datetime.now(datetime.timezone.utc).weekday() in (5, 6):
            xp_gain *= 2

        new_xp, new_lvl, leveled_up = await database.add_user_xp(message.guild.id, message.author.id, xp_gain)

        if leveled_up:
            await self.handle_level_up(message.guild, message.author, new_lvl, message.channel)

    async def handle_level_up(self, guild: discord.Guild, member: discord.Member, new_level: int, channel: discord.abc.Messageable):
        """Sends luxury level-up celebration canvas and awards coin bonus with milestone perks."""
        coin_bonus = new_level * 50

        # Milestone Perks Definition (Everglow Activity Tiers)
        MILESTONES = {
            5: {
                "title": "✨ Starlight Initiate",
                "bonus": 500,
                "perk": "Unlocked external emojis & stickers across the server!",
                "role_id": 1552378037276901547
            },
            15: {
                "title": "🌸 Aurora Voyager",
                "bonus": 1500,
                "perk": "Unlocked custom server nicknames!",
                "role_id": 1552378030855290931
            },
            30: {
                "title": "💫 Nebula Elite",
                "bonus": 5000,
                "perk": "Unlocked embed links & priority perks!",
                "role_id": 1552378026367647887
            },
            50: {
                "title": "👑 Celestial Sovereign",
                "bonus": 15000,
                "perk": "VIP Celestial badge, exclusive colored name glow & legend status!",
                "role_id": 1552378020352884756
            }
        }

        milestone_data = MILESTONES.get(new_level)
        milestone_text = ""
        if milestone_data:
            extra = milestone_data["bonus"]
            coin_bonus += extra
            milestone_text = f"\n\n🏆 **EVERGLOW TIER REACHED: {milestone_data['title']}**\n🎁 **Tier Perk:** {milestone_data['perk']}"
            if "role_id" in milestone_data:
                role = guild.get_role(milestone_data["role_id"])
                if role and role not in member.roles:
                    try:
                        await member.add_roles(role, reason=f"Level {new_level} Everglow Activity Tier Unlock")
                        milestone_text += f"\n✨ **Role Awarded:** {role.mention}"
                    except Exception as re:
                        logger.warning(f"Could not assign milestone role: {re}")

        award_vc_coins(member.id, coin_bonus)

        # Target announcement channel: #⭐・starboard (1551184190073213071) or local channel
        target_channel = guild.get_channel(1551184190073213071) or channel

        card_file = None
        try:
            avatar_bytes = await member.display_avatar.read()
            img_io = create_grand_levelup_image(
                avatar_bytes=avatar_bytes,
                username=member.display_name,
                old_level=max(1, new_level - 1),
                new_level=new_level,
                coin_bonus=coin_bonus
            )
            card_file = discord.File(fp=img_io, filename="levelup_advancement.png")
        except Exception as e:
            logger.warning(f"Could not generate levelup canvas card: {e}")

        embed = discord.Embed(
            title="⭐ ✦ LEVEL UP ADVANCEMENT ✦ ⭐",
            description=(
                f"Congratulations {member.mention}! You ascended to **Level {new_level}**!{milestone_text}\n\n"
                f"🪙 **Bonus Coins Awarded:** `+{coin_bonus:,} Coins`\n"
                f"✨ Keep chatting and participating in voice lounges to climb the leaderboards!"
            ),
            color=0xFFD700 if milestone_data else 0x00FF88
        )
        if card_file:
            embed.set_image(url="attachment://levelup_advancement.png")
        embed.set_footer(text="RAI VIBES Leveling Suite • Earn coins & prestige", icon_url=config.RAI_ICON_URL)

        try:
            if card_file:
                await target_channel.send(content=f"🎉 {member.mention}", embed=embed, file=card_file)
            else:
                await target_channel.send(content=f"🎉 {member.mention}", embed=embed)
        except Exception as e:
            logger.debug(f"Failed to post level up in {target_channel}: {e}")

    # -------------------------------------------------------------
    # VOICE XP LOOP (Runs every 2 minutes)
    # -------------------------------------------------------------
    @tasks.loop(minutes=2)
    async def voice_xp_task(self):
        await self.bot.wait_until_ready()
        for guild in self.bot.guilds:
            for vc in guild.voice_channels:
                # Skip AFK channel or empty channels
                if "afk" in vc.name.lower() or len(vc.members) < 1:
                    continue
                for member in vc.members:
                    if member.bot or member.voice.self_deaf or member.voice.deaf:
                        continue
                    # Award 15 XP (30 on weekends) + 5 Coins (10 on weekends) for active voice participation
                    is_weekend = datetime.datetime.now(datetime.timezone.utc).weekday() in (5, 6)
                    v_xp = 30 if is_weekend else 15
                    v_coins = 10 if is_weekend else 5
                    await database.add_user_xp(guild.id, member.id, v_xp)
                    award_vc_coins(member.id, amount=v_coins)

    @voice_xp_task.before_loop
    async def before_voice_task(self):
        import asyncio
        while not self.bot.is_ready():
            await asyncio.sleep(1)

    # -------------------------------------------------------------
    # SLASH COMMANDS: /rank, /coins, & /leaderboard
    # -------------------------------------------------------------
    @app_commands.command(name="rank", description="View your current level, XP, coins, and server ranking card.")
    @app_commands.describe(member="Member whose rank card you want to inspect (defaults to you)")
    async def rank_command(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        data = await database.get_user_level_data(interaction.guild.id, target.id)

        current_xp = data["xp"]
        level = data["level"]
        rank = data["rank"]
        msg_count = data["messages_count"]
        base_xp = data["current_level_base_xp"]
        next_xp = data["next_level_xp"]
        coins = get_user_coins(target.id)
        rep = get_user_rep(target.id)

        xp_in_level = max(0, current_xp - base_xp)
        xp_needed = max(1, next_xp - base_xp)
        percent = int(min(100, (xp_in_level / xp_needed) * 100))
        progress_bar = render_progress_bar(xp_in_level, xp_needed, length=12)

        embed = discord.Embed(
            title=f"✦ RANK CARD • {target.display_name}",
            color=0xFF007F
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.add_field(name="🏆 Server Rank", value=f"**#{rank}**", inline=True)
        embed.add_field(name="⭐ Level", value=f"**Level {level}**", inline=True)
        embed.add_field(name="🪙 Coins", value=f"**{coins:,}**", inline=True)
        embed.add_field(name="💖 Rep", value=f"**+{rep}**", inline=True)
        embed.add_field(name="💬 Messages", value=f"`{msg_count:,}`", inline=True)
        embed.add_field(
            name="📊 Level Progress",
            value=f"`{progress_bar}` **{percent}%**\n`{xp_in_level:,}` / `{xp_needed:,} XP` (Total: `{current_xp:,} XP`)",
            inline=False
        )
        embed.set_footer(text=f"Requested by {interaction.user.display_name} • Give rep with /rep <user>!", icon_url=interaction.user.display_avatar.url)
        embed.timestamp = discord.utils.utcnow()

        avatar_bytes = None
        try:
            avatar_bytes = await target.display_avatar.read()
        except Exception:
            pass

        card_buf = generate_rank_card(
            avatar_bytes=avatar_bytes,
            username=target.display_name,
            level=level,
            current_xp=xp_in_level,
            next_level_xp=xp_needed,
            rank=rank,
            coins=coins,
            rep=rep,
            messages=msg_count
        )
        file = discord.File(fp=card_buf, filename="rank.png")
        embed.set_image(url="attachment://rank.png")

        await interaction.response.send_message(embed=embed, file=file, ephemeral=True)

    @app_commands.command(name="coins", description="Check your current coin balance and economy status.")
    @app_commands.describe(member="Member to inspect (defaults to you)")
    async def coins_command(self, interaction: discord.Interaction, member: Optional[discord.Member] = None):
        target = member or interaction.user
        coins = get_user_coins(target.id)
        embed = discord.Embed(
            title=f"🪙 Economy Balance • {target.display_name}",
            description=(
                f"💰 **Wallet Balance:** `{coins:,} Coins`\n\n"
                f"💡 *Earn more coins by chatting in text channels, listening in VC lounges (+5 coins every 2 min), or claiming `/daily`!*"
            ),
            color=0xF1C40F
        )
        embed.set_thumbnail(url=target.display_avatar.url)
        embed.set_footer(text="RAI FAM 💗 • Economy System", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="leaderboard", description="View the Top 10 most active members on the server.")
    async def leaderboard_command(self, interaction: discord.Interaction):
        leaders = await database.get_leaderboard(interaction.guild.id, limit=10)
        if not leaders:
            return await interaction.response.send_message("ℹ️ No ranking data available yet. Start chatting to earn XP!", ephemeral=True)

        medals = {1: "🥇", 2: "🥈", 3: "🥉"}
        lines = []
        for row in leaders:
            uid = row["user_id"]
            user = interaction.guild.get_member(uid)
            user_name = user.display_name if user else f"User {uid}"
            rank_icon = medals.get(row["rank"], f"`#{row['rank']:02d}`")
            lines.append(f"{rank_icon} **{user_name}** — **Level {row['level']}** (`{row['xp']:,} XP` • `{row['messages_count']:,} msgs`)")

        embed = discord.Embed(
            title="🏆 SERVER XP LEADERBOARD • TOP 10",
            description="\n".join(lines),
            color=0xFFD700
        )
        embed.set_footer(text="Chat and participate in voice channels to climb the ranks!")
        embed.timestamp = discord.utils.utcnow()

        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="profile", description="View your luxury unified server profile codex.")
    @app_commands.describe(
        member="Member whose profile to view (defaults to you)",
        visible="Share profile publicly in channel (Defaults to False - only you can see it)"
    )
    async def profile_command(self, interaction: discord.Interaction, member: Optional[discord.Member] = None, visible: bool = False):
        target = member or interaction.user
        uid = str(target.id)

        from cogs.profile import get_user_bio
        bio = get_user_bio(target.id)

        # 1. Level & XP
        data = await database.get_user_level_data(interaction.guild.id, target.id)
        lvl = data.get("level", 0)
        xp = data.get("xp", 0)
        req_xp = data.get("next_level_xp", 100)
        base_xp = data.get("current_level_base_xp", 0)
        xp_in_level = max(0, xp - base_xp)
        xp_needed = max(1, req_xp - base_xp)
        pct = min(100, round((xp_in_level / xp_needed * 100))) if xp_needed > 0 else 0
        filled = int(round(10 * pct / 100))
        xp_bar = "▰" * filled + "▱" * (10 - filled)

        # 2. Economy & Rep
        from cogs.economy import OWNER_ID
        raw_coins = get_user_coins(target.id)
        coins = "∞ (Owner Vault)" if target.id == OWNER_ID else raw_coins
        rep = get_user_rep(target.id)

        # 3. Voice Lounge Hours
        telem_file = DATA_DIR / "telemetry.json"
        voice_hrs = 0.0
        if telem_file.exists():
            try:
                with open(telem_file, "r", encoding="utf-8") as f:
                    t_data = json.load(f)
                    total_m = t_data.get("users", {}).get(uid, {}).get("total_minutes", 0)
                    voice_hrs = round(total_m / 60, 1)
            except Exception:
                pass

        # 4. Pet Companion
        pets_file = DATA_DIR / "pets.json"
        pet_str = "None (Adopt at `/pet shop`)"
        if pets_file.exists():
            try:
                with open(pets_file, "r", encoding="utf-8") as f:
                    p_data = json.load(f)
                    user_pet = p_data.get(uid)
                    if user_pet:
                        species = user_pet.get("species", "pet")
                        pet_name = user_pet.get("name", species.capitalize())
                        pet_lvl = user_pet.get("level", 1)
                        pet_str = f"🐾 **{pet_name}** *(Lvl {pet_lvl} {species.title()})*"
            except Exception:
                pass

        # 5. Clan / Squad Tag
        squads_file = DATA_DIR / "squads.json"
        clan_str = "Solo Adventurer"
        if squads_file.exists():
            try:
                with open(squads_file, "r", encoding="utf-8") as f:
                    sq_data = json.load(f)
                    for sq in sq_data.values():
                        if target.id in sq.get("members", []) or target.id == sq.get("leader_id"):
                            clan_str = f"🛡️ **[{sq.get('tag')}]** {sq.get('name')}"
                            break
            except Exception:
                pass

        joined_str = f"<t:{int(target.joined_at.timestamp())}:D>" if target.joined_at else "Unknown"
        canvas_date_str = target.joined_at.strftime("%b %d, %Y") if target.joined_at else "Recent Citizen"

        coin_display_embed = coins if isinstance(coins, str) else f"{coins:,} Coins"

        embed = discord.Embed(
            title=f"💳 SERVER PROFILE CODEX • {target.display_name.upper()}",
            description=f"Unified identity record for {target.mention} in **{interaction.guild.name}**\n\n💬 *\"{bio}\"*\n",
            color=0xFF007F
        )
        embed.set_thumbnail(url=target.display_avatar.url)

        embed.add_field(
            name="📊 Level & Progression",
            value=f"⭐ **Level {lvl}** (`{xp:,} / {req_xp:,} XP`)\n`{xp_bar}` **{pct}%**",
            inline=False
        )
        embed.add_field(
            name="🪙 Vault & Influence",
            value=f"💰 `{coin_display_embed}` • ✨ `{rep}` Rep Points",
            inline=True
        )
        embed.add_field(
            name="🎙️ Voice Lounge Presence",
            value=f"🎧 **{voice_hrs} Hours** logged",
            inline=True
        )
        embed.add_field(
            name="🐾 Active Pet Companion",
            value=pet_str,
            inline=True
        )
        embed.add_field(
            name="⚔️ Clan / Squad",
            value=clan_str,
            inline=True
        )
        embed.add_field(
            name="📅 Server Citizen Since",
            value=joined_str,
            inline=True
        )

        embed.set_footer(text="RAI VIBES 💗 • Unified Member Codex", icon_url=config.RAI_ICON_URL)

        avatar_bytes = None
        try:
            avatar_bytes = await target.display_avatar.read()
        except Exception:
            pass

        try:
            card_buf = generate_profile_codex(
                avatar_bytes=avatar_bytes,
                username=target.display_name,
                level=lvl,
                current_xp=xp,
                req_xp=req_xp,
                coins=coins,
                rep=rep,
                voice_hrs=voice_hrs,
                pet_str=pet_str,
                clan_str=clan_str,
                join_date_str=canvas_date_str
            )
            file = discord.File(fp=card_buf, filename="profile.png")
            embed.set_image(url="attachment://profile.png")
            await interaction.response.send_message(embed=embed, file=file, ephemeral=(not visible))
        except Exception as e:
            logger.warning(f"Failed to generate profile codex canvas: {e}")
            await interaction.response.send_message(embed=embed, ephemeral=(not visible))

    @app_commands.command(name="milestones", description="View all server level milestones, coin rewards, and prestige unlocks.")
    async def milestones_command(self, interaction: discord.Interaction):
        MILESTONES = {
            5: {"title": "🥉 Bronze Voyager", "bonus": 250, "perk": "Custom chat titles & shop discount eligibility"},
            10: {"title": "🥈 Silver Challenger", "bonus": 500, "perk": "Priority reactions & VIP chat recognition"},
            15: {"title": "🥇 Gold Champion", "bonus": 1000, "perk": "Unlocked **✦ ᴅᴊ** role & DJ deck permissions", "role_id": 1545834928221069522},
            20: {"title": "💎 Diamond Virtuoso", "bonus": 2000, "perk": "Unlocked `/priority` DJ queue bump & VIP lounge access"},
            25: {"title": "👑 RAI Legend", "bonus": 5000, "perk": "Permanent Hall-of-Fame glory & custom personal status"},
            30: {"title": "✨ Celestial Apex", "bonus": 10000, "perk": "Immortalized server legend status & maximum perks"}
        }

        user_data = await database.get_user_level_data(interaction.guild.id, interaction.user.id)
        current_lvl = user_data["level"]

        embed = discord.Embed(
            title="🏆 ✦ RAI FAM LEVEL MILESTONES & PERKS ✦ 🏆",
            description=(
                f"Your current status: **Level {current_lvl}**\n"
                f"Earn XP naturally by chatting in text lounges and chilling in voice rooms!\n"
                f"Each milestone rewards lump-sum coin vaults and unlocks exclusive perks.\n"
                f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            ),
            color=0xFFD700
        )

        for lvl, data in sorted(MILESTONES.items()):
            status_icon = "✅" if current_lvl >= lvl else "🔒"
            role_hint = f" • Auto-Role: <@&{data['role_id']}>" if "role_id" in data else ""
            embed.add_field(
                name=f"{status_icon} Level {lvl} — {data['title']}",
                value=f"🪙 **Bonus:** `+{data['bonus']:,} Coins`{role_hint}\n✨ **Perk:** {data['perk']}",
                inline=False
            )

        embed.set_footer(text="RAI VIBES Leveling Suite • Earn coins & prestige", icon_url=config.RAI_ICON_URL)
        await interaction.response.send_message(embed=embed)


async def setup(bot: commands.Bot):
    await bot.add_cog(Leveling(bot))

