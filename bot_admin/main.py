import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.types import BotCommand

from config import API_TOKEN, PROXY_URL
from handlers_command import router as main_router
from database import init_admins_db
from vacancies import init_hr_db

session = AiohttpSession(proxy=PROXY_URL)
bot = Bot(token=API_TOKEN, session=session)
dp = Dispatcher()

# Устанавливает меню команд для бота
async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="Начать работу с ботом"),
        BotCommand(command="add", description="Добавить новую вакансию"),
        BotCommand(command="public", description="Опубликовать вакансию"),
        BotCommand(command="vaclist", description="Показать все вакансии"),
        BotCommand(command="wo", description="Просмотр откликов (/wo <номер>)"),
        BotCommand(command="wt", description="Просмотр профиля кандидата (/wt @username)"),
        BotCommand(command="candidates", description="Список кандидатов в боте"),
        BotCommand(command="delvac", description="Удаление вакансии по номеру (/delvac(номер))"),
        BotCommand(command="send", description="Отправить сообщение кандидату (/send(id/user))"),
    ]
    await bot.set_my_commands(commands)

# Инициализирует базы данных, настраивает роутеры и запускает бота
async def main():
    init_admins_db()
    init_hr_db()
    dp.include_router(main_router)
    await set_commands(bot)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())