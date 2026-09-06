import os
import sys
import zipfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_ZIP = BASE_DIR / "rai_fam_cloud_bot.zip"

# Strict runtime whitelist for Discloud 24/7 Hosting
CORE_ROOT_FILES = {
    "run_24_7.py",
    "main.py",
    "security_bot.py",
    "config.py",
    ".env",
    "discloud.config",
    "requirements.txt",
    "README.md"
}

INCLUDE_DIRS = {"cogs", "utils", "data"}

EXCLUDE_EXTS = {".pyc", ".pyo", ".log", ".tmp"}
EXCLUDE_DIRS = {"__pycache__", ".git", ".venv", "venv", "bin", "scratch"}

def create_package():
    print("📦 Packaging Minimal Clean Cloud Bot for Discloud...")
    if OUTPUT_ZIP.exists():
        try:
            OUTPUT_ZIP.unlink()
        except Exception:
            pass

    with zipfile.ZipFile(OUTPUT_ZIP, "w", zipfile.ZIP_DEFLATED) as zipf:
        # 1. Add essential root files
        for fname in CORE_ROOT_FILES:
            fpath = BASE_DIR / fname
            if fpath.exists():
                zipf.write(fpath, fname)
                print(f"  + Added Root: {fname}")

        # 2. Add subdirectories (cogs, utils, data)
        for dir_name in INCLUDE_DIRS:
            target_dir = BASE_DIR / dir_name
            if not target_dir.exists():
                continue
            for root, dirs, files in os.walk(target_dir):
                dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                for file in files:
                    if Path(file).suffix in EXCLUDE_EXTS:
                        continue
                    file_path = Path(root) / file
                    rel_path = file_path.relative_to(BASE_DIR)
                    zipf.write(file_path, str(rel_path).replace("\\", "/"))
                    print(f"  + Added: {rel_path}")

    size_kb = OUTPUT_ZIP.stat().st_size / 1024
    print(f"\n🎉 Super-Clean Package Ready: {OUTPUT_ZIP.name} ({size_kb:.1f} KB)")

if __name__ == "__main__":
    create_package()
