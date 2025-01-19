import asyncio
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from core.config.settings import settings
from core.database.database import Database
from core.handlers import profile, registration, info, markup, balance, basic
from core.utils.notifications import notify_users_about_restart
import logging
import sys

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bot.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Настраиваем кодировку для логгера aiogram
aiogram_logger = logging.getLogger('aiogram')
for handler in aiogram_logger.handlers:
    if isinstance(handler, logging.StreamHandler):
        handler.stream = sys.stdout

# Инициализация бота и диспетчера
bot = Bot(token=settings.bots.bot_token)
dp = Dispatcher(storage=MemoryStorage())

# Инициализация базы данных
db = Database('bot_database.db')

# Регистрация роутеров
dp.include_router(basic.router)
dp.include_router(profile.router)
dp.include_router(registration.router)
dp.include_router(info.router)
dp.include_router(markup.router)
dp.include_router(balance.router)

# Запуск бота
async def main():
    try:
        print("Бот запущен")
        
        # Проверяем и обновляем роль админа при запуске
        admin = db.get_user(settings.bots.admin_id)
        if admin and admin['role'] != 'admin':
            db.set_admin_role(settings.bots.admin_id)
        
        await notify_users_about_restart(bot, db)
        # Оптимизированный polling
        await dp.start_polling(
            bot,
            allowed_updates=['message', 'callback_query'],  # Указываем только нужные типы обновлений
            skip_updates=True,  # Пропускаем накопившиеся обновления при перезапуске
            polling_timeout=60  # Увеличиваем timeout для уменьшения количества запросов
        )
    finally:
        print("Бот остановлен")
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())