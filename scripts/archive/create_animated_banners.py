import os, math, random
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance

brain_dir = r"C:\Users\kishore\.gemini\antigravity-ide\brain\f702fb63-3851-4c49-a66f-04de06a1d35b"
output_dir = r"f:\antigravity\APEX VIBES\assets"
os.makedirs(output_dir, exist_ok=True)

vibes_base = Image.open(os.path.join(brain_dir, "rai_vibes_banner_art_1788726128368.jpg")).convert("RGBA")
sentinel_base = Image.open(os.path.join(brain_dir, "rai_sentinel_banner_art_1788726144338.jpg")).convert("RGBA")
fam_base = Image.open(os.path.join(brain_dir, "rai_fam_banner_art_1788726164969.jpg")).convert("RGBA")

W, H = 800, 450
vibes_base = vibes_base.resize((W, H), Image.Resampling.LANCZOS)
sentinel_base = sentinel_base.resize((W, H), Image.Resampling.LANCZOS)
fam_base = fam_base.resize((W, H), Image.Resampling.LANCZOS)

font_dir = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "Fonts")
title_font = ImageFont.truetype(os.path.join(font_dir, "impact.ttf"), 48)
subtitle_font = ImageFont.truetype(os.path.join(font_dir, "segoeui.ttf"), 18)
badge_font = ImageFont.truetype(os.path.join(font_dir, "segoeuib.ttf"), 14)

def draw_glowing_text(draw, pos, text, font, glow_color, text_color, glow_radius=3):
    x, y = pos
    for dx in range(-glow_radius, glow_radius + 1):
        for dy in range(-glow_radius, glow_radius + 1):
            if dx*dx + dy*dy <= glow_radius*glow_radius:
                draw.text((x + dx, y + dy), text, font=font, fill=glow_color)
    draw.text(pos, text, font=font, fill=text_color)

# ==========================================
# 1. RAI VIBES BANNER (Music, Neon Pink/Violet)
# ==========================================
print("Generating RAI VIBES animated GIF...")
vibes_frames = []
num_frames = 24

# Pre-generate stars
random.seed(42)
stars = [(random.randint(20, W-20), random.randint(15, int(H*0.45)), random.uniform(0, 2*math.pi), random.randint(2, 4)) for _ in range(40)]

for i in range(num_frames):
    t = i / num_frames
    frame = vibes_base.copy()
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Animated Equalizer Spectrum at the bottom
    num_bars = 48
    bar_w = W / num_bars
    for b in range(num_bars):
        # Audio wave modulation
        phase = t * 2 * math.pi + (b / num_bars) * 4 * math.pi
        h_factor = (math.sin(phase) * 0.4 + math.cos(phase * 1.7) * 0.3 + 0.5)
        bar_h = int(h_factor * 75 + 15)
        bx = int(b * bar_w)
        by = H - bar_h
        
        # Color gradient: Magenta to Cyan
        r = int(255 - (b / num_bars) * 100)
        g = int(40 + (b / num_bars) * 180)
        b_col = 240
        draw.rectangle([bx + 2, by, bx + bar_w - 2, H], fill=(r, g, b_col, 160))
        # Top cap glow
        draw.rectangle([bx + 2, by - 3, bx + bar_w - 2, by], fill=(255, 255, 255, 220))
        
    # Floating twinkle stars
    for sx, sy, s_phase, s_rad in stars:
        brightness = (math.sin(t * 2 * math.pi + s_phase) + 1) / 2
        alpha = int(brightness * 200 + 40)
        draw.ellipse([sx - s_rad, sy - s_rad, sx + s_rad, sy + s_rad], fill=(255, 180, 240, alpha))
        
    # Neon banner plate on top left
    plate_w, plate_h = 340, 95
    px, py = 40, 30
    draw.rounded_rectangle([px, py, px + plate_w, py + plate_h], radius=16, fill=(10, 5, 25, 170), outline=(255, 50, 180, 200), width=2)
    
    # Pulsing glow intensity
    pulse = (math.sin(t * 2 * math.pi) + 1) / 2
    glow_a = int(pulse * 60 + 195)
    
    draw_glowing_text(draw, (px + 20, py + 12), "RAI VIBES", title_font, (255, 20, 147, glow_a), (255, 255, 255, 255), glow_radius=4)
    draw.text((px + 22, py + 65), "✦  24/7 MUSIC • CHILL VIBES • LOFI  ✦", font=subtitle_font, fill=(240, 170, 255, 230))
    
    # Floating music note
    note_x = int(px + plate_w + 30 + math.sin(t * 2 * math.pi) * 10)
    note_y = int(py + 40 + math.cos(t * 2 * math.pi) * 8)
    draw.text((note_x, note_y), "♪", font=title_font, fill=(255, 100, 220, int(pulse * 100 + 150)))
    
    frame = Image.alpha_composite(frame, overlay)
    vibes_frames.append(frame.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE, colors=128))

vibes_gif_path = os.path.join(output_dir, "rai_vibes_banner.gif")
vibes_frames[0].save(vibes_gif_path, save_all=True, append_images=vibes_frames[1:], duration=70, loop=0, optimize=True)
print(f"RAI VIBES GIF created: {vibes_gif_path} ({os.path.getsize(vibes_gif_path) / 1024:.1f} KB)")


# ==========================================
# 2. RAI SENTINEL BANNER (Cyber Security, Neon Cyan)
# ==========================================
print("Generating RAI SENTINEL animated GIF...")
sentinel_frames = []

for i in range(num_frames):
    t = i / num_frames
    frame = sentinel_base.copy()
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Animated Radar scan beam across center
    center_x, center_y = W // 2, int(H * 0.46)
    radar_angle = t * 2 * math.pi
    radar_len = 160
    end_x = center_x + int(radar_len * math.cos(radar_angle))
    end_y = center_y + int(radar_len * math.sin(radar_angle))
    
    # Radar sweep beam
    draw.line([(center_x, center_y), (end_x, end_y)], fill=(0, 255, 255, 180), width=2)
    
    # Concentric pulse ring expanding outwards
    ring_r = int((t * 180) % 180)
    ring_alpha = int((1.0 - (ring_r / 180)) * 160)
    draw.ellipse([center_x - ring_r, center_y - ring_r, center_x + ring_r, center_y + ring_r], outline=(0, 230, 255, ring_alpha), width=2)
    
    # Secondary inner pulse ring
    ring_r2 = int(((t + 0.5) * 180) % 180)
    ring_alpha2 = int((1.0 - (ring_r2 / 180)) * 160)
    draw.ellipse([center_x - ring_r2, center_y - ring_r2, center_x + ring_r2, center_y + ring_r2], outline=(0, 180, 255, ring_alpha2), width=2)

    # Matrix laser scanner moving vertically
    scan_y = int(t * H)
    draw.line([(0, scan_y), (W, scan_y)], fill=(0, 255, 230, 70), width=2)
    
    # Cyber HUD Banner plate
    plate_w, plate_h = 360, 95
    px, py = 40, 30
    draw.rounded_rectangle([px, py, px + plate_w, py + plate_h], radius=8, fill=(5, 15, 30, 180), outline=(0, 230, 255, 220), width=2)
    
    # High-tech corner ticks
    tick = 10
    draw.line([(px, py), (px + tick, py)], fill=(255, 255, 255, 255), width=3)
    draw.line([(px, py), (px, py + tick)], fill=(255, 255, 255, 255), width=3)
    draw.line([(px + plate_w, py + plate_h), (px + plate_w - tick, py + plate_h)], fill=(255, 255, 255, 255), width=3)
    draw.line([(px + plate_w, py + plate_h), (px + plate_w, py + plate_h - tick)], fill=(255, 255, 255, 255), width=3)
    
    pulse = (math.sin(t * 2 * math.pi) + 1) / 2
    glow_a = int(pulse * 60 + 195)
    
    draw_glowing_text(draw, (px + 18, py + 12), "RAI SENTINEL", title_font, (0, 210, 255, glow_a), (255, 255, 255, 255), glow_radius=4)
    draw.text((px + 20, py + 65), "[ DEFENSE SHIELD • AUTO-MOD ACTIVE ]", font=subtitle_font, fill=(0, 255, 220, 230))
    
    # Live Status blinker
    blink_alpha = 255 if math.sin(t * 4 * math.pi) > 0 else 60
    draw.ellipse([px + plate_w - 30, py + 20, px + plate_w - 18, py + 32], fill=(0, 255, 150, blink_alpha))
    
    frame = Image.alpha_composite(frame, overlay)
    sentinel_frames.append(frame.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE, colors=128))

sentinel_gif_path = os.path.join(output_dir, "rai_sentinel_banner.gif")
sentinel_frames[0].save(sentinel_gif_path, save_all=True, append_images=sentinel_frames[1:], duration=70, loop=0, optimize=True)
print(f"RAI SENTINEL GIF created: {sentinel_gif_path} ({os.path.getsize(sentinel_gif_path) / 1024:.1f} KB)")


# ==========================================
# 3. RAI FAM SERVER BANNER (Chill Rooftop Lounge, Shooting Stars)
# ==========================================
print("Generating RAI FAM SERVER animated GIF...")
fam_frames = []

# Pre-generate shooting stars
shooting_stars = [
    {"start_x": 400, "start_y": 20, "speed": 22, "len": 50, "phase": 0.0},
    {"start_x": 600, "start_y": 10, "speed": 28, "len": 65, "phase": 0.4},
    {"start_x": 250, "start_y": 40, "speed": 20, "len": 40, "phase": 0.7},
]

for i in range(num_frames):
    t = i / num_frames
    frame = fam_base.copy()
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    
    # Animated Shooting Stars across the sky
    for ss in shooting_stars:
        progress = (t + ss["phase"]) % 1.0
        if progress < 0.6:  # only visible during part of cycle
            s_t = progress / 0.6
            curr_x = ss["start_x"] + int(s_t * 180)
            curr_y = ss["start_y"] + int(s_t * 100)
            tail_x = curr_x - int(ss["len"] * 0.85)
            tail_y = curr_y - int(ss["len"] * 0.5)
            alpha = int((1.0 - s_t) * 220)
            draw.line([(tail_x, tail_y), (curr_x, curr_y)], fill=(255, 240, 200, alpha), width=2)
            draw.ellipse([curr_x - 2, curr_y - 2, curr_x + 2, curr_y + 2], fill=(255, 255, 255, alpha))
            
    # Hanging Fairy Lights Twinkle (approx coordinates of string lights in background)
    random.seed(100)
    for lx, ly in [(65, 80), (85, 130), (105, 180), (135, 230), (180, 270), (220, 290), (320, 260), (380, 270), (450, 265), (510, 275)]:
        flicker = (math.sin(t * 4 * math.pi + lx * 0.1) + 1) / 2
        f_rad = int(flicker * 3 + 3)
        f_alpha = int(flicker * 100 + 155)
        draw.ellipse([lx - f_rad, ly - f_rad, lx + f_rad, ly + f_rad], fill=(255, 220, 140, f_alpha))
    
    # Center Aesthetic Floating Sign: RAI FAM
    plate_w, plate_h = 320, 95
    px, py = (W - plate_w) // 2, 25
    draw.rounded_rectangle([px, py, px + plate_w, py + plate_h], radius=18, fill=(20, 10, 30, 175), outline=(255, 130, 190, 210), width=2)
    
    pulse = (math.sin(t * 2 * math.pi) + 1) / 2
    glow_a = int(pulse * 60 + 195)
    
    draw_glowing_text(draw, (px + 45, py + 12), "RAI FAM", title_font, (255, 80, 160, glow_a), (255, 255, 255, 255), glow_radius=4)
    draw.text((px + 28, py + 65), "♥  WELCOME TO OUR COMMUNITY  ♥", font=subtitle_font, fill=(255, 190, 220, 240))
    
    frame = Image.alpha_composite(frame, overlay)
    fam_frames.append(frame.convert("RGB").convert("P", palette=Image.Palette.ADAPTIVE, colors=128))

fam_gif_path = os.path.join(output_dir, "rai_fam_server_banner.gif")
fam_frames[0].save(fam_gif_path, save_all=True, append_images=fam_frames[1:], duration=70, loop=0, optimize=True)
print(f"RAI FAM SERVER GIF created: {fam_gif_path} ({os.path.getsize(fam_gif_path) / 1024:.1f} KB)")
