import os
import sys
import shutil
import zipfile
import sqlite3
from datetime import datetime

# Ensure utf-8 output on Windows console
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding='utf-8')

SOURCE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ONEDRIVE_BASE = os.environ.get("OneDrive", r"C:\Users\kishore\OneDrive")
BACKUP_ROOT = os.path.join(ONEDRIVE_BASE, "APEX_VIBES_BACKUP")
LATEST_DIR = os.path.join(BACKUP_ROOT, "latest")
ARCHIVES_DIR = os.path.join(BACKUP_ROOT, "archives")

# Patterns and folders to ignore
IGNORE_DIRS = {
    ".venv", "venv", "env", "ENV", "__pycache__", ".git", 
    ".vscode", ".idea", "bin", "scratch"
}
IGNORE_EXTS = {
    ".pyc", ".pyo", ".pyd", ".exe", ".dll", ".zip", ".tar", ".gz"
}

def should_ignore(rel_path):
    parts = rel_path.replace("\\", "/").split("/")
    for part in parts:
        if part in IGNORE_DIRS or part.startswith("__pycache__"):
            return True
    ext = os.path.splitext(rel_path)[1].lower()
    if ext in IGNORE_EXTS and not rel_path.endswith(".zip"):
        return True
    # Ignore existing zip packages in root
    if ext == ".zip":
        return True
    return False

def backup_sqlite(src_path, dst_path):
    """Safely back up an SQLite database even if currently locked/running."""
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)
    try:
        con = sqlite3.connect(src_path)
        bck = sqlite3.connect(dst_path)
        with bck:
            con.backup(bck)
        bck.close()
        con.close()
    except Exception as e:
        print(f"  [Warning] SQLite online backup failed for {src_path} ({e}), falling back to file copy...")
        shutil.copy2(src_path, dst_path)

def run_backup():
    print("=" * 60)
    print("🚀 APEX VIBES -> OneDrive Backup Routine")
    print(f"Source:      {SOURCE_DIR}")
    print(f"Destination: {BACKUP_ROOT}")
    print("=" * 60)

    if not os.path.exists(ONEDRIVE_BASE):
        print(f"❌ Error: OneDrive directory not found at {ONEDRIVE_BASE}")
        return False

    os.makedirs(LATEST_DIR, exist_ok=True)
    os.makedirs(ARCHIVES_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    zip_filename = f"APEX_VIBES_backup_{timestamp}.zip"
    zip_filepath = os.path.join(ARCHIVES_DIR, zip_filename)

    copied_files = 0
    total_bytes = 0

    print("\n📂 1. Updating 'latest' mirror in OneDrive...")
    for root, dirs, files in os.walk(SOURCE_DIR):
        # Filter directories in-place to avoid recursing ignored folders
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS and not d.startswith(".")]

        for file in files:
            src_file = os.path.join(root, file)
            rel_file = os.path.relpath(src_file, SOURCE_DIR)

            if should_ignore(rel_file):
                continue

            dst_file = os.path.join(LATEST_DIR, rel_file)
            os.makedirs(os.path.dirname(dst_file), exist_ok=True)

            if file.endswith(".db") or file.endswith(".sqlite") or file.endswith(".sqlite3"):
                backup_sqlite(src_file, dst_file)
            else:
                shutil.copy2(src_file, dst_file)

            copied_files += 1
            total_bytes += os.path.getsize(src_file)

    print(f"  ✅ Mirrored {copied_files} files ({(total_bytes / (1024*1024)):.2f} MB) to:\n     {LATEST_DIR}")

    print("\n📦 2. Creating compressed archive snapshot...")
    with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(LATEST_DIR):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, LATEST_DIR)
                zipf.write(full_path, arcname=rel_path)

    zip_size_mb = os.path.getsize(zip_filepath) / (1024 * 1024)
    print(f"  ✅ Archive created: {zip_filename} ({zip_size_mb:.2f} MB)")
    print(f"     Saved at: {zip_filepath}")

    # Write summary metadata
    info_path = os.path.join(BACKUP_ROOT, "BACKUP_INFO.txt")
    with open(info_path, "w", encoding="utf-8") as f:
        f.write(f"APEX VIBES Backup Summary\n")
        f.write(f"Timestamp:       {datetime.now().isoformat()}\n")
        f.write(f"Source Folder:   {SOURCE_DIR}\n")
        f.write(f"Total Files:     {copied_files}\n")
        f.write(f"Mirrored Size:   {(total_bytes / (1024*1024)):.2f} MB\n")
        f.write(f"Latest Zip:      {zip_filename} ({zip_size_mb:.2f} MB)\n")
        f.write(f"Status:          SUCCESS\n")

    print("\n🎉 OneDrive Backup completed successfully!")
    print(f"OneDrive will now automatically sync {BACKUP_ROOT} to your cloud.\n")
    return True

if __name__ == "__main__":
    run_backup()
