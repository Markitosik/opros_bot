import logging
from geopy.geocoders import Nominatim
from aiogram import types
from aiogram.types import ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from datetime import datetime


from keyboards import *
from states import *
from admin_notifications import notify_admins_about_request
from config import WORKING_HOURS, WORKING_DAYS
from bot_config import bot
from save_media import save_media_file, download_media_file
from work_database import get_user_data, get_available_admin_id, save_request_data


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
logger = logging.getLogger(__name__)


# Создание объекта геокодера
geolocator = Nominatim(user_agent="myGeocoder")


async def create_request(message: types.Message, state: FSMContext):
    """Обработчик создания заявки с проверкой рабочего времени"""
    now = datetime.now()
    print(now)

    if now.weekday() not in WORKING_DAYS:
        await message.answer("Создание заявок доступно только в рабочие дни.")
        return

    if not (WORKING_HOURS[0] <= now.hour < WORKING_HOURS[1]):
        await message.answer("Создание заявок доступно только в рабочее время.")
        return

    user_data = get_user_data(message.from_user.id)
    logger.info(f"Пользователь {message.from_user.id} начал создание заявки.")

    if user_data:
        logger.debug(f"Данные пользователя {message.from_user.id} найдены: {user_data}")
        await message.answer("Выберите тему заявки", parse_mode="html", reply_markup=request_category_menu())
        await state.set_state(RequestCreationStates.select_category)
    else:
        logger.warning(f"Пользователь {message.from_user.id} не найден в базе данных.")
        await message.answer("Не удалось найти ваши данные. Пожалуйста, начните с регистрации.")


async def process_category(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    logger.info(f"Пользователь {message.from_user.id} выбрал категорию: {message.text}")

    await message.answer("Укажите адрес контейнерной площадки:", reply_markup=address_button())
    await state.set_state(RequestCreationStates.enter_address)


async def process_address(message: types.Message, state: FSMContext):
    if message.location:
        logger.debug(
            f"Пользователь {message.from_user.id} отправил геолокацию: "
            f"{message.location.latitude}, {message.location.longitude}")
        location_info = geolocator.reverse((message.location.latitude, message.location.longitude),
                                           language='ru', timeout=30)

        if location_info:
            real_address = location_info.address
            logger.debug(f"Реальный адрес по геолокации: {real_address}")
        else:
            real_address = "Адрес не найден"
            logger.warning(f"Не удалось найти адрес для геолокации пользователя {message.from_user.id}")
    else:
        real_address = message.text
        logger.debug(f"Пользователь {message.from_user.id} ввел текстовый адрес: {real_address}")

    await state.update_data(address=real_address)
    await message.answer(f"Ваш адрес: {real_address}.")
    await message.answer(f"Это верный адрес?", reply_markup=confirmation_buttons())
    await state.set_state(RequestCreationStates.confirm_address)


async def handle_address_confirmation(message: types.Message, state: FSMContext):
    user_answer = message.text.lower()

    if user_answer == "да":
        logger.info(f"Пользователь {message.from_user.id} подтвердил адрес: {message.text}")
        await message.answer(f"Адрес подтвержден: {message.text}")
        await message.answer("Теперь загрузите медиафайл:", reply_markup=ReplyKeyboardRemove())
        await state.set_state(RequestCreationStates.attach_media)
    elif user_answer == "нет":
        logger.info(f"Пользователь {message.from_user.id} отклонил адрес: {message.text}")
        await message.answer("Введите новый адрес:", reply_markup=address_button())
        await state.set_state(RequestCreationStates.enter_address)


async def process_media(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    media = None

    if message.photo:
        media = message.photo[-1]
        logger.debug(f"Пользователь {user_id} загрузил фото.")
    elif message.video:
        media = message.video
        logger.debug(f"Пользователь {user_id} загрузил видео.")
    else:
        logger.warning(f"Пользователь {user_id} отправил неподдерживаемый медиафайл.")
        await message.answer("Ошибка: Пожалуйста, загрузите изображение или видео.")
        return

    file = await bot.get_file(media.file_id)
    new_name_file = f'{file.file_id}.{file.file_path.split('.')[-1]}'

    await state.set_state(RequestCreationStates.uploading)
    await message.answer("Файл загружается, пожалуйста, подождите...")

    await state.update_data(media=new_name_file)

    if await download_media_file(file, new_name_file):
        logger.info(f"Пользователь {user_id} успешно загрузил файл {new_name_file}")
        await message.reply(f"Файл сохранён!")
    else:
        logger.error(f"Ошибка при загрузке файла от пользователя {user_id}")
        await message.answer(f"Ошибка при загрузке файла.")

    await message.answer("Опишите проблему:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(RequestCreationStates.enter_description)


async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    data = await state.get_data()

    user_data_base = get_user_data(message.from_user.id)

    request_text = (
        f"Категория: <b>{data['category']}</b>\n"
        f"ФИО: <b>{user_data_base['fio']}</b>\n"
        f"Номер: <b>{user_data_base['phone']}</b>\n"
        f"Email: <b>{user_data_base['email']}</b>\n"
        f"Адрес: <b>{data['address']}</b>\n"
        f"Описание: <b>{data['description']}</b>")

    logger.info(f"Пользователь {message.from_user.id} заполнил описание проблемы: {data['description']}")

    if data.get("media"):
        try:
            if data["media"].endswith(".jpg") or data["media"].endswith(".jpeg"):
                await message.answer_photo(photo=data["media"].split('.')[0],
                                           caption=f"Проверьте данные:\n{request_text}\nПодтвердить?",
                                           parse_mode="html", reply_markup=confirmation_buttons())
                logger.debug(f"Фото отправлено пользователю {message.from_user.id}")
            else:
                await message.answer_video(video=data["media"].split('.')[0],
                                           caption=f"Проверьте данные:\n{request_text}\nПодтвердить?",
                                           parse_mode="html", reply_markup=confirmation_buttons())
                logger.debug(f"Видео отправлено пользователю {message.from_user.id}")
        except Exception as e:
            logger.error(f"Ошибка при отправке медиа пользователю {message.from_user.id}: {e}")

    await state.set_state(RequestCreationStates.confirm_request)


async def confirm_request(message: types.Message, state: FSMContext):
    user_data_base = get_user_data(message.from_user.id)
    reply_markup = main_menu_users() if user_data_base['role'] == 'user' else main_menu_admins()
    if message.text.lower() == "да":
        data = await state.get_data()

        admin_id, admin_telegram_id = get_available_admin_id()

        # Вставляем данные заявки в БД
        last_row_id = save_request_data(user_data_base['id'], data, admin_id)

        # Обрабатываем медиафайл
        if data.get("media"):
            await save_media_file(data["media"], last_row_id)  # Сохраняем файл и запись в БД

        await message.answer(f"Ваше обращение №{last_row_id} поступило в работу. Спасибо за Ваше обращение.",
                             reply_markup=reply_markup)

        # Уведомляем администраторов
        await notify_admins_about_request(bot, last_row_id, user_data_base, data, admin_telegram_id)
    else:
        await message.answer("Отмена заявки", reply_markup=reply_markup)

    user_data_base = get_user_data(message.from_user.id)

    reply_markup = main_menu_users() if user_data_base['role'] == 'user' else main_menu_admins()
    if user_data_base['role'] == 'user':
        await state.set_state(MainMenuStates.menu_user)
    elif user_data_base['role'] == 'admin':
        await state.set_state(MainMenuStates.menu_admin)
