import io
import math
import random
from typing import Optional, List, Tuple
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
            avatar = Image.new("RGBA", (size, size), color=(255, 0, 128, 255))
    else:
        avatar = Image.new("RGBA", (size, size), color=(255, 0, 128, 255))

    mask = Image.new("L", (size, size), 0)
    draw_mask = ImageDraw.Draw(mask)
    draw_mask.ellipse((0, 0, size, size), fill=255)

    circle = ImageOps.fit(avatar, (size, size), centering=(0.5, 0.5))
    circle.putalpha(mask)
    return circle

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
    """Generates a luxury 1000x350 Cyber-Neon Glassmorphism Rank Card."""
    W, H = 1000, 350
    img = Image.new("RGBA", (W, H), color=(13, 10, 22, 255))
    draw = ImageDraw.Draw(img)

    # Ambient radial glows
    for r in range(180, 0, -15):
        alpha = int(32 * (1 - r / 180))
        draw.ellipse([80 - r, 80 - r, 80 + r, 80 + r], fill=(255, 0, 128, alpha))
        draw.ellipse([W - 120 - r, H - 60 - r, W - 120 + r, H - 60 + r], fill=(0, 240, 255, alpha))
        draw.ellipse([W // 2 - r, H // 2 - r, W // 2 + r, H // 2 + r], fill=(255, 215, 0, int(alpha * 0.4)))

    # Outer Glassmorphism Card Outline
    draw.rounded_rectangle([15, 15, W - 15, H - 15], radius=24, fill=(18, 14, 30, 210), outline=(255, 0, 128, 180), width=2)
    draw.rounded_rectangle([20, 20, W - 20, H - 20], radius=20, outline=(0, 240, 255, 90), width=1)

    # Circular Avatar with Concentric Glow Rings
    avatar_size = 180
    avatar = _crop_circular_avatar(avatar_bytes, avatar_size)

    ax, ay = 60, (H - avatar_size) // 2
    # Glow rings
    draw.ellipse([ax - 8, ay - 8, ax + avatar_size + 8, ay + avatar_size + 8], outline=(255, 0, 128, 220), width=4)
    draw.ellipse([ax - 4, ay - 4, ax + avatar_size + 4, ay + avatar_size + 4], outline=(0, 240, 255, 180), width=2)
    img.paste(avatar, (ax, ay), avatar)

    # Typography & User Info
    font_title = _get_font("arialbd", 42)
    font_sub = _get_font("arialbd", 24)
    font_stat = _get_font("arial", 20)
    font_small = _get_font("arial", 16)

    # Clean username
    clean_name = username[:18]
    draw.text((280, 50), clean_name, font=font_title, fill=(255, 255, 255, 255))
    draw.text((280 + int(draw.textlength(clean_name, font=font_title)) + 15, 62), "RAI CITIZEN", font=font_small, fill=(255, 0, 128, 240))

    # Badges: Level & Rank
    rank_badge = f"RANK #{rank}"
    lvl_badge = f"LEVEL {level}"
    draw.rounded_rectangle([280, 108, 410, 142], radius=10, fill=(255, 0, 128, 60), outline=(255, 0, 128, 220), width=1)
    draw.text((295, 114), rank_badge, font=font_small, fill=(255, 255, 255, 255))

    draw.rounded_rectangle([425, 108, 555, 142], radius=10, fill=(0, 240, 255, 60), outline=(0, 240, 255, 220), width=1)
    draw.text((440, 114), lvl_badge, font=font_small, fill=(255, 255, 255, 255))

    # Stats Row: Coins, Rep, Messages
    stats_text = f"🪙 {coins:,} Coins   •   💖 +{rep} Rep   •   💬 {messages:,} Msgs"
    draw.text((280, 162), stats_text, font=font_stat, fill=(210, 210, 230, 255))

    # XP Progress Bar
    bar_x, bar_y, bar_w, bar_h = 280, 225, 650, 26
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=13, fill=(35, 28, 55, 255), outline=(60, 50, 90, 255), width=1)

    pct = min(1.0, max(0.0, current_xp / max(1, next_level_xp)))
    fill_w = int(bar_w * pct)
    if fill_w > 16:
        # Gradient fill
        draw.rounded_rectangle([bar_x, bar_y, bar_x + fill_w, bar_y + bar_h], radius=13, fill=(255, 0, 128, 255))
        # Tip shine
        draw.ellipse([bar_x + fill_w - 18, bar_y + 2, bar_x + fill_w - 2, bar_y + bar_h - 2], fill=(0, 240, 255, 255))

    # XP label & Percentage
    pct_text = f"{int(pct * 100)}%"
    xp_text = f"{current_xp:,} / {next_level_xp:,} XP"
    draw.text((bar_x, bar_y + 36), xp_text, font=font_small, fill=(180, 180, 200, 255))
    draw.text((bar_x + bar_w - int(draw.textlength(pct_text, font=font_small)), bar_y + 36), pct_text, font=font_small, fill=(0, 240, 255, 255))

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
    coins: int,
    rep: int,
    voice_hrs: float,
    pet_str: str,
    clan_str: str,
    join_date_str: str
) -> io.BytesIO:
    """Generates a 1200x600 Luxury Holographic Cyber-ID Card."""
    W, H = 1200, 600
    img = Image.new("RGBA", (W, H), color=(10, 8, 16, 255))
    draw = ImageDraw.Draw(img)

    # Ambient cyber backdrop
    for r in range(250, 0, -20):
        alpha = int(28 * (1 - r / 250))
        draw.ellipse([100 - r, 100 - r, 100 + r, 100 + r], fill=(255, 0, 128, alpha))
        draw.ellipse([W - 100 - r, 100 - r, W - 100 + r, 100 + r], fill=(0, 240, 255, alpha))
        draw.ellipse([W // 2 - r, H - 100 - r, W // 2 + r, H - 100 + r], fill=(255, 215, 0, int(alpha * 0.5)))

    # Outer border & Luxury frame
    draw.rounded_rectangle([20, 20, W - 20, H - 20], radius=28, fill=(15, 12, 25, 225), outline=(255, 0, 128, 200), width=2)
    draw.rounded_rectangle([28, 28, W - 28, H - 28], radius=22, outline=(0, 240, 255, 100), width=1)

    # Top Holographic Header Ribbon
    draw.rectangle([100, 20, W - 100, 28], fill=(255, 0, 128, 255))
    draw.rectangle([250, 28, W - 250, 32], fill=(0, 240, 255, 255))

    font_head = _get_font("arialbd", 36)
    font_sub = _get_font("arialbd", 22)
    font_body = _get_font("arial", 20)
    font_label = _get_font("arialbd", 16)
    font_small = _get_font("arial", 15)

    # Card Title
    draw.text((60, 50), "✦ RAI VIBES • CITIZEN IDENTITY CODEX", font=font_label, fill=(255, 0, 128, 255))

    # Avatar
    avatar_size = 200
    avatar = _crop_circular_avatar(avatar_bytes, avatar_size)
    ax, ay = 60, 100
    draw.ellipse([ax - 8, ay - 8, ax + avatar_size + 8, ay + avatar_size + 8], outline=(0, 240, 255, 240), width=4)
    draw.ellipse([ax - 4, ay - 4, ax + avatar_size + 4, ay + avatar_size + 4], outline=(255, 0, 128, 180), width=2)
    img.paste(avatar, (ax, ay), avatar)

    # Verified holographic seal stamp
    draw.rounded_rectangle([60, 320, 260, 356], radius=10, fill=(0, 240, 255, 40), outline=(0, 240, 255, 200), width=1)
    draw.text((80, 328), "🛡️ VERIFIED CITIZEN", font=font_small, fill=(0, 240, 255, 255))

    # User Header
    draw.text((300, 95), username[:20], font=font_head, fill=(255, 255, 255, 255))
    draw.text((300, 145), f"Level {level} Elite Citizen • Member Since: {join_date_str}", font=font_small, fill=(180, 180, 210, 255))

    # Stats Grid Boxes
    boxes = [
        ("⭐ LEVEL & XP", f"Level {level} ({current_xp:,}/{req_xp:,})", 300, 190, 410, 90),
        ("🪙 VAULT COINS", f"{coins:,} Coins", 740, 190, 400, 90),
        ("🎙️ VOICE PRESENCE", f"{voice_hrs} Hours Logged", 300, 300, 410, 90),
        ("💖 INFLUENCE REP", f"+{rep} Rep Points", 740, 300, 400, 90),
        ("🐾 PET COMPANION", pet_str[:28], 300, 410, 410, 90),
        ("⚔️ SQUAD / CLAN", clan_str[:28], 740, 410, 400, 90),
    ]

    for label, val, bx, by, bw, bh in boxes:
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=14, fill=(22, 18, 38, 200), outline=(45, 38, 70, 255), width=1)
        draw.text((bx + 16, by + 14), label, font=font_label, fill=(255, 0, 128, 220))
        draw.text((bx + 16, by + 44), val, font=font_body, fill=(240, 240, 255, 255))

    # Progress bar at bottom
    bar_x, bar_y, bar_w, bar_h = 300, 525, 840, 18
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=9, fill=(35, 28, 55, 255))
    pct = min(1.0, max(0.0, current_xp / max(1, req_xp)))
    fw = int(bar_w * pct)
    if fw > 10:
        draw.rounded_rectangle([bar_x, bar_y, bar_x + fw, bar_y + bar_h], radius=9, fill=(0, 240, 255, 255))

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
    """Generates a 900x300 Spotify/Apple Music-style Now Playing visualizer card."""
    W, H = 900, 300
    img = Image.new("RGBA", (W, H), color=(12, 10, 20, 255))

    # Backdrop blur if album art exists
    if thumbnail_bytes:
        try:
            bg_art = Image.open(io.BytesIO(thumbnail_bytes)).convert("RGBA")
            bg_art = bg_art.resize((W, H), Image.Resampling.LANCZOS)
            bg_art = bg_art.filter(ImageFilter.GaussianBlur(radius=35))
            # Darken backdrop
            darken = Image.new("RGBA", (W, H), color=(0, 0, 0, 180))
            bg_art.paste(darken, (0, 0), darken)
            img.paste(bg_art, (0, 0))
        except Exception:
            pass

    draw = ImageDraw.Draw(img)

    # Frame
    draw.rounded_rectangle([10, 10, W - 10, H - 10], radius=20, outline=(255, 0, 128, 140), width=2)

    # Album Art Box
    art_size = 200
    art_x, art_y = 50, (H - art_size) // 2
    if thumbnail_bytes:
        try:
            art = Image.open(io.BytesIO(thumbnail_bytes)).convert("RGBA")
            art = art.resize((art_size, art_size), Image.Resampling.LANCZOS)
            mask = Image.new("L", (art_size, art_size), 0)
            ImageDraw.Draw(mask).rounded_rectangle([0, 0, art_size, art_size], radius=16, fill=255)
            art.putalpha(mask)
            img.paste(art, (art_x, art_y), art)
        except Exception:
            draw.rounded_rectangle([art_x, art_y, art_x + art_size, art_y + art_size], radius=16, fill=(255, 0, 128, 100))
    else:
        draw.rounded_rectangle([art_x, art_y, art_x + art_size, art_y + art_size], radius=16, fill=(255, 0, 128, 100))

    # Track Details
    font_title = _get_font("arialbd", 32)
    font_artist = _get_font("arial", 22)
    font_time = _get_font("arialbd", 16)
    font_small = _get_font("arial", 14)

    draw.text((280, 50), "NOW STREAMING • RAI VIBES 💗", font=font_small, fill=(0, 240, 255, 240))
    draw.text((280, 80), title[:35], font=font_title, fill=(255, 255, 255, 255))
    draw.text((280, 125), f"👤 {artist[:30]}", font=font_artist, fill=(200, 200, 220, 255))
    draw.text((280, 160), f"Requested by {requester_name[:25]}", font=font_small, fill=(160, 160, 180, 255))

    # Waveform / Progress Bar
    bar_x, bar_y, bar_w, bar_h = 280, 210, 570, 10
    draw.rounded_rectangle([bar_x, bar_y, bar_x + bar_w, bar_y + bar_h], radius=5, fill=(40, 35, 60, 255))

    total = max(1, duration_sec)
    pct = min(1.0, max(0.0, elapsed_sec / total)) if duration_sec > 0 else 0.5
    fw = int(bar_w * pct)
    if fw > 6:
        draw.rounded_rectangle([bar_x, bar_y, bar_x + fw, bar_y + bar_h], radius=5, fill=(255, 0, 128, 255))
        draw.ellipse([bar_x + fw - 8, bar_y - 3, bar_x + fw + 8, bar_y + 13], fill=(0, 240, 255, 255))

    # Timestamps
    def _fmt(s):
        m, sec = divmod(s, 60)
        return f"{m:02d}:{sec:02d}"

    t_now = _fmt(elapsed_sec)
    t_end = _fmt(duration_sec) if duration_sec > 0 else "Live"
    draw.text((bar_x, bar_y + 18), t_now, font=font_time, fill=(200, 200, 220, 255))
    draw.text((bar_x + bar_w - int(draw.textlength(t_end, font=font_time)), bar_y + 18), t_end, font=font_time, fill=(200, 200, 220, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def generate_bracket_card(matches: List[Tuple[str, str]], round_name: str = "Quarterfinals") -> io.BytesIO:
    """Generates a 1200x675 Esports Tournament Match Bracket graphic."""
    W, H = 1200, 675
    img = Image.new("RGBA", (W, H), color=(11, 9, 20, 255))
    draw = ImageDraw.Draw(img)

    # Ambient Esports glow
    draw.ellipse([-50, -50, 350, 350], fill=(255, 0, 128, 30))
    draw.ellipse([W - 350, H - 350, W + 50, H + 50], fill=(0, 240, 255, 30))
    draw.rounded_rectangle([15, 15, W - 15, H - 15], radius=24, outline=(255, 0, 128, 160), width=2)

    font_title = _get_font("arialbd", 38)
    font_round = _get_font("arialbd", 24)
    font_team = _get_font("arialbd", 20)
    font_vs = _get_font("arialbd", 18)
    font_foot = _get_font("arial", 16)

    draw.text((60, 40), "🏆 TOURNAMENT CHAMPIONSHIP BRACKET", font=font_title, fill=(255, 215, 0, 255))
    draw.text((60, 90), f"SCHEDULE: {round_name.upper()}", font=font_round, fill=(0, 240, 255, 255))

    # Render Match Boxes (up to 4 matches on this card)
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
        # Match number badge
        draw.rounded_rectangle([x, y, x + 40, y + box_h], radius=14, fill=(255, 0, 128, 80))
        draw.text((x + 12, y + 38), f"#{i+1}", font=font_vs, fill=(255, 255, 255, 255))

        # Team A
        draw.text((x + 60, y + 20), f"🔵 {team_a[:22]}", font=font_team, fill=(255, 255, 255, 255))
        # Team B
        draw.text((x + 60, y + 56), f"🔴 {team_b[:22]}", font=font_team, fill=(200, 200, 220, 255))
        # VS Badge
        draw.text((x + box_w - 75, y + 38), "⚔️ VS", font=font_vs, fill=(255, 215, 0, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def generate_booster_card(avatar_bytes: Optional[bytes], username: str, boost_count: int, tier: int) -> io.BytesIO:
    """Generates a 900x350 Nitro Diamond celebration banner."""
    W, H = 900, 350
    img = Image.new("RGBA", (W, H), color=(14, 8, 24, 255))
    draw = ImageDraw.Draw(img)

    for r in range(180, 0, -15):
        alpha = int(35 * (1 - r / 180))
        draw.ellipse([W // 2 - r, H // 2 - r, W // 2 + r, H // 2 + r], fill=(244, 127, 255, alpha))

    draw.rounded_rectangle([15, 15, W - 15, H - 15], radius=24, fill=(20, 12, 35, 210), outline=(244, 127, 255, 220), width=2)

    avatar_size = 170
    avatar = _crop_circular_avatar(avatar_bytes, avatar_size)
    ax, ay = 60, (H - avatar_size) // 2
    draw.ellipse([ax - 6, ay - 6, ax + avatar_size + 6, ay + avatar_size + 6], outline=(244, 127, 255, 255), width=4)
    img.paste(avatar, (ax, ay), avatar)

    font_head = _get_font("arialbd", 38)
    font_sub = _get_font("arialbd", 24)
    font_body = _get_font("arial", 18)

    draw.text((270, 60), "🚀 SERVER BOOST CELEBRATION!", font=font_sub, fill=(244, 127, 255, 255))
    draw.text((270, 105), username[:20], font=font_head, fill=(255, 255, 255, 255))
    draw.text((270, 165), "Thank you for boosting RAI VIBES 💗", font=font_body, fill=(220, 220, 240, 255))
    draw.text((270, 200), f"Unlocked VIP Elite Role & +2,500 Economy Coins!", font=font_body, fill=(0, 240, 255, 255))
    draw.text((270, 245), f"📊 Server Standing: Tier {tier} • {boost_count} Total Boosts", font=font_body, fill=(255, 215, 0, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf

def generate_channel_header(title: str, subtitle: str, icon_text: str = "✦", accent_color: Tuple[int, int, int] = (255, 0, 128)) -> io.BytesIO:
    """Generates a 1920x450 Ultra-Wide Studio Channel Header Banner."""
    W, H = 1920, 450
    img = Image.new("RGBA", (W, H), color=(10, 8, 16, 255))
    draw = ImageDraw.Draw(img)

    r_col, g_col, b_col = accent_color

    # Radiant background sweeps
    for r in range(400, 0, -30):
        alpha = int(45 * (1 - r / 400))
        draw.ellipse([W // 2 - r, H // 2 - r, W // 2 + r, H // 2 + r], fill=(r_col, g_col, b_col, alpha))

    # Framing lines
    draw.line([(60, 40), (W - 60, 40)], fill=(r_col, g_col, b_col, 160), width=2)
    draw.line([(60, H - 40), (W - 60, H - 40)], fill=(r_col, g_col, b_col, 160), width=2)

    font_title = _get_font("arialbd", 76)
    font_sub = _get_font("arial", 32)
    font_icon = _get_font("arialbd", 48)

    # Title centered
    t_len = draw.textlength(title, font=font_title)
    draw.text(((W - t_len) // 2, 140), title, font=font_title, fill=(255, 255, 255, 255))

    # Subtitle centered
    s_len = draw.textlength(subtitle, font=font_sub)
    draw.text(((W - s_len) // 2, 245), subtitle, font=font_sub, fill=(200, 200, 220, 255))

    # Icon badge top
    i_len = draw.textlength(icon_text, font=font_icon)
    draw.text(((W - i_len) // 2, 65), icon_text, font=font_icon, fill=(r_col, g_col, b_col, 255))

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf
