import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
import asyncio
from handlers import router
import handlers

load_dotenv()  # загружает .env

api_key = os.getenv("API_KEY")
bot = Bot(token=api_key)
dp = Dispatcher(storage=MemoryStorage())

async def main():
    dp.include_router(router)

    print("Bot is running...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
