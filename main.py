import asyncio
import logging
import os
import re
import html
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F, BaseMiddleware
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import TelegramObject
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from database import (
    SessionLocal, User, Phone, PriceHistory, Settings, init_db,
    get_user_language, set_user_language
)
from scraper import get_phone_data, find_chrome_path
from locales import (
    t, get_button_variants, SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE
)

# --- 1. CONFIGURATION & INITIALIZATION ---
load_dotenv()
API_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone="Europe/Kyiv")

# Flag to prevent overlapping manual or automated checks
is_checking = False


# Define FSM states
class Form(StatesGroup):
    waiting_for_url = State()  # Waiting for product link input
    waiting_for_username = State()  # Waiting for username or numeric ID
    waiting_for_delete_id = State()  # Waiting for product ID to delete
    waiting_for_settings_time = State()  # Waiting for check time update (HH:MM)
    waiting_for_user_delete_id = State()  # Waiting for user ID to delete


def setup_admins():
    """Populates admins from .env into the database on startup"""
    if not ADMIN_IDS:
        return

    with SessionLocal() as db:
        for tg_id in ADMIN_IDS:
            existing_user = db.query(User).filter(User.telegram_id == tg_id).first()
            if not existing_user:
                new_admin = User(telegram_id=tg_id, is_admin=1, language=DEFAULT_LANGUAGE)
                db.add(new_admin)
                logger.info(f"➕ Added admin: {tg_id}")
            else:
                if existing_user.is_admin != 1:
                    existing_user.is_admin = 1
                    logger.info(f"🆙 Admin permissions updated for: {tg_id}")
        db.commit()


def check_access(tg_id: int) -> bool:
    """Verifies access: first against ADMIN_IDS (.env), then in the database"""
    if tg_id in ADMIN_IDS:
        return True
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        return bool(user)


def is_admin(tg_id: int) -> bool:
    """Verifies if user has administrator privileges"""
    if tg_id in ADMIN_IDS:
        return True
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == tg_id).first()
        return bool(user and user.is_admin == 1)


# --- ACCESS CONTROL & LOCALIZATION MIDDLEWARE ---
class AccessMiddleware(BaseMiddleware):
    """
    Blocks incoming messages and callbacks from unauthorized users
    not present in .env or the database.
    """
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user = data.get("event_from_user")
        if not user:
            return await handler(event, data)

        user_lang = get_user_language(user.id)
        data["user_lang"] = user_lang

        if not check_access(user.id):
            if isinstance(event, types.Message):
                await event.answer(t("access_denied", user_lang))
            elif isinstance(event, types.CallbackQuery):
                await event.answer(t("access_denied", user_lang), show_alert=True)
            return

        return await handler(event, data)


dp.message.outer_middleware(AccessMiddleware())
dp.callback_query.outer_middleware(AccessMiddleware())


# --- 2. KEYBOARDS ---
def main_menu(user_id: int, lang: str = DEFAULT_LANGUAGE):
    builder = ReplyKeyboardBuilder()
    builder.button(text=t("btn_prices", lang))

    if is_admin(user_id):
        builder.button(text=t("btn_check_now", lang))
        builder.button(text=t("btn_add_product", lang))
        builder.button(text=t("btn_delete_product", lang))
        builder.button(text=t("btn_settings", lang))
        builder.adjust(2, 3)
    else:
        builder.button(text=t("btn_settings", lang))
        builder.adjust(2)

    return builder.as_markup(resize_keyboard=True)


def cancel_menu(lang: str = DEFAULT_LANGUAGE):
    builder = ReplyKeyboardBuilder()
    builder.button(text=t("btn_cancel", lang))
    return builder.as_markup(resize_keyboard=True)


def settings_menu(user_id: int, lang: str = DEFAULT_LANGUAGE):
    builder = InlineKeyboardBuilder()
    if is_admin(user_id):
        builder.button(text=t("btn_add_user", lang), callback_data="add_user")
        builder.button(text=t("btn_list_users", lang), callback_data="list_users")
        builder.button(text=t("btn_del_user", lang), callback_data="del_user")
        builder.button(text=t("btn_change_time", lang), callback_data="change_time")

    current_lang_label = SUPPORTED_LANGUAGES.get(lang, "🇺🇦 Українська")
    builder.button(text=t("btn_change_lang", lang, current=current_lang_label), callback_data="open_lang_menu")
    builder.adjust(1)
    return builder.as_markup()


def language_menu(lang: str = DEFAULT_LANGUAGE):
    builder = InlineKeyboardBuilder()
    for code, name in SUPPORTED_LANGUAGES.items():
        checkmark = " ✅" if code == lang else ""
        builder.button(text=f"{name}{checkmark}", callback_data=f"set_lang:{code}")
    builder.button(text=t("btn_back", lang), callback_data="back_to_settings")
    builder.adjust(1)
    return builder.as_markup()


async def send_chunked_message(chat_id: int, text: str):
    """Sends long message in chunks up to 3800 characters to prevent Telegram limit overflow"""
    if len(text) <= 3800:
        await bot.send_message(chat_id, text, parse_mode="HTML", disable_web_page_preview=True)
        return

    paragraphs = text.split("\n\n")
    current_chunk = ""
    for p in paragraphs:
        if len(current_chunk) + len(p) + 2 > 3800:
            if current_chunk.strip():
                await bot.send_message(chat_id, current_chunk.strip(), parse_mode="HTML", disable_web_page_preview=True)
            current_chunk = p + "\n\n"
        else:
            current_chunk += p + "\n\n"

    if current_chunk.strip():
        await bot.send_message(chat_id, current_chunk.strip(), parse_mode="HTML", disable_web_page_preview=True)


def build_broadcast_text(price_events: list[dict], status_events: list[dict], lang: str) -> str:
    """Builds localized notification text for price and stock availability changes"""
    changes_report = ""
    for ev in price_events:
        if ev["type"] == "initial_price":
            changes_report += t("report_initial_price", lang, url=ev["url"], name=ev["name"], price=ev["price"])
        elif ev["type"] == "price_change":
            diff = ev["diff"]
            diff_sign = f"+{diff}" if diff > 0 else f"{diff}"
            emoji = "📈" if diff > 0 else "📉"
            changes_report += t(
                "report_price_changed", lang,
                emoji=emoji,
                url=ev["url"],
                name=ev["name"],
                old_price=ev["old_price"],
                new_price=ev["new_price"],
                diff_sign=diff_sign
            )

    status_report = ""
    for ev in status_events:
        if ev["type"] == "redirected":
            status_report += t("report_item_redirected", lang, url=ev["url"], name=ev["name"])
        elif ev["type"] == "out_of_stock":
            status_report += t("report_item_out_of_stock", lang, url=ev["url"], name=ev["name"])
        elif ev["type"] == "back_in_stock":
            price_str = t("report_price_for_str", lang, price=ev["price"]) if ev.get("price") else ""
            status_report += t("report_item_back_in_stock", lang, url=ev["url"], name=ev["name"], price_str=price_str)

    text = ""
    if changes_report:
        text += t("report_changes_header", lang) + changes_report
    if status_report:
        text += t("report_status_header", lang) + status_report
    return text


# --- 3. CORE PRICE CHECKING LOGIC (CONCURRENT) ---
async def run_full_check(target_chat_id: int = None):
    """
    Main routine for checking prices and stock status.
    Runs concurrently (3 items in parallel) to reduce check time from ~15 minutes to ~30 seconds.
    """
    with SessionLocal() as db:
        phones = db.query(Phone).all()
        if not phones:
            if target_chat_id:
                initiator_lang = get_user_language(target_chat_id)
                await bot.send_message(target_chat_id, t("check_empty", initiator_lang))
            return

    # Check up to 3 links concurrently for optimal speed and resource usage
    semaphore = asyncio.Semaphore(3)

    async def fetch_and_update(phone):
        async with semaphore:
            return phone, await asyncio.to_thread(get_phone_data, phone.url)

    tasks = [fetch_and_update(p) for p in phones]
    results = await asyncio.gather(*tasks)

    price_events = []
    status_events = []
    out_of_stock_items = []
    removed_items = []
    error_items = []

    with SessionLocal() as db:
        for phone_obj, data in results:
            db_phone = db.get(Phone, phone_obj.id)
            if not db_phone:
                continue

            safe_name = html.escape(db_phone.name)
            old_available = getattr(db_phone, "is_available", 1)
            old_price = db_phone.current_price

            if not data:
                error_items.append(safe_name)
                continue

            # 1. PRODUCT REDIRECTED / REMOVED FROM STORE
            if data.get("is_redirected"):
                if old_available == 1:
                    status_events.append({
                        "type": "redirected",
                        "url": db_phone.url,
                        "name": safe_name
                    })
                    db_phone.is_available = 0
                removed_items.append(safe_name)
                continue

            # 2. STOCK AVAILABILITY CHANGE
            new_available = 1 if data.get("is_available", True) else 0

            if old_available != new_available:
                db_phone.is_available = new_available
                if new_available == 0:
                    status_events.append({
                        "type": "out_of_stock",
                        "url": db_phone.url,
                        "name": safe_name
                    })
                else:
                    new_pr = data.get("price") or old_price
                    status_events.append({
                        "type": "back_in_stock",
                        "url": db_phone.url,
                        "name": safe_name,
                        "price": new_pr
                    })

            if new_available == 0:
                out_of_stock_items.append(safe_name)

            # 3. PRICE CHANGE (if a valid new price was fetched)
            new_price = data.get("price")
            if new_price:
                # Update item name if previously 'Unknown'
                if data.get("name") and data["name"] not in ("Невідомо", "Unknown") and db_phone.name in ("Невідомо", "Unknown"):
                    db_phone.name = data["name"]
                    safe_name = html.escape(data["name"])

                if old_price is None:
                    price_events.append({
                        "type": "initial_price",
                        "url": db_phone.url,
                        "name": safe_name,
                        "price": new_price
                    })
                    db_phone.current_price = new_price
                    db.add(PriceHistory(phone_id=db_phone.id, price=new_price))
                elif old_price != new_price:
                    diff = new_price - old_price
                    price_events.append({
                        "type": "price_change",
                        "url": db_phone.url,
                        "name": safe_name,
                        "old_price": old_price,
                        "new_price": new_price,
                        "diff": diff
                    })
                    db_phone.current_price = new_price
                    db.add(PriceHistory(phone_id=db_phone.id, price=new_price))

        db.commit()

    # --- BROADCAST NOTIFICATIONS ---
    has_broadcast_changes = bool(price_events or status_events)

    if has_broadcast_changes:
        with SessionLocal() as db:
            all_users = db.query(User).all()

        recipient_ids = {u.telegram_id for u in all_users} | set(ADMIN_IDS)

        for user_id in recipient_ids:
            try:
                user_lang = get_user_language(user_id)
                broadcast_text = build_broadcast_text(price_events, status_events, user_lang)
                if broadcast_text:
                    await send_chunked_message(user_id, broadcast_text)
                    await asyncio.sleep(0.05)
            except Exception as e:
                logger.error(f"Failed to send report to user {user_id}: {e}")

    # Reply to manual check initiator
    if target_chat_id:
        initiator_lang = get_user_language(target_chat_id)
        if not has_broadcast_changes:
            msg = t("report_no_changes", initiator_lang)
            if out_of_stock_items:
                msg += t("report_out_of_stock_list", initiator_lang) + "\n".join(f"• {x}" for x in out_of_stock_items)
            if removed_items:
                msg += t("report_removed_list", initiator_lang) + "\n".join(f"• {x}" for x in removed_items)
            if error_items:
                msg += t("report_error_list", initiator_lang) + "\n".join(f"• {x}" for x in error_items)

            await send_chunked_message(target_chat_id, msg)
        else:
            await bot.send_message(target_chat_id, t("report_sent_to_all", initiator_lang))


# --- 4. COMMAND & BUTTON HANDLERS ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    lang = get_user_language(message.from_user.id)
    await message.answer(t("start_msg", lang), reply_markup=main_menu(message.from_user.id, lang))


@dp.message(Command("cancel"))
@dp.message(F.text.in_(get_button_variants("btn_cancel")))
async def cancel_action(message: types.Message, state: FSMContext):
    lang = get_user_language(message.from_user.id)
    await state.clear()
    await message.answer(t("action_cancelled", lang), reply_markup=main_menu(message.from_user.id, lang))


# --- BUTTON: Current Prices ---
@dp.message(F.text.in_(get_button_variants("btn_prices")))
async def show_prices(message: types.Message):
    lang = get_user_language(message.from_user.id)
    with SessionLocal() as db:
        phones = db.query(Phone).all()
        if not phones:
            await message.answer(t("prices_empty", lang))
            return

        header = t("prices_header", lang)
        lines = []
        for p in phones:
            safe_name = html.escape(p.name)
            price_val = f"<b>{p.current_price} {t('currency', lang)}</b>" if p.current_price else t("no_data", lang)

            if getattr(p, "is_available", 1) == 0:
                status_str = t("prices_out_of_stock", lang, price=price_val)
            else:
                status_str = t("prices_available", lang, price=price_val)

            lines.append(f"▪️ <a href='{p.url}'>{safe_name}</a>\n  └ {status_str}\n")

    current_chunk = header
    for line in lines:
        if len(current_chunk) + len(line) > 3800:
            await message.answer(current_chunk, parse_mode="HTML", disable_web_page_preview=True)
            current_chunk = ""
        current_chunk += line

    if current_chunk:
        await message.answer(current_chunk, parse_mode="HTML", disable_web_page_preview=True)


# --- BUTTON: Check Now ---
@dp.message(F.text.in_(get_button_variants("btn_check_now")))
async def manual_check(message: types.Message):
    if not is_admin(message.from_user.id):
        return

    lang = get_user_language(message.from_user.id)
    global is_checking
    if is_checking:
        await message.answer(t("check_already_running", lang))
        return

    is_checking = True
    await message.answer(t("check_started", lang))
    try:
        await run_full_check(target_chat_id=message.from_user.id)
    finally:
        is_checking = False


# --- BUTTON: Add Product ---
@dp.message(F.text.in_(get_button_variants("btn_add_product")))
async def process_add_product(message: types.Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    lang = get_user_language(message.from_user.id)
    await message.answer(t("add_prompt_url", lang), reply_markup=cancel_menu(lang))
    await state.set_state(Form.waiting_for_url)


@dp.message(Form.waiting_for_url)
async def catch_url(message: types.Message, state: FSMContext):
    lang = get_user_language(message.from_user.id)
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    raw_url = message.text.strip()
    if not raw_url.startswith("http"):
        await message.answer(t("add_invalid_url", lang))
        return

    # Strip UTM parameters and GET query parameters
    clean_url = raw_url.split("?")[0].strip()

    # Check if product is already tracked
    with SessionLocal() as db:
        existing = db.query(Phone).filter(Phone.url == clean_url).first()
        if existing:
            price_val = f"{existing.current_price} {t('currency', lang)}" if existing.current_price else t("no_data", lang)
            await message.answer(
                t("add_already_tracked", lang, name=html.escape(existing.name), price=price_val),
                parse_mode="HTML",
                reply_markup=main_menu(message.from_user.id, lang)
            )
            await state.clear()
            return

    msg = await message.answer(t("add_checking_url", lang))
    try:
        data = await asyncio.to_thread(get_phone_data, clean_url)
    except Exception as e:
        logger.error(f"Scraper error: {e}")
        data = None

    if data and data.get("price"):
        is_avail = 1 if data.get("is_available", True) else 0
        with SessionLocal() as db:
            new_phone = Phone(
                name=data["name"],
                url=clean_url,
                current_price=data["price"],
                is_available=is_avail
            )
            db.add(new_phone)
            db.commit()
            # Add initial price history record
            db.add(PriceHistory(phone_id=new_phone.id, price=data["price"]))
            db.commit()

        await msg.delete()
        stock_note = "" if is_avail else t("add_stock_note_out", lang)
        await message.answer(
            t(
                "add_success", lang,
                url=clean_url,
                name=html.escape(data["name"]),
                price=data["price"],
                stock_note=stock_note
            ),
            parse_mode="HTML",
            disable_web_page_preview=True,
            reply_markup=main_menu(message.from_user.id, lang)
        )
    else:
        await msg.delete()
        fail_msg = t("add_fail_price", lang)
        if data and data.get("is_redirected"):
            fail_msg += t("add_fail_redirect", lang)
        elif data and not data.get("is_available", True):
            fail_msg += t("add_fail_not_available", lang)
        await message.answer(fail_msg, reply_markup=main_menu(message.from_user.id, lang))

    await state.clear()


# --- BUTTON: Delete Product ---
@dp.message(F.text.in_(get_button_variants("btn_delete_product")))
async def list_products_for_delete(message: types.Message, state: FSMContext):
    lang = get_user_language(message.from_user.id)
    if not is_admin(message.from_user.id):
        return

    with SessionLocal() as db:
        phones = db.query(Phone).all()
        if not phones:
            await message.answer(t("del_empty", lang))
            return

        header = t("del_list_header", lang)
        lines = []
        for p in phones:
            safe_name = html.escape(p.name)
            lines.append(f"<code>ID: {p.id}</code> — {safe_name}\n")

    current_chunk = header
    for line in lines:
        if len(current_chunk) + len(line) > 3800:
            await message.answer(current_chunk, parse_mode="HTML")
            current_chunk = ""
        current_chunk += line

    current_chunk += t("del_prompt", lang)
    await message.answer(current_chunk, parse_mode="HTML", reply_markup=cancel_menu(lang))
    await state.set_state(Form.waiting_for_delete_id)


@dp.message(Form.waiting_for_delete_id)
async def process_delete(message: types.Message, state: FSMContext):
    lang = get_user_language(message.from_user.id)
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    if not message.text.strip().isdigit():
        await message.answer(t("del_invalid_id", lang))
        return

    product_id = int(message.text.strip())

    with SessionLocal() as db:
        phone = db.query(Phone).filter(Phone.id == product_id).first()
        if phone:
            name = phone.name
            db.delete(phone)
            db.commit()
            await message.answer(
                t("del_success", lang, name=html.escape(name), product_id=product_id),
                parse_mode="HTML",
                reply_markup=main_menu(message.from_user.id, lang)
            )
        else:
            await message.answer(
                t("del_not_found", lang, product_id=product_id),
                reply_markup=main_menu(message.from_user.id, lang)
            )

    await state.clear()


# --- BUTTON: Settings ---
@dp.message(F.text.in_(get_button_variants("btn_settings")))
async def show_settings(message: types.Message):
    lang = get_user_language(message.from_user.id)
    await message.answer(t("settings_title", lang), reply_markup=settings_menu(message.from_user.id, lang))


# --- SETTINGS: LANGUAGE SELECTION ---
@dp.callback_query(F.data == "open_lang_menu")
async def open_lang_menu_handler(callback: types.CallbackQuery):
    lang = get_user_language(callback.from_user.id)
    await callback.message.edit_text(t("settings_lang_choose", lang), reply_markup=language_menu(lang))
    await callback.answer()


@dp.callback_query(F.data == "back_to_settings")
async def back_to_settings_handler(callback: types.CallbackQuery):
    lang = get_user_language(callback.from_user.id)
    await callback.message.edit_text(t("settings_title", lang), reply_markup=settings_menu(callback.from_user.id, lang))
    await callback.answer()


@dp.callback_query(F.data.startswith("set_lang:"))
async def set_lang_handler(callback: types.CallbackQuery):
    new_lang = callback.data.split(":")[1]
    if new_lang not in SUPPORTED_LANGUAGES:
        new_lang = DEFAULT_LANGUAGE

    set_user_language(callback.from_user.id, new_lang)

    # Toast pop-up alert
    await callback.answer(t("settings_lang_updated_alert", new_lang))

    # Update inline settings card to the new language
    await callback.message.edit_text(
        t("settings_title", new_lang),
        reply_markup=settings_menu(callback.from_user.id, new_lang)
    )

    # Send updated reply keyboard with localized buttons
    await callback.message.answer(
        t("settings_lang_updated_msg", new_lang),
        reply_markup=main_menu(callback.from_user.id, new_lang)
    )


# --- SETTINGS: ADD USER ---
@dp.callback_query(F.data == "add_user")
async def trigger_add_user(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    lang = get_user_language(callback.from_user.id)
    await callback.message.answer(
        t("add_user_prompt", lang),
        parse_mode="HTML",
        reply_markup=cancel_menu(lang)
    )
    await state.set_state(Form.waiting_for_username)
    await callback.answer()


@dp.message(Form.waiting_for_username)
async def catch_username(message: types.Message, state: FSMContext):
    lang = get_user_language(message.from_user.id)
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    input_data = message.text.strip()
    user_id = None

    if input_data.isdigit():
        user_id = int(input_data)
    else:
        target_username = input_data if input_data.startswith("@") else f"@{input_data}"
        try:
            chat = await bot.get_chat(target_username)
            user_id = chat.id
        except Exception:
            await message.answer(
                t("add_user_not_found", lang),
                reply_markup=main_menu(message.from_user.id, lang)
            )
            await state.clear()
            return

    with SessionLocal() as db:
        existing = db.query(User).filter(User.telegram_id == user_id).first()
        if existing:
            await message.answer(t("add_user_exists", lang), reply_markup=main_menu(message.from_user.id, lang))
        else:
            new_user = User(telegram_id=user_id, is_admin=0, language=DEFAULT_LANGUAGE)
            db.add(new_user)
            db.commit()
            await message.answer(
                t("add_user_success", lang, user_id=user_id),
                parse_mode="HTML",
                reply_markup=main_menu(message.from_user.id, lang)
            )

    await state.clear()


# --- SETTINGS: USER LIST ---
@dp.callback_query(F.data == "list_users")
async def list_users(callback: types.CallbackQuery):
    if not is_admin(callback.from_user.id):
        return
    lang = get_user_language(callback.from_user.id)
    with SessionLocal() as db:
        users = db.query(User).all()
        text = t("list_users_header", lang)
        for u in users:
            status = t("role_admin", lang) if (u.is_admin == 1 or u.telegram_id in ADMIN_IDS) else t("role_user", lang)
            flag = "🇺🇦" if getattr(u, "language", "uk") == "uk" else "🇬🇧"
            text += f"ID: <code>{u.telegram_id}</code> | {status} ({flag})\n"

    await callback.message.answer(text, parse_mode="HTML")
    await callback.answer()


# --- SETTINGS: DELETE USER ---
@dp.callback_query(F.data == "del_user")
async def delete_user_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    lang = get_user_language(callback.from_user.id)
    await callback.message.answer(t("del_user_prompt", lang), reply_markup=cancel_menu(lang))
    await state.set_state(Form.waiting_for_user_delete_id)
    await callback.answer()


@dp.message(Form.waiting_for_user_delete_id)
async def delete_user_process(message: types.Message, state: FSMContext):
    lang = get_user_language(message.from_user.id)
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    if not message.text.strip().isdigit():
        await message.answer(t("del_user_invalid", lang))
        return

    target_id = int(message.text.strip())

    if target_id in ADMIN_IDS:
        await message.answer(t("del_user_admin_forbidden", lang), reply_markup=main_menu(message.from_user.id, lang))
        await state.clear()
        return

    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == target_id).first()
        if user:
            db.delete(user)
            db.commit()
            await message.answer(
                t("del_user_success", lang, target_id=target_id),
                parse_mode="HTML",
                reply_markup=main_menu(message.from_user.id, lang)
            )
        else:
            await message.answer(t("del_user_not_found", lang), reply_markup=main_menu(message.from_user.id, lang))
    await state.clear()


# --- SETTINGS: CHANGE CHECK TIME ---
@dp.callback_query(F.data == "change_time")
async def change_time_start(callback: types.CallbackQuery, state: FSMContext):
    if not is_admin(callback.from_user.id):
        return
    lang = get_user_language(callback.from_user.id)
    await callback.message.answer(t("change_time_prompt", lang), reply_markup=cancel_menu(lang))
    await state.set_state(Form.waiting_for_settings_time)
    await callback.answer()


@dp.message(Form.waiting_for_settings_time)
async def change_time_process(message: types.Message, state: FSMContext):
    lang = get_user_language(message.from_user.id)
    if not is_admin(message.from_user.id):
        await state.clear()
        return

    new_time = message.text.strip()

    if not re.match(r'^([01]?[0-9]|2[0-3]):[0-5][0-9]$', new_time):
        await message.answer(t("change_time_invalid", lang))
        return

    hour, minute = map(int, new_time.split(":"))

    with SessionLocal() as db:
        setting = db.query(Settings).first()
        if not setting:
            setting = Settings(check_time=new_time)
            db.add(setting)
        else:
            setting.check_time = new_time
        db.commit()

    # Update scheduler job without resetting the scheduler instance
    scheduler.add_job(
        run_full_check,
        'cron',
        hour=hour,
        minute=minute,
        id="daily_price_check",
        replace_existing=True
    )

    await message.answer(
        t("change_time_success", lang, new_time=new_time),
        reply_markup=main_menu(message.from_user.id, lang)
    )
    await state.clear()


# --- 5. ENTRY POINT (MAIN) ---
async def main():
    # 1. Initialize database and admin users
    init_db()
    setup_admins()

    # 2. Retrieve scheduled check time
    with SessionLocal() as db:
        setting = db.query(Settings).first()
        check_time = setting.check_time if setting else "07:00"

    hour, minute = map(int, check_time.split(":"))

    # 3. Configure and start scheduler
    scheduler.add_job(
        run_full_check,
        'cron',
        hour=hour,
        minute=minute,
        id="daily_price_check",
        replace_existing=True
    )
    scheduler.start()

    chrome_path = find_chrome_path()
    if chrome_path:
        logger.info(f"🌐 Browser executable detected: {chrome_path}")
    else:
        logger.warning("⚠️ No Chrome or Chromium binary found! Ensure Google Chrome is installed or set CHROME_PATH in .env")

    logger.info(f"🚀 Tracker v3.0 successfully started! Daily check scheduled for {check_time}")

    # 4. Start Telegram bot polling
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
