import os
import io
import textwrap
import unicodedata
import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image, ImageDraw, ImageFont, ImageOps

import config

logger = logging.getLogger("Quotes")


def sanitize_text(text: str) -> str:
    norm = unicodedata.normalize('NFKD', text)
    clean = "".join([c for c in norm if ord(c) < 128 or c.isalnum() or c in " -_!.,?':;/()[]{}@#%&*+=~"]).strip()
    return clean if clean else "..."


def render_quote_image(avatar_bytes: bytes, author_name: str, quote_text: str, timestamp_str: str) -> io.BytesIO:
    WIDTH, HEIGHT = 900, 360
    img = Image.new("RGBA", (WIDTH, HEIGHT), color=(12, 10, 20, 255))
    draw = ImageDraw.Draw(img)

    # Ambient glows
    for r in range(140, 0, -14):
        alpha = int(24 * (1 - r / 140))
        draw.ellipse([WIDTH - 80 - r, 80 - r, WIDTH - 80 + r, 80 + r], fill=(255, 105, 180, alpha))
        draw.ellipse([80 - r, HEIGHT - 80 - r, 80 + r, HEIGHT - 80 + r], fill=(0, 229, 255, alpha))

    # Outer border
    draw.rounded_rectangle([12, 12, WIDTH - 12, HEIGHT - 12], radius=24, outline=(255, 105, 180, 200), width=3)
    draw.rounded_rectangle([18, 18, WIDTH - 18, HEIGHT - 18], radius=20, outline=(255, 215, 0, 140), width=2)

    # Avatar
    try:
        raw_avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
        raw_avatar = raw_avatar.resize((150, 150), Image.Resampling.LANCZOS)
        mask = Image.new("L", (150, 150), 0)
        mask_draw = ImageDraw.Draw(mask)
        mask_draw.ellipse((0, 0, 150, 150), fill=255)
        avatar_circle = ImageOps.fit(raw_avatar, mask.size, centering=(0.5, 0.5))
        avatar_circle.putalpha(mask)

        # Concentric glow rings
        draw.ellipse([46, 101, 204, 259], outline=(255, 215, 0, 200), width=4)
        draw.ellipse([50, 105, 200, 255], outline=(0, 229, 255, 220), width=3)
        img.paste(avatar_circle, (50, 105), avatar_circle)
    except Exception as e:
        logger.warning(f"Could not render avatar: {e}")

    # Fonts
    font_large = None
    font_quote = None
    font_meta = None
    system_fonts = ["segoeui.ttf", "arial.ttf", "tahoma.ttf", "calibri.ttf"]
    for f in system_fonts:
        try:
            font_large = ImageFont.truetype(f, 32)
            font_quote = ImageFont.truetype(f, 22)
            font_meta = ImageFont.truetype(f, 16)
            break
        except Exception:
            continue

    if not font_large:
        font_large = font_quote = font_meta = ImageFont.load_default()

    # Quotation Mark
    draw.text((230, 45), "“", fill=(255, 105, 180, 230), font=font_large)

    # Text wrapping
    clean_quote = sanitize_text(quote_text)
    lines = textwrap.wrap(clean_quote, width=42)
    display_lines = lines[:5]
    if len(lines) > 5:
        display_lines[-1] = display_lines[-1][:36] + "..."

    y_offset = 85
    for line in display_lines:
        draw.text((250, y_offset), line, fill=(255, 255, 255, 255), font=font_quote)
        y_offset += 32

    # Closing quotation mark
    draw.text((250 + (len(display_lines[-1]) * 10), y_offset - 25), "”", fill=(255, 105, 180, 230), font=font_large)

    # Author Name & Server watermark
    clean_author = sanitize_text(author_name)
    draw.text((250, HEIGHT - 75), f"— {clean_author}", fill=(255, 215, 0, 255), font=font_large)
    draw.text((250, HEIGHT - 40), f"{timestamp_str} • RAI VIBES Hall of Fame", fill=(160, 150, 180, 220), font=font_meta)

    out = io.BytesIO()
    img.save(out, format="PNG")
    out.seek(0)
    return out


class Quotes(commands.Cog):
    """Aesthetic Message Quote Cards for Hall of Fame & Media Gallery."""
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        # Context Menu
        self.quote_menu = app_commands.ContextMenu(
            name="Create Quote Card",
            callback=self.context_quote_card
        )
        self.bot.tree.add_command(self.quote_menu)

    def cog_unload(self):
        self.bot.tree.remove_command(self.quote_menu.name, type=self.quote_menu.type)

    async def generate_and_post_quote(self, interaction: discord.Interaction, message: discord.Message):
        if not message.content and not message.embeds:
            return await interaction.followup.send("❌ That message doesn't contain text to quote!", ephemeral=True)

        text = message.content
        if not text and message.embeds:
            text = message.embeds[0].description or message.embeds[0].title or "Embedded Message"

        avatar_bytes = await message.author.display_avatar.read()
        time_str = message.created_at.strftime("%b %d, %Y at %H:%M UTC")

        image_stream = render_quote_image(
            avatar_bytes=avatar_bytes,
            author_name=message.author.display_name,
            quote_text=text,
            timestamp_str=time_str
        )

        discord_file = discord.File(image_stream, filename="quote_card.png")
        embed = discord.Embed(
            title="✨ MEMORABLE SERVER QUOTE",
            description=f"Quoted from {message.author.mention} in {message.channel.mention} • [Jump to Message]({message.jump_url})",
            color=0xFF69B4
        )
        embed.set_image(url="attachment://quote_card.png")
        embed.set_footer(text=f"Preserved by {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        # Target gallery channel: #📸・ᴍᴇᴅɪᴀ-ɢᴀʟʟᴇʀʏ or current channel
        gallery = (
            discord.utils.get(interaction.guild.text_channels, name="📸・ᴍᴇᴅɪᴀ-ɢᴀʟʟᴇʀʏ")
            or discord.utils.get(interaction.guild.text_channels, name="media-gallery")
            or interaction.channel
        )

        posted_msg = await gallery.send(embed=embed, file=discord_file)
        if gallery.id != interaction.channel.id:
            await interaction.followup.send(f"✅ Quote card posted in {gallery.mention}! [View Quote]({posted_msg.jump_url})", ephemeral=True)
        else:
            await interaction.followup.send("✅ Quote card created!", ephemeral=True)

    async def context_quote_card(self, interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer(ephemeral=True)
        await self.generate_and_post_quote(interaction, message)

    @app_commands.command(name="quote", description="Turn a funny or memorable message into an aesthetic canvas card!")
    @app_commands.describe(message_id="ID or jump link of the message to quote")
    async def quote_slash(self, interaction: discord.Interaction, message_id: str):
        await interaction.response.defer(ephemeral=True)
        # Extract message ID
        cleaned_id = message_id.split("/")[-1].strip()
        try:
            msg_int_id = int(cleaned_id)
            target_msg = await interaction.channel.fetch_message(msg_int_id)
        except Exception:
            return await interaction.followup.send("❌ Could not find that message in this channel. Make sure you provide a valid message ID or link!", ephemeral=True)

        await self.generate_and_post_quote(interaction, target_msg)


async def setup(bot: commands.Bot):
    await bot.add_cog(Quotes(bot))
