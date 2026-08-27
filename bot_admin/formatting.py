# Экранирует специальные символы для Telegram MarkdownV2
def escape_md(text: str) -> str:
    escape_chars = r"_*[]()~`>#+-=|{}.!"

    for ch in escape_chars:
        text = text.replace(ch, "\\" + ch)

    return text

# Форматирует строку с зарплатой, удаляя лишние слова и добавляя символ рубля
def format_salary(text: str) -> str:
    t = text.lower().strip()

    for bad in ["рублей", "руб", "р"]:
        if bad in t:
            t = t.replace(bad, "").strip()

    return t + "₽"

# Преобразует строку с разделителями в нумерованный или маркированный список
def format_list(text: str, numbered=True) -> str:
    items = [
        item.strip()
        for item in text.split(";")
        if item.strip()
    ]

    formatted = []

    for i, item in enumerate(items, start=1):
        item = item[0].upper() + item[1:] if item else item

        if numbered:
            formatted.append(f"{i}. {item}")
        else:
            formatted.append(f"• {item}")

    return "\n".join(formatted)