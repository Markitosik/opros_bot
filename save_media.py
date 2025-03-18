import logging
import os
import shutil

from bot_config import bot
from config import *
from work_database import save_media_to_db


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
logger = logging.getLogger(__name__)


# Проверка и создание директории, если её нет
def ensure_directory_exists(directory: str):
    """Проверяет наличие директории и создает директорию, если ее нет"""
    if not os.path.exists(directory):
        try:
            os.makedirs(directory)
            logger.info(f"Директория {directory} была успешно создана.")
        except Exception as e:
            logger.error(f"Ошибка при создании директории {directory}: {e}")
            return False
    return True


async def download_media_file(file, new_name_file: str) -> bool:
    """Загружает медиафайл в указанную(временную) директорию."""
    if not ensure_directory_exists(TEMP_DIR):
        return False

    try:
        await bot.download_file(file.file_path, f'{TEMP_DIR}/{new_name_file}', timeout=120)
        return True
    except Exception as e:
        logger.error(f"Ошибка при загрузке файла: {e}")
        return False


async def save_media_file(file, request_id):
    """Перемещает временный файл в постоянную папку и сохраняет в БД"""
    request_folder = os.path.join(REQUESTS_MEDIA_DIR, str(request_id))  # sources/requests/{id_заявки}

    # Проверка и создание папки с использованием функции ensure_directory_exists
    if not ensure_directory_exists(request_folder):
        return  # Если не удаётся создать директорию, выходим из функции

    # Пути файлов
    temp_file_path = os.path.join(TEMP_DIR, file)  # Временный путь
    new_file_path = os.path.join(request_folder, file)  # Конечный путь

    # Проверяем, существует ли файл
    if os.path.exists(temp_file_path):
        shutil.move(temp_file_path, new_file_path)

        # Сохраняем путь в БД
        save_media_to_db(request_id, new_file_path)

        logger.info(f"Файл успешно сохранён в {new_file_path}!")
    else:
        logger.error(f"Временный файл {temp_file_path} не найден!")
