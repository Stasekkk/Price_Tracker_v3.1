@echo off
setlocal
title Price Tracker Bot - Installer

echo ============================================================
echo  Price Tracker Bot - Automated Installation (Windows)
echo ============================================================

:: 1. Check for Python
where python >nul 2>nul
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Python is not installed or not in PATH.
    echo Please install Python 3.10+ from python.org and check "Add Python to PATH".
    pause
    exit /b 1
)

:: 2. Create virtual environment
if not exist ".venv" (
    echo [*] Creating virtual environment (.venv)...
    python -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Failed to create virtual environment.
        pause
        exit /b 1
    )
) else (
    echo [*] Virtual environment (.venv) already exists.
)

:: 3. Install dependencies
echo [*] Installing dependencies from requirements.txt...
.venv\Scripts\python.exe -m pip install --upgrade pip --quiet
.venv\Scripts\python.exe -m pip install -r requirements.txt --quiet
if %ERRORLEVEL% neq 0 (
    echo [ERROR] Failed to install requirements.
    pause
    exit /b 1
)

echo [OK] Dependencies installed successfully!
echo.
echo ============================================================
echo  Installation complete!
echo  To start the bot, double-click run.bat
echo ============================================================
echo.
pause
