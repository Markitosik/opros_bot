import asyncio
import logging

from aiogram import Dispatcher, types, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardRemove

from answer import handle_admin_answer, handle_admin_response_query
from bot_config import dp, bot
from create_request import (create_request, process_category, process_address, handle_address_confirmation,
                            process_media, process_description, confirm_request)
from keyboards import *
from report_export import handle_statistics, handle_statistics_today, handle_statistics_all_time, \
    handle_back_to_admin_menu
from states import *
from work_database import user_exists, get_user_data, save_user_data


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
logger = logging.getLogger(__name__)


async def start(message: types.Message, state: FSMContext):
    """
    Обрабатывает команду /start, проверяя наличие пользователя и отправляя соответствующее меню.
    """
    logger.info(f"Получено сообщение от пользователя с ID: {message.from_user.id}")

    if user_exists(message.from_user.id):
        # Получаем данные пользователя
        user_data = get_user_data(message.from_user.id)
        logger.info(f"Данные пользователя: {user_data}")

        if user_data["role"] == "admin":
            # Если пользователь админ, показываем меню для админов
            logger.info("Пользователь - админ. Отправляем меню администратору.")
            await message.answer(f"Привет, админ! Выбери, что хочешь сделать :", reply_markup=main_menu_admins())
            await state.set_state(MainMenuStates.menu_admin)
        else:
            # Если пользователь не админ, показываем меню для обычных пользователей
            logger.info("Пользователь не является администратором. Отправляем меню пользователю.")
            await message.answer(f"Привет! Выбери, что хочешь сделать :", reply_markup=main_menu_users())
            await state.set_state(MainMenuStates.menu_user)
    else:
        logger.info(f"Пользователь с ID {message.from_user.id} не найден в системе. Отправляем сообщение о согласии.")
        await message.answer(
            """Вас приветствует служба приёма обращений Карельский . Заполняя обращение через Чатбот, 
            Вы даёте согласие на использование ваших персональных данных.
            \n\nНажмите кнопку 'Принять', чтобы продолжить.""",
            reply_markup=accept_button()
        )
        await state.set_state(AgreementStates.accepting_agreement)


async def update_data_menu_admins(message: types.Message, state: FSMContext):
    """
    Обновляет меню для администратора, если пользователь найден и является администратором.
    """
    logger.info(f"Получено сообщение от пользователя с ID: {message.from_user.id}")

    user_data = get_user_data(message.from_user.id)
    if user_data:
        # Если пользователь найден в базе данных
        logger.info(f"Данные пользователя: {user_data}")

        if user_data["role"] == "admin":
            # Если это администратор, показываем меню для админа
            logger.info(f"Пользователь с ID {message.from_user.id} является администратором. Отправляем меню.")
            await message.answer("Вы администратор. Выберите, что хотите сделать:", reply_markup=data_menu_admins())
            await state.set_state(DataStates.data_menu)  # Переход в главное меню админа
        else:
            # Если пользователь не администратор
            logger.warning(f"Пользователь с ID {message.from_user.id} не является администратором.")
            await message.answer("Вы не являетесь администратором.", reply_markup=main_menu_users())
    else:
        # Если пользователя нет в базе данных
        logger.warning(f"Пользователь с ID {message.from_user.id} не найден в базе данных.")
        await message.answer("Не удалось найти ваши данные. Пожалуйста, начните с регистрации.")
        await message.answer(
            """Вас приветствует служба приёма обращений. Заполняя обращение через Чатбот, 
            Вы даёте согласие на использование ваших персональных данных.
            \n\nНажмите кнопку 'Принять', чтобы продолжить.""",
            reply_markup=accept_button()
        )
        await state.set_state(AgreementStates.accepting_agreement)


async def update_data(message: types.Message, state: FSMContext):
    """
    Обновляет данные пользователя и предоставляет меню для ввода нового ФИО.
    """
    logger.info(f"Получено сообщение от пользователя с ID: {message.from_user.id}")

    user_data = get_user_data(message.from_user.id)
    if user_data:
        # Если пользователь найден в базе данных
        logger.info(f"Данные пользователя: {user_data}")

        if user_data["role"] == "admin":
            await state.update_data(fio=user_data["fio"], phone=user_data["phone"],
                                    email=user_data["email"], role=user_data["role"])
            # Если это администратор, показываем меню для админа
            logger.info(f"Пользователь с ID {message.from_user.id} является администратором.")
            await message.answer("Вы администратор.", reply_markup=ReplyKeyboardRemove())
            await message.answer(
                f"Давай обновим твои данные.\n\nТекущее ФИО: <b>{user_data['fio']}</b>\nВведите новое ФИО:",
                parse_mode="html", reply_markup=empty_or_skip_buttons(show_empty=False))
            await state.set_state(UserStates.fio)  # Переход к вводу нового ФИО
        else:
            # Если обычный пользователь, показываем меню для обновления данных
            logger.info(f"Пользователь с ID {message.from_user.id} не является администратором.")
            await state.update_data(fio=user_data["fio"], phone=user_data["phone"],
                                    email=user_data["email"], role=user_data["role"])

            await message.answer(
                f"Давай обновим твои данные.\n\nТекущее ФИО: <b>{user_data['fio']}</b>\nВведите новое ФИО:",
                parse_mode="html", reply_markup=empty_or_skip_buttons(show_empty=False))
            await state.set_state(UserStates.fio)  # Переход к вводу нового ФИО
    else:
        # Если пользователя нет в базе данных
        logger.warning(f"Пользователь с ID {message.from_user.id} не найден в базе данных.")
        await message.answer("Не удалось найти ваши данные. Пожалуйста, начните с регистрации.")


async def accept_agreement(message: types.Message, state: FSMContext):
    """
    Обрабатывает согласие пользователя на обработку данных и переходит к следующему шагу.
    """
    logger.info(f"Получено сообщение от пользователя с ID: {message.from_user.id} с текстом: {message.text}")

    if message.text == "Принять":
        # Переход к заполнению данных
        logger.info(f"Пользователь с ID {message.from_user.id} принял соглашение.")
        await message.answer("Укажите Ваши данные: ФИО", reply_markup=ReplyKeyboardRemove())
        await state.set_state(UserStates.fio)
    else:
        # Если не принял, можно завершить взаимодействие или спросить повторно
        logger.warning(f"Пользователь с ID {message.from_user.id} не принял соглашение.")
        await message.answer("Для продолжения необходимо принять соглашение.")


async def get_fio(message: types.Message, state: FSMContext):
    """
    Обрабатывает введённое ФИО пользователя и переходит к следующему шагу (выбор роли или телефон).
    """
    logger.info(f"Получено сообщение от пользователя с ID: {message.from_user.id} с текстом: {message.text}")

    user_data_base = get_user_data(message.from_user.id)
    logger.info(f"Данные пользователя из базы: {user_data_base}")

    user_data = await state.get_data()
    logger.info(f"Текущие данные пользователя в сессии: {user_data}")

    is_new = not bool(user_data_base)  # Проверяем, создаются ли данные впервые

    if message.text == "Пропустить":
        logger.info(f"Пользователь с ID {message.from_user.id} пропустил ввод ФИО.")
        pass
    elif message.text == "Оставить пустым":
        logger.info(f"Пользователь с ID {message.from_user.id} оставил ФИО пустым.")
        await state.update_data(fio="")
    else:
        logger.info(f"Пользователь с ID {message.from_user.id} ввел ФИО: {message.text}")
        await state.update_data(fio=message.text)

    # reply_markup = empty_or_skip_buttons() if user_data_base else empty_or_skip_buttons(show_skip=False)

    # Если администратор, сразу после ФИО предложим выбрать роль
    if user_data_base and user_data_base["role"] == "admin":
        logger.info(f"Пользователь с ID {message.from_user.id} является администратором. Переход к выбору роли.")
        text = "Теперь выбери свою роль (Администратор или Пользователь):"
        await message.answer(text, parse_mode="html",
                             reply_markup=get_role_keyboard())
        await state.set_state(UserStates.role)  # Переход к выбору роли
    else:
        await state.update_data(role="user")
        reply_markup = empty_or_skip_buttons(show_empty=False, show_num=True) \
            if user_data_base else empty_or_skip_buttons(show_empty=False, show_skip=False, show_num=True)

        text = "Укажите способ обратной связи, мобильный номер телефона:" if is_new else \
            f"Текущий номер телефона: <b>{user_data_base['phone']}</b>\nТеперь введи новый номер телефона:"
        logger.info(f"Пользователю с ID {message.from_user.id} отправлено сообщение о введении номера телефона.")
        await message.answer(text, parse_mode="html", reply_markup=reply_markup)
        await state.set_state(UserStates.phone)


async def get_role(message: types.Message, state: FSMContext):
    """
    Обрабатывает выбор роли пользователя и переходит к вводу номера телефона.
    """
    logger.info(f"Получено сообщение от пользователя с ID: {message.from_user.id} с текстом: {message.text}")

    user_data_base = get_user_data(message.from_user.id)
    logger.info(f"Данные пользователя из базы: {user_data_base}")

    user_data = await state.get_data()
    logger.info(f"Текущие данные пользователя в сессии: {user_data}")

    is_new = not bool(user_data_base)  # Проверяем, создаются ли данные впервые

    if message.text == "Администратор":
        await state.update_data(role="admin")
        logger.info(f"Пользователь с ID {message.from_user.id} получил роль администратора.")
    elif message.text == "Пользователь":
        await state.update_data(role="user")
        logger.info(f"Пользователь с ID {message.from_user.id} понижен до роли пользователя.")
    else:
        logger.warning(f"Пользователь с ID {message.from_user.id} ввел некорректную роль: {message.text}")
        await message.answer("Некорректный ввод. Введите номер вручную или отправьте контакт.")
        return

    reply_markup = empty_or_skip_buttons(show_empty=False, show_num=True) if user_data_base else (
        empty_or_skip_buttons(show_empty=False, show_skip=False, show_num=True))

    text = "Укажите способ обратной связи, мобильный номер телефона:" if is_new else \
        f"Текущий номер телефона: <b>{user_data_base['phone']}</b>\nТеперь введи новый номер телефона:"
    logger.info(f"Пользователю с ID {message.from_user.id} отправлено сообщение о введении номера телефона.")
    await message.answer(text, parse_mode="html", reply_markup=reply_markup)
    await state.set_state(UserStates.phone)


async def get_phone(message: types.Message, state: FSMContext):
    """
    Обрабатывает введённый номер телефона пользователя и переходит к следующему шагу (email).
    """
    logger.info(f"Получено сообщение от пользователя с ID: {message.from_user.id} с текстом: {message.text}")

    user_data_base = get_user_data(message.from_user.id)
    logger.info(f"Данные пользователя из базы: {user_data_base}")

    user_data = await state.get_data()
    logger.info(f"Текущие данные пользователя в сессии: {user_data}")

    is_new = not bool(user_data_base)

    if message.text == "Пропустить":
        logger.info(f"Пользователь с ID {message.from_user.id} пропустил ввод номера телефона.")
        pass
    elif message.contact:
        await state.update_data(phone=message.contact.phone_number)
        logger.info(f"Пользователь с ID {message.from_user.id} отправил контакт. "
                    f"Номер телефона: {message.contact.phone_number}")
    elif message.text:
        await state.update_data(phone=message.text)
        logger.info(f"Пользователь с ID {message.from_user.id} ввел номер телефона: {message.text}")
    else:
        logger.warning(f"Пользователь с ID {message.from_user.id} ввел некорректный номер телефона.")
        await message.answer("Некорректный ввод. Введите номер вручную или отправьте контакт.")
        return

    reply_markup = empty_or_skip_buttons() if user_data_base else empty_or_skip_buttons(show_skip=False)

    text = "Укажите адрес Вашей эл.почты:" if is_new else \
        f"Текущий email: <b>{user_data_base['email'] or '-'}</b>\nТеперь введи новый email:"
    logger.info(f"Пользователю с ID {message.from_user.id} отправлено сообщение о введении email.")
    await message.answer(text, parse_mode="html", reply_markup=reply_markup)
    await state.set_state(UserStates.email)


async def get_email(message: types.Message, state: FSMContext):
    """
    Обрабатывает введённый email пользователя, сохраняет данные и отправляет сообщение о статусе сохранения.
    """
    logger.info(f"Получено сообщение от пользователя с ID: {message.from_user.id} с текстом: {message.text}")

    user_data_base = get_user_data(message.from_user.id)
    logger.info(f"Данные пользователя из базы: {user_data_base}")

    user_data = await state.get_data()
    logger.info(f"Текущие данные пользователя в сессии: {user_data}")

    is_new = not bool(user_data_base)

    if message.text == "Пропустить":
        logger.info(f"Пользователь с ID {message.from_user.id} пропустил ввод email.")
        pass
    elif message.text == "Оставить пустым":
        await state.update_data(email=None)
        logger.info(f"Пользователь с ID {message.from_user.id} оставил email пустым.")
    else:
        await state.update_data(email=message.text)
        logger.info(f"Пользователь с ID {message.from_user.id} ввел email: {message.text}")

    updated_data = await state.get_data()
    logger.info(f"Обновленные данные пользователя: {updated_data}")

    save_user_data(message.from_user.id, updated_data, message.from_user.username)

    status_text = "✅ Данные сохранены!\n\n" if is_new else "✅ Данные обновлены!\n\n"

    text = (
        f"<b>{status_text}</b>"
        f"Роль: <b>{updated_data.get('role') or '—'}</b>\n\n"
        f"ФИО: <b>{updated_data.get('fio', '—')}</b>\n"
        f"Телефон: <b>{updated_data.get('phone', '—')}</b>\n"
        f"Email: <b>{updated_data.get('email') or '—'}</b>\n\n"
        f"Выбери, что хочешь сделать:"
    )

    user_data_base = get_user_data(message.from_user.id)
    logger.info(f"Данные пользователя из базы после обновления: {user_data_base}")

    reply_markup = main_menu_users() if user_data_base['role'] == 'user' else main_menu_admins()
    await message.answer(text, parse_mode="html", reply_markup=reply_markup)
    if user_data_base['role'] == 'user':
        await state.set_state(MainMenuStates.menu_user)
    elif user_data_base['role'] == 'admin':
        await state.set_state(MainMenuStates.menu_admin)
    logger.info(f"Пользователю с ID {message.from_user.id} отправлено сообщение с результатами.")


# Регистрация обработчиков
def register_state_handlers(dp: Dispatcher):
    dp.message.register(start, F.text == "/start")
    dp.message.register(accept_agreement, AgreementStates.accepting_agreement)

    dp.message.register(update_data_menu_admins, F.text == "🔄 Обновить данные", StateFilter(MainMenuStates.menu_admin))

    dp.message.register(update_data, F.text == "🔄 Обновить свои данные")
    dp.message.register(create_request, F.text == "📝 Создать заявку")
    # dp.message.register(update_data, F.text == "📋 Мои заявки")

    dp.message.register(get_fio, UserStates.fio)
    dp.message.register(get_role, UserStates.role)
    dp.message.register(get_phone, UserStates.phone)
    dp.message.register(get_email, UserStates.email)

    dp.message.register(handle_back_to_admin_menu, F.text == "↩️ Назад", StateFilter(DataStates.data_menu))

    dp.message.register(process_category, RequestCreationStates.select_category)

    dp.message.register(process_address, RequestCreationStates.enter_address)
    dp.message.register(handle_address_confirmation, RequestCreationStates.confirm_address)
    dp.message.register(process_media, RequestCreationStates.attach_media)
    dp.message.register(process_description, RequestCreationStates.enter_description)
    dp.message.register(confirm_request, RequestCreationStates.confirm_request)

    dp.message.register(handle_admin_answer, AnswerStates.waiting_for_answer)

    # Обработчики для статистики
    dp.message.register(handle_statistics, F.text == "📊 Статистика", StateFilter(MainMenuStates.menu_admin))
    dp.message.register(handle_statistics_today, F.text == "📅 Статистика за сегодня",
                        StateFilter(StatsStates.stat_menu))
    dp.message.register(handle_statistics_all_time, F.text == "📊 Статистика за всё время",
                        StateFilter(StatsStates.stat_menu))
    dp.message.register(handle_back_to_admin_menu, F.text == "↩️ Назад", StateFilter(StatsStates.stat_menu))


@dp.callback_query(lambda query: query.data.startswith('answer:'))
async def process_callback(query: types.CallbackQuery, state: FSMContext):
    callback_data = query.data
    action, user_id = callback_data.split(':')

    # В передаваемой функции теперь есть state
    await handle_admin_response_query(query, user_id, state)


# Запуск бота
async def main():
    register_state_handlers(dp)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
