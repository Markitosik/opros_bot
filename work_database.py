import sqlite3
import logging

from config import *


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
logger = logging.getLogger(__name__)


def execute_db(query, params=(), fetchone=False, fetchall=False, commit=False):
    """
    Выполняет SQL-запрос к базе данных.
    """
    result = None
    last_row_id = None

    # Используем контекстный менеджер для открытия и закрытия соединения с базой данных
    with sqlite3.connect(DATABASE_PATH) as conn:
        cursor = conn.cursor()

        try:
            cursor.execute(query, params)
            if commit:
                conn.commit()  # Применяем изменения в базе
                logger.info(f"Запрос выполнен")
            else:
                logger.info(f"Запрос выполнен (без commit)")
        except Exception as e:
            logger.error(f"Ошибка выполнения запроса: {e}")
            conn.rollback()  # Отменяем изменения в случае ошибки
            return None

        if fetchone:
            result = cursor.fetchone()
        elif fetchall:
            result = cursor.fetchall()

        if commit:
            last_row_id = cursor.lastrowid

    # Контекстный менеджер автоматически закроет соединение по выходу из блока
    return result if not commit else last_row_id


def get_request_details(request_id):
    """
    Получает детали заявки по её ID.
    """
    logger.info(f"Получение данных по заявке с ID {request_id}")

    query = '''
        SELECT 
            u.id AS user_id, u.username, u.telegram_id, u.fio AS user_fio, u.phone AS user_phone, 
            u.email AS user_email, u.role,
            r.id AS request_id, r.category, r.address, r.description, r.status, r.created_at,
            media.id AS media_id, media.file_path, media.created_at AS media_created_at
        FROM requests r
        JOIN users u ON r.user_id = u.id
        LEFT JOIN media ON media.request_id = r.id
        WHERE r.id = ?
    '''

    result = execute_db(query, (request_id,), fetchall=True)

    if not result:
        logger.warning(f"Заявка с ID {request_id} не найдена.")
        return None

    # Формируем структуру данных
    request_info = {
        "user": {
            "user_id": result[0][0],
            "username": result[0][1],
            "telegram_id": result[0][2],
            "fio": result[0][3],
            "phone": result[0][4],
            "email": result[0][5],
            "role": result[0][6]
        },
        "request_id": result[0][7],
        "category": result[0][8],
        "address": result[0][9],
        "description": result[0][10],
        "status": result[0][11],
        "created_at": result[0][12],
        "media": []
    }

    for row in result:
        media_id, file_path, media_created_at = row[13:16]

        if media_id:
            request_info["media"].append({
                "media_id": media_id,
                "file_path": file_path,
                "created_at": media_created_at
            })

    logger.info(f"Данные по заявке с ID {request_id} получены.")
    return request_info


def get_available_admin_id():
    """
    Получает администратора с наименьшим количеством открытых заявок.
    """
    logger.info("Получение доступного администратора.")

    query = """
    SELECT u.id, u.telegram_id 
    FROM users u 
    LEFT JOIN requests r ON u.id = r.admin_id AND r.status = 'open' 
    WHERE u.role = 'admin'
    GROUP BY u.id 
    ORDER BY COUNT(r.id) ASC, COALESCE(MAX(r.created_at), '1970-01-01') ASC 
    LIMIT 1;
    """
    admin_id = execute_db(query, fetchone=True)

    if admin_id:
        logger.info(f"Найден доступный администратор: {admin_id[0]}")
        return admin_id[0], admin_id[1]
    else:
        logger.warning("Доступных администраторов не найдено.")
        return None


def get_admins():
    """
    Возвращает список Telegram ID администраторов.
    """
    logger.info("Получение списка администраторов.")

    admins = execute_db("SELECT telegram_id FROM users WHERE role = 'admin'", fetchall=True)

    if admins:
        logger.info(f"Найдено {len(admins)} администраторов.")
    else:
        logger.warning("Администраторы не найдены.")

    return [admin[0] for admin in admins] if admins else []


def user_exists(telegram_id):
    """
    Проверяет, существует ли пользователь в БД.
    """
    logger.info(f"Проверка существования пользователя с Telegram ID {telegram_id}.")

    exists = execute_db("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,), fetchone=True)

    if exists:
        logger.info(f"Пользователь найден: {telegram_id}")
        return True
    else:
        logger.warning(f"Пользователь не найден: {telegram_id}")
        return False


def get_user_data(telegram_id):
    """
    Получает данные пользователя по его Telegram ID.
    """
    logger.info(f"Получение данных пользователя с Telegram ID {telegram_id}.")

    data = execute_db("SELECT id, username, telegram_id, fio, phone, email, role FROM users WHERE telegram_id = ?",
                      (telegram_id,), fetchone=True)

    if data:
        logger.info(f"Данные пользователя {telegram_id} получены.")
        return {
            "id": data[0],
            "username": data[1],
            "telegram_id": data[2],
            "fio": data[3],
            "phone": data[4],
            "email": data[5],
            "role": data[6]
        }

    logger.warning(f"Пользователь с Telegram ID {telegram_id} не найден.")
    return None


def save_user_data(telegram_id, user_data, username):
    """
    Сохраняет или обновляет данные пользователя в БД.
    """
    logger.info(f"Сохранение данных пользователя с Telegram ID {telegram_id}.")

    try:
        execute_db(
            """INSERT INTO users (telegram_id, fio, phone, email, username, role) 
               VALUES (?, ?, ?, ?, ?, ?) 
               ON CONFLICT(telegram_id) 
               DO UPDATE SET fio=excluded.fio, phone=excluded.phone, email=excluded.email, role=excluded.role""",
            (telegram_id, user_data["fio"], user_data["phone"], user_data["email"], username, user_data['role']),
            commit=True
        )
        logger.info(f"Данные пользователя {telegram_id} сохранены.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных пользователя {telegram_id}: {e}")


def save_request_data(user_id, request_data, admin_id):
    """
    Сохраняет данные заявки в БД.
    """
    logger.info(f"Сохранение данных заявки пользователя с ID {user_id}.")

    try:
        last_row_id = execute_db(
            """INSERT INTO requests (user_id, admin_id, category, address, description, status) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_id, admin_id, request_data["category"], request_data["address"], request_data["description"],
             request_data['status']), commit=True)
        logger.info(f"Заявка пользователя с ID {user_id} сохранена, ID заявки: {last_row_id}.")
        return last_row_id
    except Exception as e:
        logger.error(f"Ошибка при сохранении заявки пользователя с ID {user_id}: {e}")
        return None


def update_request_status_to_closed(request_id):
    """
    Обновляет статус заявки на 'закрыта'.
    """
    logger.info(f"Обновление статуса заявки с ID {request_id}.")

    try:
        execute_db("""UPDATE requests SET status = 'closed' WHERE id = ?""", (request_id,), commit=True)
        logger.info(f"Статус заявки с ID {request_id} обновлён на 'закрыта'.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении статуса заявки с ID {request_id}: {e}")


def save_media_to_db(request_id, file_path):
    """
    Сохраняет путь к медиафайлу в БД.
    """
    logger.info(f"Сохранение пути к файлу для заявки с ID {request_id}.")

    try:
        execute_db(
            """INSERT INTO media (request_id, file_path) VALUES (?, ?)""",
            (request_id, file_path),
            commit=True
        )
        logger.info(f"Путь к файлу {file_path} сохранён.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении пути к файлу {file_path} для заявки с ID {request_id}: {e}")
