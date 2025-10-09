import asyncio
import html
import os
import logging
from email.message import EmailMessage
from pathlib import Path
from dotenv import load_dotenv
import aiosmtplib
from aiogram.types import FSInputFile
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from datetime import datetime, timezone, timedelta
from aiogram import types
from aiogram.exceptions import TelegramBadRequest
from database import add_or_update_user, get_user
from keyboards import start_inline_keyboard, back_inline_keyboard, main_menu_keyboard, yes_no_back_keyboard, \
    contact_keyboard, yes_no_back_keyboard_question
from texts import *

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
router = Router()

class Form(StatesGroup):
    questions = State()
    full_name = State()
    company_position = State()
    phone = State()

# helper: найти директорию с медиа
BASE_DIR = Path(__file__).resolve().parent
POSSIBLE_MEDIA_DIRS = [BASE_DIR / 'files', BASE_DIR / 'file', BASE_DIR.parent / 'files', BASE_DIR.parent / 'file']
MEDIA_DIR = None
for d in POSSIBLE_MEDIA_DIRS:
    if d.exists():
        MEDIA_DIR = d
        break
    if MEDIA_DIR is None:
        MEDIA_DIR = BASE_DIR # fallback

async def handle_stale_callback(callback: types.CallbackQuery, state) -> bool:
    """
    Пытается безопасно удалить сообщение с inline-кнопкой.
    Если сообщение слишком старое или Telegram вернул ошибку удаления,
    отправляет пользователю уведомление и меню в зависимости от сценария.

    Возвращает True — если выполнился fallback (нужно прервать дальнейшую обработку),
    False — если удаление прошло успешно и можно продолжать обычную обработку.
    """
    # снимем "часики" у клиента
    try:
        await callback.answer()
    except Exception:
        pass

    msg = callback.message
    if not msg:
        # Нет сообщения — ничего не делаем, но лучше прервать обработку
        return True

    # Предварительная проверка возраста — чтобы не полагаться только на исключение
    try:
        age = datetime.now(timezone.utc) - msg.date
        if age > timedelta(hours=48):
            # сообщение слишком старое — показываем приветствие и меню по сценарию
            data = await state.get_data()
            scenario = data.get("scenario")
            await state.clear()
            await callback.message.answer(STALE_TEXT)
            if scenario == "gift":
                await callback.message.answer(START_MSG, reply_markup=start_inline_keyboard())
            else:
                await callback.message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())
            return True
    except Exception:
        # если не получилось определить дату — продолжаем и попробуем удалить (или падём в except ниже)
        pass

    # Пробуем удалить; если Telegram вернёт ошибку — делаем fallback
    try:
        await msg.delete()
        return False  # удаление прошло — можно продолжать обработку
    except TelegramBadRequest as e:
        text = str(e).lower()
        # Проверяем на типичную ошибку "can't be deleted for everyone" или общую ошибку удаления
        if "can't be deleted for everyone" in text or "message can't be deleted" in text or "message to delete not found" in text:
            data = await state.get_data()
            scenario = data.get("scenario")
            await state.clear()
            # сначала уведомление
            try:
                await callback.message.answer(STALE_TEXT)
            except Exception:
                pass
            # а затем меню в зависимости от сценария
            try:
                if scenario == "gift":
                    await callback.message.answer(START_MSG, reply_markup=start_inline_keyboard())
                else:
                    await callback.message.answer(MAIN_MENU_MSG_48, reply_markup=main_menu_keyboard())
            except Exception:
                pass
            return True
        # если это другая ошибка — пробрасываем, чтобы не скрыть баги
        raise

# /start
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = await get_user(message.from_user.id)
    if user:
        await message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())
    else:
        await message.answer(START_MSG, reply_markup=start_inline_keyboard())

# Обработка inline callback
@router.callback_query()
async def callback_handler(callback: types.CallbackQuery, state: FSMContext):
    demo_request = False
    user_id = callback.from_user.id
    data = callback.data
    if await handle_stale_callback(callback, state):
        return

    if data == "gift":
        await state.update_data(scenario="gift")


        pdf_path = MEDIA_DIR / 'Политика обработки и защиты персональных данных.pdf'
        if not pdf_path.exists():
            await callback.message.answer('Файл политики не найден. Обратитесь к администратору.')
            return

        # Загружаем PDF-файл из папки
        pdf_file = FSInputFile(path=str(pdf_path))
        await callback.message.answer_document(
            pdf_file,
            caption=ASK_FULL_NAME,
            reply_markup=back_inline_keyboard()
        )

        await state.set_state(Form.full_name)

    elif data == "back":
        data = await state.get_data()
        scenario = data.get("scenario")
        await state.clear()
        if scenario == "gift":
            # По умолчанию – возврат в стартовое сообщение
            await callback.message.answer(START_MSG, reply_markup=start_inline_keyboard())
        else:
            await callback.message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())

        return

    elif data == "news":
        await callback.message.answer(NEWS_MSG)
        await callback.message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())

    elif data == "demo":
        await state.update_data(scenario="demo")
        user = await get_user(user_id)
        if user:
            await callback.message.answer(DEMO_ASK_CONFIRM.format(user[4]), reply_markup=yes_no_back_keyboard())

    elif data == "question":
        await state.update_data(scenario="question")
        user = await get_user(user_id)
        if user:
            await callback.message.answer(QUESTIONS, reply_markup=back_inline_keyboard())
            await state.set_state(Form.questions)

    elif data == "yes":
        user = await get_user(user_id)
        if user:
            await send_email_to_sales_demo(user)
            await callback.message.answer(DEMO_THANKS)
            await callback.message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())

    elif data == "yesquestion":
        user = await get_user(user_id)
        if user:
            await send_email_to_sales_question(user)
            await callback.message.answer(DEMO_THANKS)
            await callback.message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())

    elif data == "no":
        await state.update_data(scenario="no")
        await callback.message.answer(DEMO_OTHER_PHONE, reply_markup=back_inline_keyboard())
        await state.set_state(Form.phone)

    elif data == "noquestion":
        await state.update_data(scenario="noquestion")
        await callback.message.answer(DEMO_OTHER_PHONE, reply_markup=back_inline_keyboard())
        await state.set_state(Form.phone)

# FSM обработка сообщений
@router.message(Form.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text) # Обновляем full_name

    await message.answer(ASK_COMPANY_POSITION, reply_markup=back_inline_keyboard()) # Переходим в вопрос о компании
    await state.set_state(Form.company_position) # Устанавливаем стейт

@router.message(Form.company_position)
async def process_company_position(message: types.Message, state: FSMContext):
    await state.update_data(company_position=message.text) # Обновляем company_position

    await message.answer(ASK_CONTACT, reply_markup=contact_keyboard()) # Переходим в вопрос о номере телефона
    await state.set_state(Form.phone) # Устанавливаем стейт

@router.message(Form.questions)
async def process_question(message: types.Message, state: FSMContext):
    await state.update_data(question=message.text)

    # Сначала попробуем получить данные из состояния FSM
    data = await state.get_data()
    user_id = message.from_user.id
    user_from_db = await get_user(user_id)

    full_name = data.get('full_name') or (user_from_db[1] if user_from_db else "")
    company = data.get('company_position') or (user_from_db[2] if user_from_db else "")
    question = data.get('question') or message.text or (user_from_db[3] if user_from_db else "")
    phone = data.get('phone') or (user_from_db[4] if user_from_db else "")
    username = message.from_user.username

    # Сохраняем пользователя в базу
    await add_or_update_user(user_id, full_name, company, question, phone, username)

    data = await state.get_data()
    scenario = data.get("scenario")
    print(scenario)
    user = await get_user(user_id)
    if user:
        await message.answer(DEMO_ASK_CONFIRM.format(user[4]), reply_markup=yes_no_back_keyboard_question())

    await state.clear()

@router.message(Form.phone, F.content_type.in_([types.ContentType.TEXT, types.ContentType.CONTACT]))
async def process_phone(message: types.Message, state: FSMContext):
    phone = message.contact.phone_number if message.contact else message.text

    # Сначала попробуем получить данные из состояния FSM
    data = await state.get_data()
    user_id = message.from_user.id
    user_from_db = await get_user(user_id)

    full_name = data.get('full_name') or (user_from_db[1] if user_from_db else "")
    company = data.get('company_position') or (user_from_db[2] if user_from_db else "")
    question = data.get('question') or (user_from_db[3] if user_from_db else "")
    username = message.from_user.username

    # Сохраняем пользователя в базу
    await add_or_update_user(user_id, full_name, company, question, phone, username)

    data = await state.get_data()
    scenario = data.get("scenario")


    if scenario == "gift":

        if message.text == "Назад":
            await state.clear()
            await message.answer(START_MSG, reply_markup=start_inline_keyboard())
            return

        all_media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')
        gift_photo = FSInputFile(path=os.path.join(all_media_dir, 'gift.JPG'))
        await message.answer_photo(gift_photo, caption=THANKS_GIFT, show_caption_above_media=True,
                                   reply_markup=types.ReplyKeyboardRemove())


    if scenario == "no":
        user = await get_user(user_id)
        if user:
            await send_email_to_sales_demo(user)
            await message.answer(DEMO_THANKS)

    if scenario == "noquestion":
        user = await get_user(user_id)
        if user:
            await send_email_to_sales_question(user)
            await message.answer(DEMO_THANKS)

    await message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())
    await state.clear()

class EmailSendError(Exception):
    """Ошибка при отправке email."""
    pass



# Функция отправки email
async def send_email_to_sales_question(user_data):
    full_name, company, question, phone, username = user_data[1], user_data[2], user_data[3], user_data[4], user_data[5]
    logger.info("Тут мы отправялем данные: " + full_name + " " + company + " " + question + " " + phone + " " + username )

    # Простейшая валидация входных данных (можно расширить)
    if not full_name:
        logger.warning("Пустое поле full_name при отправке письма")
    if not os.getenv('EMAIL_TO'):
        logger.error("EMAIL_TO не задан в конфиге")
        raise EmailSendError("EMAIL_TO не задан в конфиге")

    # Формируем тело письма (plain + html альтернативa)
    plain = (
        f"ФИО: {full_name}\n"
        f"Компания: {company}\n"
        f"Вопрос/Комментарий: {question}\n"
        f"Телефон: {phone}\n"
        f"Telegram: @{username}"
    )

    # Экранируем значения для HTML
    def esc(s: str | None) -> str:
        return html.escape(s or "")

    html_body = (
            "<html><body>"
            "<h3>Новая заявка: вопрос</h3>"
            "<table cellpadding='4' cellspacing='0'>"
            f"<tr><td><b>ФИО</b></td><td>{esc(full_name)}</td></tr>"
            f"<tr><td><b>Компания</b></td><td>{esc(company)}</td></tr>"
            f"<tr><td><b>Вопрос</b></td><td>{esc(question)}</td></tr>"
            f"<tr><td><b>Телефон</b></td><td>{esc(phone)}</td></tr>"
            f"<tr><td><b>Telegram</b></td><td>@{esc(username)}</td></tr>"
            "</table>"
            "</body></html>"
    )

    msg = EmailMessage()
    msg["From"] = os.getenv('EMAIL_FROM')
    msg["To"] = os.getenv('EMAIL_TO')
    msg["Subject"] = "Новая заявка: вопрос"
    msg.set_content(plain)
    msg.add_alternative(html_body, subtype="html")

    # Отправка с retry и экспоненциальным бэкоффом
    max_retries = 3
    base_delay = 1.0  # секунды
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            await aiosmtplib.send(
                msg,
                hostname=os.getenv('SMTP_HOST'),
                port=os.getenv('SMTP_PORT'),
                start_tls=True,
                username=os.getenv('SMTP_USER'),
                password=os.getenv('SMTP_PASSWORD')
            )
            logger.info("Письмо успешно отправлено на %s (попытка %d)", os.getenv('EMAIL_TO'), attempt)
            return
        except Exception as exc:
            last_exc = exc
            logger.warning("Попытка %d: ошибка при отправке почты: %s", attempt, exc, exc_info=False)
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                logger.debug("Ждем %.1f сек перед следующей попыткой", delay)
                await asyncio.sleep(delay)

    logger.exception("Не удалось отправить письмо после %d попыток", max_retries)
    raise EmailSendError("Не удалось отправить письмо") from last_exc

# Функция отправки email
async def send_email_to_sales_demo(user_data):
    full_name, company, question, phone, username = user_data[1], user_data[2], user_data[3], user_data[4], user_data[5]
    logger.info("Тут мы отправялем данные: " + full_name + " " + company + " " + question + " " + phone + " " + username )

    # Простейшая валидация входных данных (можно расширить)
    if not full_name:
        logger.warning("Пустое поле full_name при отправке письма")
    if not os.getenv('EMAIL_TO'):
        logger.error("EMAIL_TO не задан в конфиге")
        raise EmailSendError("EMAIL_TO не задан в конфиге")

    # Формируем тело письма (plain + html альтернативa)
    plain = (
        f"ФИО: {full_name}\n"
        f"Компания: {company}\n"
        f"Телефон: {phone}\n"
        f"Telegram: @{username}"
    )

    # Экранируем значения для HTML
    def esc(s: str | None) -> str:
        return html.escape(s or "")

    html_body = (
            "<html><body>"
            "<h3>Новая заявка на демо</h3>"
            "<table cellpadding='4' cellspacing='0'>"
            f"<tr><td><b>ФИО</b></td><td>{esc(full_name)}</td></tr>"
            f"<tr><td><b>Компания</b></td><td>{esc(company)}</td></tr>"
            f"<tr><td><b>Телефон</b></td><td>{esc(phone)}</td></tr>"
            f"<tr><td><b>Telegram</b></td><td>@{esc(username)}</td></tr>"
            "</table>"
            "</body></html>"
    )

    msg = EmailMessage()
    msg["From"] = os.getenv('EMAIL_FROM')
    msg["To"] = os.getenv('EMAIL_TO')
    msg["Subject"] = "Новая заявка на демо"
    msg.set_content(plain)
    msg.add_alternative(html_body, subtype="html")

    # Отправка с retry и экспоненциальным бэкоффом
    max_retries = 3
    base_delay = 1.0  # секунды
    last_exc: Exception | None = None

    for attempt in range(1, max_retries + 1):
        try:
            await aiosmtplib.send(
                msg,
                hostname=os.getenv('SMTP_HOST'),
                port=os.getenv('SMTP_PORT'),
                start_tls=True,
                username=os.getenv('SMTP_USER'),
                password=os.getenv('SMTP_PASSWORD')
            )
            logger.info("Письмо успешно отправлено на %s (попытка %d)", os.getenv('EMAIL_TO'), attempt)
            return
        except Exception as exc:
            last_exc = exc
            logger.warning("Попытка %d: ошибка при отправке почты: %s", attempt, exc, exc_info=False)
            if attempt < max_retries:
                delay = base_delay * (2 ** (attempt - 1))
                logger.debug("Ждем %.1f сек перед следующей попыткой", delay)
                await asyncio.sleep(delay)

    logger.exception("Не удалось отправить письмо после %d попыток", max_retries)
    raise EmailSendError("Не удалось отправить письмо") from last_exc