import psutil
import os

my_pid = os.getpid()
killed = []
for p in psutil.process_iter(["pid", "name", "cmdline"]):
    try:
        if p.info["pid"] == my_pid:
            continue
        cmd = " ".join(p.info["cmdline"] or [])
        if any(script in cmd for script in ["main.py", "security_bot.py", "run_24_7.py"]):
            p.kill()
            killed.append(p.info["pid"])
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass

print(f"Cleaned up {len(killed)} bot processes: {killed}")
