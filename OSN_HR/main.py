import asyncio
from aiogram import Bot, Dispatcher
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand  

from config import TOKEN, PROXY_URL 
from handlers.command import register_all_handlers
from db.database import init_db

# Устанавливает меню команд для бота
async def set_bot_commands(bot: Bot):
    await bot.set_my_commands([
        BotCommand(command="start", description="🚀 Запуск бота"),
        BotCommand(command="profile", description="👤 Посмотреть профиль"),
        BotCommand(command="delme", description="❌ Удалить профиль"),
        BotCommand(command="vaclist", description="📒 Список вакансий")
    ])

# Инициализирует базу данных, настраивает и запускает бота
async def main():
    init_db()
    session = AiohttpSession(proxy=PROXY_URL)
    bot = Bot(token=TOKEN, session=session)
    dp = Dispatcher(storage=MemoryStorage())
    
    await set_bot_commands(bot)
    register_all_handlers(dp)
    
    print("Бот кандидатов успешно запущен!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())