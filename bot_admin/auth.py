from database import get_connection

# Проверяет, привязан ли Telegram ID к какому-либо администратору
def is_registered(tg_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT id FROM admins WHERE tg_id = ?",
        (tg_id,)
    )

    result = cursor.fetchone()

    conn.close()

    return bool(result)

# Возвращает ФИО администратора по его Telegram ID
def get_user_by_tg_id(tg_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT full_name FROM admins WHERE tg_id = ?",
        (tg_id,)
    )

    result = cursor.fetchone()

    conn.close()

    return result

# Ищет администратора в базе по совпадению ФИО и номера телефона
def get_user_by_fio_and_phone(fio: str, phone: str):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, full_name
        FROM admins
        WHERE full_name = ? AND phone = ?
    """, (fio, phone))

    result = cursor.fetchone()

    conn.close()

    return result

# Привязывает Telegram ID к записи администратора и обновляет статус
def register_user(user_id: int, tg_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE admins
        SET tg_id = ?, status = 'register'
        WHERE id = ?
    """, (tg_id, user_id))

    conn.commit()
    conn.close()