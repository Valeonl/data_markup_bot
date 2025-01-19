from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from core.database.database import Database
from core.keyboards.profile import profile_keyboard, confirm_delete_keyboard, cancel_keyboard
from core.keyboards.main import main_keyboard, admin_keyboard
from core.states.states import ProfileStates
from datetime import datetime, timedelta
from core.utils.logger import bot_logger
from core.config.settings import settings

router = Router()
db = Database('bot_database.db')

@router.message(F.text == '👤 Личный кабинет')
async def profile(message: Message, telegram_id: int = None):
    user_id = telegram_id or message.from_user.id
    bot_logger.log_action(user_id, "Открыт личный кабинет")
    
    user = db.get_user(user_id)
    if not user:
        db.create_user(user_id, message.from_user.username)
        user = db.get_user(user_id)

    registration_date = datetime.strptime(user['registration_date'], '%Y-%m-%d %H:%M:%S')
    registration_date = registration_date + timedelta(hours=3)
    formatted_date = registration_date.strftime('%d.%m.%Y %H:%M')

    profile_text = (
        f"👤 <b>Ваш профиль:</b>\n\n"
        f"<b>Роль:</b> {user['role_display']}\n"
        f"<b>Имя:</b> {user['display_name'] or 'Не указано'}\n"
        f"<b>Username:</b> @{user['username']}\n"
        f"<b>Email:</b> {user['email'] or 'Не указан'}\n"
        f"<b>Организация:</b> {user['organization'] or 'Не указана'}\n"
        f"<b>Соц. сеть:</b> {user['social_link'] or 'Не указана'}\n"
        f"<b>Баллы:</b> {user['points']}\n"
        f"<b>Дата регистрации:</b> {formatted_date}"
    )

    # Получаем фотографии профиля пользователя
    user_profile_photos = await message.bot.get_user_profile_photos(user_id)
    
    # Если у пользователя есть аватарка, отправляем её вместе с информацией
    if user_profile_photos.total_count > 0:
        photo = user_profile_photos.photos[0][-1]
        await message.answer_photo(
            photo.file_id,
            caption=profile_text,
            reply_markup=profile_keyboard,
            parse_mode="HTML"
        )
    else:
        # Если аватарки нет, отправляем только текст
        await message.answer(
            profile_text,
            reply_markup=profile_keyboard,
            parse_mode="HTML"
        )

@router.message(F.text == '👤 Изменить имя')
async def change_name(message: Message, state: FSMContext):
    bot_logger.log_action(message.from_user.id, "Запрошено изменение имени")
    await state.set_state(ProfileStates.waiting_for_name)
    await message.answer("Введите ваше новое имя:", reply_markup=cancel_keyboard)

@router.message(ProfileStates.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    if message.text == '🔙 Отмена':
        bot_logger.log_action(message.from_user.id, "Отменено изменение имени")
        await state.clear()
        await profile(message)
        return

    bot_logger.log_action(
        message.from_user.id, 
        "Изменено имя",
        {"new_name": message.text}
    )
    db.update_user(message.from_user.id, display_name=message.text)
    await state.clear()
    await message.answer("Имя успешно обновлено!")
    await profile(message)

@router.message(F.text == '📧 Изменить почту')
async def change_email(message: Message, state: FSMContext):
    await state.set_state(ProfileStates.waiting_for_email)
    await message.answer("Введите вашу новую почту:", reply_markup=cancel_keyboard)

@router.message(ProfileStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    if message.text == '🔙 Отмена':
        await state.clear()
        await profile(message)
        return

    db.update_user(message.from_user.id, email=message.text)
    await state.clear()
    await message.answer("Почта успешно обновлена!")
    await profile(message)

@router.message(F.text == '🏢 Изменить организацию')
async def change_organization(message: Message, state: FSMContext):
    await state.set_state(ProfileStates.waiting_for_organization)
    await message.answer("Введите название вашей организации:", reply_markup=cancel_keyboard)

@router.message(ProfileStates.waiting_for_organization)
async def process_organization(message: Message, state: FSMContext):
    if message.text == '🔙 Отмена':
        await state.clear()
        await profile(message)
        return

    db.update_user(message.from_user.id, organization=message.text)
    await state.clear()
    await message.answer("Организация успешно обновлена!")
    await profile(message)

@router.message(F.text == '🔗 Изменить соц. сеть')
async def change_social(message: Message, state: FSMContext):
    await state.set_state(ProfileStates.waiting_for_social)
    await message.answer(
        "Введите ссылку на вашу страницу в социальной сети (ВКонтакте, Одноклассники и т.д.):",
        reply_markup=cancel_keyboard
    )

@router.message(ProfileStates.waiting_for_social)
async def process_social(message: Message, state: FSMContext):
    if message.text == '🔙 Отмена':
        await state.clear()
        await profile(message)
        return

    db.update_user(message.from_user.id, social_link=message.text)
    await state.clear()
    await message.answer("Ссылка на социальную сеть успешно обновлена!")
    await profile(message)

@router.message(F.text == '❌ Удалить аккаунт')
async def delete_account(message: Message):
    await message.answer(
        "⚠️ Вы уверены, что хотите удалить свой аккаунт? Это действие нельзя отменить.",
        reply_markup=confirm_delete_keyboard
    )

@router.callback_query(F.data == 'confirm_delete')
async def confirm_delete_account(callback: CallbackQuery):
    db.delete_user(callback.from_user.id)
    
    # Проверяем, является ли пользователь админом
    if callback.from_user.id == settings.bots.admin_id:
        await callback.message.answer(
            "Ваш аккаунт был удален. Используйте /start для создания нового аккаунта администратора."
        )
    else:
        await callback.message.answer(
            "Ваш аккаунт был успешно удален.\n"
            "Чтобы начать работу заново, используйте команду /start для новой регистрации."
        )

@router.callback_query(F.data == 'cancel_delete')
async def cancel_delete_account(callback: CallbackQuery):
    await callback.message.delete()
    temp_message = await callback.message.answer("Отмена удаления аккаунта")
    await profile(temp_message, callback.from_user.id)

@router.message(F.text == '🔙 Назад в меню')
async def back_to_menu(message: Message):
    user = db.get_user(message.from_user.id)
    if not user:
        # Если пользователь не найден, проверяем является ли он админом
        role_id = 2 if message.from_user.id == settings.bots.admin_id else 1
        db.create_user(message.from_user.id, message.from_user.username)
        keyboard = admin_keyboard if role_id == 2 else main_keyboard
    else:
        keyboard = admin_keyboard if user['role'] == 'admin' else main_keyboard
    await message.answer("Главное меню", reply_markup=keyboard)

# ... остальные обработчики профиля ... 