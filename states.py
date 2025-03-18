from aiogram.fsm.state import StatesGroup, State


class AgreementStates(StatesGroup):
    accepting_agreement = State()   # Согласие на обработку данных


class UserStates(StatesGroup):
    fio = State()                   # Ввод ФИО
    phone = State()                 # Ввод номера телефона
    email = State()                 # Ввод электронной почты
    role = State()                  # Ввод роли пользователя

    main_dialog = State()           # Главное меню


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


class AnswerStates(StatesGroup):
    waiting_for_answer = State()    # Ввод ответа по заявке


class UserMenuStates(StatesGroup):
    main_menu = State()             # Основное меню
    messages_menu = State()         # Меню сообщений
    requests_menu = State()         # Меню заявок
