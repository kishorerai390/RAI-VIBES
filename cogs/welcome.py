import io
import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
from PIL import Image, ImageDraw, ImageFont, ImageOps

import config

logger = logging.getLogger("Welcome")

def create_welcome_image(avatar_bytes: bytes, username: str, member_count: int, guild_name: str) -> io.BytesIO:
    """Generates an aesthetic 800x300 Cyber-Pink dynamic welcome card with user avatar."""
    WIDTH, HEIGHT = 800, 300
    
    # 1. Base Image with Deep Gradient Dark Background
    img = Image.new("RGBA", (WIDTH, HEIGHT), color=(13, 11, 20, 255))
    draw = ImageDraw.Draw(img)

    # 2. Cyber-Pink / Neon Blue Glow Decorative Accents
    # Draw soft glowing background circles
    for r in range(120, 0, -10):
        alpha = int(25 * (1 - r / 120))
        draw.ellipse([50 - r, 50 - r, 50 + r, 50 + r], fill=(255, 105, 180, alpha))
        draw.ellipse([WIDTH - 50 - r, HEIGHT - 50 - r, WIDTH - 50 + r, HEIGHT - 50 + r], fill=(0, 240, 255, alpha))

    # Outer Cyber Frame Border
    draw.rounded_rectangle([10, 10, WIDTH - 10, HEIGHT - 10], radius=24, outline=(255, 105, 180, 180), width=3)
    draw.rounded_rectangle([15, 15, WIDTH - 15, HEIGHT - 15], radius=20, outline=(30, 24, 45, 255), width=2)
    
    # Top Accent Ribbon
    draw.rectangle([100, 10, WIDTH - 100, 14], fill=(255, 20, 147, 220))

    # 3. Avatar Processing (Circular Crop with Glowing Double Ring)
    try:
        raw_avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        raw_avatar = raw_avatar.resize((160, 160), Image.Resampling.LANCZOS)
        
        # Circular Mask
        mask = Image.new("L", (160, 160), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 160, 160), fill=255)
        
        avatar_circle = ImageOps.fit(raw_avatar, mask.size, centering=(0.5, 0.5))
        avatar_circle.putalpha(mask)

        # Draw Avatar Glow Ring
        draw.ellipse([55, 65, 225, 235], outline=(255, 20, 147, 255), width=5)
        draw.ellipse([58, 68, 222, 232], outline=(0, 240, 255, 200), width=2)
        
        # Paste Circular Avatar
        img.paste(avatar_circle, (60, 70), avatar_circle)
    except Exception as e:
        logger.warning(f"Could not render avatar image: {e}")
        draw.ellipse([60, 70, 220, 230], fill=(255, 105, 180, 255))

    # 4. Text Content Rendering
    try:
        font_sub = ImageFont.truetype("arialbd.ttf", 20)
        font_name = ImageFont.truetype("arialbd.ttf", 36)
        font_count = ImageFont.truetype("arial.ttf", 22)
        font_tags = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font_sub = ImageFont.load_default()
        font_name = font_sub
        font_count = font_sub
        font_tags = font_sub

    # Header: "WELCOME TO <GUILD>"
    draw.text((250, 65), f"WELCOME TO {guild_name.upper()}", fill=(255, 105, 180, 255), font=font_sub)
    
    # Truncate username if too long
    clean_name = username if len(username) <= 16 else f"{username[:14]}..."
    draw.text((250, 95), clean_name, fill=(255, 255, 255, 255), font=font_name)
    
    # Member Count Tag Badge
    badge_bg = [250, 150, 520, 188]
    draw.rounded_rectangle(badge_bg, radius=12, fill=(25, 20, 38, 255), outline=(0, 240, 255, 160), width=2)
    draw.text((265, 156), f"MEMBER #{member_count}", fill=(0, 240, 255, 255), font=font_count)

    # Feature Highlights Badges
    pills = ["🌸 RAI FAMILY", "🎧 RYTHM VIBES", "🍿 CINEMA HUB", "🛡️ SECURE"]
    px = 250
    for pill in pills:
        pill_len = len(pill) * 8 + 18
        draw.rounded_rectangle([px, 210, px + pill_len, 240], radius=8, fill=(38, 28, 55, 220), outline=(255, 105, 180, 120), width=1)
        draw.text((px + 8, 217), pill, fill=(240, 220, 255, 230), font=font_tags)
        px += pill_len + 10

    # 5. Export to BytesIO
    output = io.BytesIO()
    img.save(output, format="PNG")
    output.seek(0)
    return output


class Welcome(commands.Cog):
    """Aesthetic Dynamic Welcome Cards, Dynamic Member Count & Onboarding."""
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

        # 2. Update Server Stats Channel if present
        for vc in guild.voice_channels:
            if "members:" in vc.name.lower() or "member count" in vc.name.lower():
                try:
                    await vc.edit(name=f"👥・Members: {member_count}")
                except Exception:
                    pass

        # 3. Find Welcome Channel & Send Dynamic Canvas Card
        welcome_chan = (
            discord.utils.get(guild.text_channels, name="welcome") or
            discord.utils.get(guild.text_channels, name="👋・welcome") or
            discord.utils.get(guild.text_channels, name="╭・「👋」welcome") or
            discord.utils.get(guild.text_channels, name="general-chat")
        )

        if welcome_chan:
            rules_chan = discord.utils.get(guild.text_channels, name="rules") or discord.utils.get(guild.text_channels, name="├・「📜」rules-and-guidelines")
            roles_chan = discord.utils.get(guild.text_channels, name="self-roles") or discord.utils.get(guild.text_channels, name="├・「⭐」self-roles")

            rules_mention = rules_chan.mention if rules_chan else "#rules"
            roles_mention = roles_chan.mention if roles_chan else "#self-roles"

            # Render Dynamic Canvas Card
            try:
                avatar_bytes = await member.display_avatar.with_format("png").with_size(256).read()
                card_bytes = await asyncio.to_thread(
                    create_welcome_image,
                    avatar_bytes,
                    member.display_name,
                    member_count,
                    guild.name
                )
                card_file = discord.File(card_bytes, filename="welcome.png")
            except Exception as e:
                logger.error(f"Failed to generate welcome image: {e}")
                card_file = None

            embed = discord.Embed(
                title=f"🌸 WELCOME TO {guild.name.upper()}! 🌸",
                description=(
                    f"Hey {member.mention}, welcome to the family! You've been granted the **`🌸 ┊ 𝐑𝐀𝐈 𝐅𝐀𝐌𝐈𝐋𝐘`** role! 🎉\n\n"
                    f"✨ **You are Member #{member_count}**\n\n"
                    f"**🚀 Quick Start:**\n"
                    f"1️⃣ Read server guidelines in {rules_mention}\n"
                    f"2️⃣ Pick optional movie/music pings in {roles_mention}\n"
                    f"3️⃣ Hang out in voice lounges or chat in **`#general-chat`**!\n"
                ),
                color=config.COLOR_PRIMARY
            )
            if card_file:
                embed.set_image(url="attachment://welcome.png")
            else:
                embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text=f"User ID: {member.id} • Have fun in RAI FAM!", icon_url=config.RAI_ICON_URL)

            try:
                if card_file:
                    await welcome_chan.send(content=f"👋 Welcome to RAI FAM, {member.mention}!", embed=embed, file=card_file)
                else:
                    await welcome_chan.send(content=f"👋 Welcome to RAI FAM, {member.mention}!", embed=embed)
            except Exception as e:
                logger.error(f"Failed to send welcome message: {e}")

        # 4. Anti-Alt Account Check
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

    @commands.hybrid_command(name="testwelcome", description="Preview the dynamic Cyber-Pink welcome card.")
    @commands.has_permissions(administrator=True)
    async def testwelcome(self, ctx: commands.Context, member: discord.Member = None):
        target = member or ctx.author
        guild = ctx.guild
        member_count = len(guild.members)
        
        await ctx.defer()
        try:
            avatar_bytes = await target.display_avatar.with_format("png").with_size(256).read()
            card_bytes = await asyncio.to_thread(
                create_welcome_image,
                avatar_bytes,
                target.display_name,
                member_count,
                guild.name
            )
            card_file = discord.File(card_bytes, filename="welcome_preview.png")
            
            embed = discord.Embed(
                title=f"🌸 WELCOME TO {guild.name.upper()}! 🌸",
                description=f"Hey {target.mention}, welcome to the family! (Preview Mode)\n✨ **Member #{member_count}**",
                color=config.COLOR_PRIMARY
            )
            embed.set_image(url="attachment://welcome_preview.png")
            embed.set_footer(text=f"User ID: {target.id} • Dynamic Canvas Preview", icon_url=config.RAI_ICON_URL)
            await ctx.send(content=f"🎨 **Dynamic Welcome Card Preview for {target.mention}:**", embed=embed, file=card_file)
        except Exception as e:
            await ctx.send(f"❌ Failed to generate preview: {e}")


async def setup(bot: commands.Bot):
    await bot.add_cog(Welcome(bot))
