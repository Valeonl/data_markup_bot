from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# Главная клавиатура
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

# Клавиатуры для информации о проекте
project_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Информация об авторе', callback_data='author_info')],
    [InlineKeyboardButton(text='Связаться с автором', url='https://t.me/valeonl')]
])

author_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text='Вернуться к описанию проекта', callback_data='project_info')],
    [InlineKeyboardButton(text='Связаться с автором', url='https://t.me/valeonl')]
])

# Клавиатура для админа
admin_keyboard = ReplyKeyboardMarkup(keyboard=[
    [
        KeyboardButton(text='🎯 Перейти к разметке'),
        KeyboardButton(text='💰 Мой баланс')
    ],
    [
        KeyboardButton(text='👤 Личный кабинет'),
        KeyboardButton(text='⚙️ Редактор разметки')  # Новая кнопка для админа
    ],
    [
        KeyboardButton(text='ℹ️ Информация о проекте')
    ]
], resize_keyboard=True) 