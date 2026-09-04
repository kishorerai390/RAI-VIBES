@echo off
title Thor Vibes - Dependency Installer
color 0B

echo =========================================================
echo       THOR VIBES DISCORD BOT - INSTALLER
echo       Command The Power - Hear The Rhythm
echo =========================================================
echo.

echo [1/3] Checking Python installation...
python --version
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Python is not installed or not added to PATH!
    echo Please download and install Python 3.10+ from https://www.python.org/downloads/
    echo Make sure to check "Add python.exe to PATH" during installation.
    pause
    exit /b
)

echo.
echo [2/3] Installing Python dependencies...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if %errorlevel% neq 0 (
    color 0C
    echo [ERROR] Failed to install requirements.
    pause
    exit /b
)

echo.
echo [3/3] Checking FFmpeg audio support...
python utils/ffmpeg_setup.py

echo.
echo =========================================================
echo [SUCCESS] Thor Vibes setup complete!
echo Next step: Make sure to add your DISCORD_BOT_TOKEN to the '.env' file.
echo Then launch 'run.bat' to start your bot!
echo =========================================================
pause
