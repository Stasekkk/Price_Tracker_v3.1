import re
import time
import random
import tempfile
import logging
import os
import shutil
import threading
from DrissionPage import ChromiumPage, ChromiumOptions

# Suppress benign JSONDecodeError in DrissionPage background thread on browser shutdown
def _quiet_thread_errors(args):
    if args.exc_type and args.exc_type.__name__ == 'JSONDecodeError':
        return
    threading.__excepthook__(args)

threading.excepthook = _quiet_thread_errors

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def find_chrome_path() -> str | None:
    """Finds the path to Google Chrome or Chromium executable on the system (Linux, macOS, Windows)"""
    custom_path = os.getenv("CHROME_PATH")
    if custom_path and os.path.exists(custom_path):
        return custom_path

    known_paths = [
        # Linux
        '/usr/bin/google-chrome',
        '/usr/bin/google-chrome-stable',
        '/usr/bin/chromium',
        '/usr/bin/chromium-browser',
        '/snap/bin/chromium',
        # macOS
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
        '/Applications/Chromium.app/Contents/MacOS/Chromium',
        # Windows
        os.path.expandvars(r'%ProgramFiles%\Google\Chrome\Application\chrome.exe'),
        os.path.expandvars(r'%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe'),
        os.path.expandvars(r'%LocalAppData%\Google\Chrome\Application\chrome.exe'),
    ]
    for path in known_paths:
        if path and os.path.exists(path):
            return path

    return (
        shutil.which('google-chrome') or
        shutil.which('google-chrome-stable') or
        shutil.which('chrome') or
        shutil.which('chromium') or
        shutil.which('chromium-browser')
    )


def get_phone_data(url: str) -> dict:
    """
    Fetches real-time product data: name, price, stock availability.
    Returns dictionary:
    {
        "name": str,
        "price": int | None,
        "url": str,
        "is_available": bool,
        "is_redirected": bool
    }
    """
    clean_url = url.split("?")[0].strip()
    logger.info(f"🔍 Starting scraper for: {clean_url}")

    # Minimal jitter pause before start
    time.sleep(random.uniform(0.1, 0.4))

    temp_dir = tempfile.TemporaryDirectory()
    port = random.randint(10000, 60000)

    co = ChromiumOptions()

    browser_path = find_chrome_path()
    if browser_path:
        co.set_browser_path(browser_path)

    # Optimal flags for headless execution without graphical display
    co.set_argument('--headless=new')
    co.set_argument('--blink-settings=imagesEnabled=false')
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-dev-shm-usage')
    co.set_argument(
        '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    co.set_argument('--disable-blink-features=AutomationControlled')
    co.set_local_port(port)
    co.set_user_data_path(temp_dir.name)

    # Short element lookup timeouts (1s instead of default 10s) to avoid hanging on missing tags
    try:
        co.set_timeouts(base=1, pageLoad=15, script=5)
    except Exception:
        pass

    data = {
        "name": "Unknown",
        "price": None,
        "url": clean_url,
        "is_available": True,
        "is_redirected": False
    }
    page = None

    try:
        page = ChromiumPage(co)
        page.get(clean_url)

        # Wait for Cloudflare anti-bot verification (short 0.5s intervals)
        for _ in range(10):
            if "Just a moment" not in page.title and "Cloudflare" not in page.title:
                break
            time.sleep(0.5)

        # 1. CHECK FOR REDIRECT (if product is discontinued, Allo redirects to catalog /products/mobile/)
        cur_url = page.url.split('?')[0].rstrip('/')
        orig_url = clean_url.rstrip('/')
        if cur_url != orig_url and not cur_url.endswith('.html'):
            logger.warning(f"⚠️ Product redirects to another page: {cur_url}")
            data["is_redirected"] = True
            data["is_available"] = False
            return data

        # 2. PRODUCT TITLE
        h1 = page.ele('tag:h1', timeout=1)
        if h1 and h1.text:
            data["name"] = h1.text.strip()

        # 3. STOCK AVAILABILITY CHECK (OFFICIAL ALLO MARKERS)
        # A) Direct stock text label: <p class="product-trade__stock-label">Немає в наявності</p>
        stock_label = page.ele('css:.product-trade__stock-label', timeout=0.8) or \
                      page.ele('css:.p-trade-price__status', timeout=0.5) or \
                      page.ele('css:.v-pb__status', timeout=0.5)
        if stock_label and stock_label.text:
            lbl_text = stock_label.text.lower()
            if "немає" in lbl_text or "закінчився" in lbl_text or "недоступн" in lbl_text or "out of stock" in lbl_text:
                data["is_available"] = False

        # B) Buy button check:
        # If product is out of stock, button has class 'buy-button--out-stock' and text 'Повідомити про наявність'
        buy_button = page.ele('css:.product-trade__buy-button', timeout=0.8) or \
                     page.ele('css:.p-tabs__buy-button', timeout=0.5) or \
                     page.ele('tag:button@class:buy-button', timeout=0.5)

        if buy_button:
            btn_class = buy_button.attr('class') or ''
            btn_text = buy_button.text.lower() if buy_button.text else ''

            if "out-stock" in btn_class or "повідомити" in btn_text or "немає" in btn_text or "notify" in btn_text:
                data["is_available"] = False
            elif ("купити" in btn_text or "buy" in btn_text) and data["is_available"] is not False:
                data["is_available"] = True

        # 4. PRICE EXTRACTION
        # A) Via Schema.org / OpenGraph meta tags
        price_meta = page.ele('xpath://meta[@property="product:price:amount"]', timeout=0.5) or \
                     page.ele('xpath://meta[@itemprop="price"]', timeout=0.5)

        if price_meta:
            res = price_meta.attr('content')
            if res:
                try:
                    data["price"] = int(float(res))
                except (ValueError, TypeError):
                    pass

        # B) Regex search in JSON / page source if meta tags are missing
        if not data["price"]:
            match = re.search(r'["\']?price["\']?\s*:\s*["\']?(\d+(?:\.\d+)?)["\']?', page.html)
            if match:
                try:
                    data["price"] = int(float(match.group(1)))
                except (ValueError, TypeError):
                    pass

        # C) CSS class selector fallbacks
        if not data["price"]:
            price_element = page.ele('css:.p-trade-price__current-price', timeout=0.5) or \
                            page.ele('css:.price__current', timeout=0.5) or \
                            page.ele('css:.v-pb__cur', timeout=0.5)
            if price_element and price_element.text:
                price_digits = re.sub(r'\D', '', price_element.text)
                if price_digits:
                    try:
                        data["price"] = int(price_digits)
                    except (ValueError, TypeError):
                        pass

    except Exception as e:
        logger.error(f"❌ Error scraping {clean_url}: {e}")
    finally:
        if page:
            try:
                page.quit()
            except Exception as e:
                logger.debug(f"Error closing page: {e}")
        try:
            temp_dir.cleanup()
        except Exception:
            pass

    return data


if __name__ == "__main__":
    test_urls = [
        "https://allo.ua/ua/products/mobile/xiaomi-redmi-15-8-256gb-midnight-black.html",
        "https://allo.ua/ua/products/mobile/xiaomi-redmi-note-15-pro-5g-titanium-color-8-256gb.html",
        "https://allo.ua/ua/products/mobile/xiaomi-redmi-a5-4-128gb-midnight-black.html"
    ]
    for u in test_urls:
        print(get_phone_data(u))