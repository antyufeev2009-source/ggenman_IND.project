import os
import sqlite3
from datetime import datetime
from typing import Optional
from config import DB_PATH

db_dir = os.path.dirname(os.path.abspath(DB_PATH))
if db_dir and not os.path.exists(db_dir):
    os.makedirs(db_dir, exist_ok=True)

# Устанавливает и настраивает соединение с базой данных
def _get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

# Создает таблицы и индексы в базе данных, если они еще не существуют
def init_db():
    with _get_conn() as conn:
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

# Сохраняет новую анкету кандидата или обновляет существующую по Telegram ID
def save_candidate(data: dict):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with _get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT id FROM candidates WHERE telegram_id = ?", (data.get("telegram_id"),))
        if cur.fetchone():
            cur.execute("""
                UPDATE candidates SET
                    full_name=?, birth_date=?, age=?, phone=?, telegram_user=?, 
                    specialization=?, desired_jobs=?, city=?, photo_path=?, updated_at=?
                WHERE telegram_id=?
            """, (data.get("full_name"), data.get("birth_date"), data.get("age"), data.get("phone"),
                  data.get("telegram_user"), data.get("specialization"), data.get("desired_jobs"),
                  data.get("city"), data.get("photo_path"), now, data.get("telegram_id")))
        else:
            cur.execute("""
                INSERT INTO candidates (
                    full_name, birth_date, age, phone, telegram_id, telegram_user, 
                    specialization, desired_jobs, city, photo_path, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (data.get("full_name"), data.get("birth_date"), data.get("age"), data.get("phone"),
                  data.get("telegram_id"), data.get("telegram_user"), data.get("specialization"),
                  data.get("desired_jobs"), data.get("city"), data.get("photo_path"), now))
        conn.commit()

# Получает профиль кандидата из базы данных по его Telegram ID или username
def get_profile(tg_id: Optional[int], tg_user: Optional[str]) -> Optional[dict]:
    with _get_conn() as conn:
        cur = conn.cursor()
        if tg_id and tg_user:
            cur.execute("SELECT * FROM candidates WHERE telegram_id=? OR telegram_user=? LIMIT 1", (tg_id, tg_user))
        elif tg_id:
            cur.execute("SELECT * FROM candidates WHERE telegram_id=? LIMIT 1", (tg_id,))
        elif tg_user:
            cur.execute("SELECT * FROM candidates WHERE telegram_user=? LIMIT 1", (tg_user,))
        else:
            return None
        row = cur.fetchone()
    return dict(row) if row else None