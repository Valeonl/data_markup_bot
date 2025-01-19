from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from core.database.database import Database
from core.keyboards.profile import cancel_registration_keyboard
from core.keyboards.main import main_keyboard
from core.states.states import RegistrationStates

router = Router()
db = Database('bot_database.db')

@router.message(RegistrationStates.waiting_for_name)
async def process_reg_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer(
        "Спасибо! Теперь укажите вашу организацию (учебное заведение или место работы):"
    )
    await state.set_state(RegistrationStates.waiting_for_organization)

@router.message(RegistrationStates.waiting_for_organization)
async def process_reg_organization(message: Message, state: FSMContext):
    await state.update_data(organization=message.text)
    
    # Создаем клавиатуру с кнопкой "Указать позже"
    later_keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Указать позже')]
    ], resize_keyboard=True)
    
    await message.answer(
        "Отлично! Последний шаг - вы можете указать ссылку на вашу страницу в социальной сети "
        "(ВКонтакте или другой). Если хотите добавить её позже, нажмите кнопку 'Указать позже':",
        reply_markup=later_keyboard
    )
    await state.set_state(RegistrationStates.waiting_for_social)

@router.message(RegistrationStates.waiting_for_social)
async def process_reg_social(message: Message, state: FSMContext):
    user_data = await state.get_data()
    social_link = None if message.text == 'Указать позже' else message.text
    
    # Создаем пользователя в базе данных
    db.create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username
    )
    
    # Обновляем информацию о пользователе
    db.update_user(
        message.from_user.id,
        display_name=user_data['name'],
        organization=user_data['organization'],
        social_link=social_link
    )
    
    await state.clear()
    await message.answer(
        "Регистрация успешно завершена! Теперь вы можете использовать все функции бота.\n"
        "Дополнительную информацию можно изменить в личном кабинете.",
        reply_markup=main_keyboard
    )

@router.message(F.text == 'Отменить регистрацию')
async def cancel_registration(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state and current_state.startswith('RegistrationStates:'):
        await state.clear()
        await message.answer(
            "Регистрация отменена. Вы можете начать заново, использовав команду /start",
            reply_markup=ReplyKeyboardRemove()
        )

# ... остальные обработчики регистрации ... 