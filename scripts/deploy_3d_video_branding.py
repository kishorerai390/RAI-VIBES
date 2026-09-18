import asyncio
import base64
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Any

import requests
from dotenv import load_dotenv
from PIL import Image, ImageChops, ImageEnhance, ImageOps

REPO_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_DIR))

from utils.ffmpeg_setup import get_ffmpeg_executable

from utils.ffmpeg_setup import get_ffmpeg_executable

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv()

ASSETS_DIR = REPO_DIR / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)
BRAIN_DIR = Path(r"C:\Users\kishore\.gemini\antigravity-ide\brain\22c8bdd0-47bb-4906-8eb0-132a037ee268")

FFMPEG_BIN = get_ffmpeg_executable()

BOTS_CONFIG = {
    "VIBES": {
        "name": "RAI VIBES 💗",
        "token": os.getenv("DISCORD_BOT_TOKEN"),
        "logo_src": BRAIN_DIR / "rai_vibes_3d_logo_1789750278862.jpg",
        "banner_src": BRAIN_DIR / "rai_vibes_3d_banner_1789750290783.jpg",
        "avatar_gif": ASSETS_DIR / "rai_vibes_3d_avatar.gif",
        "avatar_mp4": ASSETS_DIR / "rai_vibes_3d_avatar.mp4",
        "banner_gif": ASSETS_DIR / "rai_vibes_3d_banner.gif",
        "banner_mp4": ASSETS_DIR / "rai_vibes_3d_banner.mp4",
        "sheen_color": (255, 105, 180)  # Neon Pink Sheen
    },
    "PLAY": {
        "name": "RAI PLAY 🎮",
        "token": os.getenv("COMMUNITY_BOT_TOKEN") or os.getenv("ARCADE_BOT_TOKEN"),
        "logo_src": BRAIN_DIR / "rai_play_3d_logo_1789750312120.jpg",
        "banner_src": BRAIN_DIR / "rai_play_3d_banner_1789750325088.jpg",
        "avatar_gif": ASSETS_DIR / "rai_play_3d_avatar.gif",
        "avatar_mp4": ASSETS_DIR / "rai_play_3d_avatar.mp4",
        "banner_gif": ASSETS_DIR / "rai_play_3d_banner.gif",
        "banner_mp4": ASSETS_DIR / "rai_play_3d_banner.mp4",
        "sheen_color": (0, 255, 204)  # Cyber Cyan Sheen
    },
    "SENTINEL": {
        "name": "RAI SENTINEL 🛡️",
        "token": os.getenv("SECURITY_BOT_TOKEN"),
        "logo_src": BRAIN_DIR / "rai_sentinel_3d_logo_1789750345134.jpg",
        "banner_src": BRAIN_DIR / "rai_sentinel_3d_banner_1789750361433.jpg",
        "avatar_gif": ASSETS_DIR / "rai_sentinel_3d_avatar.gif",
        "avatar_mp4": ASSETS_DIR / "rai_sentinel_3d_avatar.mp4",
        "banner_gif": ASSETS_DIR / "rai_sentinel_3d_banner.gif",
        "banner_mp4": ASSETS_DIR / "rai_sentinel_3d_banner.mp4",
        "sheen_color": (155, 89, 182)  # Royal Purple Sheen
    }
}


def find_perspective_coeffs(source_coords, target_coords):
    matrix = []
    for s, t in zip(source_coords, target_coords):
        matrix.append([t[0], t[1], 1, 0, 0, 0, -s[0]*t[0], -s[0]*t[1]])
        matrix.append([0, 0, 0, t[0], t[1], 1, -s[1]*t[0], -s[1]*t[1]])
    A = matrix
    B = [c for pt in source_coords for c in pt]
    
    n = 8
    for i in range(n):
        max_el = abs(A[i][i])
        max_row = i
        for k in range(i+1, n):
            if abs(A[k][i]) > max_el:
                max_el = abs(A[k][i])
                max_row = k
        A[i], A[max_row] = A[max_row], A[i]
        B[i], B[max_row] = B[max_row], B[i]
        
        for k in range(i+1, n):
            c = -A[k][i] / (A[i][i] if A[i][i] != 0 else 1e-9)
            for j in range(i, n):
                if i == j:
                    A[k][j] = 0
                else:
                    A[k][j] += c * A[i][j]
            B[k] += c * B[i]
            
    x = [0] * n
    for i in range(n-1, -1, -1):
        x[i] = B[i] / (A[i][i] if A[i][i] != 0 else 1e-9)
        for k in range(i-1, -1, -1):
            B[k] -= A[k][i] * x[i]
    return x


def create_light_sweep(size, progress, width=140, intensity=60, color=(255, 255, 255)):
    """Generates an angled 3D specular light beam reflection."""
    w, h = size
    overlay = Image.new("RGBA", size, (0, 0, 0, 0))
    travel = w + h + width * 2
    pos = int(progress * travel) - width
    
    strip = Image.new("RGBA", (w * 2, h * 2), (0, 0, 0, 0))
    cr, cg, cb = color
    for x in range(width):
        dist = abs(x - width // 2) / (width / 2)
        alpha = int(intensity * max(0, 1.0 - dist ** 1.6))
        for y in range(0, h * 2, 4):
            strip.putpixel((x, y), (cr, cg, cb, alpha))
            strip.putpixel((x, min(h * 2 - 1, y + 1)), (cr, cg, cb, alpha))
            strip.putpixel((x, min(h * 2 - 1, y + 2)), (cr, cg, cb, alpha))
            strip.putpixel((x, min(h * 2 - 1, y + 3)), (cr, cg, cb, alpha))
            
    rotated = strip.rotate(35, resample=Image.Resampling.BILINEAR)
    px = pos - w // 2
    py = (h - rotated.height) // 2
    overlay.paste(rotated, (px, py), rotated)
    return overlay


def generate_3d_avatar(src_path: Path, gif_out: Path, mp4_out: Path, sheen_color=(255, 255, 255), size=(512, 512), num_frames=20):
    print(f"  🎬 Rendering 3D Avatar for {gif_out.name}...")
    with Image.open(src_path) as img:
        img = img.convert("RGBA")
        # 12% circular margin to fit Discord's round avatar mask perfectly
        inner_size = int(size[0] * 0.88)
        img_fitted = ImageOps.contain(img, (inner_size, inner_size), Image.Resampling.LANCZOS)
        
        base_canvas = Image.new("RGBA", size, (8, 8, 14, 255))
        ox = (size[0] - img_fitted.width) // 2
        oy = (size[1] - img_fitted.height) // 2
        base_canvas.paste(img_fitted, (ox, oy), img_fitted)
        
    frames = []
    w, h = size
    
    for i in range(num_frames):
        phase = (i / num_frames) * 2 * math.pi
        
        # 3D Tilt perspective oscillation
        tilt_x = math.sin(phase) * 12
        tilt_y = math.cos(phase) * 7
        zoom = 1.0 + 0.03 * (0.5 - 0.5 * math.cos(phase))
        
        coeffs = find_perspective_coeffs(
            [(0, 0), (w, 0), (w, h), (0, h)],
            [
                (tilt_x, -tilt_y),
                (w - tilt_x, tilt_y),
                (w + tilt_x, h - tilt_y),
                (-tilt_x, h + tilt_y)
            ]
        )
        tilted = base_canvas.transform(size, Image.Transform.PERSPECTIVE, coeffs, Image.Resampling.BICUBIC)
        
        # Scale zoom
        nw, nh = int(w * zoom), int(h * zoom)
        zoomed = tilted.resize((nw, nh), Image.Resampling.BILINEAR)
        cx, cy = (nw - w) // 2, (nh - h) // 2
        frame = zoomed.crop((cx, cy, cx + w, cy + h))
        
        # Specular 3D light sweep
        sheen = create_light_sweep(size, i / num_frames, width=150, intensity=65, color=sheen_color)
        frame = Image.alpha_composite(frame.convert("RGBA"), sheen)
        
        # 3D chromatic stereoscopic edge pulse
        if abs(math.sin(phase)) > 0.35:
            shift = int(round(math.sin(phase) * 2.0))
            r, g, b, a = frame.split()
            frame = Image.merge("RGBA", (ImageChops.offset(r, shift, 0), g, ImageChops.offset(b, -shift, 0), a))
            
        # Quantize for optimal GIF palette and clean file size
        paletted = frame.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT)
        frames.append(paletted)
        
    frames[0].save(
        gif_out,
        save_all=True,
        append_images=frames[1:],
        duration=70,  # ~14 fps
        loop=0,
        optimize=True
    )
    print(f"    ✅ Avatar GIF: {gif_out.name} ({gif_out.stat().st_size / 1024:.1f} KB)")
    
    # Also render clean MP4 video using ffmpeg
    try:
        cmd = [
            FFMPEG_BIN, "-y",
            "-i", str(gif_out),
            "-movflags", "faststart",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=512:512",
            str(mp4_out)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"    ✅ Avatar MP4: {mp4_out.name} ({mp4_out.stat().st_size / 1024:.1f} KB)")
    except Exception as e:
        print(f"    Note on MP4 conversion: {e}")


def generate_3d_banner(src_path: Path, gif_out: Path, mp4_out: Path, sheen_color=(255, 255, 255), size=(960, 540), num_frames=20):
    print(f"  🎬 Rendering 3D Banner for {gif_out.name}...")
    with Image.open(src_path) as img:
        img = img.convert("RGB")
        fitted = ImageOps.fit(img, size, Image.Resampling.LANCZOS)
        
    frames = []
    w, h = size
    
    for i in range(num_frames):
        phase = (i / num_frames) * 2 * math.pi
        
        # 3D cinematic camera dolly and pan
        zoom = 1.0 + 0.04 * (0.5 - 0.5 * math.cos(phase))
        pan_x = math.sin(phase) * 14
        pan_y = math.cos(phase) * 5
        
        nw, nh = int(w * zoom), int(h * zoom)
        zoomed = fitted.resize((nw, nh), Image.Resampling.BILINEAR)
        cx, cy = (nw - w) // 2 + int(pan_x), (nh - h) // 2 + int(pan_y)
        frame = zoomed.crop((cx, cy, cx + w, cy + h))
        
        # Dynamic 3D lighting breathing pulse
        pulse = 1.0 + 0.07 * math.sin(phase)
        enhancer = ImageEnhance.Brightness(frame)
        frame = enhancer.enhance(pulse)
        
        # Specular light flare sweep
        sheen = create_light_sweep(size, i / num_frames, width=260, intensity=50, color=sheen_color)
        frame_rgba = Image.alpha_composite(frame.convert("RGBA"), sheen)
        
        paletted = frame_rgba.convert("RGB").quantize(colors=128, method=Image.Quantize.MEDIANCUT)
        frames.append(paletted)
        
    frames[0].save(
        gif_out,
        save_all=True,
        append_images=frames[1:],
        duration=75,
        loop=0,
        optimize=True
    )
    print(f"    ✅ Banner GIF: {gif_out.name} ({gif_out.stat().st_size / 1024:.1f} KB)")
    
    try:
        cmd = [
            FFMPEG_BIN, "-y",
            "-i", str(gif_out),
            "-movflags", "faststart",
            "-pix_fmt", "yuv420p",
            "-vf", "scale=960:540",
            str(mp4_out)
        ]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        print(f"    ✅ Banner MP4: {mp4_out.name} ({mp4_out.stat().st_size / 1024:.1f} KB)")
    except Exception as e:
        print(f"    Note on MP4 conversion: {e}")


def upload_to_discord(token: str, bot_name: str, avatar_path: Path, banner_path: Path):
    if not token or token.startswith("YOUR_"):
        print(f"  ⚠️ No valid token for {bot_name}. Skipping Discord API upload.")
        return
        
    headers = {
        "Authorization": f"Bot {token}",
        "Content-Type": "application/json"
    }
    
    payload = {}
    
    if avatar_path.exists():
        with open(avatar_path, "rb") as f:
            b64_avatar = base64.b64encode(f.read()).decode("utf-8")
        payload["avatar"] = f"data:image/gif;base64,{b64_avatar}"
        
    if banner_path.exists():
        with open(banner_path, "rb") as f:
            b64_banner = base64.b64encode(f.read()).decode("utf-8")
        payload["banner"] = f"data:image/gif;base64,{b64_banner}"
        
    if not payload:
        return
        
    print(f"  🚀 Applying 3D Animated Avatar & Banner to {bot_name} on Discord...")
    try:
        r = requests.patch("https://discord.com/api/v10/users/@me", headers=headers, json=payload)
        if r.status_code == 200:
            data = r.json()
            print(f"  ✨ SUCCESS! {bot_name} updated! (Avatar: {data.get('avatar')}, Banner: {data.get('banner')})")
        else:
            print(f"  ⚠️ Discord API response ({r.status_code}): {r.text[:180]}")
            # If banner failed due to non-nitro restriction, fallback to avatar update only
            if "banner" in payload and r.status_code in [400, 403]:
                print(f"  🔄 Retrying avatar update only for {bot_name}...")
                r2 = requests.patch("https://discord.com/api/v10/users/@me", headers=headers, json={"avatar": payload["avatar"]})
                if r2.status_code == 200:
                    print(f"  ✨ SUCCESS! {bot_name} 3D Avatar updated!")
                else:
                    print(f"  ⚠️ Avatar fallback note ({r2.status_code}): {r2.text[:150]}")
    except Exception as e:
        print(f"  ❌ Error uploading to Discord: {e}")


def main():
    print("=========================================================")
    print("  RENDER & DEPLOY 3D EFFECT VIDEO/GIF BRANDING FOR ALL BOTS")
    print("=========================================================\n")
    
    for key, cfg in BOTS_CONFIG.items():
        print(f"\n--- Processing {cfg['name']} ---")
        if cfg["logo_src"].exists():
            generate_3d_avatar(cfg["logo_src"], cfg["avatar_gif"], cfg["avatar_mp4"], sheen_color=cfg["sheen_color"])
        else:
            print(f"  ⚠️ Logo source missing: {cfg['logo_src']}")
            
        if cfg["banner_src"].exists():
            generate_3d_banner(cfg["banner_src"], cfg["banner_gif"], cfg["banner_mp4"], sheen_color=cfg["sheen_color"])
        else:
            print(f"  ⚠️ Banner source missing: {cfg['banner_src']}")
            
        upload_to_discord(cfg["token"], cfg["name"], cfg["avatar_gif"], cfg["banner_gif"])
        time.sleep(2.0)  # Gentle spacing for Discord rate limits
        
    print("\n🎉 ALL BOT 3D EFFECT VIDEOS & BANNERS RENDERED & DEPLOYED!")


if __name__ == "__main__":
    main()
