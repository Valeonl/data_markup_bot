from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from typing import List, Dict, Any

def get_command_management_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления командами"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="➕ Добавить команду")],
            [KeyboardButton(text="📝 Список команд")],
            [KeyboardButton(text="🎤 Тест распознавания")],
            [KeyboardButton(text="📊 Экспорт данных из БД")],
            [KeyboardButton(text="🔙 Назад в меню")]
        ],
        resize_keyboard=True
    )

def get_commands_list_keyboard(commands: List[Dict[str, Any]]) -> InlineKeyboardMarkup:
    """Создает клавиатуру со списком команд"""
    keyboard = []
    for cmd in commands:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{cmd['tag']} - {cmd['description'][:30]}...",
                callback_data=f"cmd_{cmd['id']}"
            )
        ])
    keyboard.append([
        InlineKeyboardButton(text="❌ Удалить все", callback_data="delete_all_commands")
    ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def get_command_actions_keyboard(command_id: int) -> InlineKeyboardMarkup:
    """Клавиатура действий с командой"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="❌ Удалить",
                    callback_data=f"delete_cmd_{command_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="🔙 Назад к списку",
                    callback_data="back_to_commands"
                )
            ]
        ]
    )

def get_user_markup_keyboard():
    """Клавиатура разметки для пользователей"""
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🎯 Доступные команды")],
            [KeyboardButton(text="📊 Мои записи")],
            [KeyboardButton(text="🔙 Назад в меню")]
        ],
        resize_keyboard=True
    )
    return keyboard

def get_command_record_keyboard(command_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для записи команды"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🎤 Записать команду",
                    callback_data=f"record_cmd_{command_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏭ Пропустить",
                    callback_data="skip_command"
                )
            ]
        ]
    )

def get_recordings_management_keyboard() -> ReplyKeyboardMarkup:
    """Клавиатура управления записями"""
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="✅ Проверить записи")],
            [KeyboardButton(text="📊 Статистика записей")],
            [KeyboardButton(text="🔙 Назад в меню")]
        ],
        resize_keyboard=True
    )

def get_recording_review_keyboard(recording_id: int) -> InlineKeyboardMarkup:
    """Клавиатура для проверки записи"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="✅ Принять",
                    callback_data=f"approve_rec_{recording_id}"
                ),
                InlineKeyboardButton(
                    text="❌ Отклонить",
                    callback_data=f"reject_rec_{recording_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="⏭ Пропустить",
                    callback_data="skip_recording"
                )
            ]
        ]
    ) 