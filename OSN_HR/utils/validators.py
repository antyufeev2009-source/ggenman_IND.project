from datetime import datetime

# Проверяет наличие ровно трех слов в ФИО и приводит каждое к заглавной букве
def normalize_full_name(text: str):
    parts = [p.strip() for p in text.split() if p.strip()]
    if len(parts) != 3:
        return None
    return " ".join(p.capitalize() for p in parts)

# Валидирует дату рождения и вычисляет возраст на текущий момент
def normalize_birth_date(text: str):
    try:
        d = datetime.strptime(text, "%d.%m.%Y")
        today = datetime.today()
        age = today.year - d.year - ((today.month, today.day) < (d.month, d.day))
        return text, age
    except ValueError:
        return None, None

# Извлекает цифры из переданной строки и приводит номер телефона к формату +7
def normalize_phone(text: str):
    digits = "".join(ch for ch in text if ch.isdigit())
    if len(digits) < 10:
        return None
    return "+7" + digits[-10:]

# Преобразует строку с профессиями, перечисленными через запятую, в нумерованный список
def format_jobs(text: str):
    items = [i.strip() for i in text.split(",") if i.strip()]
    return "\n".join(f"{n}. {i.capitalize()}" for n, i in enumerate(items, 1))