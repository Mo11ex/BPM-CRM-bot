from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
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
    builder.add(InlineKeyboardButton(text="Наши новости", callback_data="news"))
    builder.add(InlineKeyboardButton(text="Запросить демо", callback_data="demo"))
    return builder.as_markup()

def yes_no_back_keyboard():
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Да", callback_data="yes"))
    builder.add(InlineKeyboardButton(text="Нет", callback_data="no"))
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

"""
inline_gift = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Хочу подарок!", callback_data='Gift'),
        ],
    ],
)

inline_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Новости Коруса", callback_data='News'),
            InlineKeyboardButton(text="Запросить демо", callback_data='subscribe'),
        ],
    ],
)
"""