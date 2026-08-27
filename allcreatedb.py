import sqlite3
import os

SHARED_DIR = "/app/OSN_HR"
os.makedirs(SHARED_DIR, exist_ok=True)

ADMINS_DB_PATH = os.path.join(SHARED_DIR, "admins.db")
HR_DB_PATH = os.path.join(SHARED_DIR, "hr.db")

# Создает таблицу администраторов и заполняет ее базовыми контактами по умолчанию
def init_admins_db():
    conn = sqlite3.connect(ADMINS_DB_PATH)
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

# Создает таблицы и индексы основной базы данных HR (вакансии, кандидаты, отклики)
def init_hr_db():
    conn = sqlite3.connect(HR_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;") 
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY,
            company_name TEXT,
            title TEXT, address TEXT, address_link TEXT,
            salary TEXT, duties TEXT, conditions TEXT, requirements TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT, birth_date TEXT, age INTEGER, phone TEXT,
            telegram_id INTEGER UNIQUE, telegram_user TEXT UNIQUE,
            specialization TEXT, desired_jobs TEXT, city TEXT,
            photo_path TEXT, created_at TEXT DEFAULT (datetime('now','localtime')),
            updated_at TEXT
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id INTEGER,
            candidate_telegram_id INTEGER,
            candidate_telegram_user TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (vacancy_id) REFERENCES vacancies (id),
            FOREIGN KEY (candidate_telegram_id) REFERENCES candidates (telegram_id)
        )
    """)
    
    cur.execute("CREATE INDEX IF NOT EXISTS idx_tg_id ON candidates(telegram_id)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_app_vac_id ON applications(vacancy_id)")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    init_admins_db()
    init_hr_db()