from aiogram.fsm.state import StatesGroup, State


class AgreementStates(StatesGroup):
    accepting_agreement = State()   # Согласие на обработку данных


class DataStates(StatesGroup):
    data_menu = State()


class StatsStates(StatesGroup):
    stat_menu = State()  # Меню статистики
    stat_all_time = State()  # Статистика за все время
    stat_last_day = State()  # Статистика за последний день


class UserStates(StatesGroup):
    fio = State()                   # Ввод ФИО
    phone = State()                 # Ввод номера телефона
    email = State()                 # Ввод электронной почты
    role = State()                  # Ввод роли пользователя


class MainMenuStates(StatesGroup):
    menu_admin = State()
    menu_user = State()


class AnswerStates(StatesGroup):
    waiting_for_answer = State()  # Ввод ответа по заявке


class RequestCreationStates(StatesGroup):
    select_category = State()       # Выбор категории заявки
    enter_fio = State()             # Ввод ФИО
    enter_phone = State()           # Ввод номера телефона
    enter_email = State()           # Ввод электронной почты
    enter_address = State()         # Ввод адреса
    confirm_address = State()       # Подтверждение адреса
    attach_media = State()          # Прикрепление медиафайла
    uploading = State()             # Загрузка медиафайла
    enter_description = State()     # Ввод описания заявки
    confirm_request = State()       # Подтверждение заявки перед отправкой


class UserMenuStates(StatesGroup):
    main_menu = State()             # Основное меню
    messages_menu = State()         # Меню сообщений
    requests_menu = State()         # Меню заявок
