#!/usr/bin/env bash
# ==============================================================================
# Price Tracker Bot - Launcher Script (Linux & macOS)
# ==============================================================================

set -e

# Change directory to script directory
cd "$(dirname "$0")"

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "⚠️ Virtual environment (.venv) not found!"
    echo "Running automated installation first..."
    ./install.sh
fi

echo "🚀 Starting Price Tracker Bot..."
exec .venv/bin/python main.py
