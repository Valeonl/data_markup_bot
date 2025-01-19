from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import Message
from core.handlers.basic import get_start, get_voice
from core.settings import settings
from aiogram.filters import CommandStart, Command
import asyncio
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

kb = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='/start')],
    [KeyboardButton(text='/help')]
])

async def start_bot(bot: Bot):
    """Функция отправки сообщения админу бота о его запуске"""
    await bot.send_message(settings.bots.admin_id, text="Разметыш запущен")


async def stop_bot(bot: Bot):
    """Функция отправки сообщения админу бота о его остановке"""
    await bot.send_message(settings.bots.admin_id, text="Разметыш отстановлен")


bot = Bot(token=settings.bots.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()
@dp.message(CommandStart())
async def start(message: Message):
    await message.answer('Здравствуйте!', reply_markup=kb)

async def main():
    
    # Функция бота при его старте
    dp.startup.register(start_bot)
    # Функция бота при его остановке
    dp.shutdown.register(stop_bot)
    # Функция бота при отправки ему сообщения /start
    #dp.message.register(get_start, F.text)
    # Функция бота при отправки ему голосового сообщения
    dp.message.register(get_voice, F.voice)
    
    try:
        print("Бот запущен")
        await dp.start_polling(bot)
    finally:
        print("Бот отстановлен")
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())