import asyncio
import logging
from dotenv import load_dotenv

# Загрузим переменные окружения
load_dotenv()

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from database import init_db_pool, close_db_pool
from handlers import router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = None

async def main():
    global API_KEY
    API_KEY = __import__('os').getenv('API_KEY')
    if not API_KEY:
        logger.error('API_KEY not found in environment. Set API_KEY in .env')
        return

    # Инициализация пула БД
    await init_db_pool()

    bot = Bot(token=API_KEY)
    dp = Dispatcher(storage=MemoryStorage())

    dp.include_router(router)

    logger.info('Bot is starting...')
    try:
        await dp.start_polling(bot)
    finally:
        logger.info('Shutting down...')
        await close_db_pool()
        # корректно закрываем сессию бота
        try:
            await bot.session.close()
        except Exception:
            pass

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass