# 🛒 Price Tracker Bot (Telegram) — v3.2

An asynchronous Telegram bot for automated price monitoring and stock availability tracking on the e-commerce platform **Allo.ua**.

---

### 🆕 What's New in v3.2 (Plug & Play Update)
- ⚡️ **1-Click Automated Installers:** Added `install.sh` (Linux/macOS) and `install.bat` (Windows) for zero-friction dependency setup.
- 🚀 **1-Click Launchers:** Added `run.sh` and `run.bat` for instant bot startup.
- 🧙‍♂️ **Interactive Setup Wizard:** Built-in terminal wizard (`wizard.py`) automatically configures `.env` on first launch.
- 🌐 **Full i18n Localization:** Dual language support (Ukrainian 🇺🇦 & English 🇬🇧) with in-bot switching and multilingual broadcasts.

---

## ✨ Features

- ⚡️ **Fast Concurrent Scraping:** Built-in concurrency control (`asyncio.Semaphore(3)`) scrapes 20+ items in under 30 seconds.
- 📦 **Accurate Stock Tracking:** Detects out-of-stock items ("Notify when available") and discontinued items (redirected to parent category catalog).
- 📈 **Price History & Alerts:** Logs historical price changes and delivers instant notifications with price difference calculations (📈 / 📉).
- ⏰ **Automated Scheduler:** Daily automated checks at a scheduled time (default `07:00`) with in-bot configuration.
- 🛡 **Access Control & Security:** Two-tier authorization using aiogram `AccessMiddleware` ensuring only whitelisted users can interact with the bot.
- 🌐 **Multi-language Support (i18n):** Full localization support for Ukrainian (`uk`) and English (`en`), customizable per-user in bot settings with multilingual broadcast reports.
- 💻 **Cross-Platform Compatibility:** Runs on Linux, macOS (Intel & Apple Silicon), and Windows.
- 📱 **Telegram UX:** Clickable HTML links directly to product pages, interactive inline settings, and automatic message chunking to prevent Telegram 4096-character limit overflow.

---

## 🛠 Tech Stack

- **Python 3.11+ / 3.12 / 3.13**
- **[aiogram 3.x](https://github.com/aiogram/aiogram)** — Modern asynchronous framework for Telegram Bot API
- **[DrissionPage](https://github.com/g1879/DrissionPage)** — High-performance headless Chromium automation with anti-bot and Cloudflare handling
- **[SQLAlchemy 2.0](https://www.sqlalchemy.org/)** — Robust ORM supporting SQLite and PostgreSQL
- **[APScheduler](https://github.com/agronholm/apscheduler)** — Advanced Python scheduler for background jobs

---

## 📁 Project Structure

```text
├── main.py            # Entry point: bot handlers, menus, scheduler, and FSM
├── wizard.py          # Interactive first-run setup wizard (creates .env)
├── locales.py         # Multi-language dictionary (UK / EN) and i18n helper functions
├── scraper.py         # Scraping engine powered by DrissionPage (cross-platform)
├── database.py        # Database schema (SQLAlchemy), migrations, and session management
├── test_tracker.py    # Automated unit and integration test suite
├── requirements.txt   # Project dependencies
├── install.sh         # 1-Click installer for Linux & macOS
├── install.bat        # 1-Click installer for Windows
├── run.sh             # 1-Click runner for Linux & macOS
├── run.bat            # 1-Click runner for Windows
├── .env.example       # Environment configuration template
├── LICENSE            # MIT License
└── README.md          # Project documentation
```

---

## 🚀 Quick Start (1-Click Automated Setup)

### Linux & macOS:
```bash
git clone https://github.com/your-username/tracker_v3.git
cd tracker_v3

# 1. Run automated installer (creates .venv and installs dependencies)
./install.sh

# 2. Start the bot (runs interactive setup wizard on first launch)
./run.sh
```

### Windows:
1. Clone or download the repository.
2. Double-click **`install.bat`** to create virtual environment and install packages.
3. Double-click **`run.bat`** to start the bot.

> 💡 **First-Run Wizard:** If `.env` is not found, the bot will automatically launch an interactive terminal wizard asking for your Telegram Bot Token and Admin ID, and create `.env` for you!

---

## 🛠 Manual Installation & Setup (Alternative)

### 1. Clone the repository
```bash
git clone https://github.com/your-username/tracker_v3.git
cd tracker_v3
```

### 2. Create and activate a virtual environment
- **Linux / macOS:**
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  ```
- **Windows (PowerShell):**
  ```powershell
  python -m venv .venv
  .venv\Scripts\activate
  ```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Ensure Google Chrome or Chromium is installed
The scraper requires a desktop Google Chrome or Chromium installation:
- **Linux (Ubuntu / Debian):**
  ```bash
  sudo apt update && sudo apt install -y google-chrome-stable
  # or
  sudo apt install -y chromium chromium-driver
  ```
- **macOS:**
  Install [Google Chrome](https://www.google.com/chrome/) or run:
  ```bash
  brew install --cask google-chrome
  ```
- **Windows:**
  Install standard [Google Chrome](https://www.google.com/chrome/).

*(The scraper automatically detects standard Chrome locations across Linux, macOS, and Windows. You can also specify a custom path using `CHROME_PATH` in `.env`).*

### 5. Configure environment variables
Create a `.env` file from the provided example:
```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:
```env
TELEGRAM_TOKEN=1234567890:ABCdefGHIjklMNOpqrSTUvwxYZ
ADMIN_IDS=123456789
```

### 6. Run automated tests (optional)
```bash
python test_tracker.py
```

### 7. Start the bot
```bash
python main.py
```

---

## ⚙️ Environment Variables

| Variable | Description | Default |
| :--- | :--- | :--- |
| `TELEGRAM_TOKEN` | Bot API token from [@BotFather](https://t.me/BotFather) | *Required* |
| `ADMIN_IDS` | Comma-separated list of Telegram admin user IDs | *Required* |
| `DATABASE_URL` | SQLAlchemy connection URL (SQLite or PostgreSQL) | `sqlite:///fallback.db` |
| `CHROME_PATH` | Explicit path to Chrome or Chromium executable | *Auto-detected* |

---

## 🤖 Bot Usage & Features

- **/start** — Initializes the bot and shows the role-based main menu.
- **/cancel** / **❌ Cancel** — Cancels any active conversation or input state.
- **📊 Current Prices** — Displays the latest prices and availability of all tracked products.
- **🔄 Check Now** *(Admin)* — Triggers an immediate concurrent price and stock verification.
- **➕ Add Product** *(Admin)* — Adds a new Allo.ua product link to the tracking database.
- **🗑 Delete Product** *(Admin)* — Deletes a product and its price history by ID.
- **⚙️ Settings**:
  - 🌐 **Language Switcher** — Interactive toggle between `🇺🇦 Українська` and `🇬🇧 English`.
  - 👤 **Add User** *(Admin)* — Whitelists a new user by Telegram ID or username.
  - 👥 **User List** *(Admin)* — Displays all authorized users with their roles and preferred languages.
  - 🗑 **Delete User** *(Admin)* — Removes a user from access whitelist.
  - ⏰ **Change Check Time** *(Admin)* — Reconfigures the daily scheduled check time (HH:MM).

---

## 🧪 Testing

The test suite runs against an isolated in-memory SQLite database and validates models, cascading deletes, regular expressions, HTML escaping, and translation completeness:

```bash
python test_tracker.py
```

Expected output:
```text
Ran 11 tests in 0.025s

OK
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
