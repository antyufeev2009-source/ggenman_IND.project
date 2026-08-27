import sqlite3
from config import ADMINS_DB_PATH

# Устанавливает соединение с базой данных администраторов
def get_connection():
    return sqlite3.connect(ADMINS_DB_PATH)

# Создает таблицу администраторов и заполняет ее базовыми контактами по умолчанию
def init_admins_db():
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            phone TEXT NOT NULL UNIQUE,
            tg_id INTEGER,
            status TEXT DEFAULT 'no_register'
        );
    """)
    
    admins = [
        ("Антюфеев Евгений Борисович", "+79889700631"),
        ("Антюфеев Александр Евгеньевич", "+79616601602"),
        ("Антюфеева Анна Николаевна", "+79696560303")
    ]
    
    for full_name, phone in admins:
        cur.execute(
            "INSERT OR IGNORE INTO admins (full_name, phone) VALUES (?, ?)", 
            (full_name, phone)
        )
        
    conn.commit()
    conn.close()