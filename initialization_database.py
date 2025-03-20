import sqlite3
import os
import logging

from config import DATABASE_PATH


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
logger = logging.getLogger(__name__)


def init_db():
    """Создаёт таблицы в базе данных, если они не существуют."""
    conn = None  # Инициализируем conn как None для предотвращения ошибки

    # Проверка, существует ли папка для базы данных
    db_directory = os.path.dirname(DATABASE_PATH)
    if not os.path.exists(db_directory):
        try:
            os.makedirs(db_directory)
            logger.info(f"Папка для базы данных была успешно создана: {db_directory}")
        except Exception as e:
            logger.error(f"Ошибка при создании папки для базы данных: {e}")
            return

    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()
        logger.info("Подключение к базе данных успешно")

        # Создание таблицы пользователей с добавлением username, telegram_id и уникальности для phone и telegram_id
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT,
                telegram_id INTEGER NOT NULL UNIQUE,
                fio TEXT NOT NULL,
                phone TEXT UNIQUE,
                email TEXT,
                role TEXT NOT NULL
            )
        ''')
        logger.info("Таблица 'users' успешно создана или уже существует")

        # Создание таблицы заявок с добавлением связи с пользователем и администратором
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                admin_id INTEGER,  -- Новый столбец для связи с администратором
                category TEXT,
                address TEXT,
                description TEXT,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT (DATETIME('now', '+3 hours')),
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (admin_id) REFERENCES users (id)  -- Внешний ключ для администратора
            )
        ''')
        logger.info("Таблица 'requests' успешно создана или уже существует")

        # Создание таблицы сообщений с добавлением связи с пользователем
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER NOT NULL,
                sender_id INTEGER NOT NULL,
                message TEXT,
                created_at TIMESTAMP DEFAULT (DATETIME('now', '+3 hours')),
                FOREIGN KEY (request_id) REFERENCES requests (id)
            )
        ''')
        logger.info("Таблица 'messages' успешно создана или уже существует")

        # Создание таблицы media для связи как с заявками, так и с сообщениями
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id INTEGER,
                message_id INTEGER,
                file_path TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT (DATETIME('now', '+3 hours')),
                FOREIGN KEY (request_id) REFERENCES requests (id),
                FOREIGN KEY (message_id) REFERENCES messages (id),
                CHECK (request_id IS NOT NULL OR message_id IS NOT NULL)
            )
        ''')
        logger.info("Таблица 'media' успешно создана или уже существует")

        conn.commit()
        logger.info("Изменения в базе данных успешно сохранены")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
    finally:
        if conn:  # Проверяем, был ли объект соединения создан
            conn.close()
            logger.info("Соединение с базой данных закрыто")


init_db()
