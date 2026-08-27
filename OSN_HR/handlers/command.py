import os
import sqlite3
import sys

from aiogram import Dispatcher, F, types, Bot
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import DB_PATH, ADMIN_BOT_TOKEN, ADMINS_DB_PATH, PROXY_URL
from db.database import get_profile, save_candidate
from file_storage.photos import save_photo_locally
from messages.registration import (
    ASK_BIRTH_DATE, ASK_CITY, ASK_FULL_NAME, ASK_JOBS, ASK_PHONE, 
    ASK_PHOTO, ASK_SPECIALIZATION, CONFIRM_TEXT, REG_CANCELLED, REG_FINISHED
)
from states.registration import RegState
from utils.validators import format_jobs, normalize_birth_date, normalize_full_name, normalize_phone

# Регистрирует все обработчики сообщений и callback-вызовов
def register_all_handlers(dp: Dispatcher):
    
    # Обрабатывает команду /start, проверяет регистрацию и запускает процесс анкетирования
    @dp.message(Command("start"))
    async def cmd_start(message: types.Message, state: FSMContext):
        await state.clear()
        tg_id = message.from_user.id
        tg_user = f"@{message.from_user.username}" if message.from_user.username else None

        if profile := get_profile(tg_id, tg_user):
            await message.answer(f"Добро пожаловать, {profile['full_name'].split()[1]}!")
            return

        await state.update_data(telegram_id=tg_id, telegram_user=tg_user)
        await message.answer(ASK_FULL_NAME)
        await state.set_state(RegState.full_name)

    # Обрабатывает ввод ФИО кандидата и запрашивает фотографию
    @dp.message(RegState.full_name)
    async def h_full_name(message: types.Message, state: FSMContext):
        if not (v := normalize_full_name(message.text)):
            await message.answer("❌ ФИО должно состоять из 3 слов.")
            return
        await state.update_data(full_name=v)
        await message.answer(ASK_PHOTO)
        await state.set_state(RegState.photo)

    # Сохраняет фотографию кандидата и запрашивает дату рождения
    @dp.message(RegState.photo)
    async def h_photo(message: types.Message, state: FSMContext):
        if not message.photo:
            await message.answer("❌ Отправьте фото.")
            return
        await state.update_data(photo_path=await save_photo_locally(message))
        await message.answer(ASK_BIRTH_DATE)
        await state.set_state(RegState.birth_date)

    # Проверяет дату рождения, вычисляет возраст и запрашивает номер телефона
    @dp.message(RegState.birth_date)
    async def h_birth_date(message: types.Message, state: FSMContext):
        date, age = normalize_birth_date(message.text)
        if not date:
            await message.answer("❌ Неверный формат даты.")
            return
        await state.update_data(birth_date=date, age=age)
        await message.answer(ASK_PHONE)
        await state.set_state(RegState.phone)

    # Валидирует номер телефона и запрашивает специализацию
    @dp.message(RegState.phone)
    async def h_phone(message: types.Message, state: FSMContext):
        if not (phone := normalize_phone(message.text)):
            await message.answer("❌ Неверный номер.")
            return
        await state.update_data(phone=phone)
        await message.answer(ASK_SPECIALIZATION)
        await state.set_state(RegState.specialization)

    # Сохраняет специализацию и запрашивает желаемые должности
    @dp.message(RegState.specialization)
    async def h_spec(message: types.Message, state: FSMContext):
        await state.update_data(specialization=message.text)
        await message.answer(ASK_JOBS)
        await state.set_state(RegState.desired_jobs)

    # Форматирует список желаемых должностей и запрашивает город
    @dp.message(RegState.desired_jobs)
    async def h_jobs(message: types.Message, state: FSMContext):
        await state.update_data(desired_jobs=format_jobs(message.text))
        await message.answer(ASK_CITY)
        await state.set_state(RegState.city)

    # Сохраняет город и выводит собранную анкету для подтверждения кандидатом
    @dp.message(RegState.city)
    async def h_city(message: types.Message, state: FSMContext):
        await state.update_data(city=message.text)
        data = await state.get_data()
        preview = (
            f"Проверьте данные:\n\nФИО: {data.get('full_name')}\n"
            f"Дата рождения: {data.get('birth_date')} (Возраст: {data.get('age')})\n"
            f"Телефон: {data.get('phone')}\nTelegram: {data.get('telegram_user')}\n"
            f"Специализация: {data.get('specialization')}\nЖелаемые вакансии:\n{data.get('desired_jobs')}\n"
            f"Город: {data.get('city')}\n\n{CONFIRM_TEXT}"
        )
        await message.answer(preview)
        await state.set_state(RegState.confirm)

    # Обрабатывает решение пользователя, сохраняет анкету в базу или отменяет регистрацию
    @dp.message(RegState.confirm)
    async def h_confirm(message: types.Message, state: FSMContext):
        if message.text.lower() != "да":
            await message.answer(REG_CANCELLED)
            await state.clear()
            return
            
        data = await state.get_data()
        data.setdefault("telegram_user", f"@{message.from_user.username}" if message.from_user.username else None)
        data.setdefault("telegram_id", message.from_user.id)
        
        save_candidate(data)
        await message.answer(REG_FINISHED)
        await state.clear()

    # Выводит профиль пользователя с фотографией и сохраненными данными
    @dp.message(Command("profile"))
    async def cmd_profile(message: types.Message):
        if not (profile := get_profile(message.from_user.id, f"@{message.from_user.username}" if message.from_user.username else None)):
            await message.answer("Доступ запрещён. Зарегистрируйтесь через /start.")
            return

        text = (
            f"Ваша анкета\n\nФИО: {profile['full_name']}\nДата рождения: {profile['birth_date']} "
            f"(Возраст: {profile['age']})\nТелефон: {profile['phone']}\nTelegram: {profile['telegram_user']}\n"
            f"Специализация: {profile['specialization']}\nЖелаемые вакансии:\n{profile['desired_jobs']}\n"
            f"Город: {profile['city']}\n"
        )
        if profile.get("photo_path") and os.path.exists(profile["photo_path"]):
            await message.answer_photo(FSInputFile(profile["photo_path"]), caption=text)
        else:
            await message.answer(text)

    # Удаляет анкету кандидата из базы данных и стирает локальный файл фотографии
    @dp.message(Command("delme"))
    async def cmd_delme(message: types.Message, state: FSMContext):
        telegram_id = message.from_user.id
        if not get_profile(telegram_id, None):
            return await message.answer("Доступ запрещён. Зарегистрируйтесь через /start.")

        try:
            with sqlite3.connect(DB_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT photo_path FROM candidates WHERE telegram_id = ?", (telegram_id,))
                
                if row := cursor.fetchone():
                    if row["photo_path"] and os.path.exists(row["photo_path"]):
                        os.remove(row["photo_path"])
                
                cursor.execute("DELETE FROM candidates WHERE telegram_id = ?", (telegram_id,))
                conn.commit()
                
            await state.clear()
            await message.answer("❌ Ваша анкета и данные успешно удалены.")
        except Exception as e:
            await message.answer("⚠️ Ошибка удаления данных.")

    # Возвращает следующую вакансию, на которую кандидат еще не откликался
    def get_next_vacancy(tg_id: int, current_id: int) -> dict | None:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("""
                SELECT * FROM vacancies WHERE id > ? 
                AND id NOT IN (SELECT vacancy_id FROM applications WHERE candidate_telegram_id = ?)
                ORDER BY id ASC LIMIT 1
            """, (current_id, tg_id))
            row = cur.fetchone()
        return dict(row) if row else None

    # Формирует и отправляет сообщение с описанием вакансии и кнопками действий
    async def send_vacancy(message: types.Message, vac: dict):
        text = (
            f"🏢 <b>Компания: {vac['company_name']}</b>\n"
            f"📌 <b>Вакансия: {vac['title']}</b>\n\n"
            f"📍 Адрес: <a href='{vac['address_link']}'>{vac['address']}</a>\n"
            f"💰 Зарплата: {vac['salary']}\n\n"
            f"📋 <b>Обязанности:</b>\n{vac['duties']}\n\n"
            f"⚙️ <b>Требования:</b>\n{vac['requirements']}\n\n"
            f"🤝 <b>Условия:</b>\n{vac['conditions']}\n"
        )
        builder = InlineKeyboardBuilder()
        builder.button(text="✅ Откликнуться", callback_data=f"apply_{vac['id']}")
        builder.button(text="❌ Игнор", callback_data=f"ignore_{vac['id']}")
        await message.answer(text, reply_markup=builder.adjust(2).as_markup(), parse_mode="HTML", disable_web_page_preview=True)

    # Обрабатывает команду /vaclist и предлагает начать просмотр вакансий
    @dp.message(Command("vaclist"))
    async def cmd_vaclist(message: types.Message):
        if not get_profile(message.from_user.id, None):
            return await message.answer("Зарегистрируйтесь через /start.")
        builder = InlineKeyboardBuilder()
        builder.button(text="🚀 Начать просмотр", callback_data="start_vaclist")
        await message.answer("Готовы посмотреть доступные вакансии?", reply_markup=builder.as_markup())

    # Запускает процесс просмотра вакансий, отправляя первую доступную
    @dp.callback_query(F.data == "start_vaclist")
    async def start_vaclist(callback: types.CallbackQuery):
        if not get_profile(callback.from_user.id, None): return await callback.answer("Регистрация!", show_alert=True)
        await callback.message.delete()
        
        if vac := get_next_vacancy(callback.from_user.id, 0):
            await send_vacancy(callback.message, vac)
        else:
            await callback.message.answer("К сожалению, новых вакансий пока нет.")
        await callback.answer()

    # Обрабатывает отклик на вакансию, сохраняет его и уведомляет администраторов через отдельного бота
    @dp.callback_query(F.data.startswith("apply_"))
    async def process_application(callback: types.CallbackQuery):
        candidate_tg_id = callback.from_user.id
        if not get_profile(candidate_tg_id, None): return await callback.answer("Регистрация!", show_alert=True)

        vacancy_id = int(callback.data.split("_")[1])
        candidate_tg_user = f"@{callback.from_user.username}" if callback.from_user.username else None

        with sqlite3.connect(DB_PATH) as conn:
            cur = conn.cursor()
            cur.execute("SELECT id FROM vacancies WHERE id = ?", (vacancy_id,))
            if not cur.fetchone():
                return await callback.answer("❌ Вакансия неактуальна.", show_alert=True)

            cur.execute("SELECT id FROM applications WHERE vacancy_id=? AND candidate_telegram_id=?", (vacancy_id, candidate_tg_id))
            if cur.fetchone():
                return await callback.answer("Уже откликнулись!", show_alert=True)

            cur.execute("INSERT INTO applications (vacancy_id, candidate_telegram_id, candidate_telegram_user) VALUES (?, ?, ?)",
                        (vacancy_id, candidate_tg_id, candidate_tg_user))
            conn.commit()

        try:
            with sqlite3.connect(ADMINS_DB_PATH) as conn_admin:
                admins = conn_admin.cursor().execute("SELECT tg_id FROM admins WHERE status='register'").fetchall()
            
            if admins:
                bot = Bot(token=ADMIN_BOT_TOKEN, session=AiohttpSession(proxy=PROXY_URL))
                notify = f"Новый отклик на вакансию {vacancy_id}.\nВведите /wo {vacancy_id}"
                for (adm_id,) in admins:
                    if adm_id:
                        try: await bot.send_message(adm_id, text=notify)
                        except: pass
                await bot.session.close()
        except: pass

        await callback.message.edit_text(f"{callback.message.html_text}\n\n<i>✅ Вы откликнулись!</i>", parse_mode="HTML")
        await callback.answer("Отклик сохранен!", show_alert=True)

        if next_vac := get_next_vacancy(candidate_tg_id, vacancy_id):
            await send_vacancy(callback.message, next_vac)
        else:
            await callback.message.answer("🎉 Вы просмотрели все вакансии!")

    # Обрабатывает пропуск вакансии и переходит к следующей доступной
    @dp.callback_query(F.data.startswith("ignore_"))
    async def process_ignore(callback: types.CallbackQuery):
        if not get_profile(callback.from_user.id, None): return await callback.answer("Регистрация!", show_alert=True)

        vacancy_id = int(callback.data.split("_")[1])
        await callback.message.edit_text(f"{callback.message.html_text}\n\n<i>❌ Пропущена</i>", parse_mode="HTML")
        await callback.answer("Вакансия пропущена")
        
        if next_vac := get_next_vacancy(callback.from_user.id, vacancy_id):
            await send_vacancy(callback.message, next_vac)
        else:
            await callback.message.answer("🎉 Вы просмотрели все вакансии!")