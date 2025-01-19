from aiogram import Bot
from core.database.database import Database
import logging

async def notify_users_about_restart(bot: Bot, db: Database):
    """Уведомляет всех пользователей о перезапуске бота"""
    try:
        users = db.get_all_users()
        for user in users:
            try:
                await bot.send_message(
                    user['telegram_id'],
                    "🔄 Бот был обновлен и перезапущен!\n"
                    "Все функции снова доступны."
                )
            except Exception as e:
                logging.error(f"Ошибка отправки уведомления пользователю {user['telegram_id']}: {e}")
    except Exception as e:
        logging.error(f"Ошибка при рассылке уведомлений: {e}") 