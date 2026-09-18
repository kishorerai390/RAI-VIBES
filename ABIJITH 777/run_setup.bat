@echo off
chcp 65001 >nul
title ABIJITH 777 - Server Operations & Automation Suite
cls

:menu
echo ========================================================
echo   ABIJITH 777 (1428058914141900860) - AUTOMATION SUITE
echo ========================================================
echo.
echo   [1] Inspect Full Server State (Roles, Channels, Audit)
echo   [2] Sync & Setup Admin Suite (VIP Category, Channels, Permissions)
echo   [3] Apply Aesthetic Font Style (| • format)
echo   [4] Refresh Interactive Embeds (Verify & Ticket Panels)
echo   [5] Setup Live Server Stats Counters
echo   [6] Exit
echo.
echo ========================================================
set /p opt="Choose an option [1-6]: "

if "%opt%"=="1" (
    cls
    python inspect_server.py
    pause
    goto menu
)
if "%opt%"=="2" (
    cls
    python setup_admin_suite.py
    pause
    goto menu
)
if "%opt%"=="3" (
    cls
    python apply_font_style.py
    pause
    goto menu
)
if "%opt%"=="4" (
    cls
    python deploy_embeds.py
    pause
    goto menu
)
if "%opt%"=="5" (
    cls
    python setup_server_stats.py
    pause
    goto menu
)
if "%opt%"=="6" (
    exit
)

echo Invalid selection. Please try again.
pause
goto menu
