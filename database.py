import os
import psycopg2

conn = psycopg2.connect(
    dbname=os.getenv("POSTGRES_DB", "event_bot_db"),
    user=os.getenv("POSTGRES_USER", "admin"),
    password=os.getenv("POSTGRES_PASSWORD", "mypassword"),  # замени на свой
    host=os.getenv("DATABASE_HOST", "db"),
    port=os.getenv("DATABASE_PORT", "5432"),
)
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT,
    company TEXT,
    question TEXT,
    phone TEXT,
    username TEXT
)
''')
conn.commit()

def add_or_update_user(user_id, full_name, company, question, phone, username):
    with conn.cursor() as cursor:
        cursor.execute('''
            INSERT INTO users (user_id, full_name, company, question, phone, username)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (user_id) DO UPDATE
            SET full_name = EXCLUDED.full_name,
                company   = EXCLUDED.company,
                question  = EXCLUDED.question,
                phone     = EXCLUDED.phone,
                username  = EXCLUDED.username
        ''', (user_id, full_name, company, question, phone, username))
        conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()