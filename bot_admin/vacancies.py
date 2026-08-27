import sqlite3
from config import HR_DB_PATH

# Устанавливает соединение с базой данных
def get_connection():
    conn = sqlite3.connect(HR_DB_PATH)
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

# Создает таблицы и индексы при первой инициализации базы данных
def init_hr_db():
    conn = get_connection()
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
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id INTEGER,
            candidate_telegram_id INTEGER,
            candidate_telegram_user TEXT,
            created_at TEXT DEFAULT (datetime('now', 'localtime')),
            FOREIGN KEY (vacancy_id) REFERENCES vacancies (id)
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

    cur.execute("CREATE INDEX IF NOT EXISTS idx_app_vac_id ON applications(vacancy_id)")
    conn.commit()
    conn.close()

# Сохраняет новую вакансию в базу и возвращает ее ID
def save_vacancy(data: dict) -> int:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id FROM vacancies ORDER BY id ASC")
    existing_ids = [row[0] for row in cursor.fetchall()]

    vac_id = 1
    for eid in existing_ids:
        if eid == vac_id:
            vac_id += 1
        else:
            break

    cursor.execute("""
        INSERT INTO vacancies (
            id, company_name, title, address, address_link, salary, duties, conditions, requirements
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        vac_id, data["company_name"], data["title"], data["address"], data["address_link"],
        data["salary"], data["duties"], data["conditions"], data["requirements"]
    ))

    conn.commit()
    conn.close()
    return vac_id

# Получает все данные конкретной вакансии по ее ID
def get_vacancy_by_id(vac_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vacancies WHERE id = ?", (vac_id,))
    row = cursor.fetchone()
    conn.close()
    return row

# Получает список всех существующих вакансий
def get_all_vacancies():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM vacancies ORDER BY id ASC")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Удаляет вакансию и все связанные с ней отклики
def delete_vacancy_by_id(vac_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM vacancies WHERE id = ?", (vac_id,))
    exists = cursor.fetchone()

    if not exists:
        conn.close()
        return False

    cursor.execute("DELETE FROM applications WHERE vacancy_id = ?", (vac_id,))
    cursor.execute("DELETE FROM vacancies WHERE id = ?", (vac_id,))

    conn.commit()
    conn.close()
    return True