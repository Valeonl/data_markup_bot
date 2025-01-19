import os
from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from core.backend.audio_handler import save_voice_to_file, voice_to_text_google, text_to_sentence,voice_to_text_whisper
from core.database.database import Database
from core.keyboards.main import admin_keyboard, main_keyboard
from core.config.settings import settings
from core.utils.logger import bot_logger
from core.states.states import RegistrationStates

router = Router()
db = Database('bot_database.db')

async def get_start(message: Message, bot: Bot):
    """Функция при отправке боту сообщения /start"""
    await bot.send_message(message.from_user.id, f"<b>Привет, {message.from_user.first_name}!</b>")
    await message.answer(f"Привет, {message.from_user.username}!")
    await message.reply(f"Привет, {message.from_user.first_name}!")


async def get_voice(message: Message, bot:Bot):
    """Функция для получения голосовых сообщений пользователя"""
    await message.answer("Вы прислали аудиофайл!")
    voice_path = await save_voice_to_file(bot, message)
    #transcript_voice_text_with_google = await voice_to_text_google(voice_path)
    transcript_voice_text_with_whisper = await voice_to_text_whisper(voice_path)
    transcript_voice_text = (f"<b>Расшифровка от Whisper:</b> {transcript_voice_text_with_whisper}")
    #transcript_voice_text = (f"<b>Google:</b> {transcript_voice_text_with_google}\n\n"
    #                         f"<b>Whisper:</b> {transcript_voice_text_with_whisper}")
    forward_date = message.date
    formatted_date = forward_date.strftime("%Y-%m-%d")
    formatted_time = forward_date.strftime("%H:%M:%S")
    os.remove(voice_path)

    if transcript_voice_text:
        #text_sentence = await text_to_sentence(transcript_voice_text)
        text_sentence = "\n".join(transcript_voice_text)
        await message.reply(text=transcript_voice_text)
        print(f"{formatted_date} {formatted_time} | Получено аудиосообщение от {message.from_user.username}:\nТекст сообщения: '{transcript_voice_text}'")

@router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    user = db.get_user(message.from_user.id)
    bot_logger.log_action(message.from_user.id, "Использована команда /start")
    
    if not user:
        # Проверяем, является ли пользователь админом по ID
        if message.from_user.id == settings.bots.admin_id:
            # Создаем пользователя с ролью админа
            db.create_user(message.from_user.id, message.from_user.username)
            bot_logger.log_action(message.from_user.id, "Создан новый аккаунт администратора")
            await message.answer(
                f"Добро пожаловать, администратор!\n"
                f"Вы можете использовать все функции бота.",
                reply_markup=admin_keyboard
            )
        else:
            # Для обычных пользователей запускаем регистрацию
            bot_logger.log_action(message.from_user.id, "Начата регистрация нового пользователя")
            await message.answer(
                "Добро пожаловать! Для начала работы необходимо пройти регистрацию.\n"
                "Пожалуйста, введите ваше имя:"
            )
            await state.set_state(RegistrationStates.waiting_for_name)
    else:
        # Проверяем и обновляем роль, если это админ
        if message.from_user.id == settings.bots.admin_id and user['role'] != 'admin':
            db.set_admin_role(message.from_user.id)
            user = db.get_user(message.from_user.id)  # Получаем обновленные данные
        
        keyboard = admin_keyboard if user['role'] == 'admin' else main_keyboard
        await message.answer(
            f"С возвращением, {user['display_name']}!",
            reply_markup=keyboard
        )

@router.message(Command("make_admin"))
async def make_admin(message: Message):
    if message.from_user.id == settings.bots.admin_id or db.is_admin(message.from_user.id):
        db.set_admin_role(message.from_user.id)
        await message.answer("Вы назначены администратором!")
    else:
        await message.answer("У вас нет прав для выполнения этой команды.")

@router.message(Command("logging_off"))
async def disable_logging(message: Message):
    """Отключает логирование действий для пользователя"""
    bot_logger.disable_logging(message.from_user.id)
    await message.answer("Логирование ваших действий отключено")

@router.message(Command("logging_on"))
async def enable_logging(message: Message):
    """Включает логирование действий для пользователя"""
    bot_logger.enable_logging(message.from_user.id)
    await message.answer("Логирование ваших действий включено")

@router.message(Command("logging_status"))
async def logging_status(message: Message):
    """Показывает текущий статус логирования"""
    status = "отключено" if message.from_user.id in bot_logger.disabled_users else "включено"
    await message.answer(f"Логирование ваших действий {status}")