import asyncio
from aiogram import Bot, Dispatcher, F
from aiogram.types import FSInputFile, InputMediaPhoto, CallbackQuery, Message
from aiogram.filters import CommandStart
from aiogram.fsm.storage.memory import MemoryStorage
from core.settings import settings
from core.keyboards import main_keyboard, project_keyboard, author_keyboard

# Инициализация бота и диспетчера
# Замените 'YOUR_TOKEN' на ваш токен бота
bot = Bot(token=settings.bots.bot_token)
dp = Dispatcher(storage=MemoryStorage())


# Словарь для хранения баланса пользователей
user_balances = {}

# Обработчик команды /start
@dp.message(CommandStart())
async def start(message: Message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = {'balance': 0, 'penalties': 0}
        await message.answer("Это чат-бот для сбора и разметки обучающих наборов данных.", reply_markup=main_keyboard)
    else:
        await message.answer("С возвращением!", reply_markup=main_keyboard)

# Обработчик кнопки "Информация о чат-боте"
@dp.message(F.text == 'Информация о чат-боте')
async def bot_info(message: Message):
    photo_id = "AgACAgIAAxkDAAOWZx_5uCSgtlqgw-wGK7ySD0siGG0AAtPhMRu1awABSf9ysR7lIyeoAQADAgADeAADNgQ"
    await message.answer_photo(photo=photo_id, caption="Это чат-бот для сбора и разметки обучающих наборов данных")

# Обработчик кнопки "Информация о проекте"
@dp.message(F.text == 'Информация о проекте')
async def project_info(message: Message):
    photo_id = "AgACAgIAAxkDAAOWZx_5uCSgtlqgw-wGK7ySD0siGG0AAtPhMRu1awABSf9ysR7lIyeoAQADAgADeAADNgQ"
    await message.answer_photo(
        photo=photo_id,
        caption="*Чат-бот 'Разметыш'* является частью магистерской работы, посвящённой созданию системы голосового помощника в сфере видеомонтажа *Voice3Frame*.\n\nАвтор проекта: *Трифонов Валентин*",
        parse_mode="Markdown",
        reply_markup=project_keyboard
    )

# Обработчик кнопки "Мой баланс"
@dp.message(F.text == 'Мой баланс')
async def my_balance(message: Message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = {'balance': 0, 'penalties': 0}
    
    balance = user_balances[user_id]['balance']
    penalties = user_balances[user_id]['penalties']
    await message.answer(
        f"Заработано баллов: {balance} 💼\n"
        f"Штрафных баллов: {penalties} 😠\n"
        f"Текущий баланс: *{balance - penalties}*",
        parse_mode="Markdown"
    )

# Обработчик кнопки "Перейти к разметке"
@dp.message(F.text == 'Перейти к разметке')
async def start_markup(message: Message):
    user_id = message.from_user.id
    if user_id not in user_balances:
        user_balances[user_id] = {'balance': 0, 'penalties': 0}
    
    user_balances[user_id]['balance'] += 1
    await message.answer("+ 1 балл")

# Обработчик колбэк-запроса для переключения на страницу автора
@dp.callback_query(F.data == 'author_info')
async def author_info(callback: CallbackQuery):
    photo_id = "AgACAgIAAxkDAAOkZx_9MIy3zgF04WOIF26CKyPzAkwAAtjhMRu1awABSbJse_3Ba9rvAQADAgADcwADNgQ"
    await callback.message.answer_photo(
        photo=photo_id,
        caption="*Трифонов Валентин Николаевич*\nСтудент магистратуры ИТМО\nГруппа: Р4123",
        parse_mode="Markdown",
        reply_markup=author_keyboard
    )

# Обработчик колбэк-запроса для возврата к описанию проекта
@dp.callback_query(F.data == 'project_info')
async def return_to_project_info(callback: CallbackQuery):
    photo_id = "AgACAgIAAxkDAAOWZx_5uCSgtlqgw-wGK7ySD0siGG0AAtPhMRu1awABSf9ysR7lIyeoAQADAgADeAADNgQ"
    await callback.message.answer_photo(
        photo=photo_id,
        caption="*Чат-бот 'Разметыш'* является частью магистерской работы, посвящённой созданию системы голосового помощника в сфере видеомонтажа *Voice3Frame*.\n\nАвтор проекта: *Трифонов Валентин*",
        parse_mode="Markdown",
        reply_markup=project_keyboard
    )

# Запуск бота
async def main():
    try:
        print("Бот запущен")
        await dp.start_polling(bot)
    finally:
        print("Бот отстановлен")
        await bot.session.close()

if __name__ == '__main__':
    asyncio.run(main())