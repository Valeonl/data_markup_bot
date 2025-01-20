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

# Добавим словарь для хранения ID последнего голосового сообщения для каждого чата
last_voice_messages = {}

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
            f"ID записи: <code>{cmd['voice_file_id']}</code>\n"
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
    
    try:
        # Получаем file_id голосового сообщения
        voice_file_id = message.voice.file_id
        
        # Сначала отправляем сообщение о начале обработки
        processing_msg = await message.answer("🔄 Обрабатываю голосовое сообщение...")
        
        # Получаем расшифровку
        temp_file = f"temp_{message.from_user.id}.ogg"
        await save_voice_to_file(message.bot, message, temp_file)
        transcript = await voice_to_text_whisper(temp_file)
        os.remove(temp_file)  # Удаляем временный файл
        
        # Сначала показываем транскрипцию
        await message.answer(
            f"📝 <b>Расшифровка вашего сообщения:</b>\n\n"
            f"{transcript}",
            parse_mode="HTML"
        )
        
        # Сохраняем в БД
        if db.add_user_command(
            message.from_user.id,
            command_id,
            voice_file_id,
            transcript
        ):
            await message.answer(
                "✅ Голосовая команда успешно сохранена!\n\n"
                f"🎯 <b>Команда:</b> {command['tag']}\n"
                f"📋 <b>Описание:</b> {command['description']}\n"
                f"🆔 <b>ID записи:</b> <code>{voice_file_id}</code>\n\n"
                f"📝 <b>Расшифровка:</b>\n{transcript}",
                parse_mode="HTML",
                reply_markup=get_user_markup_keyboard()
            )
            
            # Удаляем сообщение о обработке
            await processing_msg.delete()
            
            # Показываем следующую доступную команду
            await show_available_commands(message)
        else:
            await message.answer(
                "❌ Ошибка при сохранении команды.\n"
                "Пожалуйста, обратитесь к администратору."
            )
    except Exception as e:
        await message.answer(
            f"❌ Произошла ошибка при обработке голосового сообщения:\n{str(e)}"
        )
        print(f"Error processing voice message: {e}")  # Добавляем логирование ошибки
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

def create_commands_keyboard(commands: list) -> InlineKeyboardMarkup:
    """Создает клавиатуру со списком команд и кнопкой удаления всех"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text=f"📝 {cmd['tag']}",
                callback_data=f"view_cmd_{cmd['tag']}"
            )
        ]
        for cmd in commands
    ])
    
    # Добавляем кнопку удаления всех команд
    keyboard.inline_keyboard.append([
        InlineKeyboardButton(
            text="🗑 Удалить все команды",
            callback_data="delete-all-commands"
        )
    ])
    
    return keyboard

@router.message(F.text == "📝 Список команд")
async def list_commands(message: Message):
    if not db.is_admin(message.from_user.id):
        await message.answer("У вас нет доступа к этой функции!")
        return
    
    commands = db.get_all_commands()
    if not commands:
        await message.answer("Список команд пуст!")
        return
    
    keyboard = create_commands_keyboard(commands)
    
    await message.answer(
        "📋 <b>Список всех команд:</b>\n"
        "Нажмите на команду для просмотра всех записей",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("view_cmd_"))
async def view_command_recordings(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    
    # Удаляем последнее голосовое сообщение при просмотре новой команды
    if chat_id in last_voice_messages:
        try:
            await callback.bot.delete_message(
                chat_id=chat_id,
                message_id=last_voice_messages[chat_id]
            )
            del last_voice_messages[chat_id]
        except Exception as e:
            print(f"Error deleting voice message: {e}")
    
    # Используем весь текст после view_cmd_ как тег команды
    command_tag = callback.data[9:]  # Убираем префикс "view_cmd_"
    recordings = db.get_command_recordings(command_tag)
    
    # Создаем клавиатуру
    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    
    # Добавляем кнопки для записей, если они есть
    if recordings:
        keyboard.inline_keyboard.extend([
            [
                InlineKeyboardButton(
                    text=f"🎧 {rec['username'] or 'Аноним'}",
                    callback_data=f"play_rec_{rec['id']}"
                )
            ]
            for rec in recordings
        ])
    
    # Добавляем кнопки управления
    keyboard.inline_keyboard.extend([
        [
            InlineKeyboardButton(
                text="🗑 Удалить команду",
                callback_data=f"delete_cmd_{command_tag}"
            )
        ],
        [
            InlineKeyboardButton(
                text="🔙 Назад к списку команд",
                callback_data="back_to_commands"
            )
        ]
    ])
    
    # Формируем текст
    if recordings:
        first_rec = recordings[0]
        text = (
            f"🎯 <b>Команда: {first_rec['command_tag']}</b>\n"
            f"📋 <b>Описание:</b> {first_rec['command_description']}\n\n"
            f"<b>Записи команды:</b>\n\n"
        )
        
        for i, rec in enumerate(recordings, 1):
            status_emoji = "✅" if rec['status'] == 'approved' else "❌" if rec['status'] == 'rejected' else "⏳"
            text += (
                f"{i}. От: @{rec['username'] or 'Аноним'}\n"
                f"👤 {rec['display_name']}\n"
                f"📝 Расшифровка: {rec['transcript']}\n"
                f"📅 Дата: {rec['created_at']}\n"
                f"Статус: {status_emoji}\n\n"
            )
    else:
        text = (
            f"🎯 <b>Команда: {command_tag}</b>\n"
            f"Для этой команды пока нет записей.\n"
        )
    
    await callback.message.edit_text(
        text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("play_rec_"))
async def play_recording(callback: CallbackQuery):
    recording_id = int(callback.data.split("_")[2])
    voice_file_id = db.get_voice_file_id(recording_id)
    chat_id = callback.message.chat.id
    
    if voice_file_id:
        # Удаляем предыдущее голосовое сообщение если оно есть
        if chat_id in last_voice_messages:
            try:
                await callback.bot.delete_message(
                    chat_id=chat_id,
                    message_id=last_voice_messages[chat_id]
                )
            except Exception as e:
                print(f"Error deleting previous voice message: {e}")
        
        # Отправляем новое голосовое
        voice_message = await callback.message.answer_voice(
            voice_file_id,
            caption="🎤 Голосовое сообщение"
        )
        # Сохраняем ID нового голосового сообщения
        last_voice_messages[chat_id] = voice_message.message_id
    else:
        await callback.answer("Ошибка: запись не найдена", show_alert=True)

@router.callback_query(F.data.startswith("back_to_recordings_"))
async def back_to_recordings(callback: CallbackQuery):
    command_tag = callback.data.split("_")[3]
    # Удаляем сообщение с голосовой записью
    await callback.message.delete()
    # Возвращаемся к списку записей для этой команды
    await view_command_recordings(callback)

@router.callback_query(F.data == "back_to_commands")
async def back_to_commands_list(callback: CallbackQuery):
    chat_id = callback.message.chat.id
    
    # Удаляем последнее голосовое сообщение при возврате к списку команд
    if chat_id in last_voice_messages:
        try:
            await callback.bot.delete_message(
                chat_id=chat_id,
                message_id=last_voice_messages[chat_id]
            )
            del last_voice_messages[chat_id]
        except Exception as e:
            print(f"Error deleting voice message: {e}")
    
    commands = db.get_all_commands()
    if not commands:
        await callback.message.edit_text("Список команд пуст!")
        return
    
    keyboard = create_commands_keyboard(commands)
    
    await callback.message.edit_text(
        "📋 <b>Список всех команд:</b>\n"
        "Нажмите на команду для просмотра всех записей",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("cmd_"))
async def command_details(callback: CallbackQuery):
    command_id = int(callback.data.split("_")[1])
    # Получаем детали команды и показываем их
    # ... код ...

@router.callback_query(F.data.startswith("delete_cmd_"))
async def confirm_delete_command(callback: CallbackQuery):
    # Убираем префикс "delete_cmd_" без тире
    command_tag = callback.data.replace("delete_cmd_", "")
    recordings_count = db.get_command_recordings_count(command_tag)
    
    if recordings_count == 0:
        if db.delete_command_by_tag(command_tag):
            await callback.answer("✅ Команда успешно удалена!")
            # Проверяем остались ли ещё команды
            commands = db.get_all_commands()
            if not commands:
                await callback.message.edit_text(
                    "📋 Список команд пуст!",
                    parse_mode="HTML"
                )
            else:
                await back_to_commands_list(callback)
        else:
            await callback.answer("❌ Ошибка при удалении команды!", show_alert=True)
    else:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Да, удалить",
                    callback_data=f"confirm-delete-{command_tag}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data=f"view_cmd_{command_tag}"
                )
            ]
        ])
        
        await callback.message.edit_text(
            f"⚠️ <b>Внимание!</b>\n\n"
            f"Для команды <b>{command_tag}</b> существует "
            f"{recordings_count} записей.\n"
            f"Вы уверены, что хотите удалить команду?\n"
            f"Все записи также будут удалены!",
            reply_markup=keyboard,
            parse_mode="HTML"
        )

@router.callback_query(F.data.startswith("confirm-delete-"))
async def execute_delete_command(callback: CallbackQuery):
    # Убираем префикс "confirm-delete-" без тире
    command_tag = callback.data.replace("confirm-delete-", "")
    
    if db.delete_command_by_tag(command_tag):
        await callback.answer("✅ Команда и все её записи удалены!")
        await back_to_commands_list(callback)
    else:
        await callback.answer("❌ Ошибка при удалении команды!", show_alert=True)

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
        f"ID записи: <code>{recording['voice_file_id']}</code>\n"
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

@router.callback_query(F.data == "delete-all-commands")
async def confirm_delete_all_commands(callback: CallbackQuery):
    # Получаем общее количество команд и записей
    total_commands = len(db.get_all_commands())
    total_recordings = db.get_total_recordings_count()  # Нужно добавить этот метод в Database
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Да, удалить всё",
                callback_data="confirm-delete-all"
            )
        ],
        [
            InlineKeyboardButton(
                text="Отмена",
                callback_data="back_to_commands"
            )
        ]
    ])
    
    await callback.message.edit_text(
        f"⚠️ <b>Внимание!</b>\n\n"
        f"Вы собираетесь удалить <b>ВСЕ</b> команды!\n\n"
        f"📊 Статистика:\n"
        f"• Всего команд: {total_commands}\n"
        f"• Всего записей: {total_recordings}\n\n"
        f"❗️ Это действие необратимо. Все команды и их записи будут удалены!\n"
        f"Вы уверены?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == "confirm-delete-all")
async def execute_delete_all_commands(callback: CallbackQuery):
    print(f"Starting delete all commands process...")
    
    # Получаем все команды перед удалением для проверки
    commands = db.get_all_commands()
    print(f"Current commands before deletion: {commands}")
    
    if not commands:
        print("No commands found to delete")
        await callback.answer("Нет команд для удаления!", show_alert=True)
        return
    
    # Удаляем все команды
    print("Attempting to delete all commands...")
    deletion_result = db.delete_all_commands()
    print(f"Deletion result: {deletion_result}")
    
    if deletion_result:
        # Проверяем, что все команды действительно удалены
        remaining_commands = db.get_all_commands()
        print(f"Remaining commands after deletion: {remaining_commands}")
        
        if not remaining_commands:
            print("All commands successfully deleted")
            await callback.answer("✅ Все команды успешно удалены!", show_alert=True)
            await callback.message.edit_text(
                "📋 Список команд пуст!",
                parse_mode="HTML"
            )
        else:
            print(f"Warning: {len(remaining_commands)} commands still remain")
            await callback.answer("⚠️ Удалены не все команды!", show_alert=True)
            await back_to_commands_list(callback)
    else:
        print("Error occurred during deletion")
        await callback.answer("❌ Ошибка при удалении команд!", show_alert=True)
        await back_to_commands_list(callback) 