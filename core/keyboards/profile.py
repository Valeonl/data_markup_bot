from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

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

confirm_delete_keyboard = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text='✅ Да, удалить', callback_data='confirm_delete'),
        InlineKeyboardButton(text='❌ Отмена', callback_data='cancel_delete')
    ]
])

cancel_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='🔙 Отмена')]
], resize_keyboard=True)

cancel_registration_keyboard = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text='Отменить регистрацию')]
], resize_keyboard=True) 