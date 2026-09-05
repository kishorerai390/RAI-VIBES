@echo off
title RAI SENTINEL - Security & Moderation Bot
color 0C

echo =========================================================
echo       RAI SENTINEL DISCORD BOT - STARTUP
echo       Automated Anti-Raid - Moderation - Server Defender
echo =========================================================
echo.

python security_bot.py

if %errorlevel% neq 0 (
    echo.
    echo Sentinel bot encountered an error or was stopped.
    pause
)
