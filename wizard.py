"""
Interactive First-Run Setup Wizard for Price Tracker Bot.
Automatically prompts user for required configuration if .env file is missing.
"""

import os
import sys
from dotenv import load_dotenv


def run_setup_wizard() -> None:
    """Guides user through initial interactive configuration in terminal"""
    print("\n" + "=" * 60)
    print("🚀 PRICE TRACKER BOT — FIRST RUN SETUP WIZARD")
    print("=" * 60)
    print("Configuration file (.env) was not found or is incomplete.")
    print("Let's configure the bot in 2 quick steps!\n")

    # 1. Telegram Bot Token
    while True:
        try:
            token = input("🔑 1. Enter Telegram Bot Token (from @BotFather): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            sys.exit(1)

        if token and ":" in token and len(token) > 15:
            break
        print("❌ Invalid token format. It should look like: 1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ\n")

    # 2. Telegram Admin ID(s)
    while True:
        try:
            admin_input = input("👤 2. Enter your Telegram Admin ID (from @userinfobot): ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nSetup cancelled.")
            sys.exit(1)

        ids = [x.strip() for x in admin_input.split(",") if x.strip()]
        if ids and all(x.isdigit() for x in ids):
            break
        print("❌ Please enter valid numeric ID(s) (e.g. 123456789 or 111,222)\n")

    env_content = f"""# Price Tracker Bot Configuration
TELEGRAM_TOKEN={token}
ADMIN_IDS={','.join(ids)}

# Database URL (optional, defaults to SQLite)
DATABASE_URL=sqlite:///fallback.db
"""

    with open(".env", "w", encoding="utf-8") as f:
        f.write(env_content)

    print("\n" + "=" * 60)
    print("✅ Configuration saved successfully to .env!")
    print("=" * 60 + "\n")


def ensure_environment() -> None:
    """Checks if .env is valid; triggers setup wizard if token or file is missing"""
    load_dotenv()
    token = os.getenv("TELEGRAM_TOKEN")
    admin_ids = os.getenv("ADMIN_IDS")

    if not token or not admin_ids or not os.path.exists(".env"):
        # Check if stdin is interactive
        if sys.stdin.isatty():
            run_setup_wizard()
            load_dotenv(override=True)
        else:
            print("❌ Error: .env file missing or incomplete and terminal is not interactive.")
            print("Please create .env manually from .env.example")
            sys.exit(1)


if __name__ == "__main__":
    ensure_environment()
