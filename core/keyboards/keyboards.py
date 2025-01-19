from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
"""Клавиатуры для главного экрана и экранов с информацией"""
# Клавиатура с кнопками по 2 в ряд
main_keyboard = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='🎯 Перейти к разметке'),
        KeyboardButton(text='💰 Мой баланс')
    ],
    [
        KeyboardButton(text='👤 Личный кабинет')
    ],
    [
        KeyboardButton(text='ℹ️ Информация о проекте')
    ]
], resize_keyboard=True)

# Инлайн-клавиатура для переключения между страницами
project_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Информация об авторе', callback_data='author_info')],
    [InlineKeyboardButton(text='Связаться с автором', url='https://t.me/valeonl')]
])

author_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Вернуться к описанию проекта', callback_data='project_info')],
    [InlineKeyboardButton(text='Связаться с автором', url='https://t.me/valeonl')]
])

# Клавиатура личного кабинета с эмодзи
profile_keyboard = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='👤 Изменить имя'),
        KeyboardButton(text='📧 Изменить почту')
    ],
    [
        KeyboardButton(text='🏢 Изменить организацию'),
        KeyboardButton(text='🔗 Изменить соц. сеть')
    ],
    [
        KeyboardButton(text='❌ Удалить аккаунт')
    ],
    [
        KeyboardButton(text='🔙 Назад в меню')
    ]
], resize_keyboard=True)

# Клавиатура подтверждения удаления с эмодзи
confirm_delete_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='✅ Да, удалить', callback_data='confirm_delete'),
        InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_delete')
    ]
])

# Клавиатура отмены с эмодзи
cancel_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🔙 Отмена')]
], resize_keyboard=True)

# Добавим клавиатуру для отмены регистрации
cancel_registration_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отменить регистрацию')]
], resize_keyboard=True)