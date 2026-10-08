import unittest
import os
import re
import html
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker

from database import Base, Phone, PriceHistory, User, Settings
from locales import t, get_button_variants, TEXTS, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
from main import build_broadcast_text


class TestTrackerDatabase(unittest.TestCase):
    def setUp(self):
        # Use temporary in-memory test database
        self.engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
        
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        self.Session = sessionmaker(bind=self.engine)
        Base.metadata.create_all(self.engine)
        self.db = self.Session()

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)

    def test_phone_crud_and_cascade_delete(self):
        """Test cascade deletion of price history when parent product is deleted"""
        phone = Phone(name="Test Phone", url="https://allo.ua/test.html", current_price=1000, is_available=1)
        self.db.add(phone)
        self.db.commit()

        # Add price history entries
        h1 = PriceHistory(phone_id=phone.id, price=1000)
        h2 = PriceHistory(phone_id=phone.id, price=900)
        self.db.add_all([h1, h2])
        self.db.commit()

        self.assertEqual(self.db.query(PriceHistory).count(), 2)

        # Delete product
        self.db.delete(phone)
        self.db.commit()

        # Associated price history must be automatically deleted
        self.assertEqual(self.db.query(Phone).count(), 0)
        self.assertEqual(self.db.query(PriceHistory).count(), 0)

    def test_user_admin_roles_and_language(self):
        """Test user creation, admin role assignment, and language preference persistence"""
        admin = User(telegram_id=111, is_admin=1, language="en")
        viewer = User(telegram_id=222, is_admin=0)  # default language is 'uk'
        self.db.add_all([admin, viewer])
        self.db.commit()

        u1 = self.db.query(User).filter(User.telegram_id == 111).first()
        u2 = self.db.query(User).filter(User.telegram_id == 222).first()
        self.assertEqual(u1.is_admin, 1)
        self.assertEqual(u1.language, "en")
        self.assertEqual(u2.is_admin, 0)
        self.assertEqual(u2.language, "uk")


class TestTrackerLocalization(unittest.TestCase):
    def test_translation_dictionaries_completeness(self):
        """Verify that all translation keys exist in both Ukrainian and English dictionaries"""
        uk_keys = set(TEXTS["uk"].keys())
        en_keys = set(TEXTS["en"].keys())

        missing_in_en = uk_keys - en_keys
        missing_in_uk = en_keys - uk_keys

        self.assertEqual(missing_in_en, set(), f"Missing keys in English dictionary: {missing_in_en}")
        self.assertEqual(missing_in_uk, set(), f"Missing keys in Ukrainian dictionary: {missing_in_uk}")

    def test_translation_function(self):
        """Test t(...) function for uk, en, and fallback mechanisms"""
        # Ukrainian
        uk_prices = t("btn_prices", "uk")
        self.assertEqual(uk_prices, "📊 Актуальні ціни")

        # English
        en_prices = t("btn_prices", "en")
        self.assertEqual(en_prices, "📊 Current Prices")

        # String parameter interpolation
        uk_formatted = t("add_success", "uk", url="http://x", name="Тест", price=500, stock_note="")
        self.assertIn("Тест", uk_formatted)
        self.assertIn("500 грн", uk_formatted)

        en_formatted = t("add_success", "en", url="http://x", name="Test", price=500, stock_note="")
        self.assertIn("Test", en_formatted)
        self.assertIn("500 UAH", en_formatted)

        # Unknown language code falls back to DEFAULT_LANGUAGE ('uk')
        self.assertEqual(t("btn_prices", "de"), "📊 Актуальні ціни")

        # Non-existent translation key returns the key itself
        self.assertEqual(t("non_existent_key", "uk"), "non_existent_key")

    def test_get_button_variants(self):
        """Test retrieving all localized button labels for aiogram message filters"""
        variants = get_button_variants("btn_prices")
        self.assertIn("📊 Актуальні ціни", variants)
        self.assertIn("📊 Current Prices", variants)
        self.assertEqual(len(variants), 2)

    def test_build_broadcast_text_multilingual(self):
        """Test notification report generation across languages"""
        price_events = [{
            "type": "price_change",
            "url": "https://allo.ua/test.html",
            "name": "Phone X",
            "old_price": 1000,
            "new_price": 800,
            "diff": -200
        }]
        status_events = [{
            "type": "out_of_stock",
            "url": "https://allo.ua/test.html",
            "name": "Phone X"
        }]

        uk_report = build_broadcast_text(price_events, status_events, "uk")
        self.assertIn("Зміни цін на товари:", uk_report)
        self.assertIn("1000 ➔ <b>800 грн</b>", uk_report)
        self.assertIn("закінчився на складі", uk_report)

        en_report = build_broadcast_text(price_events, status_events, "en")
        self.assertIn("Product price changes:", en_report)
        self.assertIn("1000 ➔ <b>800 UAH</b>", en_report)
        self.assertIn("out of stock", en_report)


class TestTrackerLogic(unittest.TestCase):
    def test_url_sanitization(self):
        """Test cleaning product URLs from tracking parameters and whitespace"""
        raw_url = "  https://allo.ua/products/item.html?utm_source=telegram&utm_medium=share#anchor  "
        clean_url = raw_url.strip().split("?")[0].split("#")[0]
        self.assertEqual(clean_url, "https://allo.ua/products/item.html")

    def test_time_regex(self):
        """Test validation of check time format (HH:MM)"""
        time_pattern = r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$'
        self.assertTrue(re.match(time_pattern, "07:00"))
        self.assertTrue(re.match(time_pattern, "23:59"))
        self.assertTrue(re.match(time_pattern, "00:00"))
        self.assertFalse(re.match(time_pattern, "24:00"))
        self.assertFalse(re.match(time_pattern, "7:000"))
        self.assertFalse(re.match(time_pattern, "abc"))

    def test_price_regex_extraction(self):
        """Test regex extraction of price value from embedded JSON/scripts"""
        snippet = 'var productData = {"name": "Test", "price": 14999.00, "sku": "123"};'
        match = re.search(r'["\']?price["\']?\s*:\s*["\']?(\d+(?:\.\d+)?)["\']?', snippet)
        self.assertIsNotNone(match)
        price = int(float(match.group(1)))
        self.assertEqual(price, 14999)

    def test_html_escaping(self):
        """Test HTML entity escaping for Telegram messages"""
        bad_name = "Phone <Pro> & 'Super' \"Edition\""
        safe_name = html.escape(bad_name)
        self.assertNotIn("<Pro>", safe_name)
        self.assertIn("&lt;Pro&gt;", safe_name)

    def test_chunking_long_message(self):
        """Test splitting long text into chunks smaller than 3800 characters"""
        paragraphs = [f"Item {i}: " + ("x" * 150) for i in range(40)]
        full_text = "\n\n".join(paragraphs)
        self.assertGreater(len(full_text), 4000)

        chunks = []
        current_chunk = ""
        for p in paragraphs:
            if len(current_chunk) + len(p) + 2 > 3800:
                if current_chunk.strip():
                    chunks.append(current_chunk.strip())
                current_chunk = p + "\n\n"
            else:
                current_chunk += p + "\n\n"
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        self.assertGreater(len(chunks), 1)
        for chunk in chunks:
            self.assertLessEqual(len(chunk), 3800)


if __name__ == "__main__":
    unittest.main()
