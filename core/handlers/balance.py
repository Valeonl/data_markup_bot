from aiogram import Router, F
from aiogram.types import Message
from core.database.database import Database

router = Router()
db = Database('bot_database.db')

@router.message(F.text == '💰 Мой баланс')
async def show_balance(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Для просмотра баланса необходимо зарегистрироваться!")
        return
        
    balance_text = (
        f"💰 <b>Ваш баланс:</b>\n\n"
        f"Баллы: {user['points']}\n"
        f"Выполнено заданий: 0\n"  # Можно добавить в БД поле для подсчета заданий
        f"Штрафы: 0"  # Можно добавить в БД поле для штрафов
    )
    
    await message.answer(balance_text, parse_mode="HTML") 