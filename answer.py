import logging
import os
from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove, FSInputFile

from bot_config import bot
from config import *
from keyboards import main_menu_users, main_menu_admins
from states import *
from new_send_email import send_email
from work_database import get_request_details, update_request_status_to_closed, user_exists, get_user_data

logger = logging.getLogger(__name__)


async def handle_admin_response_query(query: types.CallbackQuery, request_id: int, state: FSMContext):
    """
    Обрабатывает запрос от администратора на отправку ответа по заявке.
    Проверяет статус заявки и запрашивает ответ администратора.
    """
    # Проверяем, является ли пользователь администратором
    if not user_exists(query.from_user.id):  # Проверяем, существует ли пользователь
        logger.warning(f"Пользователь {query.from_user.id} не найден в системе.")
        await query.message.answer("Вы не авторизованы для выполнения этой операции.")
        await query.answer()
        return

    user_data = get_user_data(query.from_user.id)
    if user_data["role"] != "admin":  # Проверяем роль пользователя
        logger.warning(f"Пользователь {query.from_user.id} не является администратором.")
        await query.message.answer("У вас нет прав для выполнения этой операции.")
        await query.answer()
        return

    logger.info(f"Получение информации по заявке {request_id}")

    # Получаем информацию по заявке
    request_details = get_request_details(request_id)

    if request_details and request_details["status"] == "closed":
        logger.warning(f"Заявка {request_id} уже закрыта.")
        await query.message.answer(f"Ответ по заявке {request_id} уже отправлен, так как заявка закрыта.")
        await query.answer()
        return  # Прерываем выполнение функции, если заявка закрыта

    # Сохраняем request_id в состояние
    await state.update_data(request_id=request_id)

    logger.info(f"Запрашиваем ответ по заявке {request_id}")
    await query.message.answer(f"Введите ответ пользователю по заявке {request_id}:",
                               reply_markup=ReplyKeyboardRemove())

    # Устанавливаем состояние для ввода ответа
    await state.set_state(AnswerStates.waiting_for_answer)
    await query.answer()


async def handle_admin_answer(message: types.Message, state: FSMContext):
    """
    Обрабатывает ответ администратора на заявку. Отправляет ответ пользователю по заявке.
    Сохраняет медиафайл, если он прикреплён.
    """
    # Проверяем, является ли пользователь администратором
    if not user_exists(message.from_user.id):  # Проверяем, существует ли пользователь
        logger.warning(f"Пользователь {message.from_user.id} не найден в системе.")
        await message.answer("Вы не авторизованы для выполнения этой операции.")
        return

    user_data = get_user_data(message.from_user.id)
    if user_data["role"] != "admin":  # Проверяем роль пользователя
        logger.warning(f"Пользователь {message.from_user.id} не является администратором.")
        await message.answer("У вас нет прав для выполнения этой операции.")
        return

    # Получаем данные из состояния
    user_data = await state.get_data()
    request_id = user_data.get("request_id")

    if not request_id:
        logger.error("Не удалось найти связанную заявку.")
        await message.answer("Ошибка: не удалось найти связанную заявку.")
        return

    # Получаем данные о заявке
    request_data = get_request_details(request_id)

    if not request_data:
        logger.error(f"Заявка {request_id} не найдена.")
        await message.answer(f"Ошибка: заявка {request_id} не найдена.")
        return

    # Проверяем, есть ли данные о пользователе в заявке
    user_info = request_data.get("user")
    if not user_info or "telegram_id" not in user_info:
        logger.error("Не удалось получить информацию о пользователе.")
        await message.answer("Ошибка: не удалось получить информацию о пользователе.")
        return

    user_id = user_info["telegram_id"]

    # Проверяем, есть ли текст в сообщении
    text = message.text or message.caption
    if not text:
        logger.error("Ответ не содержит текста.")
        await message.answer("Ошибка: в ответе отсутствует текст.")
        return

    # Формируем окончательное сообщение
    response_text = f"Ответ на вашу заявку {request_id}:\n{text}"

    # Обработка медиафайла (если есть)
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

        # Устанавливаем состояние загрузки
        await state.set_state(RequestCreationStates.uploading)
        await message.answer("Файл загружается, пожалуйста, подождите...")

        # Обновляем состояние с путём к временному файлу
        await state.update_data(media=new_name_file)
        file_path = f'{REQUESTS_MEDIA_DIR}{request_id}/answer/{new_name_file}'

        # Проверяем наличие папки и создаём её, если нужно
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Папка {directory} была создана.")

        try:
            # Загружаем файл
            await bot.download_file(file.file_path, file_path, timeout=120)
            logger.info(f"Файл {file_path} успешно загружен.")
            await message.reply(f"Файл сохранён!")

        except Exception as e:
            logger.error(f"Ошибка при загрузке файла: {e}")
            await message.answer(f"Ошибка при загрузке файла: {e}")

    # Отправляем ответ пользователю
    send_email(request_data, response_text, file_path)

    user_data_base = get_user_data(user_id)

    reply_markup = main_menu_users() if user_data_base['role'] == 'user' else main_menu_admins()

    try:
        if media:
            # Отправляем фото или видео с подписью
            if message.photo:
                print(file_path)
                await bot.send_photo(user_id, photo=FSInputFile(file_path), caption=response_text,
                                     parse_mode="html", reply_markup=reply_markup)
            elif message.video:
                print(file_path)
                await bot.send_video(user_id, video=FSInputFile(file_path), caption=response_text,
                                     parse_mode="html", reply_markup=reply_markup)
        else:
            # Отправляем только текст, если нет медиафайла
            await bot.send_message(user_id, response_text, parse_mode="html", reply_markup=reply_markup)

        # Закрываем заявку
        update_request_status_to_closed(request_id)
        logger.info(f"Ответ отправлен пользователю {user_id} по заявке {request_id}.")

        await message.answer("Ответ отправлен пользователю!", reply_markup=main_menu_admins())

    except Exception as e:
        logger.error(f"Ошибка при отправке ответа пользователю: {e}")
        await message.answer(f"Ошибка при отправке ответа: {e}")

    await state.set_state(MainMenuStates.menu_admin)
