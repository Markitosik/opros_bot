from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.types import KeyboardButton, ReplyKeyboardMarkup, InlineKeyboardButton


def main_menu_users():
    """Создает клавиатуру основного меню для пользователей"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🔄 Обновить свои данные"))
    # builder.add(KeyboardButton(text="📋 Мои заявки"))
    builder.add(KeyboardButton(text="📝 Создать заявку"))
    return builder.as_markup(resize_keyboard=True)


def main_menu_admins():
    """Создает клавиатуру основного меню для администраторов"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="🔄 Обновить данные"))
    # builder.add(KeyboardButton(text="📋 Заявки"))
    builder.add(KeyboardButton(text="📝 Создать заявку"))
    return builder.as_markup(resize_keyboard=True)


def data_menu_admins():
    """Создает клавиатуру меню обновления данных для администраторов"""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text="🔄 Обновить свои данные"))
    # builder.row(KeyboardButton(text="👥 Данные пользователей"))
    # builder.row(KeyboardButton(text="↩️ Назад"))
    return builder.as_markup(resize_keyboard=True)


def requests_menu_admins():
    """Создает клавиатуру меню работы с заявками для администраторов"""
    builder = ReplyKeyboardBuilder()
    # builder.row(KeyboardButton(text="📋 Заявки пользователей"))
    # builder.add(KeyboardButton(text="📋 Мои заявки"))
    # builder.add(KeyboardButton(text="📊 Статистика"))
    # builder.row(KeyboardButton(text="↩️ Назад"))
    return builder.as_markup(resize_keyboard=True)


def empty_or_skip_buttons(show_empty=True, show_skip=True, show_num=False):
    """Создает клавиатуру с кнопками для оставления поля пустым или пропуска."""
    builder = ReplyKeyboardBuilder()

    if show_num:
        builder.add(KeyboardButton(text="Отправить номер", request_contact=True))
    if show_empty:
        builder.row(KeyboardButton(text="Оставить пустым"))
    if show_skip:
        builder.row(KeyboardButton(text="Пропустить"))

    return builder.as_markup(resize_keyboard=True)


def get_role_keyboard():
    """Создает клавиатуру для выбора роли (Администратор или Пользователь)"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Администратор"))
    builder.add(KeyboardButton(text="Пользователь"))
    return builder.as_markup(resize_keyboard=True)


def accept_button():
    """Создает клавиатуру с кнопкой "Принять" для подтверждения действия"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Принять"))
    return builder.as_markup(resize_keyboard=True)


def confirmation_buttons():
    """Создает клавиатуру с кнопками "Да" и "Нет" для подтверждения/отказа"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Да"), KeyboardButton(text="Нет"))
    return builder.as_markup(resize_keyboard=True)


def request_category_menu():
    """Создает клавиатуру с кнопками для выбора категории заявки"""
    builder = ReplyKeyboardBuilder()
    builder.add(
        KeyboardButton(text="Вывоз ТКО"),
        KeyboardButton(text="Вывоз КГО"),
        KeyboardButton(text="Вывоз РСО"),
        KeyboardButton(text="Начисления"),
        KeyboardButton(text="Корректировки данных в квитанции"),
        KeyboardButton(text="Другое")
    )
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)


def create_keyboard_button(value: str | None) -> ReplyKeyboardMarkup:
    """Создает клавиатуру с одной кнопкой, если значение передано."""
    builder = ReplyKeyboardBuilder()
    if value:
        builder.add(KeyboardButton(text=value))
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def address_button():
    """Создает клавиатуру с кнопкой для отправки адреса (геолокации)"""
    builder = ReplyKeyboardBuilder()
    builder.add(KeyboardButton(text="Отправить адрес", request_location=True))
    return builder.as_markup(resize_keyboard=True)


def create_keyboard_answer(request_id):
    """Создает клавиатуру с кнопкой "Написать ответ" для заявки с указанным ID"""
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(text="Написать ответ", callback_data=f'answer:{request_id}'))
    return builder.as_markup()
