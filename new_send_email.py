from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import smtplib
from pathlib import Path
import logging

from config import FROM_EMAIL, FROM_PASSWORD


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
logger = logging.getLogger(__name__)


def send_email(request_data, response_text, file_path):
    """Отправка email с ответом на заявку пользователя"""

    subject = f"Заявка №{request_data['request_id']}"

    # Создаем email сообщение
    msg = MIMEMultipart()
    msg['From'] = FROM_EMAIL
    msg['To'] = request_data['user']['email']
    msg['Subject'] = subject
    msg.attach(MIMEText(response_text, 'plain'))

    logger.info(f"Отправка письма пользователю {request_data['user']['email']} по заявке №{request_data['request_id']}")

    # Прикрепляем файл, если он есть
    if file_path:
        media_path = Path(file_path)
        logger.info(f"Проверка наличия файла для прикрепления: {media_path}")
        if media_path.exists():
            try:
                logger.info(f"Файл найден, начинаем загрузку: {media_path}")
                with open(media_path, 'rb') as file:
                    attachment = MIMEBase('application', 'octet-stream')
                    attachment.set_payload(file.read())
                    encoders.encode_base64(attachment)
                    attachment.add_header('Content-Disposition', f'attachment; filename="{media_path.name}"')
                    msg.attach(attachment)
                logger.info(f"Файл успешно прикреплен: {media_path.name}")
            except Exception as e:
                logger.error(f"Ошибка при добавлении вложения: {e}")
        else:
            logger.warning(f"Файл {media_path} не найден, отправка без вложения.")

    # Отправка письма
    try:
        logger.info(f"Подключение к SMTP серверу для отправки письма на {request_data['user']['email']}")
        with smtplib.SMTP_SSL("smtp.yandex.ru", 465) as server:
            server.login(FROM_EMAIL, FROM_PASSWORD)
            server.sendmail(FROM_EMAIL, request_data['user']['email'], msg.as_string())
            logger.info(f"Ответ на заявку №{request_data['request_id']} успешно отправлен на "
                        f"{request_data['user']['email']}")
    except Exception as e:
        logger.error(f"Ошибка при отправке письма: {e}")
        raise
