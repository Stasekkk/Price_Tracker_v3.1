@echo off
setlocal
title Price Tracker Bot

cd /d "%~dp0"

:: Check if virtual environment exists
if not exist ".venv\Scripts\python.exe" (
    echo [!] Virtual environment (.venv) not found.
    echo [*] Running automated installation first...
    call install.bat
)

echo [*] Starting Price Tracker Bot...
.venv\Scripts\python.exe main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo [ERROR] Bot process stopped unexpectedly.
    pause
)
