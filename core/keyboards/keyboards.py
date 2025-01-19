from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
"""Клавиатуры для главного экрана и экранов с информацией"""
# Клавиатура с кнопками по 2 в ряд
main_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Перейти к разметке'), KeyboardButton(text='Мой баланс')],
    [KeyboardButton(text='Информация о чат-боте'), KeyboardButton(text='Информация о проекте')]
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