import logging
from aiogram import Bot

from keyboards import create_keyboard_answer


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(filename)s - %(message)s')
logger = logging.getLogger(__name__)


async def notify_admins_about_request(bot: Bot, request_id, user_data, request_data, admin_id):
    """
    Отправляет уведомление администраторам о новой заявке.
    """
    request_text = (
        f"\U0001F514 <b>Новая заявка!</b>\n\n"
        f"ID заявки: <b>{request_id}</b>\n"
        f"Категория: <b>{request_data['category']}</b>\n"
        f"ФИО: <b>{user_data['fio']}</b>\n"
        f"Номер: <b>{user_data['phone']}</b>\n"
        f"Email: <b>{user_data['email']}</b>\n"
        f"{f'Адрес: <b>{request_data.get("address")}</b>\n' if request_data.get('address') else ''}"
        f"Описание: <b>{request_data['description']}</b>"
    )

    logger.info(f"Отправка уведомления админу {admin_id} о заявке {request_id}")

    try:
        if request_data.get("media"):
            file_path = request_data["media"].split('.')[0]
            try:
                logger.info(f"Отправка фото админу {admin_id} для заявки {request_id}")
                await bot.send_photo(chat_id=admin_id, photo=file_path, caption=request_text,
                                     reply_markup=create_keyboard_answer(request_id), parse_mode="html")
            except Exception:
                logger.warning(f"Ошибка при отправке фото, пробуем отправить видео админу {admin_id}")
                await bot.send_video(chat_id=admin_id, video=file_path, caption=request_text,
                                     reply_markup=create_keyboard_answer(request_id), parse_mode="html")
        else:
            logger.info(f"Отправка текстового сообщения админу {admin_id} для заявки {request_id}")
            await bot.send_message(chat_id=admin_id, text=request_text,
                                   reply_markup=create_keyboard_answer(request_id), parse_mode="html")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления админу {admin_id}: {e}")
