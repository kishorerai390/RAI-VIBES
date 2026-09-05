import os
import sys
import time
import json
import subprocess
import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [RAI GUARDIAN]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("Guardian")

PROJECT_DIR = Path(__file__).resolve().parent
MAIN_SCRIPT = PROJECT_DIR / "main.py"
DATA_DIR = PROJECT_DIR / "data"
STATUS_FILE = DATA_DIR / "guardian_status.json"

DATA_DIR.mkdir(exist_ok=True)

def update_guardian_status(status: str, crashes: int, last_crash_reason: str = None):
    """Writes real-time supervisor status for Discord /guardian telemetry."""
    try:
        data = {
            "guardian_status": status,
            "total_recovers": crashes,
            "last_crash_reason": last_crash_reason or "None",
            "last_updated": time.time(),
            "auto_healing": True
        }
        with open(STATUS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass

# Lightweight Health-Check HTTP server for Render / Cloud Web Services
class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status": "ok", "service": "RAI VIBES 24/7 Music Engine & Guardian", "uptime": "online"}')

    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", "10000"))
    try:
        server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
        logger.info(f"🌐 Cloud Health-Check HTTP Server listening on port {port}")
        server.serve_forever()
    except Exception as e:
        logger.warning(f"Health-check port {port} binding notice: {e}")

def run_bot_loop():
    logger.info("🛡️ =====================================================")
    logger.info("🛡️   RAI GUARDIAN • 24/7 AUTO-HEALING SUPERVISOR        ")
    logger.info("🛡️ =====================================================")
    
    # Start web health server in background thread
    web_thread = threading.Thread(target=start_health_server, daemon=True)
    web_thread.start()

    crash_count = 0
    update_guardian_status("ACTIVE (MONITORING)", crash_count)

    while True:
        logger.info("🚀 Starting RAI VIBES 💗...")
        start_time = time.time()
        
        try:
            # Launch the main bot process
            process = subprocess.Popen(
                [sys.executable, str(MAIN_SCRIPT)],
                cwd=str(PROJECT_DIR)
            )
            update_guardian_status("RUNNING", crash_count)
            process.wait()
            
            uptime = time.time() - start_time
            exit_code = process.returncode
            logger.warning(f"⚠️ Bot exited with code {exit_code} (Uptime: {uptime:.1f}s)")

            if exit_code == 0:
                logger.info("Clean shutdown detected. Resuming in 2s...")
                time.sleep(2)
            else:
                crash_count += 1
                reason = f"Process crash with exit code {exit_code}"
                logger.error(f"🚨 [AUTO-HEALING ACTIVATED] Crash #{crash_count} detected. Rectifying...")
                update_guardian_status("AUTO-HEALING", crash_count, reason)
                
                # Wait 2 seconds before instant revival
                time.sleep(2)

        except KeyboardInterrupt:
            logger.info("Guardian stopped by user.")
            update_guardian_status("STOPPED", crash_count, "User stopped supervisor")
            break
        except Exception as e:
            crash_count += 1
            logger.error(f"Supervisor loop exception: {e}. Auto-recovering in 3s...")
            update_guardian_status("ERROR_RECOVERY", crash_count, str(e))
            time.sleep(3)

if __name__ == "__main__":
    run_bot_loop()
