import logging
import pandas as pd
from datetime import datetime
import hashlib
import uuid
import os

from config import REPORTS_DIR
from work_database import execute_db

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
logger = logging.getLogger(__name__)


def fetch_data_from_db(filter_condition):
    """
    Функция для получения данных из базы данных с учётом фильтрации.
    :param filter_condition: условие фильтрации SQL-запроса
    :return: DataFrame с результатами запроса
    """
    query = f"""
    SELECT r.id, u.fio, u.phone, u.email, r.category, r.address, r.description, 
           r.status, r.created_at, a.fio AS admin_fio
    FROM requests r
    JOIN users u ON r.user_id = u.id
    LEFT JOIN users a ON r.admin_id = a.id
    WHERE {filter_condition}
    """

    # Выполнение запроса и получение всех результатов
    result = execute_db(query, fetchall=True)
    if result:
        return pd.DataFrame(result,
                            columns=["id", "fio", "phone", "email", "category", "address", "description", "status",
                                     "created_at", "admin_fio"])
    return None


def generate_unique_filename(filter_type):
    """
    Генерирует уникальное имя для отчёта, используя хэширование на основе времени и фильтра.
    Также проверяет наличие директории и создаёт её, если не существует.
    :param filter_type: тип фильтрации (по времени или без)
    :return: строка с уникальным именем файла
    """
    # Проверка и создание директории, если она не существует
    os.makedirs(REPORTS_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filter_string = f"{filter_type}_{timestamp}_{uuid.uuid4().hex[:8]}"  # Составляем строку для хэширования
    hash_object = hashlib.sha256(filter_string.encode())  # Хэшируем строку
    filename_hash = hash_object.hexdigest()  # Берём первые 8 символов хэша
    return os.path.join(REPORTS_DIR, f"{filter_type}_{filename_hash}.xlsx")


def export_requests_to_excel(filter_type="all_time"):
    """
    Функция для экспорта данных в Excel.
    :param filter_type: тип фильтрации (по времени или без)
    :return: название файла отчёта или None
    """
    now = datetime.now()
    logger.info(f"Запуск экспорта с фильтром: {filter_type}")

    if filter_type == "today":
        eight_am = datetime(now.year, now.month, now.day, 8, 0)
        filter_condition = f"r.created_at >= '{eight_am}'"
        logger.info(f"Фильтруем данные с {eight_am}")
    else:
        filter_condition = "1=1"
        logger.info("Фильтрация по всем данным")

    # Получаем данные из базы
    df = fetch_data_from_db(filter_condition)
    if df is None or df.empty:
        logger.warning("Нет данных для экспорта")
        return None

    output_file = generate_unique_filename(filter_type)
    logger.info(f"Генерация отчёта: {output_file}")

    try:
        with pd.ExcelWriter(output_file, engine="xlsxwriter") as writer:
            df.to_excel(writer, sheet_name="Requests", index=False)

            workbook = writer.book
            worksheet = writer.sheets["Requests"]

            # Формат заголовков (тёмно-зелёный, жирный, белый текст)
            header_format = workbook.add_format({
                "bold": True,
                "bg_color": "#4F7942",  # Тёмно-зелёный фон
                "font_color": "white",
                "align": "center",
                "valign": "vcenter",
                "border": 1  # Добавим границу
            })

            # Форматы строк для открытых и закрытых заявок (не яркие зеленые и красные)
            closed_format = workbook.add_format({
                "bg_color": "#A5D6A7",  # Нежно-зеленый для закрытых заявок
                "text_wrap": True,
                "align": "left",
                "valign": "top",
                "border": 1  # Добавим границу
            })

            open_format = workbook.add_format({
                "bg_color": "#FFCCBC",  # Светло-красный для открытых заявок
                "text_wrap": True,
                "align": "left",
                "valign": "top",
                "border": 1  # Добавим границу
            })

            # Устанавливаем заголовки с форматированием
            for col_num, col_name in enumerate(df.columns):
                worksheet.write(0, col_num, col_name, header_format)

            # Чередуем цвета строк в зависимости от статуса заявки
            for row_num in range(1, len(df) + 1):
                status = df.iloc[row_num - 1]["status"]  # Получаем статус заявки

                # Проверяем, если строка имеет статус и он не пустой
                if pd.notnull(status) and status != "":
                    row_format = closed_format if status == "closed" else open_format
                    for col_num in range(len(df.columns)):
                        worksheet.write(row_num, col_num, df.iloc[row_num - 1, col_num], row_format)

            # Включаем автофильтр
            worksheet.autofilter(0, 0, 0, len(df.columns) - 1)

            # Закрепляем заголовки
            worksheet.freeze_panes(1, 0)

            # Устанавливаем ширину колонок
            for i, col in enumerate(df.columns):
                max_len = max(df[col].astype(str).apply(len).max(), len(col)) + 2
                if col == "description":
                    worksheet.set_column(i, i, 50)  # 50 ≈ 600 пикселей
                else:
                    worksheet.set_column(i, i, max_len)

        logger.info(f"Отчёт успешно сохранён: {output_file}")
        return output_file  # Возвращаем название файла, если экспорт успешен
    except Exception as e:
        logger.error(f"Ошибка при сохранении отчёта в Excel: {e}")
        return None  # Возвращаем None в случае ошибки
