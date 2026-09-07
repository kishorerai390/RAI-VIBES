import os
import sys
import glob
from pathlib import Path
from PIL import Image
import discord
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(r"f:\antigravity\APEX VIBES\.env")
token = os.getenv("DISCORD_BOT_TOKEN")
GUILD_ID = 1457382179981099090

STICKERS_DIR = Path(r"f:\antigravity\APEX VIBES\stickers")
STICKERS_DIR.mkdir(parents=True, exist_ok=True)

def prepare_emoji_bytes(image_path: Path) -> bytes:
    """Resize to 128x128 transparent PNG/WEBP under 256KB for Discord."""
    im = Image.open(image_path).convert("RGBA")
    # Resize keeping aspect ratio
    im.thumbnail((128, 128), Image.Resampling.LANCZOS)
    temp_out = STICKERS_DIR / "_temp_emoji.png"
    im.save(temp_out, format="PNG", optimize=True)
    with open(temp_out, "rb") as f:
        data = f.read()
    temp_out.unlink(missing_ok=True)
    return data

async def upload_all_stickers():
    client = discord.Client(intents=discord.Intents.default())
    
    @client.event
    async def on_ready():
        guild = client.get_guild(GUILD_ID)
        print(f"Connected to {guild.name} ({guild.id})", flush=True)
        
        # Check current emojis
        current_emojis = {e.name.lower(): e for e in guild.emojis}
        print(f"Server currently has {len(guild.emojis)} / {guild.emoji_limit} emojis.", flush=True)
        
        # Find all images in stickers folder
        valid_exts = ("*.webp", "*.png", "*.jpg", "*.jpeg", "*.gif")
        files = []
        for ext in valid_exts:
            files.extend(STICKERS_DIR.glob(ext))
            
        if not files:
            print(f"\n⚠️ No sticker files found in {STICKERS_DIR} yet!", flush=True)
            print("👉 Drop your WhatsApp sticker (.webp / .png) files into this folder and run again!", flush=True)
            await client.close()
            return
            
        print(f"\nFound {len(files)} sticker files to process...", flush=True)
        for f in files:
            # Clean name for Discord emoji (alphanumeric and underscores, 2-32 chars)
            base_name = f.stem.lower()
            clean_name = "".join(c if c.isalnum() else "_" for c in base_name).strip("_")
            if len(clean_name) < 2:
                clean_name = f"emoji_{clean_name}"
            clean_name = clean_name[:32]
            
            if clean_name in current_emojis:
                print(f"Skipping :{clean_name}: (already exists)", flush=True)
                continue
                
            try:
                emoji_bytes = prepare_emoji_bytes(f)
                new_emoji = await guild.create_custom_emoji(
                    name=clean_name,
                    image=emoji_bytes,
                    reason="Uploaded from WhatsApp Stickers"
                )
                print(f"✅ Successfully created emoji :{new_emoji.name}: ({new_emoji.id})", flush=True)
            except Exception as e:
                print(f"❌ Failed to upload {f.name} as :{clean_name}:: {e}", flush=True)
                
        await client.close()
        
    await client.start(token)

if __name__ == "__main__":
    import asyncio
    asyncio.run(upload_all_stickers())
