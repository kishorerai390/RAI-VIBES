import sys
import time
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [SUPERVISOR]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("Supervisor")

PROJECT_DIR = Path(__file__).resolve().parent
MAIN_SCRIPT = PROJECT_DIR / "main.py"

def run_bot_loop():
    logger.info("⚡ RAI VIBES 💗 24/7 Non-Stop Music & Guard Sentinel Supervisor Started!")
    logger.info(f"Targeting script: {MAIN_SCRIPT}")
    
    crash_count = 0
    while True:
        logger.info("🚀 Launching RAI VIBES 💗 Engine...")
        start_time = time.time()
        try:
            process = subprocess.Popen([sys.executable, str(MAIN_SCRIPT)], cwd=str(PROJECT_DIR))
            process.wait()
            
            uptime = time.time() - start_time
            exit_code = process.returncode
            logger.warning(f"⚠️ Bot process exited with code {exit_code} after {uptime:.1f}s uptime.")

            if exit_code == 0:
                logger.info("Bot exited cleanly. Restarting in 2s to maintain 24/7 uptime...")
                time.sleep(2)
            else:
                crash_count += 1
                logger.error(f"Bot experienced abnormal exit (Crash #{crash_count}). Auto-recovering in 3s...")
                time.sleep(3)
        except KeyboardInterrupt:
            logger.info("Supervisor stopped by user.")
            break
        except Exception as e:
            logger.error(f"Supervisor error: {e}. Retrying in 5s...")
            time.sleep(5)

if __name__ == "__main__":
    run_bot_loop()
