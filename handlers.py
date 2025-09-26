import os
from aiogram.types import FSInputFile
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from database import add_or_update_user, get_user
from keyboards import start_inline_keyboard, back_inline_keyboard, main_menu_keyboard, yes_no_back_keyboard, contact_keyboard
from texts import *

router = Router()

class Form(StatesGroup):
    questions = State()
    full_name = State()
    company_position = State()
    phone = State()

# /start
@router.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    user = get_user(message.from_user.id)
    if user:
        await message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())
    else:
        await message.answer(START_MSG, reply_markup=start_inline_keyboard())

# Обработка inline callback
@router.callback_query()
async def callback_handler(callback: types.CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    data = callback.data

    if data == "gift":
        await state.update_data(scenario="gift")
        await callback.message.delete()
        all_media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'files')
        # Загружаем PDF-файл из папки
        pdf_file = FSInputFile(path=os.path.join(all_media_dir, 'Политика обработки и защиты персональных данных.pdf'))
        await callback.message.answer_document(
            pdf_file,
            caption=ASK_FULL_NAME,
            reply_markup=back_inline_keyboard()
        )
        await state.set_state(Form.full_name)

    elif data == "back":
        data = await state.get_data()
        scenario = data.get("scenario")
        if scenario == "demo":
            # Возврат в главное меню
            await state.clear()
            await callback.message.delete()
            await callback.message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())
            #await message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())
        elif scenario == "question":
            await state.clear()
            await callback.message.delete()
            await callback.message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())
        else:
            # По умолчанию – возврат в стартовое сообщение
            await state.clear()
            await callback.message.delete()
            await callback.message.answer(START_MSG, reply_markup=start_inline_keyboard())
        return

        await state.clear()
        await callback.message.answer(START_MSG, reply_markup=start_inline_keyboard())

    elif data == "news":
        await callback.message.delete()
        await callback.message.answer(NEWS_MSG)
        await callback.message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())

    elif data == "demo":
        await callback.message.delete()
        user = get_user(user_id)
        await state.update_data(scenario="demo")
        if user:
            await callback.message.answer(DEMO_ASK_CONFIRM.format(user[4]), reply_markup=yes_no_back_keyboard())

    elif data == "question":
        await callback.message.delete()
        user = get_user(user_id)
        await state.update_data(scenario="question")
        if user:
            await callback.message.answer(QUESTIONS, reply_markup=back_inline_keyboard())
            await state.set_state(Form.questions)

    elif data == "yes":
        await callback.message.delete()
        user = get_user(user_id)
        if user:
            await send_email_to_sales(user)
            await callback.message.answer(DEMO_THANKS)
            await callback.message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())

    elif data == "no":
        await callback.message.delete()
        await state.update_data(scenario="no")
        await callback.message.answer(DEMO_OTHER_PHONE, reply_markup=back_inline_keyboard())
        await state.set_state(Form.phone)

# FSM обработка сообщений
@router.message(Form.full_name)
async def process_full_name(message: types.Message, state: FSMContext):
    await state.update_data(full_name=message.text)

    #await message.answer_document(pdf_file)
    await message.answer(ASK_COMPANY_POSITION, reply_markup=back_inline_keyboard())
    await state.set_state(Form.company_position)

@router.message(Form.company_position)
async def process_company_position(message: types.Message, state: FSMContext):
    await state.update_data(company_position=message.text)
    await message.answer(ASK_CONTACT, reply_markup=contact_keyboard())
    await state.set_state(Form.phone)

@router.message(Form.questions)
async def process_question(message: types.Message, state: FSMContext):
    await state.update_data(question=message.text)

    # Сначала попробуем получить данные из состояния FSM
    data = await state.get_data()
    user_id = message.from_user.id
    user_from_db = get_user(user_id)

    full_name = data.get('full_name') or (user_from_db[1] if user_from_db else "")
    company = data.get('company_position') or (user_from_db[2] if user_from_db else "")
    question = data.get('question') or message.text or (user_from_db[3] if user_from_db else "")
    phone = data.get('phone') or (user_from_db[4] if user_from_db else "")
    username = message.from_user.username

    # Сохраняем пользователя в базу
    add_or_update_user(user_id, full_name, company, question, phone, username)

    data = await state.get_data()
    scenario = data.get("scenario")
    print(scenario)
    if scenario == "gift":
        await message.answer(THANKS_GIFT, reply_markup=types.ReplyKeyboardRemove())
        await message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())
        await state.clear()
    else:
        user = get_user(user_id)
        if user:
            await message.answer(DEMO_ASK_CONFIRM.format(user[4]), reply_markup=yes_no_back_keyboard())
        #await message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())
        await state.clear()
    #await state.update_data(scenario="demo")
    #await state.set_state(Form.questions)
    #if user:
        #await callback.message.answer(DEMO_ASK_CONFIRM.format(user[4]), reply_markup=yes_no_back_keyboard())
    #await message.answer(ASK_CONTACT, reply_markup=contact_keyboard())
    #await state.set_state(Form.phone)

@router.message(Form.phone, F.content_type.in_([types.ContentType.TEXT, types.ContentType.CONTACT]))
async def process_phone(message: types.Message, state: FSMContext):
    if message.text == "Назад":
        await state.clear()
        await message.answer(START_MSG, reply_markup=start_inline_keyboard())
        return

    phone = message.contact.phone_number if message.contact else message.text

    # Сначала попробуем получить данные из состояния FSM
    data = await state.get_data()
    user_id = message.from_user.id
    user_from_db = get_user(user_id)

    full_name = data.get('full_name') or (user_from_db[1] if user_from_db else "")
    company = data.get('company_position') or (user_from_db[2] if user_from_db else "")
    question = data.get('question') or (user_from_db[3] if user_from_db else "")
    username = message.from_user.username

    # Сохраняем пользователя в базу
    add_or_update_user(user_id, full_name, company, question, phone, username)

    data = await state.get_data()
    scenario = data.get("scenario")
    print(scenario)
    if scenario == "gift":
        await message.answer(THANKS_GIFT, reply_markup=types.ReplyKeyboardRemove())

    if scenario == "no":
        user = get_user(user_id)
        if user:
            await send_email_to_sales(user)
            await message.answer(DEMO_THANKS)

    await message.answer(MAIN_MENU_MSG, reply_markup=main_menu_keyboard())
    await state.clear()



# Функция отправки email
async def send_email_to_sales(user_data):
    full_name, company, position, phone, username = user_data[1], user_data[2], user_data[3], user_data[4], user_data[5]
    print("Тут мы отправялем данные: " + full_name + " " + company + " " + position + " " + phone + " " + username )
    #msg = EmailMessage()
    #msg["From"] = config.EMAIL_FROM
    #msg["To"] = config.EMAIL_TO
    #msg["Subject"] = "Новая заявка на демо"
    #msg.set_content(f"ФИО: {full_name}\nКомпания: {company}\nДолжность: {position}\nТелефон: {phone}")

    #await aiosmtplib.send(
   #     msg,
    #    hostname=config.SMTP_HOST,
    #    port=config.SMTP_PORT,
    #    start_tls=True,
    #    username=config.SMTP_USER,
    #    password=config.SMTP_PASSWORD
    #)

"""
router = Router()

@router.message()
async def handler_step1(message, state):

    await state.set_state(DialogBot.step1)

@router.message()
async def handler_step2(message, state):

   await state.set_state(DialogBot.step2)

@router.message()
async def handler_step4(message, state):

   await state.clear()




@router.callback_query(F.data == 'Gift')
async def gift(call):
    print('Пользователь нажал на кнопку Gift')
    await call.answer()

# При начале диалога с ботом (когда пишется в бота /start)
@router.message(CommandStart())
async def start(message):
    # Отвечаем на сообщение
    await message.answer(texts.start, reply_markup=keyboards.inline_gift)
   
"""