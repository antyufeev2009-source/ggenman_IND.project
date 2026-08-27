import os
from aiogram.types import Message, FSInputFile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_DIR = os.path.join(BASE_DIR, "..", "photos")

os.makedirs(PHOTO_DIR, exist_ok=True)

# Формирует путь для сохранения или загрузки фотографии по ID пользователя
def get_photo_path(user_id: int) -> str:
    return os.path.join(PHOTO_DIR, f"{user_id}.jpg")

# Скачивает фотографию в максимальном качестве из сообщения и сохраняет ее локально
async def save_photo_locally(message: Message) -> str:
    photo = message.photo[-1]
    file = await message.bot.get_file(photo.file_id)

    filepath = get_photo_path(message.from_user.id)
    await message.bot.download(file, destination=filepath)

    return filepath

# Загружает локально сохраненную фотографию пользователя для отправки через бота
def load_photo(user_id: int) -> FSInputFile:
    filepath = get_photo_path(user_id)
    return FSInputFile(filepath)