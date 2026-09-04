@echo off
title Thor Vibes - Music Bot Engine
color 09

echo =========================================================
echo       THOR VIBES DISCORD BOT - STARTUP
echo       Command The Power - Hear The Rhythm
echo =========================================================
echo.

python main.py

if %errorlevel% neq 0 (
    echo.
    echo Bot encountered an error or was stopped.
    pause
)
