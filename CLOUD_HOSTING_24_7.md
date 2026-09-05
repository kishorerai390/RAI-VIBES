# 🌐 24/7 Cloud Hosting Guide for RAI VIBES 💗

When you turn off your laptop, your local machine stops running programs. To keep **RAI VIBES 💗** running **24/7 non-stop in Discord without needing your laptop on**, you can host it on a free cloud server.

Here are the **top 3 easiest and 100% free ways** to keep it online forever:

---

## 🌟 Option 1: Render.com or Railway (Recommended & Easiest)

1. Push or upload your `APEX VIBES` folder to a **GitHub Repository** (Public or Private).
2. Go to **[Render.com](https://render.com/)** (or [Railway.app](https://railway.app/)) and sign in with GitHub.
3. Click **New +** ➡️ **Background Worker** (or Web Service / Docker).
4. Select your GitHub repository.
5. In **Environment Variables**, add:
   * Key: `DISCORD_BOT_TOKEN`
   * Value: `(Your bot token from .env)`
6. Click **Deploy**!
   * Render automatically builds the included `Dockerfile` with FFmpeg and runs `keep_alive_supervisor.py`.
   * The bot stays online in Discord 24/7 even when your laptop is completely turned off!

---

## ⚡ Option 2: Specialized Free Discord Bot Hosting (Bot-Hosting.net or Discloud)

1. Go to **[bot-hosting.net](https://bot-hosting.net/)** or **[discloud.app](https://discloud.app/)**.
2. Create a free account.
3. Upload the files in `APEX VIBES` (or upload as a zip).
4. Set startup file to: `keep_alive_supervisor.py` or `main.py`.
5. Enter your `DISCORD_BOT_TOKEN`.
6. Click **Start Bot**!

---

## 🖥️ Option 3: Free Cloud VPS (Oracle Cloud Free Tier / AWS Free Tier)

1. Create a free Ubuntu instance on Oracle Cloud Always-Free or AWS EC2.
2. Clone your code onto the server:

   ```bash
   git clone <your-repo>
   cd "APEX VIBES"
   sudo apt update && sudo apt install -y ffmpeg python3-pip python3-venv
   pip install -r requirements.txt
   ```

3. Run it in a background screen or systemd service:

   ```bash
   nohup python3 keep_alive_supervisor.py > bot.log 2>&1 &
   ```

4. Now it runs forever 24/7 in the cloud!
