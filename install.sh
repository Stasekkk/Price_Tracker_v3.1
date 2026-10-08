#!/usr/bin/env bash
# ==============================================================================
# Price Tracker Bot - Automated Installation Script (Linux & macOS)
# ==============================================================================

set -e

echo "============================================================"
echo "🚀 Installing Price Tracker Bot"
echo "============================================================"

# 1. Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Error: python3 is not installed."
    echo "Please install Python 3 (3.10+ recommended) and rerun this script."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Found Python $PYTHON_VERSION"

# 2. Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment (.venv)..."
    python3 -m venv .venv
else
    echo "📦 Virtual environment (.venv) already exists."
fi

# 3. Install dependencies
echo "📥 Installing dependencies from requirements.txt..."
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet

echo "✅ Dependencies installed successfully!"

# 4. Check for Google Chrome or Chromium
echo "🔍 Checking for Google Chrome or Chromium..."
if command -v google-chrome &> /dev/null || command -v chromium &> /dev/null || [ -f "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" ]; then
    echo "✅ Chrome/Chromium installation detected!"
else
    echo "⚠️ Warning: Google Chrome or Chromium was not detected."
    echo "  - On Ubuntu/Debian, install with: sudo apt install -y google-chrome-stable"
    echo "  - On macOS, install with: brew install --cask google-chrome"
fi

echo "============================================================"
echo "🎉 Installation complete!"
echo "To start the bot, simply run: ./run.sh"
echo "============================================================"
