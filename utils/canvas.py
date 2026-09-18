import io
import math
import random
from typing import Optional, List, Tuple, Union
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

def _get_font(name: str, size: int):
    candidates = [
        f"{name}.ttf",
        "segoeuib.ttf" if "bd" in name or "bold" in name else "segoeui.ttf",
        "arialbd.ttf" if "bd" in name or "bold" in name else "arial.ttf",
        "DejaVuSans-Bold.ttf" if "bd" in name or "bold" in name else "DejaVuSans.ttf"
    ]
    for c in candidates:
        try:
            return ImageFont.truetype(c, size)
        except Exception:
            continue
    return ImageFont.load_default()

def _crop_circular_avatar(avatar_bytes: Optional[bytes], size: int) -> Image.Image:
    """Crops avatar bytes into a smooth antialiased circular image with fallback."""
    if avatar_bytes:
        try:
            avatar = Image.open(io.BytesIO(avatar_bytes)).convert("RGBA")
            avatar = avatar.resize((size, size), Image.Resampling.LANCZOS)
        except Exception:
            avatar = Image.new("RGBA", (size, size), color=(255, 20, 147, 255))
    else:
        avatar = Image.new("RGBA", (size, size), color=(255, 20, 147, 255))

    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size, size), fill=255)

    circle = ImageOps.fit(avatar, (size, size), centering=(0.5, 0.5))
    circle.putalpha(mask)
    return circle

def _draw_3d_glass_panel(
    draw: ImageDraw.Draw,
    bbox: Tuple[int, int, int, int],
    radius: int = 24,
    fill: Tuple[int, int, int, int] = (16, 12, 28, 220),
    border_color: Tuple[int, int, int, int] = (255, 0, 128, 180),
    highlight_color: Tuple[int, int, int, int] = (255, 255, 255, 90),
    shadow_depth: int = 14
):
    """Draws a floating 3D glassmorphic panel with ambient occlusion shadow and specular edges."""
    x1, y1, x2, y2 = bbox
    for s in range(shadow_depth, 0, -2):
        s_alpha = int(45 * (1 - s / shadow_depth))
        draw.rounded_rectangle(
            [x1 - s // 2, y1 + s // 2, x2 + s // 2, y2 + s + 4],
            radius=radius + s // 2,
            fill=(0, 0, 0, s_alpha)
        )
    draw.rounded_rectangle([x1, y1, x2, y2], radius=radius, fill=fill, outline=border_color, width=2)
    draw.line([(x1 + radius, y1 + 1), (x2 - radius, y1 + 1)], fill=highlight_color, width=1)
    draw.line([(x1 + 1, y1 + radius), (x1 + 1, y2 - radius)], fill=highlight_color, width=1)
    draw.line([(x1 + radius, y2 - 1), (x2 - radius, y2 - 1)], fill=(0, 0, 0, 140), width=1)
    draw.line([(x2 - 1, y1 + radius), (x2 - 1, y2 - radius)], fill=(0, 0, 0, 140), width=1)

def _draw_3d_vinyl(
    img: Image.Image,
    cx: int,
    cy: int,
    radius: int,
    thumb_img: Optional[Image.Image] = None
):
    """Renders an ultra-realistic 3D grooved vinyl record with anisotropic light sheen."""
    size = radius * 2 + 30
    v_img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    v_draw = ImageDraw.Draw(v_img)
    vx, vy = size // 2, size // 2

    for s in range(16, 0, -3):
        v_draw.ellipse(
            [vx - radius - s, vy - radius - s + 6, vx + radius + s, vy + radius + s + 6],
            fill=(0, 0, 0, int(40 * (1 - s / 16)))
        )

    v_draw.ellipse([vx - radius, vy - radius, vx + radius, vy + radius], fill=(12, 12, 16, 255), outline=(90, 85, 110, 200), width=2)

    groove_colors = [
        (26, 25, 34, 255),
        (38, 36, 50, 255),
        (20, 19, 28, 255),
        (45, 42, 60, 255),
        (28, 27, 38, 255)
    ]
    for r in range(radius - 6, radius // 3, -4):
        col = groove_colors[r % len(groove_colors)]
        v_draw.ellipse([vx - r, vy - r, vx + r, vy + r], outline=col, width=1)

    sweep_mask = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    s_draw = ImageDraw.Draw(sweep_mask)
    s_draw.polygon([(vx, vy), (vx - radius + 10, vy - radius // 2), (vx - radius // 2, vy - radius + 10)], fill=(255, 255, 255, 26))
    s_draw.polygon([(vx, vy), (vx + radius - 10, vy + radius // 2), (vx + radius // 2, vy + radius - 10)], fill=(255, 255, 255, 26))
    v_img.alpha_composite(sweep_mask)

    label_r = radius // 3
    if thumb_img:
        try:
            resized_thumb = thumb_img.resize((label_r * 2, label_r * 2), Image.Resampling.LANCZOS)
            mask_l = Image.new("L", (label_r * 2, label_r * 2), 0)
            ImageDraw.Draw(mask_l).ellipse((0, 0, label_r * 2, label_r * 2), fill=255)
            resized_thumb.putalpha(mask_l)
            v_img.paste(resized_thumb, (vx - label_r, vy - label_r), resized_thumb)
        except Exception:
            v_draw.ellipse([vx - label_r, vy - label_r, vx + label_r, vy + label_r], fill=(255, 0, 128, 240))
    else:
        v_draw.ellipse([vx - label_r, vy - label_r, vx + label_r, vy + label_r], fill=(255, 0, 128, 240))

    v_draw.ellipse([vx - label_r, vy - label_r, vx + label_r, vy + label_r], outline=(255, 215, 0, 220), width=2)
    hole_r = 8
    v_draw.ellipse([vx - hole_r, vy - hole_r, vx + hole_r, vy + hole_r], fill=(10, 8, 16, 255), outline=(255, 215, 0, 255), width=2)

    img.paste(v_img, (cx - size // 2, cy - size // 2), v_img)

def generate_rank_card(
    avatar_bytes: Optional[bytes],
    username: str,
    level: int,
    current_xp: int,
    next_level_xp: int,
    rank: int,
    coins: int,
    rep: int,
    messages: int
) -> io.BytesIO:
    """Generates a luxury 1000x350 3D Cyber-Neon Glassmorphic Rank Card."""
    W, H = 1000, 350
    img = Image.new("RGBA", (W, H), color=(10, 8, 18, 255))
    draw = ImageDraw.Draw(img)

    for r in range(220, 0, -20):
        alpha = int(32 * (1 - r / 220))
        draw.ellipse([90 - r, 90 - r, 90 + r, 90 + r], fill=(255, 0, 128, alpha))
        draw.ellipse([W - 120 - r, H - 80 - r, W - 120 + r, H - 80 + r], fill=(0, 240, 255, alpha))

    _draw_3d_glass_panel(
        draw,
        (16, 16, W - 16, H - 16),
        radius=24,
        fill=(15, 12, 26, 225),
        border_color=(255, 0, 128, 180),
        highlight_color=(255, 255, 255, 80),
        shadow_depth=14
    )

    avatar_size = 180
    avatar = _crop_circular_avatar(avatar_bytes, avatar_size)
    ax, ay = 60, (H - avatar_size) // 2

    for s in range(12, 0, -2):
        draw.ellipse([ax - s, ay - s + 4, ax + avatar_size + s, ay + avatar_size + s + 4], fill=(0, 0, 0, int(50 * (1 - s / 12))))

    draw.ellipse([ax - 8, ay - 8, ax + avatar_size + 8, ay + avatar_size + 8], outline=(255, 0, 128, 230), width=4)
    draw.ellipse([ax - 4, ay - 4, ax + avatar_size + 4, ay + avatar_size + 4], outline=(0, 240, 255, 200), width=2)
    img.paste(avatar, (ax, ay), avatar)

    draw = ImageDraw.Draw(img)

    font_title = _get_font("arialbd", 42)
    font_stat = _get_font("arialbd", 19)
    font_small = _get_font("arialbd", 15)

    clean_name = username[:18]
    draw.text((280, 48), clean_name, font=font_title, fill=(255, 255, 255, 255))
    name_len = int(draw.textlength(clean_name, font=font_title))

    draw.rounded_rectangle([280 + name_len + 16, 58, 280 + name_len + 150, 86], radius=8, fill=(255, 0, 128, 45), outline=(255, 0, 128, 220), width=1)
    draw.text((280 + name_len + 28, 64), "RAI CITIZEN", font=font_small, fill=(255, 0, 128, 255))

    rank_badge = f"GLOBAL RANK #{rank}"
    lvl_badge = f"LEVEL {level}"

    draw.rounded_rectangle([280, 108, 445, 144], radius=10, fill=(255, 215, 0, 40), outline=(255, 215, 0, 240), width=1)
    draw.line([(282, 109), (443, 109)], fill=(255, 255, 255, 180), width=1)
    draw.text((298, 116), rank_badge, font=font_small, fill=(255, 215, 0, 255))

    draw.rounded_rectangle([460, 108, 595, 144], radius=10, fill=(0, 240, 255, 40), outline=(0, 240, 255, 240), width=1)
    draw.line([(462, 109), (593, 109)], fill=(255, 255, 255, 180), width=1)
    draw.text((478, 116), lvl_badge, font=font_small, fill=(0, 240, 255, 255))

    stat_box_x, stat_box_y, stat_box_w, stat_box_h = 280, 160, 655, 52
    draw.rounded_rectangle([stat_box_x, stat_box_y, stat_box_x + stat_box_w, stat_box_y + stat_box_h], radius=12, fill=(22, 17, 36, 210), outline=(45, 36, 68, 255), width=1)
    draw.line([(stat_box_x + 10, stat_box_y + 1), (stat_box_x + stat_box_w - 10, stat_box_y + 1)], fill=(255, 255, 255, 40), width=1)

    s1 = f"COINS: {coins:,}"
    s2 = f"REP: +{rep}"
    s3 = f"MSGS: {messages:,}"
    draw.text((stat_box_x + 24, stat_box_y + 15), s1, font=font_stat, fill=(255, 215, 0, 255))
    draw.text((stat_box_x + 240, stat_box_y + 15), s2, font=font_stat, fill=(255, 0, 128, 255))
    draw.text((stat_box_x + 440, stat_box_y + 15), s3, font=font_stat, fill=(0, 240, 255, 255))

    bar_x, bar_y, bar_w, bar_h = 280, 235, 655, 26
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=13, fill=(24, 18, 38, 255), outline=(48, 38, 72, 255), width=1)
    draw.line([(bar_x + 8, bar_y + 1), (bar_x + bar_w - 8, bar_y + 1)], fill=(12, 9, 20, 255), width=1)

    pct = min(1.0, max(0.0, current_xp / max(1, next_level_xp)))
    fill_w = int(bar_w * pct)
    if fill_w > 16:
        draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], radius=13, fill=(255, 0, 128, 255))
        draw.line([(bar_x + 6, bar_y + 2), (bar_x + fill_w - 6, bar_y + 2)], fill=(255, 180, 220, 220), width=1)
        draw.ellipse([bar_x + fill_w - 18, bar_y + 2, bar_x + fill_w - 2, bar_y + bar_h - 2], fill=(0, 240, 255, 255))

    pct_text = f"{int(pct * 100)}%"
    xp_text = f"XP: {current_xp:,} / {next_level_xp:,}"
    draw.text((bar_x, bar_y + 34), xp_text, font=font_small, fill=(190, 190, 215, 255))
    draw.text((bar_x + bar_w - int(draw.textlength(pct_text, font=font_small)), bar_y + 34), pct_text, font=font_small, fill=(0, 240, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def generate_profile_codex(
    avatar_bytes: Optional[bytes],
    username: str,
    level: int,
    current_xp: int,
    req_xp: int,
    coins: Union[int, str],
    rep: int,
    voice_hrs: float,
    pet_str: str,
    clan_str: str,
    join_date_str: str
) -> io.BytesIO:
    """Generates an ultra-luxurious 1200x650 3D Holographic Citizen Identity Codex."""
    W, H = 1200, 650
    img = Image.new("RGBA", (W, H), color=(9, 7, 15, 255))
    draw = ImageDraw.Draw(img)

    for r in range(280, 0, -25):
        alpha = int(30 * (1 - r / 280))
        draw.ellipse([120 - r, 120 - r, 120 + r, 120 + r], fill=(255, 0, 128, alpha))
        draw.ellipse([W - 120 - r, 120 - r, W - 120 + r, 120 + r], fill=(0, 240, 255, alpha))
        draw.ellipse([W // 2 - r, H - 80 - r, W // 2 + r, H - 80 + r], fill=(255, 215, 0, int(alpha * 0.4)))

    _draw_3d_glass_panel(
        draw,
        (20, 20, W - 20, H - 20),
        radius=28,
        fill=(14, 11, 24, 230),
        border_color=(255, 0, 128, 190),
        highlight_color=(255, 255, 255, 85),
        shadow_depth=16
    )

    draw.rectangle([100, 20, W - 100, 28], fill=(255, 0, 128, 255))
    draw.rectangle([250, 28, W - 250, 32], fill=(0, 240, 255, 255))

    font_head = _get_font("arialbd", 38)
    font_sub = _get_font("arialbd", 20)
    font_label = _get_font("arialbd", 15)
    font_body = _get_font("arialbd", 22)
    font_small = _get_font("arial", 15)

    draw.text((60, 48), "RAI CITIZEN IDENTITY CODEX // VERIFIED SYSTEM PROFILE", font=font_label, fill=(255, 0, 128, 255))

    avatar_size = 200
    avatar = _crop_circular_avatar(avatar_bytes, avatar_size)
    ax, ay = 60, 95

    for s in range(12, 0, -2):
        draw.ellipse([ax - s, ay - s + 4, ax + avatar_size + s, ay + avatar_size + s + 4], fill=(0, 0, 0, int(50 * (1 - s / 12))))

    draw.ellipse([ax - 8, ay - 8, ax + avatar_size + 8, ay + avatar_size + 8], outline=(0, 240, 255, 240), width=4)
    draw.ellipse([ax - 4, ay - 4, ax + avatar_size + 4, ay + avatar_size + 4], outline=(255, 0, 128, 180), width=2)
    img.paste(avatar, (ax, ay), avatar)

    draw = ImageDraw.Draw(img)

    chip_x, chip_y, chip_w, chip_h = 60, 315, 200, 42
    draw.rounded_rectangle([chip_x, chip_y, chip_x + chip_w, chip_y + chip_h], radius=10, fill=(0, 240, 255, 35), outline=(0, 240, 255, 220), width=1)
    draw.line([(chip_x + 4, chip_y + 1), (chip_x + chip_w - 4, chip_y + 1)], fill=(255, 255, 255, 140), width=1)
    draw.text((chip_x + 18, chip_y + 12), "SECURE CITIZEN ID", font=font_label, fill=(0, 240, 255, 255))

    draw.text((295, 90), str(username or "RAI Citizen")[:20], font=font_head, fill=(255, 255, 255, 255))
    draw.text((295, 142), f"Level {level} Elite Citizen • Member Since: {join_date_str}", font=font_small, fill=(185, 185, 215, 255))

    if isinstance(coins, str):
        coin_display = coins
    elif isinstance(coins, (int, float)) and coins >= 999999999:
        coin_display = "INFINITY (Owner)"
    elif isinstance(coins, (int, float)):
        coin_display = f"{int(coins):,} COINS"
    else:
        coin_display = str(coins)

    boxes = [
        ("LEVEL & PROGRESS", f"LVL {level} ({current_xp:,}/{req_xp:,})", 295, 190, 420, 95, (255, 0, 128)),
        ("VAULT TREASURY", coin_display, 740, 190, 420, 95, (255, 215, 0)),
        ("VOICE SANCTUARY", f"{voice_hrs} Hours Logged", 295, 305, 420, 95, (0, 240, 255)),
        ("COMMUNITY INFLUENCE", f"+{rep} Rep Points", 740, 305, 420, 95, (255, 0, 128)),
        ("PET COMPANION", str(pet_str or 'None')[:28].upper(), 295, 420, 420, 95, (0, 240, 255)),
        ("SQUAD & GUILD", str(clan_str or 'Solo Operative')[:28].upper(), 740, 420, 420, 95, (255, 215, 0)),
    ]

    for label, val, bx, by, bw, bh, acc in boxes:
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=14, fill=(20, 16, 32, 220), outline=(48, 38, 70, 255), width=1)
        draw.line([(bx + 8, by + 1), (bx + bw - 8, by + 1)], fill=(255, 255, 255, 40), width=1)
        draw.text((bx + 18, by + 16), label, font=font_label, fill=acc)
        draw.text((bx + 18, by + 48), val, font=font_body, fill=(245, 245, 255, 255))

    bar_x, bar_y, bar_w, bar_h = 295, 545, 865, 20
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=10, fill=(24, 18, 38, 255), outline=(48, 38, 72, 255), width=1)
    draw.line([(bar_x + 6, bar_y + 1), (bar_x + bar_w - 6, bar_y + 1)], fill=(12, 9, 20, 255), width=1)

    pct = min(1.0, max(0.0, current_xp / max(1, req_xp)))
    fw = int(bar_w * pct)
    if fw > 10:
        draw.rounded_rectangle([bar_x, bar_y, bar_x + fw, bar_y + bar_h], radius=10, fill=(0, 240, 255, 255))
        draw.line([(bar_x + 4, bar_y + 2), (bar_x + fw - 4, bar_y + 2)], fill=(255, 255, 255, 180), width=1)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def generate_nowplaying_card(
    thumbnail_bytes: Optional[bytes],
    title: str,
    artist: str,
    duration_sec: int,
    elapsed_sec: int,
    requester_name: str
) -> io.BytesIO:
    """Generates an ultra-luxe 1000x380 3D Glassmorphic Now Playing Card with an extruding 3D Vinyl record."""
    W, H = 1000, 380
    img = Image.new("RGBA", (W, H), color=(10, 8, 18, 255))

    thumb_img = None
    if thumbnail_bytes:
        try:
            thumb_img = Image.open(io.BytesIO(thumbnail_bytes)).convert("RGBA")
            bg_art = thumb_img.resize((W, H), Image.Resampling.LANCZOS)
            bg_art = bg_art.filter(ImageFilter.GaussianBlur(radius=40))
            darken = Image.new("RGBA", (W, H), color=(5, 4, 10, 195))
            bg_art.paste(darken, (0, 0), darken)
            img.paste(bg_art, (0, 0))
        except Exception:
            pass

    draw = ImageDraw.Draw(img)

    for r in range(260, 0, -20):
        alpha = int(35 * (1 - r / 260))
        draw.ellipse([180 - r, 190 - r, 180 + r, 190 + r], fill=(255, 0, 128, alpha))
        draw.ellipse([W - 150 - r, 190 - r, W - 150 + r, 190 + r], fill=(0, 240, 255, int(alpha * 0.8)))

    _draw_3d_glass_panel(
        draw,
        (18, 18, W - 18, H - 18),
        radius=26,
        fill=(14, 11, 24, 220),
        border_color=(255, 0, 128, 170),
        highlight_color=(255, 255, 255, 80),
        shadow_depth=16
    )

    vinyl_cx = 295
    vinyl_cy = 190
    vinyl_r = 135
    _draw_3d_vinyl(img, vinyl_cx, vinyl_cy, vinyl_r, thumb_img)

    sleeve_size = 230
    sx, sy = 55, (H - sleeve_size) // 2

    for s in range(12, 0, -2):
        draw.rounded_rectangle([sx + 4, sy + 4, sx + sleeve_size + s, sy + sleeve_size + s], radius=18, fill=(0, 0, 0, int(60 * (1 - s / 12))))

    if thumb_img:
        try:
            art = thumb_img.resize((sleeve_size, sleeve_size), Image.Resampling.LANCZOS)
            mask = Image.new("L", (sleeve_size, sleeve_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, sleeve_size, sleeve_size], radius=16, fill=255)
            art.putalpha(mask)
            img.paste(art, (sx, sy), art)
        except Exception:
            draw.rounded_rectangle([sx, sy, sx + sleeve_size, sy + sleeve_size], radius=16, fill=(255, 0, 128, 160))
    else:
        draw.rounded_rectangle([sx, sy, sx + sleeve_size, sy + sleeve_size], radius=16, fill=(28, 20, 44, 255))
        draw.ellipse([sx + 40, sy + 40, sx + sleeve_size - 40, sy + sleeve_size - 40], outline=(255, 0, 128, 200), width=3)
        draw.text((sx + 65, sy + 105), "RAI VIBES", font=_get_font("arialbd", 18), fill=(255, 255, 255, 255))

    draw.rounded_rectangle([sx, sy, sx + sleeve_size, sy + sleeve_size], radius=16, outline=(255, 255, 255, 110), width=1)
    draw.line([(sx + 3, sy + 16), (sx + 3, sy + sleeve_size - 16)], fill=(255, 255, 255, 160), width=2)

    draw = ImageDraw.Draw(img)

    font_badge = _get_font("arialbd", 14)
    font_title = _get_font("arialbd", 34)
    font_artist = _get_font("arialbd", 22)
    font_time = _get_font("arialbd", 16)

    tx = 445

    draw.rounded_rectangle([tx, 50, tx + 240, 78], radius=8, fill=(255, 0, 128, 50), outline=(255, 0, 128, 220), width=1)
    draw.text((tx + 14, 56), "LIVE :: 3D HI-FI AUDIO", font=font_badge, fill=(255, 0, 128, 255))

    req_str = f"REQ: {requester_name[:20]}"
    req_w = int(draw.textlength(req_str, font=font_badge)) + 24
    draw.rounded_rectangle([tx + 250, 50, tx + 250 + req_w, 78], radius=8, fill=(0, 240, 255, 35), outline=(0, 240, 255, 180), width=1)
    draw.text((tx + 262, 56), req_str, font=font_badge, fill=(0, 240, 255, 240))

    clean_title = title[:32] if title else "Unknown Stream"
    draw.text((tx, 94), clean_title, font=font_title, fill=(255, 255, 255, 255))

    clean_artist = artist[:35] if artist else "RAI Studio Sound"
    draw.text((tx, 142), clean_artist, font=font_artist, fill=(210, 210, 230, 255))

    eq_x, eq_y = tx, 185
    num_bars = 28
    bar_w = 12
    gap = 5
    random.seed(len(title) + elapsed_sec)
    for i in range(num_bars):
        wave = math.sin(i * 0.45 + (elapsed_sec * 0.5)) * 0.5 + 0.5
        bh = int(8 + wave * 32 + random.randint(0, 12))
        bx = eq_x + i * (bar_w + gap)
        by = eq_y + 45 - bh

        draw.rounded_rectangle([bx, by, bx + bar_w, eq_y + 45], radius=4, fill=(255, 0, 128, 210))
        draw.rounded_rectangle([bx + 1, by + 1, bx + bar_w - 1, by + 5], radius=2, fill=(0, 240, 255, 255))
        draw.rounded_rectangle([bx, eq_y + 47, bx + bar_w, eq_y + 47 + bh // 4], radius=2, fill=(255, 0, 128, 40))

    prog_x, prog_y = tx, 268
    prog_w = 510
    prog_h = 12

    draw.rounded_rectangle([prog_x, prog_y, prog_x + prog_w, prog_y + prog_h], radius=6, fill=(24, 20, 36, 255), outline=(45, 38, 65, 255), width=1)
    draw.line([(prog_x + 6, prog_y + 1), (prog_x + prog_w - 6, prog_y + 1)], fill=(10, 8, 16, 255), width=1)

    total = max(1, duration_sec)
    pct = min(1.0, max(0.0, elapsed_sec / total)) if duration_sec > 0 else 0.58
    fw = int(prog_w * pct)
    if fw > 6:
        draw.rounded_rectangle([prog_x, prog_y, prog_x + fw, prog_y + prog_h], radius=6, fill=(255, 0, 128, 255))
        draw.line([(prog_x + 4, prog_y + 2), (prog_x + fw - 4, prog_y + 2)], fill=(255, 180, 220, 220), width=1)
        kx = prog_x + fw
        ky = prog_y + prog_h // 2
        draw.ellipse([kx - 9, ky - 7, kx + 9, ky + 11], fill=(0, 0, 0, 140))
        draw.ellipse([kx - 8, ky - 8, kx + 8, ky + 8], fill=(0, 240, 255, 255), outline=(255, 255, 255, 230), width=2)
        draw.ellipse([kx - 4, ky - 5, kx - 1, ky - 2], fill=(255, 255, 255, 255))

    def _fmt(s):
        m, sec = divmod(s, 60)
        return f"{m:02d}:{sec:02d}"

    t_now = _fmt(elapsed_sec)
    t_end = _fmt(duration_sec) if duration_sec > 0 else "LIVE STREAM"
    draw.text((prog_x, prog_y + 20), t_now, font=font_time, fill=(200, 200, 225, 255))
    draw.text((prog_x + prog_w - int(draw.textlength(t_end, font=font_time)), prog_y + 20), t_end, font=font_time, fill=(0, 240, 255, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def generate_bracket_card(matches: List[Tuple[str, str]], round_name: str = "Quarterfinals") -> io.BytesIO:
    """Generates a 1200x675 3D Esports Tournament Match Bracket graphic."""
    W, H = 1200, 675
    img = Image.new("RGBA", (W, H), color=(10, 8, 18, 255))
    draw = ImageDraw.Draw(img)

    draw.ellipse([-50, -50, 350, 350], fill=(255, 0, 128, 30))
    draw.ellipse([W - 350, H - 350, W + 50, H + 50], fill=(0, 240, 255, 30))

    _draw_3d_glass_panel(
        draw,
        (16, 16, W - 16, H - 16),
        radius=24,
        fill=(14, 11, 24, 220),
        border_color=(255, 0, 128, 170),
        highlight_color=(255, 255, 255, 80),
        shadow_depth=14
    )

    font_title = _get_font("arialbd", 38)
    font_round = _get_font("arialbd", 24)
    font_team = _get_font("arialbd", 20)
    font_vs = _get_font("arialbd", 18)

    draw.text((60, 40), "TOURNAMENT CHAMPIONSHIP BRACKET", font=font_title, fill=(255, 215, 0, 255))
    draw.text((60, 90), f"SCHEDULE: {round_name.upper()}", font=font_round, fill=(0, 240, 255, 255))

    box_w, box_h = 520, 100
    positions = [
        (60, 150),
        (620, 150),
        (60, 280),
        (620, 280),
        (60, 410),
        (620, 410),
        (60, 540),
        (620, 540),
    ]

    for i, (team_a, team_b) in enumerate(matches[:8]):
        x, y = positions[i]
        draw.rounded_rectangle([x, y, x + box_w, y + box_h], radius=14, fill=(20, 16, 32, 220), outline=(255, 0, 128, 120), width=1)
        draw.line([(x + 4, y + 1), (x + box_w - 4, y + 1)], fill=(255, 255, 255, 50), width=1)
        draw.rounded_rectangle([x, y, x + 40, y + box_h], radius=14, fill=(255, 0, 128, 80))
        draw.text((x + 10, y + 38), f"#{i+1}", font=font_vs, fill=(255, 255, 255, 255))

        draw.text((x + 60, y + 20), f"[A] {team_a[:22]}", font=font_team, fill=(255, 255, 255, 255))
        draw.text((x + 60, y + 56), f"[B] {team_b[:22]}", font=font_team, fill=(200, 200, 220, 255))
        draw.text((x + box_w - 75, y + 38), "VS", font=font_vs, fill=(255, 215, 0, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def generate_booster_card(avatar_bytes: Optional[bytes], username: str, boost_count: int, tier: int) -> io.BytesIO:
    """Generates a 900x350 3D Nitro Diamond celebration banner."""
    W, H = 900, 350
    img = Image.new("RGBA", (W, H), color=(14, 8, 24, 255))
    draw = ImageDraw.Draw(img)

    for r in range(180, 0, -15):
        alpha = int(35 * (1 - r / 180))
        draw.ellipse([W // 2 - r, H // 2 - r, W // 2 + r, H // 2 + r], fill=(244, 127, 255, alpha))

    _draw_3d_glass_panel(
        draw,
        (16, 16, W - 16, H - 16),
        radius=24,
        fill=(18, 12, 32, 220),
        border_color=(244, 127, 255, 200),
        highlight_color=(255, 255, 255, 90),
        shadow_depth=14
    )

    avatar_size = 170
    avatar = _crop_circular_avatar(avatar_bytes, avatar_size)
    ax, ay = 60, (H - avatar_size) // 2

    for s in range(12, 0, -2):
        draw.ellipse([ax - s, ay - s + 4, ax + avatar_size + s, ay + avatar_size + s + 4], fill=(0, 0, 0, int(50 * (1 - s / 12))))

    draw.ellipse([ax - 6, ay - 6, ax + avatar_size + 6, ay + avatar_size + 6], outline=(244, 127, 255, 255), width=4)
    img.paste(avatar, (ax, ay), avatar)

    draw = ImageDraw.Draw(img)

    font_head = _get_font("arialbd", 38)
    font_sub = _get_font("arialbd", 24)
    font_body = _get_font("arial", 18)

    draw.text((270, 60), "SERVER BOOST CELEBRATION", font=font_sub, fill=(244, 127, 255, 255))
    draw.text((270, 105), username[:20], font=font_head, fill=(255, 255, 255, 255))
    draw.text((270, 165), "Thank you for boosting RAI VIBES", font=font_body, fill=(220, 220, 240, 255))
    draw.text((270, 200), "Unlocked VIP Elite Role & +2,500 Economy Coins!", font=font_body, fill=(0, 240, 255, 255))
    draw.text((270, 245), f"Server Standing: Tier {tier} • {boost_count} Total Boosts", font=font_body, fill=(255, 215, 0, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def generate_channel_header(
    title: str,
    subtitle: str,
    icon_text: str = "✦",
    accent_color: Tuple[int, int, int] = (255, 0, 128),
    secondary_color: Tuple[int, int, int] = (0, 240, 255),
    badge_tag: Optional[str] = None
) -> io.BytesIO:
    """Generates a 1920x600 Ultra-Wide 3D Studio Channel Header Banner with perspective grid and floating monolith."""
    W, H = 1920, 600
    img = Image.new("RGBA", (W, H), color=(8, 6, 14, 255))
    draw = ImageDraw.Draw(img)

    r1, g1, b1 = accent_color
    r2, g2, b2 = secondary_color

    horizon_y = 360
    vp_x = W // 2

    for i in range(1, 14):
        p = i / 14.0
        y = int(horizon_y + (H - horizon_y) * (p ** 2.2))
        alpha = int(70 * (p ** 1.5))
        draw.line([(0, y), (W, y)], fill=(r1, g1, b1, alpha), width=1)

    for x in range(-200, W + 300, 75):
        alpha = int(45 * (1 - abs(x - vp_x) / (W // 1.2)))
        draw.line([(vp_x, horizon_y), (x, H)], fill=(r2, g2, b2, max(10, alpha)), width=1)

    for r in range(450, 0, -30):
        a1 = int(35 * (1 - r / 450))
        a2 = int(25 * (1 - r / 450))
        draw.ellipse([W // 2 - r, 200 - r // 2, W // 2 + r, 200 + r // 2], fill=(r1, g1, b1, a1))
        draw.ellipse([250 - r, 300 - r, 250 + r, 300 + r], fill=(r2, g2, b2, a2))
        draw.ellipse([W - 250 - r, 300 - r, W - 250 + r, 300 + r], fill=(r1, g1, b1, a2))

    mx1, my1, mx2, my2 = 180, 80, W - 180, 520

    for s in range(24, 0, -3):
        draw.rounded_rectangle([mx1 - s, my1 + s, mx2 + s, my2 + s + 10], radius=32 + s, fill=(0, 0, 0, int(45 * (1 - s / 24))))

    draw.rounded_rectangle([mx1, my1, mx2, my2], radius=30, fill=(14, 11, 24, 215), outline=(r1, g1, b1, 200), width=2)
    draw.line([(mx1 + 30, my1 + 1), (mx2 - 30, my1 + 1)], fill=(255, 255, 255, 120), width=2)
    draw.line([(mx1 + 1, my1 + 30), (mx1 + 1, my2 - 30)], fill=(255, 255, 255, 120), width=2)
    draw.line([(mx1 + 30, my2 - 1), (mx2 - 30, my2 - 1)], fill=(0, 0, 0, 160), width=2)
    draw.line([(mx2 - 1, my1 + 30), (mx2 - 1, my2 - 30)], fill=(0, 0, 0, 160), width=2)
    draw.rounded_rectangle([mx1 + 12, my1 + 12, mx2 - 12, my2 - 12], radius=22, outline=(r2, g2, b2, 80), width=1)

    font_badge = _get_font("arialbd", 18)
    font_title = _get_font("arialbd", 72)
    font_sub = _get_font("arialbd", 26)
    font_system = _get_font("arialbd", 16)

    tag_str = (badge_tag or "OFFICIAL SERVER PORTAL").upper()
    badge_txt = f":: {tag_str} ::"
    b_len = int(draw.textlength(badge_txt, font=font_badge))
    bx1 = (W - b_len - 50) // 2
    by1 = my1 + 45
    draw.rounded_rectangle([bx1, by1, bx1 + b_len + 50, by1 + 42], radius=12, fill=(r1, g1, b1, 40), outline=(r1, g1, b1, 240), width=1)
    draw.line([(bx1 + 10, by1 + 1), (bx1 + b_len + 40, by1 + 1)], fill=(255, 255, 255, 150), width=1)
    draw.text(((W - b_len) // 2, by1 + 10), badge_txt, font=font_badge, fill=(r1, g1, b1, 255))

    t_len = int(draw.textlength(title, font=font_title))
    tx = (W - t_len) // 2
    ty = my1 + 125
    draw.text((tx + 3, ty + 4), title, font=font_title, fill=(0, 0, 0, 220))
    draw.text((tx, ty), title, font=font_title, fill=(255, 255, 255, 255))

    s_len = int(draw.textlength(subtitle, font=font_sub))
    sx = (W - s_len) // 2
    sy = ty + 105
    draw.text((sx + 2, sy + 2), subtitle, font=font_sub, fill=(0, 0, 0, 180))
    draw.text((sx, sy), subtitle, font=font_sub, fill=(215, 215, 240, 255))

    for side in [-1, 1]:
        cx = W // 2 + side * 620
        cy = my1 + 210
        draw.line([(cx, cy - 60), (cx + side * 40, cy - 60)], fill=(r1, g1, b1, 200), width=3)
        draw.line([(cx + side * 40, cy - 60), (cx + side * 40, cy + 60)], fill=(r2, g2, b2, 200), width=3)
        draw.line([(cx + side * 40, cy + 60), (cx, cy + 60)], fill=(r1, g1, b1, 200), width=3)

    bot_bar_y = my2 - 60
    draw.line([(mx1 + 40, bot_bar_y), (mx2 - 40, bot_bar_y)], fill=(r2, g2, b2, 90), width=1)
    stat_left = "NETWORK: RAI FAM HIGH-SPEED CLUSTER"
    stat_right = "SECURITY: SENTINEL PROTOCOL 24/7 ACTIVE"
    draw.text((mx1 + 50, bot_bar_y + 18), stat_left, font=font_system, fill=(r2, g2, b2, 220))
    r_len = int(draw.textlength(stat_right, font=font_system))
    draw.text((mx2 - 50 - r_len, bot_bar_y + 18), stat_right, font=font_system, fill=(r1, g1, b1, 220))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
