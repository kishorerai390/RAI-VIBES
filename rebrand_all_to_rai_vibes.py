import os
import re

ICON_URL = "https://cdn-icons-png.flaticon.com/512/3844/3844724.png"

def clean_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    # Replace branding
    content = content.replace("RAI_ICON_URL", "RAI_ICON_URL")
    content = content.replace("RAI VIBES 💗 • Music Engine", "RAI VIBES 💗 • Music Engine")
    content = content.replace("RAI VIBES 💗", "RAI VIBES 💗")
    content = content.replace("RAI VIBES 💗", "RAI VIBES 💗")
    content = content.replace("RaiVibes", "RaiVibes")
    content = content.replace("RAI", "RAI")

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated branding in: {filepath}")

# Process all python files in APEX VIBES
base_dir = r"f:\antigravity\APEX VIBES"
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith(".py"):
            clean_file(os.path.join(root, file))

print("All branding completely rebranded to RAI VIBES 💗!")
