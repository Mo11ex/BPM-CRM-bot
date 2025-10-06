from aiogram.types import InlineKeyboardButton, KeyboardButton, ReplyKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

def start_inline_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Хочу подарок", callback_data="gift"))
    return builder.as_markup()

def back_inline_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Назад", callback_data="back"))
    return builder.as_markup()

def main_menu_keyboard():
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="Наши новости", callback_data="news"),
        InlineKeyboardButton(text="Задать вопрос", callback_data="question"),
    )
    builder.row(
        InlineKeyboardButton(text="Запросить демо", callback_data="demo")
    )
    return builder.as_markup()

def yes_no_back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да", callback_data="yes"))
    builder.add(InlineKeyboardButton(text="Нет", callback_data="no"))
    builder.add(InlineKeyboardButton(text="Назад", callback_data="back"))
    return builder.as_markup()

def yes_no_back_keyboard_question():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да", callback_data="yesquestion"))
    builder.add(InlineKeyboardButton(text="Нет", callback_data="noquestion"))
    builder.add(InlineKeyboardButton(text="Назад", callback_data="back"))
    return builder.as_markup()

def contact_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Отправить номер", request_contact=True)],
            [KeyboardButton(text="Назад")]
        ],
        resize_keyboard=True,
        one_time_keyboard=True
    )
    return keyboard