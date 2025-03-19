import os
from aiogram.types import Message, FSInputFile
from aiogram.fsm.context import FSMContext

from keyboards import *
from export_requests import export_requests_to_excel
from states import StatisticsStates, UserStates
from work_database import get_user_data


async def handle_statistics(message: Message, state: FSMContext):
    """Обработчик для кнопки '📊 Статистика'"""
    # Переход в состояние выбора статистики
    await state.set_state(StatisticsStates.waiting_for_statistics_choice)
    await message.answer(
        "Выберите, за какой период хотите получить статистику:",
        reply_markup=statistics_selection_menu()
    )


async def handle_statistics_today(message: Message, state: FSMContext):
    """Обработчик для выбора статистики за сегодняшний день"""
    # Переходим к состоянию статистики за сегодня
    await state.set_state(StatisticsStates.showing_today_statistics)

    # Генерируем файл отчёта за сегодняшний день
    file_path = export_requests_to_excel(filter_type="today")

    if file_path is None:
        await message.answer("Нет данных для статистики за сегодня.")
        await state.set_state(StatisticsStates.waiting_for_statistics_choice)
        return

    user_data_base = get_user_data(message.from_user.id)
    reply_markup = main_menu_users() if user_data_base['role'] == 'user' else main_menu_admins()

    # Отправляем файл пользователю
    await message.answer_document(document=FSInputFile(file_path, filename="statistic_today.xlsx"),
                                  caption="Ваш файл с отчетом", reply_markup=reply_markup)

    os.remove(file_path)

    await state.set_state(UserStates.main_dialog)


async def handle_statistics_all_time(message: Message, state: FSMContext):
    """Обработчик для выбора статистики за всё время"""
    # Переходим к состоянию статистики за всё время
    await state.set_state(StatisticsStates.showing_all_time_statistics)

    # Генерируем файл отчёта за всё время
    file_path = export_requests_to_excel(filter_type="all_time")

    if file_path is None:
        await message.answer("Нет данных для статистики за всё время.")
        await state.set_state(StatisticsStates.waiting_for_statistics_choice)
        return

    user_data_base = get_user_data(message.from_user.id)
    reply_markup = main_menu_users() if user_data_base['role'] == 'user' else main_menu_admins()

    # Отправляем файл пользователю
    await message.answer_document(document=FSInputFile(file_path, filename="statistic_all_time.xlsx"),
                                  caption="Ваш файл с отчетом", reply_markup=reply_markup)

    os.remove(file_path)

    await state.set_state(UserStates.main_dialog)


async def handle_back_to_admin_menu(message: Message, state: FSMContext):
    """Обработчик для кнопки '🔙 Назад'"""
    # Завершаем текущее состояние
    await state.set_state(UserStates.main_dialog)
    # Возвращаемся в основное меню
    await message.answer(
        "Вы вернулись в основное меню.",
        reply_markup=main_menu_admins()  # Возвращаем основное меню
    )
