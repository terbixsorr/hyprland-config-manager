@echo off
title Hyprland Config Manager - Windows Desktop Demo
cd /d "%~dp0"

echo =======================================================
echo   Hyprland Config Manager - Windows Desktop Demo
echo =======================================================
echo Starting demo server and launching desktop window...

python demo\run_demo.py
if errorlevel 1 (
    py demo\run_demo.py
)
pause
