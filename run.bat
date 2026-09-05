@echo off
title RAI VIBES - Pure Music & Karaoke Sound Engine
color 0D

echo =========================================================
echo       RAI VIBES DISCORD BOT - STARTUP
echo       Pure Music - Karaoke - Sound Engine - 24/7 Vibe
echo =========================================================
echo.

python main.py

if %errorlevel% neq 0 (
    echo.
    echo Bot encountered an error or was stopped.
    pause
)
