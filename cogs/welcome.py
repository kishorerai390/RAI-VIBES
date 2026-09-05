import io
import json
import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps

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
        
        # Paste Circular Avatar
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
    clean_name = username if len(username) <= 16 else f"{username[:14]}..."
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


class WelcomeQuickActionsView(discord.ui.View):
    """Interactive Buttons attached to the Welcome Announcement."""
    def __init__(self, member: discord.Member):
        super().__init__(timeout=None)
        self.member_id = member.id
        self.member_mention = member.mention

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

        # 4. Generate Dynamic Canvas Welcome Card
        card_file = None
        try:
            avatar_bytes = await member.display_avatar.with_format("png").with_size(256).read()
            card_bytes = await asyncio.to_thread(
                create_grand_welcome_image,
                avatar_bytes,
                member.display_name,
                member_count,
                guild.name
            )
            card_file = discord.File(card_bytes, filename="grand_welcome.png")
        except Exception as e:
            logger.error(f"Failed to generate grand welcome image: {e}")

        # 5. Send Grand Announcement in Welcome Channel
        welcome_chan = (
            discord.utils.get(guild.text_channels, name="welcome") or
            discord.utils.get(guild.text_channels, name="👋・welcome") or
            discord.utils.get(guild.text_channels, name="╭・「👋」welcome") or
            discord.utils.get(guild.text_channels, name="general-chat")
        )

        if welcome_chan:
            rules_chan = discord.utils.get(guild.text_channels, name="rules") or discord.utils.get(guild.text_channels, name="├・「📜」rules-and-guidelines")
            roles_chan = discord.utils.get(guild.text_channels, name="self-roles") or discord.utils.get(guild.text_channels, name="├・「⭐」self-roles")
            gen_chan = discord.utils.get(guild.text_channels, name="💬・general-chat") or discord.utils.get(guild.text_channels, name="general-chat")

            rules_mention = rules_chan.mention if rules_chan else "#rules"
            roles_mention = roles_chan.mention if roles_chan else "#self-roles"
            gen_mention = gen_chan.mention if gen_chan else "#general-chat"

            embed = discord.Embed(
                title=f"🌸 GRAND ROYAL WELCOME TO {guild.name.upper()}! 🌸",
                description=(
                    f"A heartfelt royal welcome to {member.mention}! You are officially part of the **`🌸 ┊ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘`**! 🎉✨\n\n"
                    f"👑 **You are our honored Member #{member_count}**\n\n"
                    f"🎁 **Starter Gift Credited:**\n"
                    f"• **+100 Apex Coins** 🪙 deposited to your wallet (`/balance`)\n"
                    f"• **+50 Starter XP** ✨ added to your rank profile (`/rank`)\n\n"
                    f"**🚀 Explore The Community:**\n"
                    f"1️⃣ **Rules & Guidelines:** Check {rules_mention} to stay informed\n"
                    f"2️⃣ **Self Roles:** Pick custom colors and gaming tags in {roles_mention}\n"
                    f"3️⃣ **Hangout:** Come say hi to everyone in {gen_mention} and join our voice lounges!\n"
                ),
                color=config.COLOR_PRIMARY
            )
            if card_file:
                embed.set_image(url="attachment://grand_welcome.png")
            else:
                embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id} • RAI FAM Luxury Welcome System 💗", icon_url=config.RAI_ICON_URL)

            view = WelcomeQuickActionsView(member)
            try:
                if card_file:
                    await welcome_chan.send(
                        content=f"🎉 **Everyone welcome {member.mention} to {guild.name}!** 🌸✨",
                        embed=embed,
                        file=card_file,
                        view=view
                    )
                else:
                    await welcome_chan.send(
                        content=f"🎉 **Everyone welcome {member.mention} to {guild.name}!** 🌸✨",
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

        log_chan = discord.utils.get(guild.text_channels, name="📋・mod-logs")
        if log_chan:
            embed = discord.Embed(
                title="👋 Member Left",
                description=f"**{member.name}** (`{member.id}`) has left the server. Member count is now **{member_count}**.",
                color=config.COLOR_SECONDARY
            )
            try:
                await log_chan.send(embed=embed)
            except Exception:
                pass

    @commands.hybrid_command(name="testwelcome", description="Preview the Grand Royal Welcome Card & Announcement.")
    @commands.has_permissions(administrator=True)
    async def testwelcome(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        guild = ctx.guild
        member_count = len(guild.members)
        
        await ctx.defer()
        try:
            avatar_bytes = await target.display_avatar.with_format("png").with_size(256).read()
            card_bytes = await asyncio.to_thread(
                create_grand_welcome_image,
                avatar_bytes,
                target.display_name,
                member_count,
                guild.name
            )
            card_file = discord.File(card_bytes, filename="grand_welcome_preview.png")
            
            embed = discord.Embed(
                title=f"🌸 GRAND ROYAL WELCOME TO {guild.name.upper()}! 🌸",
                description=(
                    f"A heartfelt royal welcome to {target.mention}! You are officially part of the **`🌸 ┊ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘`**! 🎉✨\n\n"
                    f"👑 **You are our honored Member #{member_count}**\n\n"
                    f"🎁 **Starter Gift Credited:**\n"
                    f"• **+100 Apex Coins** 🪙 deposited to your wallet (`/balance`)\n"
                    f"• **+50 Starter XP** ✨ added to your rank profile (`/rank`)\n\n"
                    f"**🚀 Explore The Community:**\n"
                    f"1️⃣ **Rules & Guidelines:** Check `#rules-and-guidelines`\n"
                    f"2️⃣ **Self Roles:** Pick custom colors and gaming tags in `#self-roles`\n"
                    f"3️⃣ **Hangout:** Come say hi to everyone in `#general-chat`!\n"
                ),
                color=config.COLOR_PRIMARY
            )
            embed.set_image(url="attachment://grand_welcome_preview.png")
            embed.set_footer(text=f"User ID: {target.id} • Grand Royal Welcome Preview 💗", icon_url=config.RAI_ICON_URL)
            
            view = WelcomeQuickActionsView(target)
            await ctx.send(
                content=f"🎉 **[TEST PREVIEW] Everyone welcome {target.mention} to {guild.name}!** 🌸✨",
                embed=embed,
                file=card_file,
                view=view
            )
        except Exception as e:
            await ctx.send(f"❌ Failed to generate preview: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
