from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from core.database.database import Database
from core.states.states import CommandStates
from core.keyboards.markup import (
    get_command_management_keyboard,
    get_commands_list_keyboard,
    get_command_actions_keyboard,
    get_user_markup_keyboard,
    get_command_record_keyboard,
    get_recording_review_keyboard
)
from core.keyboards.main import admin_keyboard, main_keyboard
import os
from datetime import datetime
from core.backend.audio_handler import save_voice_to_file, voice_to_text_whisper

router = Router()
db = Database('bot_database.db')

@router.message(F.text == '🎯 Перейти к разметке')
async def start_markup(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, сначала зарегистрируйтесь!")
        return
    
    await message.answer(
        "Выберите действие:",
        reply_markup=get_user_markup_keyboard()
    )

@router.message(F.text == "🎯 Доступные команды")
async def show_available_commands(message: Message):
    commands = db.get_pending_commands(message.from_user.id)
    if not commands:
        await message.answer(
            "Поздравляем! Вы выполнили все доступные команды! 🎉\n"
            "Ожидайте новых заданий."
        )
        return
    
    command = commands[0]  # Берем первую невыполненную команду
    await message.answer(
        f"📝 <b>Команда для записи:</b>\n\n"
        f"<b>Тег:</b> {command['tag']}\n"
        f"<b>Описание:</b> {command['description']}\n\n"
        f"Нажмите кнопку ниже, чтобы записать голосовое сообщение с этой командой.",
        reply_markup=get_command_record_keyboard(command['id']),
        parse_mode="HTML"
    )

@router.message(F.text == "📊 Мои записи")
async def show_user_commands(message: Message):
    commands = db.get_user_commands(message.from_user.id)
    if not commands:
        await message.answer("Вы еще не записали ни одной команды.")
        return
    
    text = "📊 <b>Ваши записи:</b>\n\n"
    for i, cmd in enumerate(commands, 1):
        text += (
            f"{i}. <b>{cmd['tag']}</b>\n"
            f"Описание: {cmd['description']}\n"
            f"Расшифровка: {cmd['transcript']}\n"
            f"Статус: {cmd['status']}\n"
            f"Дата: {cmd['created_at']}\n\n"
        )
    
    await message.answer(text, parse_mode="HTML")

@router.callback_query(F.data.startswith("record_cmd_"))
async def start_recording(callback: CallbackQuery, state: FSMContext):
    command_id = int(callback.data.split("_")[2])
    await state.update_data(recording_command_id=command_id)
    await state.set_state(CommandStates.waiting_for_voice)
    
    await callback.message.answer(
        "🎤 Запишите голосовое сообщение с командой.\n"
        "Постарайтесь говорить четко и следовать описанию команды."
    )

@router.message(CommandStates.waiting_for_voice, F.voice)
async def process_voice_command(message: Message, state: FSMContext):
    data = await state.get_data()
    command_id = data['recording_command_id']
    
    # Получаем информацию о команде
    command = db.get_command_by_id(command_id)
    if not command:
        await message.answer("Ошибка: команда не найдена!")
        await state.clear()
        return
    
    # Создаем структуру папок
    base_dir = "voice_commands"
    command_dir = os.path.join(base_dir, command['tag'])
    os.makedirs(command_dir, exist_ok=True)
    
    # Генерируем имя файла
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{message.from_user.id}_{timestamp}.ogg"
    
    try:
        # Сохраняем голосовое сообщение
        voice_path = await save_voice_to_file(message.bot, message)
        voice_path = os.path.join(command_dir, os.path.basename(voice_path))
        os.rename(voice_path, os.path.join(command_dir, filename))
        
        # Получаем расшифровку
        transcript = await voice_to_text_whisper(voice_path)
        
        # Сохраняем в БД
        if db.add_user_command(
            message.from_user.id,
            command_id,
            message.voice.file_id,
            voice_path,
            transcript
        ):
            await message.answer(
                "✅ Голосовая команда успешно записана!\n\n"
                f"📝 Расшифровка: {transcript}\n\n"
                "Хотите записать следующую команду?",
                reply_markup=get_user_markup_keyboard()
            )
            await show_available_commands(message)
        else:
            await message.answer(
                "❌ Ошибка при сохранении команды.\n"
                "Пожалуйста, попробуйте еще раз."
            )
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка при обработке голосового сообщения: {str(e)}"
        )
    finally:
        await state.clear()

@router.message(F.text == '💰 Мой баланс')
async def my_balance(message: Message):
    user_id = message.from_user.id
    await message.answer("Функционал баланса в разработке")

@router.message(F.text == '⚙️ Редактор разметки')
async def markup_editor(message: Message):
    user = db.get_user(message.from_user.id)
    if not user or user['role'] != 'admin':
        await message.answer("У вас нет доступа к этой функции!")
        return
    
    await message.answer(
        "🛠 <b>Редактор разметки</b>\n\n"
        "Здесь вы можете:\n"
        "• Добавлять новые команды\n"
        "• Просматривать список команд\n"
        "• Удалять команды",
        parse_mode="HTML",
        reply_markup=get_command_management_keyboard()
    )

@router.message(F.text == "➕ Добавить команду")
async def add_command_start(message: Message, state: FSMContext):
    if not db.is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой функции!")
        return
    
    await state.set_state(CommandStates.waiting_for_command)
    await message.answer(
        "Введите описание команды.\n"
        "Например: 'обрезать видео с 5 по 10 минуту'"
    )

@router.message(CommandStates.waiting_for_command)
async def process_command_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(CommandStates.waiting_for_tag)
    await message.answer(
        "Теперь введите тег команды (короткое название на английском).\n"
        "Например: cut_advance"
    )

@router.message(CommandStates.waiting_for_tag)
async def process_command_tag(message: Message, state: FSMContext):
    data = await state.get_data()
    description = data['description']
    tag = message.text.lower()
    
    if db.get_command_by_tag(tag):
        await message.answer(
            "Команда с таким тегом уже существует! "
            "Пожалуйста, выберите другой тег."
        )
        return
    
    if db.add_command(tag, description):
        await message.answer(
            f"✅ Команда успешно добавлена!\n\n"
            f"Тег: {tag}\n"
            f"Описание: {description}"
        )
    else:
        await message.answer("❌ Ошибка при добавлении команды!")
    
    await state.clear()

@router.message(F.text == "📝 Список команд")
async def list_commands(message: Message):
    if not db.is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой функции!")
        return
    
    commands = db.get_all_commands()
    if not commands:
        await message.answer("Список команд пуст!")
        return
    
    text = "📝 Список команд:\n\n"
    for cmd in commands:
        text += f"🔹 {cmd['tag']}: {cmd['description']}\n"
    
    await message.answer(
        text,
        reply_markup=get_commands_list_keyboard(commands)
    )

@router.callback_query(F.data.startswith("cmd_"))
async def command_details(callback: CallbackQuery):
    command_id = int(callback.data.split("_")[1])
    # Получаем детали команды и показываем их
    # ... код ...

@router.callback_query(F.data.startswith("delete_cmd_"))
async def delete_command(callback: CallbackQuery):
    command_id = int(callback.data.split("_")[2])
    if db.delete_command(command_id):
        await callback.answer("Команда удалена!")
        await list_commands(callback.message)
    else:
        await callback.answer("Ошибка при удалении команды!")

@router.callback_query(F.data == "delete_all_commands")
async def confirm_delete_all(callback: CallbackQuery):
    await callback.message.answer(
        "⚠️ Вы уверены, что хотите удалить ВСЕ команды?",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text="Да, удалить все",
                        callback_data="confirm_delete_all"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="Отмена",
                        callback_data="back_to_commands"
                    )
                ]
            ]
        )
    )

@router.message(F.text == "🔙 Назад в меню")
async def back_to_main_menu(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        await message.answer("Пожалуйста, сначала зарегистрируйтесь!")
        return
    
    keyboard = admin_keyboard if user['role'] == 'admin' else main_keyboard
    await message.answer(
        "Вы вернулись в главное меню",
        reply_markup=keyboard
    )

@router.message(F.text == "✅ Проверить записи")
async def check_recordings(message: Message):
    if not db.is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой функции!")
        return
    
    recordings = db.get_pending_recordings()
    if not recordings:
        await message.answer("Нет записей, ожидающих проверки!")
        return
    
    recording = recordings[0]  # Берем первую запись
    
    # Отправляем информацию о записи
    await message.answer(
        f"📝 <b>Запись для проверки:</b>\n\n"
        f"Команда: <b>{recording['command_tag']}</b>\n"
        f"Описание: {recording['command_description']}\n"
        f"Пользователь: @{recording['username']}\n"
        f"Расшифровка: {recording['transcript']}\n"
        f"Дата записи: {recording['created_at']}",
        parse_mode="HTML"
    )
    
    # Отправляем голосовое сообщение
    await message.answer_voice(
        recording['voice_file_id'],
        caption="🎤 Голосовое сообщение пользователя",
        reply_markup=get_recording_review_keyboard(recording['id'])
    )

@router.callback_query(F.data.startswith("approve_rec_"))
async def approve_recording(callback: CallbackQuery):
    recording_id = int(callback.data.split("_")[2])
    points = 10  # Количество баллов за одобренную запись
    
    if db.update_recording_status(recording_id, 'approved', points):
        await callback.answer("Запись одобрена! Пользователю начислено 10 баллов.")
        await check_recordings(callback.message)  # Показываем следующую запись
    else:
        await callback.answer("Ошибка при обновлении статуса записи!")

@router.callback_query(F.data.startswith("reject_rec_"))
async def reject_recording(callback: CallbackQuery):
    recording_id = int(callback.data.split("_")[2])
    
    if db.update_recording_status(recording_id, 'rejected'):
        await callback.answer("Запись отклонена!")
        await check_recordings(callback.message)  # Показываем следующую запись
    else:
        await callback.answer("Ошибка при обновлении статуса записи!")

@router.message(F.text == "📊 Статистика записей")
async def recordings_statistics(message: Message):
    if not db.is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой функции!")
        return
    
    stats = db.get_recordings_statistics()  # Нужно реализовать этот метод
    
    await message.answer(
        "📊 <b>Статистика записей:</b>\n\n"
        f"Всего записей: {stats['total']}\n"
        f"Ожидают проверки: {stats['pending']}\n"
        f"Одобрено: {stats['approved']}\n"
        f"Отклонено: {stats['rejected']}\n\n"
        f"Топ пользователей по записям:\n"
        f"{stats['top_users']}",
        parse_mode="HTML"
    ) 