@echo off
title Apex Server Architect - Auto Setup
color 0A

echo ===============================================================
echo     APEX SERVER ARCHITECT & COMMUNITY BUILDER
echo     Transforming Server 1457382179981099090 into a Fine Server
echo ===============================================================
echo.

python server_architect.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Setup encountered an issue or requires bot invite.
    pause
) else (
    echo.
    echo ===============================================================
    echo [SUCCESS] Server structure, roles, and embeds are now live!
    echo ===============================================================
    pause
)
