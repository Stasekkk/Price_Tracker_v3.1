"""
Internationalization (i18n) module for Tracker v3.
Contains dictionaries for Ukrainian (uk) and English (en) languages,
as well as helper functions for string formatting and button variant matching.
"""

DEFAULT_LANGUAGE = "uk"

SUPPORTED_LANGUAGES = {
    "uk": "🇺🇦 Українська",
    "en": "🇬🇧 English"
}

TEXTS = {
    "uk": {
        # --- Main menu buttons ---
        "btn_prices": "📊 Актуальні ціни",
        "btn_check_now": "🔄 Перевірити зараз",
        "btn_add_product": "➕ Додати товар",
        "btn_delete_product": "🗑 Видалити товар",
        "btn_settings": "⚙️ Налаштування",
        "btn_cancel": "❌ Скасувати",

        # --- Settings menu buttons ---
        "btn_add_user": "👤 Додати користувача",
        "btn_list_users": "👥 Список користувачів",
        "btn_del_user": "🗑 Видалити користувача",
        "btn_change_time": "⏰ Змінити час перевірки",
        "btn_change_lang": "🌐 Мова: {current}",
        "btn_lang_uk": "🇺🇦 Українська",
        "btn_lang_en": "🇬🇧 English",
        "btn_back": "« Назад",

        # --- General messages ---
        "access_denied": "⛔️ Доступ заборонено.",
        "start_msg": "🚀 Tracker v3.0 запущено!",
        "action_cancelled": "Дію скасовано. Повертаємось до головного меню.",
        "currency": "грн",
        "no_data": "немає даних",
        "unknown_item": "Невідомо",
        "menu_updated": "Меню оновлено.",

        # --- Price view ---
        "prices_empty": "📭 Список порожній. Додайте товар.",
        "prices_header": "📱 <b>Поточні ціни на товари:</b>\n\n",
        "prices_out_of_stock": "⚠️ <i>Немає в наявності</i> (остання ціна: {price})",
        "prices_available": "💰 {price}",

        # --- Price checking (manual & background) ---
        "check_already_running": "⏳ Перевірка вже триває. Будь ласка, зачекайте.",
        "check_started": "🔄 Запускаю швидку паралельну перевірку цін у фоні...",
        "check_empty": "📭 Список товарів порожній.",
        "report_changes_header": "🔔 <b>Зміни цін на товари:</b>\n\n",
        "report_status_header": "📦 <b>Зміни наявності:</b>\n\n",
        "report_item_redirected": "❌ <a href='{url}'>{name}</a> — <b>знято з продажу</b> (сторінку видалено магазином)\n\n",
        "report_item_out_of_stock": "📦 <a href='{url}'>{name}</a> — <b>закінчився на складі</b> (немає в наявності)\n\n",
        "report_item_back_in_stock": "🎉 <a href='{url}'>{name}</a> — <b>знову в наявності{price_str}!</b>\n\n",
        "report_price_for_str": " за <b>{price} грн</b>",
        "report_initial_price": "🆕 <a href='{url}'>{name}</a>\nВстановлено ціну: <b>{price} грн</b>\n\n",
        "report_price_changed": "{emoji} <a href='{url}'>{name}</a>\n{old_price} ➔ <b>{new_price} грн</b> ({diff_sign} грн)\n\n",
        "report_no_changes": "✅ Перевірка завершена. Змін цін та статусів не виявлено.",
        "report_out_of_stock_list": "\n\n📦 <b>Зараз немає в наявності:</b>\n",
        "report_removed_list": "\n\n❌ <b>Знято з продажу:</b>\n",
        "report_error_list": "\n\n⚠️ <b>Помилка перевірки (можливо, збій зв'язку):</b>\n",
        "report_sent_to_all": "✅ Перевірка завершена. Звіт надіслано всім користувачам.",

        # --- Add product ---
        "add_prompt_url": "🔗 Надішліть посилання на товар (наприклад, з Allo):",
        "add_invalid_url": "❌ Це не схоже на посилання. Надішліть коректне посилання або натисніть ❌ Скасувати.",
        "add_already_tracked": "⚠️ Цей товар уже відстежується:\n<b>{name}</b>\nЦіна: <b>{price} грн</b>",
        "add_checking_url": "⏳ Перевіряю посилання та шукаю ціну на сторінці...",
        "add_success": "✅ Товар додано до відстеження:\n<b><a href='{url}'>{name}</a></b>\nЦіна: <b>{price} грн</b>{stock_note}",
        "add_stock_note_out": "\n⚠️ <i>(Зараз немає в наявності на складі)</i>",
        "add_fail_price": "❌ Не вдалося отримати ціну з цього посилання.",
        "add_fail_redirect": "\n(Сторінка редіректить у загальний каталог — можливо, товар знято з продажу)",
        "add_fail_not_available": "\n(На сайті вказано, що товару немає в наявності)",

        # --- Delete product ---
        "del_empty": "📭 У базі немає товарів для видалення.",
        "del_list_header": "<b>Список товарів у базі:</b>\n\n",
        "del_prompt": "\n🔢 Введіть <b>числовий ID товару</b> для видалення або натисніть ❌ Скасувати",
        "del_invalid_id": "❌ Будь ласка, введіть числовий ID товару.",
        "del_success": "✅ Товар <b>{name}</b> (ID: {product_id}) успішно видалений!",
        "del_not_found": "❌ Товар з ID {product_id} не знайдено.",

        # --- Settings ---
        "settings_title": "⚙️ Меню налаштувань:",
        "settings_lang_choose": "🌐 Оберіть мову інтерфейсу:",
        "settings_lang_updated_alert": "Мову успішно змінено!",
        "settings_lang_updated_msg": "✅ Мову змінено на: Українська 🇺🇦",

        # --- User management (Admin) ---
        "add_user_prompt": "👤 Введіть Telegram ID користувача або юзернейм (@username):\n💡 <i>Надійніше вводити числовий ID (його можна дізнатися через бота @userinfobot)</i>",
        "add_user_not_found": "❌ Не вдалося знайти користувача за цим юзернеймом.\n💡 У Telegram бот може знайти за @username тільки користувача, який хоч раз писав боту.\nСпробуйте ввести числовий Telegram ID або попросіть користувача спочатку написати /start боту.",
        "add_user_exists": "ℹ️ Цей користувач вже має доступ до бота.",
        "add_user_success": "✅ Користувача з ID <code>{user_id}</code> додано!",
        "list_users_header": "<b>Допущені користувачі:</b>\n\n",
        "role_admin": "👑 Адмін",
        "role_user": "👤 Користувач",
        "del_user_prompt": "🔢 Введіть Telegram ID користувача, якого треба видалити:",
        "del_user_invalid": "❌ Введіть коректний числовий ID.",
        "del_user_admin_forbidden": "⚠️ Не можна видалити адміністратора, вказаного в .env!",
        "del_user_success": "✅ Користувача <code>{target_id}</code> видалено.",
        "del_user_not_found": "❌ Такого користувача немає в базі.",

        # --- Time settings (Admin) ---
        "change_time_prompt": "⏰ Введіть новий час у форматі HH:MM (наприклад, 08:30):",
        "change_time_invalid": "❌ Невірний формат. Введіть час як HH:MM (наприклад, 07:00 або 19:30)",
        "change_time_success": "✅ Час щоденної автоматичної перевірки змінено на {new_time}"
    },

    "en": {
        # --- Main menu buttons ---
        "btn_prices": "📊 Current Prices",
        "btn_check_now": "🔄 Check Now",
        "btn_add_product": "➕ Add Product",
        "btn_delete_product": "🗑 Delete Product",
        "btn_settings": "⚙️ Settings",
        "btn_cancel": "❌ Cancel",

        # --- Settings menu buttons ---
        "btn_add_user": "👤 Add User",
        "btn_list_users": "👥 User List",
        "btn_del_user": "🗑 Delete User",
        "btn_change_time": "⏰ Change Check Time",
        "btn_change_lang": "🌐 Language: {current}",
        "btn_lang_uk": "🇺🇦 Ukrainian",
        "btn_lang_en": "🇬🇧 English",
        "btn_back": "« Back",

        # --- General messages ---
        "access_denied": "⛔️ Access denied.",
        "start_msg": "🚀 Tracker v3.0 started!",
        "action_cancelled": "Action cancelled. Returning to main menu.",
        "currency": "UAH",
        "no_data": "no data",
        "unknown_item": "Unknown",
        "menu_updated": "Menu updated.",

        # --- Price view ---
        "prices_empty": "📭 Product list is empty. Add a product.",
        "prices_header": "📱 <b>Current product prices:</b>\n\n",
        "prices_out_of_stock": "⚠️ <i>Out of stock</i> (last price: {price})",
        "prices_available": "💰 {price}",

        # --- Price checking (manual & background) ---
        "check_already_running": "⏳ Check is already running. Please wait.",
        "check_started": "🔄 Starting fast parallel price check in background...",
        "check_empty": "📭 Product list is empty.",
        "report_changes_header": "🔔 <b>Product price changes:</b>\n\n",
        "report_status_header": "📦 <b>Stock status changes:</b>\n\n",
        "report_item_redirected": "❌ <a href='{url}'>{name}</a> — <b>discontinued</b> (page removed by store)\n\n",
        "report_item_out_of_stock": "📦 <a href='{url}'>{name}</a> — <b>out of stock</b>\n\n",
        "report_item_back_in_stock": "🎉 <a href='{url}'>{name}</a> — <b>back in stock{price_str}!</b>\n\n",
        "report_price_for_str": " for <b>{price} UAH</b>",
        "report_initial_price": "🆕 <a href='{url}'>{name}</a>\nInitial price set: <b>{price} UAH</b>\n\n",
        "report_price_changed": "{emoji} <a href='{url}'>{name}</a>\n{old_price} ➔ <b>{new_price} UAH</b> ({diff_sign} UAH)\n\n",
        "report_no_changes": "✅ Check complete. No price or status changes detected.",
        "report_out_of_stock_list": "\n\n📦 <b>Currently out of stock:</b>\n",
        "report_removed_list": "\n\n❌ <b>Discontinued:</b>\n",
        "report_error_list": "\n\n⚠️ <b>Check errors (possible connection issue):</b>\n",
        "report_sent_to_all": "✅ Check complete. Report sent to all users.",

        # --- Add product ---
        "add_prompt_url": "🔗 Send product link (e.g. from Allo):",
        "add_invalid_url": "❌ This doesn't look like a valid link. Send a valid link or click ❌ Cancel.",
        "add_already_tracked": "⚠️ This item is already tracked:\n<b>{name}</b>\nPrice: <b>{price} UAH</b>",
        "add_checking_url": "⏳ Checking link and looking up price on page...",
        "add_success": "✅ Product added to tracking:\n<b><a href='{url}'>{name}</a></b>\nPrice: <b>{price} UAH</b>{stock_note}",
        "add_stock_note_out": "\n⚠️ <i>(Currently out of stock)</i>",
        "add_fail_price": "❌ Failed to retrieve price from this link.",
        "add_fail_redirect": "\n(Page redirects to catalog — item may be discontinued)",
        "add_fail_not_available": "\n(Website indicates that product is out of stock)",

        # --- Delete product ---
        "del_empty": "📭 No products in database to delete.",
        "del_list_header": "<b>List of tracked products:</b>\n\n",
        "del_prompt": "\n🔢 Enter <b>numeric product ID</b> to delete or click ❌ Cancel",
        "del_invalid_id": "❌ Please enter a numeric product ID.",
        "del_success": "✅ Product <b>{name}</b> (ID: {product_id}) successfully deleted!",
        "del_not_found": "❌ Product with ID {product_id} not found.",

        # --- Settings ---
        "settings_title": "⚙️ Settings menu:",
        "settings_lang_choose": "🌐 Choose interface language:",
        "settings_lang_updated_alert": "Language successfully updated!",
        "settings_lang_updated_msg": "✅ Language changed to: English 🇬🇧",

        # --- User management (Admin) ---
        "add_user_prompt": "👤 Enter Telegram ID or username (@username):\n💡 <i>Using numeric ID is more reliable (you can check it via @userinfobot)</i>",
        "add_user_not_found": "❌ Could not find user with this username.\n💡 In Telegram, bot can only find by @username if the user messaged the bot.\nTry entering numeric Telegram ID or ask user to send /start first.",
        "add_user_exists": "ℹ️ This user already has access to the bot.",
        "add_user_success": "✅ User with ID <code>{user_id}</code> added!",
        "list_users_header": "<b>Whitelisted users:</b>\n\n",
        "role_admin": "👑 Admin",
        "role_user": "👤 User",
        "del_user_prompt": "🔢 Enter Telegram ID of user to delete:",
        "del_user_invalid": "❌ Enter a valid numeric ID.",
        "del_user_admin_forbidden": "⚠️ Cannot delete administrator specified in .env!",
        "del_user_success": "✅ User <code>{target_id}</code> deleted.",
        "del_user_not_found": "❌ User not found in database.",

        # --- Time settings (Admin) ---
        "change_time_prompt": "⏰ Enter new time in HH:MM format (e.g. 08:30):",
        "change_time_invalid": "❌ Invalid format. Enter time as HH:MM (e.g. 07:00 or 19:30)",
        "change_time_success": "✅ Daily automated check time changed to {new_time}"
    }
}


def t(key: str, lang: str = "uk", **kwargs) -> str:
    """
    Returns localized string by key.
    Falls back to default language ('uk') if key or language is missing.
    Supports dynamic string formatting via **kwargs.
    """
    lang = lang if lang in TEXTS else DEFAULT_LANGUAGE
    template = TEXTS.get(lang, {}).get(key)
    if template is None:
        template = TEXTS.get(DEFAULT_LANGUAGE, {}).get(key, key)

    if kwargs:
        try:
            return template.format(**kwargs)
        except (KeyError, IndexError, ValueError):
            return template
    return template


def get_button_variants(key: str) -> list[str]:
    """
    Returns a list of all localized variants for a specific button (used for F.text.in_(...)).
    """
    variants = []
    for lang_dict in TEXTS.values():
        if key in lang_dict:
            val = lang_dict[key]
            if val not in variants:
                variants.append(val)
    return variants
