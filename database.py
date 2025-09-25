import sqlite3

conn = sqlite3.connect("users.db")
cursor = conn.cursor()

cursor.execute('''
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    full_name TEXT,
    company TEXT,
    position TEXT,
    phone TEXT,
    username TEXT
)
''')
conn.commit()

def add_or_update_user(user_id, full_name, company, position, phone, username):
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, full_name, company, position, phone, username)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (user_id, full_name, company, position, phone, username))
    conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()