# db_async.py (пример, с asyncpg)
import os
import asyncpg
import logging

logger = logging.getLogger(__name__)
_pool: asyncpg.pool.Pool | None = None

async def init_db_pool():
    global _pool
    if _pool is not None:
        return

    db_config = {
        'user': os.getenv('POSTGRES_USER', 'admin'),
        'password': os.getenv('POSTGRES_PASSWORD', 'mypassword'),
        'database': os.getenv('POSTGRES_DB', 'event_bot_db'),
        'host': os.getenv('DATABASE_HOST', 'db'),
        'port': int(os.getenv('DATABASE_PORT', 5432)),
    }
    logger.info('Initializing DB pool...')
    _pool = await asyncpg.create_pool(min_size=1, max_size=10, **db_config)
    # Создадим таблицу, если её нет
    async with _pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id BIGINT PRIMARY KEY,
                full_name TEXT,
                company TEXT,
                question TEXT,
                phone TEXT,
                username TEXT
            )
        ''')

        # Проверяем, есть ли колонка created_at
        column_info = await conn.fetchrow('''
                    SELECT column_name, data_type
                    FROM information_schema.columns
                    WHERE table_name='users' AND column_name='created_at'
                ''')

        if column_info is None:
            # Колонки нет — создаём TIMESTAMPTZ с московским временем
            await conn.execute('''
                        ALTER TABLE users
                        ADD COLUMN created_at TIMESTAMPTZ DEFAULT (NOW() AT TIME ZONE 'Europe/Moscow')
                    ''')
            logger.info("Column created_at added as TIMESTAMPTZ with Moscow timezone")
        elif column_info['data_type'] == 'timestamp without time zone':
            # Колонка есть как TIMESTAMP — конвертируем в TIMESTAMPTZ
            await conn.execute('''
                        ALTER TABLE users
                        ALTER COLUMN created_at TYPE TIMESTAMPTZ
                        USING created_at AT TIME ZONE 'Europe/Moscow'
                    ''')
            logger.info("Column created_at converted from TIMESTAMP to TIMESTAMPTZ with Moscow timezone")

        # Обновляем NULL значения старых записей
        await conn.execute('''
                    UPDATE users
                    SET created_at = NOW() AT TIME ZONE 'Europe/Moscow'
                    WHERE created_at IS NULL
                ''')

    logger.info('DB pool initialized')


async def close_db_pool():
    global _pool
    if _pool is None:
        return
    await _pool.close()
    _pool = None
    logger.info('DB pool closed')


async def add_or_update_user(user_id: int, full_name: str | None, company: str | None,
question: str | None, phone: str | None, username: str | None):
    """Insert or update user in DB."""
    global _pool
    if _pool is None:
        raise RuntimeError('DB pool is not initialized. Call init_db_pool() first')

    async with _pool.acquire() as conn:
        await conn.execute('''
            INSERT INTO users (user_id, full_name, company, question, phone, username)
            VALUES ($1, $2, $3, $4, $5, $6)
            ON CONFLICT (user_id) DO UPDATE
            SET full_name = EXCLUDED.full_name,
                company = EXCLUDED.company,
                question = EXCLUDED.question,
                phone = EXCLUDED.phone,
                username = EXCLUDED.username
        ''', user_id, full_name, company, question, phone, username)


async def get_user(user_id: int):
    """Return a Record-like tuple (same order as earlier code) or None."""
    global _pool
    if _pool is None:
        raise RuntimeError('DB pool is not initialized. Call init_db_pool() first')

    async with _pool.acquire() as conn:
        row = await conn.fetchrow('SELECT user_id, full_name, company, question, phone, username FROM users WHERE user_id = $1', user_id)
        return row # может быть None или asyncpg.Record