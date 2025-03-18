import logging
import os
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from bot_config import bot
from config import *
from states import *
from new_send_email import send_email
from save_media import download_media_file, save_media_file
from work_database import get_request_details, update_request_status_to_closed


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
logger = logging.getLogger(__name__)


async def handle_admin_response_query(query: types.CallbackQuery, request_id: int, state: FSMContext):
    """
    Обрабатывает запрос от администратора на отправку ответа по заявке.
    Проверяет статус заявки и запрашивает ответ администратора.
    """
    logger.info(f"Получение информации по заявке {request_id}")
    request_details = get_request_details(request_id)

    if request_details and request_details["status"] == "closed":
        logger.warning(f"Заявка {request_id} уже закрыта.")
        await query.message.answer(f"Ответ по заявке {request_id} уже отправлен, так как заявка закрыта.")
        await query.answer()
        return

    await state.update_data(request_id=request_id)
    logger.info(f"Запрашиваем ответ по заявке {request_id}")
    await query.message.answer(f"Введите ответ пользователю по заявке {request_id}:",
                               reply_markup=ReplyKeyboardRemove())
    await state.set_state(AnswerStates.waiting_for_answer)
    await query.answer()


async def handle_admin_answer(message: types.Message, state: FSMContext):
    """
    Обрабатывает ответ администратора на заявку. Отправляет ответ пользователю, загружает медиафайл.
    """
    user_data = await state.get_data()
    request_id = user_data.get("request_id")

    if not request_id:
        logger.error("Не удалось найти связанную заявку.")
        await message.answer("Ошибка: не удалось найти связанную заявку.")
        return

    request_data = get_request_details(request_id)
    if not request_data:
        logger.error(f"Заявка {request_id} не найдена.")
        await message.answer(f"Ошибка: заявка {request_id} не найдена.")
        return

    user_info = request_data.get("user")
    if not user_info or "telegram_id" not in user_info:
        logger.error("Не удалось получить информацию о пользователе.")
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    user_id = user_info["telegram_id"]
    text = message.text or message.caption
    if not text:
        logger.error("Ответ не содержит текста.")
        await message.answer("Ошибка: в ответе отсутствует текст.")
        return

    response_text = f"Ответ на вашу заявку {request_id}:\n{text}"
    media = None
    file_path = None

    if message.photo:
        media = message.photo[-1]
    elif message.video:
        media = message.video

    if media:
        file = await bot.get_file(media.file_id)
        logger.info(f"Загружаем файл: {file.file_id}")
        new_name_file = f'{file.file_id}.{file.file_path.split('.')[-1]}'

        await state.set_state(RequestCreationStates.uploading)
        await message.answer("Файл загружается, пожалуйста, подождите...")

        if await download_media_file(file, new_name_file):
            await save_media_file(new_name_file, request_id)
            file_path = os.path.join(REQUESTS_MEDIA_DIR, str(request_id), new_name_file)
            await message.reply("Файл сохранён!")
        else:
            await message.answer("Ошибка при загрузке файла.")
    if not media:
        file_path = None

    send_email(request_data, response_text, file_path)
    try:
        if file_path:
            if message.photo:
                await bot.send_photo(user_id, photo=file_path, caption=response_text, parse_mode="html")
            else:
                await bot.send_video(user_id, video=file_path, caption=response_text, parse_mode="html")
        else:
            await bot.send_message(user_id, response_text, parse_mode="html")

        update_request_status_to_closed(request_id)
        logger.info(f"Ответ отправлен пользователю {user_id} по заявке {request_id}.")
        await message.answer("Ответ отправлен пользователю!")
    except Exception as e:
        logger.error(f"Ошибка при отправке ответа пользователю: {e}")
        await message.answer(f"Ошибка при отправке ответа: {e}")

    await state.set_state(UserStates.main_dialog)
