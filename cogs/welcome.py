import io
import json
import unicodedata
import discord
from discord.ext import commands
from discord import app_commands
import logging
from pathlib import Path
try:
    from PIL import Image, ImageDraw, ImageFont, ImageOps
except ImportError:
    pass

import config

logger = logging.getLogger("Welcome")

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
ECONOMY_FILE = DATA_DIR / "economy.json"
LEVELS_FILE = DATA_DIR / "levels.json"

def award_welcome_bonus(user_id: str):
    """Credit +100 Coins and +50 XP starter bonus to new members."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Economy Coins
    try:
        eco_data = {}
        if ECONOMY_FILE.exists():
            with open(ECONOMY_FILE, "r", encoding="utf-8") as f:
                eco_data = json.load(f)
        if user_id not in eco_data:
            eco_data[user_id] = {"coins": 200, "last_daily": 0, "wins": 0, "losses": 0}
        eco_data[user_id]["coins"] += 100
        with open(ECONOMY_FILE, "w", encoding="utf-8") as f:
            json.dump(eco_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not award economy bonus to {user_id}: {e}")

    # 2. Levels XP
    try:
        lvl_data = {}
        if LEVELS_FILE.exists():
            with open(LEVELS_FILE, "r", encoding="utf-8") as f:
                lvl_data = json.load(f)
        if user_id not in lvl_data:
            lvl_data[user_id] = {"xp": 0, "level": 1, "last_msg": 0}
        lvl_data[user_id]["xp"] += 50
        with open(LEVELS_FILE, "w", encoding="utf-8") as f:
            json.dump(lvl_data, f, indent=2)
    except Exception as e:
        logger.warning(f"Could not award levels XP to {user_id}: {e}")


def sanitize_for_canvas(text: str, max_len: int = 16) -> str:
    norm = unicodedata.normalize('NFKD', text)
    clean = "".join([c for c in norm if ord(c) < 128 or c.isalnum() or c in " -_!."]).strip()
    if not clean:
        clean = "RAI Member"
    return clean[:max_len] if len(clean) <= max_len else f"{clean[:max_len-2]}.."


def create_grand_welcome_image(avatar_bytes: bytes, username: str, member_count: int, guild_name: str) -> io.BytesIO:
    """Generates a luxury 900x350 Cyber-Pink & Royal Gold dynamic welcome card with user avatar."""
    WIDTH, HEIGHT = 900, 350
    
    # 1. Base Image with Deep Gradient Dark Background
    img = Image.new("RGBA", (WIDTH, HEIGHT), color=(11, 9, 18, 255))
    draw = ImageDraw.Draw(img)

    # 2. Ambient Cyber-Pink & Cyan Radiant Glow
    for r in range(160, 0, -12):
        alpha = int(28 * (1 - r / 160))
        draw.ellipse([60 - r, 60 - r, 60 + r, 60 + r], fill=(255, 105, 180, alpha))
        draw.ellipse([WIDTH - 60 - r, HEIGHT - 60 - r, WIDTH - 60 + r, HEIGHT - 60 + r], fill=(0, 240, 255, alpha))
        draw.ellipse([WIDTH // 2 - r, 20 - r, WIDTH // 2 + r, 20 + r], fill=(255, 215, 0, int(alpha * 0.6)))

    # Outer Cyber Frame (Gold + Pink Accents)
    draw.rounded_rectangle([12, 12, WIDTH - 12, HEIGHT - 12], radius=28, outline=(255, 105, 180, 200), width=3)
    draw.rounded_rectangle([18, 18, WIDTH - 18, HEIGHT - 18], radius=24, outline=(255, 215, 0, 140), width=2)
    draw.rounded_rectangle([22, 22, WIDTH - 22, HEIGHT - 22], radius=20, outline=(28, 22, 42, 255), width=2)

    # Top Crown Ribbon Accent
    draw.rectangle([140, 12, WIDTH - 140, 18], fill=(255, 20, 147, 240))
    draw.rectangle([200, 18, WIDTH - 200, 22], fill=(255, 215, 0, 255))

    # Corner Decorative Sparkles / Brackets
    bracket_color = (255, 215, 0, 220)
    draw.line([(30, 45), (45, 30)], fill=bracket_color, width=3)
    draw.line([(WIDTH - 45, 30), (WIDTH - 30, 45)], fill=bracket_color, width=3)
    draw.line([(30, HEIGHT - 45), (45, HEIGHT - 30)], fill=bracket_color, width=3)
    draw.line([(WIDTH - 45, HEIGHT - 30), (WIDTH - 30, HEIGHT - 45)], fill=bracket_color, width=3)

    # 3. Avatar Processing (Circular Crop with 3-Layer Concentric Glowing Rings)
    try:
        raw_avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        raw_avatar = raw_avatar.resize((180, 180), Image.Resampling.LANCZOS)
        
        # Circular Mask
        mask = Image.new("L", (180, 180), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 180, 180), fill=255)
        
        avatar_circle = ImageOps.fit(raw_avatar, mask.size, centering=(0.5, 0.5))
        avatar_circle.putalpha(mask)

        # Concentric Outer Glow Rings (Gold -> Cyan -> Pink)
        draw.ellipse([58, 80, 252, 274], outline=(255, 215, 0, 180), width=6)
        draw.ellipse([62, 84, 248, 270], outline=(0, 240, 255, 220), width=4)
        draw.ellipse([65, 87, 245, 267], outline=(255, 20, 147, 255), width=3)
        img.paste(avatar_circle, (65, 87), avatar_circle)
    except Exception as e:
        logger.warning(f"Could not render avatar image: {e}")
        draw.ellipse([65, 87, 245, 267], fill=(255, 105, 180, 255))

    # 4. Text Content Rendering
    try:
        font_sub = ImageFont.truetype("arialbd.ttf", 22)
        font_name = ImageFont.truetype("arialbd.ttf", 40)
        font_count = ImageFont.truetype("arialbd.ttf", 24)
        font_tags = ImageFont.truetype("arialbd.ttf", 16)
    except Exception:
        font_sub = ImageFont.load_default()
        font_name = font_sub
        font_count = font_sub
        font_tags = font_sub

    # Header: "✨ WELCOME TO <GUILD> ✨"
    draw.text((280, 75), f"✨ WELCOME TO {guild_name.upper()} ✨", fill=(255, 105, 180, 255), font=font_sub)
    
    # Username with Glow/Shadow Effect
    clean_name = sanitize_for_canvas(username, max_len=18)
    draw.text((282, 112), clean_name, fill=(20, 10, 30, 255), font=font_name)
    draw.text((280, 110), clean_name, fill=(255, 255, 255, 255), font=font_name)
    
    # Member Count Tag Badge with Gold Border
    badge_bg = [280, 175, 570, 220]
    draw.rounded_rectangle(badge_bg, radius=14, fill=(24, 18, 38, 255), outline=(255, 215, 0, 220), width=2)
    draw.text((298, 183), f"👑 MEMBER #{member_count}", fill=(255, 215, 0, 255), font=font_count)

    # Feature Highlights Badges
    pills = [
        ("🌸 RAI FAMILY", (255, 105, 180)),
        ("🎧 RYTHM VIBES", (0, 240, 255)),
        ("🍿 CINEMA HUB", (255, 215, 0)),
        ("🎁 +100 COINS BONUS", (50, 205, 50))
    ]
    px = 280
    for pill, color in pills:
        pill_len = len(pill) * 9 + 18
        draw.rounded_rectangle([px, 245, px + pill_len, 280], radius=10, fill=(35, 25, 50, 230), outline=(color[0], color[1], color[2], 160), width=1)
        draw.text((px + 10, 253), pill, fill=color, font=font_tags)
        px += pill_len + 12

    # 5. Export to BytesIO
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output


def create_grand_goodbye_image(avatar_bytes: bytes, username: str, member_count: int = 0, guild_name: str = "") -> io.BytesIO:
    """Generates an exact Koya-style clean dark goodbye card."""
    WIDTH, HEIGHT = 800, 450
    # Discord dark background: #2b2d31
    img = Image.new("RGBA", (WIDTH, HEIGHT), color=(43, 45, 49, 255))
    draw = ImageDraw.Draw(img)

    # 1. Centered Circular Avatar
    avatar_size = 190
    avatar_x = (WIDTH - avatar_size) // 2
    avatar_y = 40

    try:
        raw_avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        raw_avatar = raw_avatar.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)
        
        # High-res circular mask for ultra-smooth anti-aliasing
        mask_scale = 4
        big_mask = Image.new("L", (avatar_size * mask_scale, avatar_size * mask_scale), 0)
        mask_draw = ImageDraw.Draw(big_mask)
        mask_draw.ellipse((0, 0, avatar_size * mask_scale, avatar_size * mask_scale), fill=255)
        smooth_mask = big_mask.resize((avatar_size, avatar_size), Image.Resampling.LANCZOS)

        avatar_circle = ImageOps.fit(raw_avatar, (avatar_size, avatar_size), centering=(0.5, 0.5))
        avatar_circle.putalpha(smooth_mask)

        # White Circular Border
        draw.ellipse([avatar_x - 5, avatar_y - 5, avatar_x + avatar_size + 5, avatar_y + avatar_size + 5], outline=(255, 255, 255, 255), width=5)
        img.paste(avatar_circle, (avatar_x, avatar_y), avatar_circle)
    except Exception as e:
        logger.warning(f"Could not render goodbye avatar: {e}")
        draw.ellipse([avatar_x, avatar_y, avatar_x + avatar_size, avatar_y + avatar_size], fill=(255, 105, 180, 255))

    # 2. Typography
    try:
        font_title = ImageFont.truetype("arialbd.ttf", 52)
        font_name = ImageFont.truetype("arialbd.ttf", 36)
    except Exception:
        font_title = ImageFont.load_default()
        font_name = font_title

    # "GOOD BYE" (Centered Bold White with clean shadow)
    title_text = "GOOD BYE"
    bbox_title = draw.textbbox((0, 0), title_text, font=font_title)
    w_title = bbox_title[2] - bbox_title[0]
    tx = (WIDTH - w_title) // 2
    ty = 255
    # Shadow
    draw.text((tx + 2, ty + 2), title_text, fill=(18, 18, 20, 255), font=font_title)
    # Main text
    draw.text((tx, ty), title_text, fill=(255, 255, 255, 255), font=font_title)

    # Username (Centered Bold White with clean shadow)
    clean_user = sanitize_for_canvas(username, max_len=20).upper()
    bbox_name = draw.textbbox((0, 0), clean_user, font=font_name)
    w_name = bbox_name[2] - bbox_name[0]
    nx = (WIDTH - w_name) // 2
    ny = 325
    # Shadow
    draw.text((nx + 2, ny + 2), clean_user, fill=(18, 18, 20, 255), font=font_name)
    # Main text
    draw.text((nx, ny), clean_user, fill=(255, 255, 255, 255), font=font_name)

    # 3. Export
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output


class WelcomeQuickActionsView(discord.ui.View):
    """Interactive Buttons attached to the Welcome Announcement."""
    def __init__(self, member: discord.Member = None):
        super().__init__(timeout=None)
        self.member_id = member.id if member else None
        self.member_mention = member.mention if member else "our new member"

    @discord.ui.button(label="📜 Server Rules", style=discord.ButtonStyle.secondary, emoji="📜", custom_id="welcome_rules_btn")
    async def rules_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        rules_chan = discord.utils.get(guild.text_channels, name="rules") or discord.utils.get(guild.text_channels, name="├・「📜」rules-and-guidelines")
        rules_text = rules_chan.mention if rules_chan else "the rules channel"
        await interaction.response.send_message(
            f"📜 **RAI FAM Community Rules:**\n"
            f"1. Be respectful to all members and staff.\n"
            f"2. Keep topics in their appropriate channels.\n"
            f"3. No spamming, self-promotion, or unsolicited DMs.\n"
            f"4. Have fun and vibe with the music! 💗\n\n"
            f"Check {rules_text} for full guidelines.",
            ephemeral=True
        )

    @discord.ui.button(label="🎨 Pick Roles", style=discord.ButtonStyle.primary, emoji="⭐", custom_id="welcome_roles_btn")
    async def roles_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        roles_chan = discord.utils.get(guild.text_channels, name="self-roles") or discord.utils.get(guild.text_channels, name="├・「⭐」self-roles")
        roles_text = roles_chan.mention if roles_chan else "the self-roles channel"
        await interaction.response.send_message(
            f"🎨 **Customize Your Profile:**\n"
            f"Head over to {roles_text} to pick your favorite **Name Color**, **Gaming Tags** (Free Fire, BGMI, Roblox), and **Movie/Giveaway Notification Pings**!",
            ephemeral=True
        )

    @discord.ui.button(label="🎵 Music Guide", style=discord.ButtonStyle.secondary, emoji="🎧", custom_id="welcome_music_btn")
    async def music_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            f"🎵 **How to play music with RAI VIBES 💗:**\n"
            f"• `/play <song or URL>` — Play any song instantly.\n"
            f"• `/radio` — 24/7 Lofi, Tamil, Bollywood, EDM live radio streams.\n"
            f"• `/musicquiz` — Play the 15-second audio guess quiz for coins!\n"
            f"• `#song-requests` — Type any song name without prefix to queue it!",
            ephemeral=True
        )

    @discord.ui.button(label="👋 Say Hi!", style=discord.ButtonStyle.success, emoji="🎉", custom_id="welcome_sayhi_btn")
    async def say_hi_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id == self.member_id:
            return await interaction.response.send_message("👋 Welcome to the server! We are so glad to have you here! 💗", ephemeral=True)
        await interaction.response.send_message(
            f"🎉 {interaction.user.mention} says: **`Welcome to RAI FAM, {self.member_mention}! Glad you're here! 🌸✨`**",
            ephemeral=False
        )


class Welcome(commands.Cog):
    """Grand Welcome System: Luxury Canvas Cards, DM Onboarding & Starter Rewards."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        member_count = len(guild.members)

        # 1. Automatic Role Assignment on Join
        try:
            if member.bot:
                bot_role = discord.utils.get(guild.roles, name="🤖 ┊ 𝐀𝐔𝐃𝐈𝐎 𝐁𝐎𝐓𝐒") or discord.utils.get(guild.roles, name="Bots")
                if bot_role:
                    await member.add_roles(bot_role, reason="Auto-role for bot")
            else:
                family_role = discord.utils.get(guild.roles, name="🌸 ┊ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘")
                if not family_role:
                    for r in guild.roles:
                        if "RAI FAMILY" in r.name.upper() or "FAMILY" in r.name.upper():
                            family_role = r
                            break
                if family_role:
                    await member.add_roles(family_role, reason="Auto-role on join: RAI FAMILY")
                    logger.info(f"Granted {family_role.name} to {member.display_name}")
        except Exception as e:
            logger.error(f"Failed to auto-assign role to {member.display_name}: {e}")

        # 2. Award Starter Bonus (+100 Coins & +50 XP)
        if not member.bot:
            award_welcome_bonus(str(member.id))

        # 3. Update Server Stats Channel if present
        for vc in guild.voice_channels:
            if "members:" in vc.name.lower() or "member count" in vc.name.lower():
                try:
                    await vc.edit(name=f"👥・Members: {member_count}")
                except Exception:
                    pass

        # 4. Default Welcome Image (Image 1 - The Office Celebration GIF)
        DEFAULT_WELCOME_IMAGE_URL = "https://media.giphy.com/media/l0MYt5jPR6QX5pnqM/giphy.gif"

        # 5. Send Grand Announcement in Welcome Channel
        welcome_chan = next((ch for ch in guild.text_channels if "welcome" in ch.name.lower()), None)
        if not welcome_chan:
            welcome_chan = discord.utils.get(guild.text_channels, name="general")

        if welcome_chan:
            rules_chan = next((ch for ch in guild.text_channels if "rules" in ch.name.lower()), None)
            verify_chan = next((ch for ch in guild.text_channels if "verify" in ch.name.lower()), None)
            roles_chan = next((ch for ch in guild.text_channels if "role" in ch.name.lower()), None)
            gen_chan = next((ch for ch in guild.text_channels if "general" in ch.name.lower()), None)
            gaming_chan = next((ch for ch in guild.text_channels if "gaming" in ch.name.lower()), None)
            fun_vc = next((vc for vc in guild.voice_channels if "fun" in vc.name.lower()), None)
            lofi_vc = next((vc for vc in guild.voice_channels if "lo-fi" in vc.name.lower() or "lofi" in vc.name.lower()), None)

            rules_ref = rules_chan.mention if rules_chan else "#rules"
            verify_ref = verify_chan.mention if verify_chan else "#verify"
            roles_ref = roles_chan.mention if roles_chan else "#self-roles"
            gen_ref = gen_chan.mention if gen_chan else "#general"
            gaming_ref = gaming_chan.mention if gaming_chan else "#gaming-chat"
            fun_ref = fun_vc.mention if fun_vc else "🐣 ┊ Fun Time"
            lofi_ref = lofi_vc.mention if lofi_vc else "🌧️ ┊ Lo-Fi Chill"

            embed = discord.Embed(
                title=f"🌸 {guild.name.upper()} !",
                description=(
                    f"**HEY BUDDY!** **{member.display_name}** ({member.mention})\n\n"
                    f"**Welcome To {guild.name} !**\n"
                    f"**Get started with below:** {rules_ref}\n\n"
                    f"**Follow The Server Guidelines:** {rules_ref}\n\n"
                    f"**Verify For Full Access:** {verify_ref}\n\n"
                    f"**Claim Your Roles:** {roles_ref}\n\n"
                    f"**Fun With Us:** {fun_ref}\n\n"
                    f"**Gaming Zone:** {gaming_ref}\n\n"
                    f"**24/7 Lo-Fi & Beats:** {lofi_ref}\n\n"
                    f"**Join And Chill With Us!:** {gen_ref}\n\n"
                    f"**Thanks For Joining. Hope You Have A Great Time Here!**"
                ),
                color=0xFF69B4  # Vibrant Sakura Pink
            )
            embed.set_author(name=f"{guild.name}", icon_url=guild.icon.url if guild.icon else None)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"Member #{member_count} • User ID: {member.id} • RAI FAM Luxury Welcome 💗", icon_url=guild.icon.url if guild.icon else None)
            embed.set_image(url=DEFAULT_WELCOME_IMAGE_URL)

            view = WelcomeQuickActionsView(member)
            try:
                user_name = member.display_name if member.display_name else member.name
                welcome_text = f"🎉 Welcome **{user_name}** ({member.mention}) to **{guild.name}**! 🚀"
                await welcome_chan.send(
                    content=welcome_text,
                    embed=embed,
                    view=view
                )
            except Exception as e:
                logger.error(f"Failed to send grand welcome message: {e}")

        # 6. Send Royal Direct Message (DM) Onboarding Letter
        if not member.bot:
            try:
                dm_embed = discord.Embed(
                    title=f"🌸 Welcome to {guild.name}, {member.display_name}! 💗",
                    description=(
                        f"Hey **{member.name}**, thank you for joining **{guild.name}**!\n\n"
                        f"We are delighted to have you with us. Here is your quick VIP starter kit:\n\n"
                        f"✨ **Granted Role:** `🌸 ┊ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘`\n"
                        f"🪙 **Bonus Received:** `+100 Coins` & `+50 XP`\n\n"
                        f"**🎵 Music & Radio:**\n"
                        f"• Use `/play <song name>` to stream high-fidelity music.\n"
                        f"• Use `/radio` for 24/7 non-stop lofi, Tamil, and EDM stations.\n"
                        f"• Use `/musicquiz` to challenge friends in audio trivia!\n\n"
                        f"**🍿 Cinema & Gaming:**\n"
                        f"• Join our Cinema Lounge for weekly watch parties.\n"
                        f"• Join dynamic voice rooms to hang out with friends!\n\n"
                        f"Have an awesome time, and don't hesitate to ask our Staff team if you need anything! 🌸✨"
                    ),
                    color=config.COLOR_PRIMARY
                )
                dm_embed.set_thumbnail(url=guild.icon.url if guild.icon else config.RAI_ICON_URL)
                dm_embed.set_footer(text="RAI VIBES 💗 • Music & Community Bot", icon_url=config.RAI_ICON_URL)
                await member.send(embed=dm_embed)
            except Exception:
                # User has DMs closed
                pass

        # 7. Anti-Alt Account Check
        now_dt = discord.utils.utcnow()
        account_age = (now_dt - member.created_at).days
        if account_age < 3:
            log_chan = discord.utils.get(guild.text_channels, name="📋・mod-logs")
            if log_chan:
                alt_embed = discord.Embed(
                    title="⚠️ [SECURITY ALERT] New / Alt Account Joined",
                    description=(
                        f"**User:** {member.mention} (`{member.id}`)\n"
                        f"**Account Age:** `{account_age} day(s) old` (Created <t:{int(member.created_at.timestamp())}:R>)\n"
                        f"**Notice:** Monitored for suspicious raid activity."
                    ),
                    color=config.COLOR_WARNING
                )
                try:
                    await log_chan.send(embed=alt_embed)
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        """Server Booster Celebration Announcer."""
        if before.premium_since is None and after.premium_since is not None:
            guild = after.guild
            elite_role = discord.utils.get(guild.roles, name="💎 ┊ 𝐑𝐀𝐈 𝐄𝐋𝐈𝐓𝐄")
            if elite_role:
                try:
                    await after.add_roles(elite_role, reason="Server Booster Reward")
                except Exception:
                    pass

            gen_chan = discord.utils.get(guild.text_channels, name="💬・general-chat")
            if gen_chan:
                embed = discord.Embed(
                    title="🚀 NEW SERVER BOOSTER • ROYAL RESPECT! 💎",
                    description=(
                        f"A huge thank you to {after.mention} for boosting **{guild.name}**! 💖✨\n\n"
                        f"You have unlocked the prestigious **`💎 ┊ 𝐑𝐀𝐈 𝐄𝐋𝐈𝐓𝐄`** role & VIP perks!\n"
                        f"Server Boost Level is now **Level {guild.premium_tier}** ({guild.premium_subscription_count} Boosts)."
                    ),
                    color=discord.Color.nitro_pink()
                )
                embed.set_thumbnail(url=after.display_avatar.url)
                embed.set_image(url="https://images.unsplash.com/photo-1518709268805-4e9042af9f23?q=80&w=1000&auto=format&fit=crop")
                embed.set_footer(text="Thank you for supporting RAI FAM!", icon_url=config.RAI_ICON_URL)
                try:
                    await gen_chan.send(content=f"🎉 **NEW BOOST!** {after.mention}", embed=embed)
                except Exception:
                    pass

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        guild = member.guild
        member_count = len(guild.members)

        # 1. Update Server Stats Channel
        for vc in guild.voice_channels:
            if "members:" in vc.name.lower() or "member count" in vc.name.lower():
                try:
                    await vc.edit(name=f"👥・Members: {member_count}")
                except Exception:
                    pass

        # 2. Generate Dynamic Goodbye Canvas Card
        card_file = None
        try:
            avatar_bytes = await member.display_avatar.with_format("png").with_size(256).read()
            card_bytes = await asyncio.to_thread(
                create_grand_goodbye_image,
                avatar_bytes,
                member.display_name,
                member_count,
                guild.name
            )
            card_file = discord.File(card_bytes, filename="grand_goodbye.png")
        except Exception as e:
            logger.warning(f"Could not generate goodbye card for {member.name}: {e}")

        # 3. Post Goodbye Announcement in Dedicated Goodbye Channel
        goodbye_chan = (
            guild.get_channel(1546122222329008199) or
            discord.utils.get(guild.text_channels, name="👋・good-bye") or
            discord.utils.get(guild.text_channels, name="good-bye") or
            discord.utils.get(guild.text_channels, name="goodbye")
        )

        if goodbye_chan:
            user_display = member.display_name if member.display_name else member.name
            msg_content = f"👋 **{user_display}** has left **{guild.name}** ."
            try:
                if card_file:
                    await goodbye_chan.send(
                        content=msg_content,
                        file=card_file
                    )
                else:
                    await goodbye_chan.send(
                        content=msg_content
                    )
            except Exception as e:
                logger.error(f"Failed to send goodbye announcement: {e}")

        # 4. Mod Log Record
        log_chan = discord.utils.get(guild.text_channels, name="📋・mod-logs")
        if log_chan:
            log_embed = discord.Embed(
                title="👋 Member Left",
                description=f"**{member.name}** (`{member.id}`) has departed. Member count is now **{member_count}**.",
                color=config.COLOR_SECONDARY
            )
            try:
                await log_chan.send(embed=log_embed)
            except Exception:
                pass

    @commands.hybrid_command(name="testwelcome", description="Preview the Grand Royal Welcome Card & Announcement.")
    @commands.has_permissions(administrator=True)
    async def testwelcome(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        guild = ctx.guild
        member_count = len(guild.members)
        target_name = target.display_name if target.display_name else target.name
        
        await ctx.defer()
        try:
            avatar_bytes = await target.display_avatar.with_format("png").with_size(256).read()
            card_bytes = await asyncio.to_thread(
                create_grand_welcome_image,
                avatar_bytes,
                target_name,
                member_count,
                guild.name
            )
            card_file = discord.File(card_bytes, filename="grand_welcome_preview.png")
            
            rules_chan = discord.utils.get(guild.text_channels, name="📜・rules") or discord.utils.get(guild.text_channels, name="rules")
            verify_chan = discord.utils.get(guild.text_channels, name="✅・verify") or discord.utils.get(guild.text_channels, name="verify")
            roles_chan = discord.utils.get(guild.text_channels, name="🎭・self-roles") or discord.utils.get(guild.text_channels, name="self-roles")
            gen_chan = discord.utils.get(guild.text_channels, name="💬・general") or discord.utils.get(guild.text_channels, name="general")
            gaming_chan = discord.utils.get(guild.text_channels, name="💬・gaming-text")
            fun_vc = discord.utils.get(guild.voice_channels, name="🐣 | FUN TIME")
            lofi_vc = discord.utils.get(guild.voice_channels, name="🎧 | LO-FI CHILL [24/7]")

            rules_ref = rules_chan.mention if rules_chan else "#rules"
            verify_ref = verify_chan.mention if verify_chan else "#verify"
            roles_ref = roles_chan.mention if roles_chan else "#self-roles"
            gen_ref = gen_chan.mention if gen_chan else "#general"
            gaming_ref = gaming_chan.mention if gaming_chan else "#gaming-text"
            fun_ref = fun_vc.mention if fun_vc else "🐣 | FUN TIME"
            lofi_ref = lofi_vc.mention if lofi_vc else "🎧 | LO-FI CHILL [24/7]"

            embed = discord.Embed(
                title=f"🌸 {guild.name.upper()} !",
                description=(
                    f"**HEY BUDDY!** **{target_name}** ({target.mention})\n\n"
                    f"**Welcome To {guild.name} !**\n"
                    f"**Get started with below:** {rules_ref}\n\n"
                    f"**Follow The Server Guidelines:** {rules_ref}\n\n"
                    f"**Verify For Full Access:** {verify_ref}\n\n"
                    f"**Pick Your Roles:** {roles_ref}\n\n"
                    f"**Fun With Us:** {fun_ref}\n\n"
                    f"**Gaming Zone:** {gaming_ref}\n\n"
                    f"**24/7 Lo-Fi & Beats:** {lofi_ref}\n\n"
                    f"**Join And Chill With Us!:** {gen_ref}\n\n"
                    f"**Thanks For Joining. Hope You Have A Great Time Here!**"
                ),
                color=0xFF69B4
            )
            embed.set_author(name=f"{guild.name}", icon_url=guild.icon.url if guild.icon else None)
            embed.set_thumbnail(url=target.display_avatar.url)
            embed.set_image(url="attachment://grand_welcome_preview.png")
            embed.set_footer(text=f"Member #{member_count} • User ID: {target.id} • RAI FAM Luxury Welcome 💗", icon_url=guild.icon.url if guild.icon else None)
            
            view = WelcomeQuickActionsView(target)
            await ctx.send(
                content=f"🎉 Welcome **{target_name}** to **{guild.name}**! 🚀",
                embed=embed,
                file=card_file,
                view=view
            )
        except Exception as e:
            await ctx.send(f"❌ Failed to generate preview: {e}")

    @commands.hybrid_command(name="testgoodbye", description="Preview the Grand Royal Farewell & Goodbye Card.")
    @commands.has_permissions(administrator=True)
    async def testgoodbye(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        guild = ctx.guild
        member_count = len(guild.members)
        target_name = target.display_name if target.display_name else target.name
        
        await ctx.defer()
        try:
            avatar_bytes = await target.display_avatar.with_format("png").with_size(256).read()
            card_bytes = await asyncio.to_thread(
                create_grand_goodbye_image,
                avatar_bytes,
                target_name,
                member_count,
                guild.name
            )
            card_file = discord.File(card_bytes, filename="grand_goodbye_preview.png")

            msg_content = f"👋 **{target_name}** has left **{guild.name}** ."
            await ctx.send(
                content=msg_content,
                file=card_file
            )
        except Exception as e:
            await ctx.send(f"❌ Failed to generate goodbye preview: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
