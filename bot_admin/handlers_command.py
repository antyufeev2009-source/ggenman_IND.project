import os
import sqlite3

from aiogram import Bot, F, Router, types
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile, Message

from address import validate_address
from auth import (
    get_user_by_fio_and_phone,
    get_user_by_tg_id,
    is_registered,
    register_user,
)
from config import HR_DB_PATH, CANDIDATE_BOT_TOKEN, PROXY_URL
from formatting import format_list, format_salary
from states import RegState, VacancyState
from vacancies import (
    delete_vacancy_by_id,
    get_all_vacancies,
    get_vacancy_by_id,
    save_vacancy,
)

router = Router()

# Обрабатывает команду /start, проверяет регистрацию администратора или запрашивает ввод ФИО
@router.message(Command("start"))
async def start_cmd(message: Message, state: FSMContext):
    tg_id = message.from_user.id
    user = get_user_by_tg_id(tg_id)
    await state.clear()

    if user:
        short_name = user[0].split()[1]
        await message.answer(f"С возвращением, {short_name}! Доступ разрешён.")
        return

    await message.answer("Для доступа к боту необходимо пройти регистрацию.\nВведите ваше ФИО (три слова):")
    await state.set_state(RegState.waiting_fio)

# Проверяет формат введенного ФИО и запрашивает номер телефона
@router.message(RegState.waiting_fio)
async def process_fio(message: Message, state: FSMContext):
    fio = message.text.strip()
    if len(fio.split()) != 3:
        await message.answer("ФИО должно состоять из трёх слов. Попробуйте снова.")
        return
    await state.update_data(fio=fio)
    await message.answer("Теперь введите номер телефона (формат: +7XXXXXXXXXX):")
    await state.set_state(RegState.waiting_phone)

# Проверяет номер телефона, сверяет данные с базой администраторов и завершает регистрацию
@router.message(RegState.waiting_phone)
async def process_phone(message: Message, state: FSMContext):
    phone = message.text.strip()
    if not phone.startswith("+7") or len(phone) != 12 or not phone[2:].isdigit():
        await message.answer("Номер телефона должен быть в формате +7XXXXXXXXXX. Попробуйте снова.")
        return

    data = await state.get_data()
    found = get_user_by_fio_and_phone(data["fio"], phone)

    if not found:
        await message.answer("ФИО и номер телефона не найдены в базе. Доступ запрещён.")
        await state.clear()
        return

    user_id, full_name = found
    register_user(user_id, message.from_user.id)
    await message.answer(f"Регистрация успешна, {full_name.split()[1]}! Доступ разрешён.")
    await state.clear()

# Начинает пошаговое создание вакансии и запрашивает наименование компании
@router.message(Command("add"))
async def add_vacancy(message: Message, state: FSMContext):
    if not is_registered(message.from_user.id):
        await message.answer("Доступ запрещён. Вы не зарегистрированы.")
        return
    await message.answer("Введите наименование компании:")
    await state.set_state(VacancyState.company_name)

# Сохраняет название компании и запрашивает название вакансии
@router.message(VacancyState.company_name)
async def vacancy_company(message: Message, state: FSMContext):
    await state.update_data(company_name=message.text.strip())
    await message.answer("Введите название вакансии:")
    await state.set_state(VacancyState.title)

# Сохраняет название вакансии и запрашивает адрес работы
@router.message(VacancyState.title)
async def vacancy_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("Введите адрес работы:")
    await state.set_state(VacancyState.address)

# Валидирует адрес через сервис карт, сохраняет ссылку и запрашивает уровень зарплаты
@router.message(VacancyState.address)
async def vacancy_address(message: Message, state: FSMContext):
    address = message.text.strip()
    link = await validate_address(address)
    if link is None:
        await message.answer("Адрес не является действительным или в нём есть ошибка.\nПопробуйте снова.")
        return
    await state.update_data(address=address, address_link=link)
    await message.answer("Введите зарплату:")
    await state.set_state(VacancyState.salary)

# Форматирует и сохраняет зарплату, запрашивает перечень обязанностей
@router.message(VacancyState.salary)
async def vacancy_salary(message: Message, state: FSMContext):
    await state.update_data(salary=format_salary(message.text.strip()))
    await message.answer("Введите обязанности:")
    await state.set_state(VacancyState.duties)

# Форматирует список обязанностей и запрашивает условия работы
@router.message(VacancyState.duties)
async def vacancy_duties(message: Message, state: FSMContext):
    await state.update_data(duties=format_list(message.text.strip(), numbered=True))
    await message.answer("Введите условия:")
    await state.set_state(VacancyState.conditions)

# Форматирует список условий работы и запрашивает требования к кандидату
@router.message(VacancyState.conditions)
async def vacancy_conditions(message: Message, state: FSMContext):
    await state.update_data(conditions=format_list(message.text.strip(), numbered=True))
    await message.answer("Введите требования:")
    await state.set_state(VacancyState.requirements)

# Форматирует требования, генерирует предпросмотр вакансии в HTML и ожидает подтверждения
@router.message(VacancyState.requirements)
async def vacancy_requirements(message: Message, state: FSMContext):
    await state.update_data(requirements=format_list(message.text.strip(), numbered=False))
    data = await state.get_data()

    vacancy_text = (
        f"🏢 <b>Компания:</b> {data['company_name']}\n"
        f"📌 <b>Вакансия:</b> {data['title']}\n\n"
        f"📍 <b>Адрес работы:</b> <a href='{data['address_link']}'>{data['address']}</a>\n\n"
        f"💰 <b>Зарплата:</b> {data['salary']}\n\n"
        f"📝 <b>Обязанности:</b>\n{data['duties']}\n\n"
        f"💼 <b>Условия:</b>\n{data['conditions']}\n\n"
        f"📋 <b>Требования:</b>\n{data['requirements']}\n\n"
        "Для публикации введите команду /public"
    )
    
    await message.answer(vacancy_text, parse_mode="HTML", disable_web_page_preview=True)
    await state.set_state(VacancyState.waiting_public)

# Сохраняет подготовленную вакансию в базу данных и завершает процесс создания
@router.message(Command("public"))
async def publish_vacancy(message: Message, state: FSMContext):
    if not is_registered(message.from_user.id):
        return
    if await state.get_state() != VacancyState.waiting_public.state:
        await message.answer("Нет вакансии, ожидающей публикации.")
        return

    data = await state.get_data()
    vacancy_id = save_vacancy(data)
    await message.answer(f"Вакансия №{vacancy_id} опубликована!")
    await state.clear()

# Получает и отправляет администратору список всех активных вакансий в HTML
@router.message(Command("vaclist"))
async def vac_list(message: Message):
    if not is_registered(message.from_user.id):
        return

    vacancies = get_all_vacancies()
    if not vacancies:
        await message.answer("Вакансий пока нет.")
        return

    for vac in vacancies:
        vac_id, comp, title, address, link, salary, duties, cond, req = vac
        text = (
            f"🏢 <b>Компания:</b> {comp}\n"
            f"📌 <b>Вакансия №{vac_id}:</b> {title}\n\n"
            f"📍 <b>Адрес:</b>\n<a href='{link}'>{address}</a>\n\n"
            f"💰 <b>Зарплата:</b>\n{salary}\n\n"
            f"📝 <b>Обязанности:</b>\n{duties}\n\n"
            f"💼 <b>Условия:</b>\n{cond}\n\n"
            f"📋 <b>Требования:</b>\n{req}"
        )
        await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

# Находит и отправляет информацию о конкретной вакансии по ее ID из команды
@router.message(F.text.regexp(r"^/vac\d+$"))
async def vac_single(message: Message):
    if not is_registered(message.from_user.id):
        return

    vac_id = int(message.text.strip()[4:])
    vac = get_vacancy_by_id(vac_id)
    if not vac:
        await message.answer(f"Вакансии №{vac_id} не существует.")
        return

    vac_id, comp, title, address, link, salary, duties, cond, req = vac
    text = (
        f"🏢 <b>Компания:</b> {comp}\n"
        f"📌 <b>Вакансия №{vac_id}:</b> {title}\n\n"
        f"📍 <b>Адрес:</b>\n<a href='{link}'>{address}</a>\n\n"
        f"💰 <b>Зарплата:</b>\n{salary}\n\n"
        f"📝 <b>Обязанности:</b>\n{duties}\n\n"
        f"💼 <b>Условия:</b>\n{cond}\n\n"
        f"📋 <b>Требования:</b>\n{req}"
    )
    await message.answer(text, parse_mode="HTML", disable_web_page_preview=True)

# Удаляет вакансию из базы данных по переданному ID команды
@router.message(F.text.regexp(r"^/delvac\d+$"))
async def delete_vacancy(message: Message):
    if not is_registered(message.from_user.id):
        return

    vac_id = int(message.text.strip()[7:])
    if not delete_vacancy_by_id(vac_id):
        await message.answer(f"Вакансии №{vac_id} не существует.")
        return
    await message.answer(f"Вакансия №{vac_id} успешно удалена.")

# Выводит администратору список всех зарегистрированных кандидатов
@router.message(Command("candidates"))
async def cmd_candidates_list(message: types.Message):
    if not is_registered(message.from_user.id): return
    conn = sqlite3.connect(HR_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT id, full_name, telegram_user, city FROM candidates")
    rows = cur.fetchall()
    conn.close()

    if not rows:
        await message.answer("Список кандидатов пуст.")
        return

    text = "📋 <b>Список кандидатов:</b>\n\n"
    for row in rows:
        tg_user = row["telegram_user"] or "Нет @username"
        text += f"👤 [ID: {row['id']}] {row['full_name']} | {tg_user} | г. {row['city']}\n"
    await message.answer(text, parse_mode="HTML")

# Ищет и отображает полную анкету кандидата с фотографией по его Telegram username
@router.message(Command("wt"))
async def cmd_wt(message: types.Message):
    if not is_registered(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ Использование: /wt @username")
        return

    tg_user = args[1] if args[1].startswith("@") else "@" + args[1]
    conn = sqlite3.connect(HR_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM candidates WHERE telegram_user = ? LIMIT 1", (tg_user,))
    profile = cur.fetchone()
    conn.close()

    if not profile:
        await message.answer("Кандидат не найден.")
        return

    text = (
        f"Анкета кандидата\n\nID в базе: {profile['id']}\nФИО: {profile['full_name']}\n"
        f"Дата рождения: {profile['birth_date']} (Возраст: {profile['age']})\n"
        f"Телефон: {profile['phone']}\nTelegram: {profile['telegram_user']}\n"
        f"Специализация: {profile['specialization']}\nЖелаемые вакансии:\n{profile['desired_jobs']}\n"
        f"Город: {profile['city']}\nСоздано: {profile['created_at']}\n"
    )

    if profile["photo_path"] and os.path.exists(profile["photo_path"]):
        await message.answer_photo(FSInputFile(profile["photo_path"]), caption=text)
    else:
        await message.answer(text)

# Отображает список откликов кандидатов на конкретную вакансию
@router.message(Command("wo"))
async def cmd_wo(message: types.Message):
    if not is_registered(message.from_user.id): return
    args = message.text.split()
    if len(args) < 2 or not args[1].isdigit():
        await message.answer("⚠️ Использование: /wo <номер_вакансии>")
        return

    conn = sqlite3.connect(HR_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT c.id, a.candidate_telegram_user, c.full_name, c.city 
        FROM applications a
        LEFT JOIN candidates c ON a.candidate_telegram_id = c.telegram_id
        WHERE a.vacancy_id = ?
    """, (args[1],))
    applications = cur.fetchall()
    conn.close()

    if not applications:
        await message.answer(f"На вакансию #{args[1]} пока нет откликов.")
        return

    text = f"🔥 <b>Отклики на вакансию #{args[1]} ({len(applications)}):</b>\n\n"
    for app in applications:
        name = app["full_name"] or "Имя не указано"
        city = app["city"] or "Не указан"
        tg_user = app["candidate_telegram_user"] or "Нет @username"
        text += f"👤 [ID: {app['id']}] {name} | {tg_user} | г. {city}\n"
    await message.answer(text, parse_mode="HTML")

# Отправляет прямое сообщение кандидату через клиентского бота по его ID или username
@router.message(Command("send"))
async def cmd_send_message(message: Message):
    if not is_registered(message.from_user.id): return
    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer("⚠️ Использование: /send @username Текст или /send ID Текст")
        return

    target, text_to_send = args[1], args[2]
    conn = sqlite3.connect(HR_DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    if target.isdigit():
        cur.execute("SELECT telegram_id, telegram_user FROM candidates WHERE id = ? LIMIT 1", (int(target),))
    else:
        target = target if target.startswith("@") else "@" + target
        cur.execute("SELECT telegram_id, telegram_user FROM candidates WHERE telegram_user = ? LIMIT 1", (target,))
        
    candidate = cur.fetchone()
    conn.close()

    if not candidate:
        await message.answer("❌ Кандидат не найден.")
        return

    try:
        session = AiohttpSession(proxy=PROXY_URL)
        bot = Bot(token=CANDIDATE_BOT_TOKEN, session=session)
        await bot.send_message(
            chat_id=candidate["telegram_id"], 
            text=f"📩 <b>Сообщение от HR-менеджера:</b>\n\n{text_to_send}",
            parse_mode="HTML"
        )
        await bot.session.close()
        await message.answer("✅ Успешно отправлено!")
    except Exception as e:
        await message.answer(f"❌ Ошибка отправки: {e}")