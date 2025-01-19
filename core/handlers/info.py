from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from core.keyboards.main import project_keyboard, author_keyboard
from core.config.settings import settings
import logging

router = Router()

@router.message(F.text == 'ℹ️ Информация о проекте')
async def project_info(message: Message):
    photo_id = "AgACAgIAAxkDAAOWZx_5uCSgtlqgw-wGK7ySD0siGG0AAtPhMRu1awABSf9ysR7lIyeoAQADAgADeAADNgQ"
    await message.answer_photo(
        photo=photo_id,
        caption=(
            "🤖 <b>О проекте</b>\n\n"
            "Чат-бот 'Разметыш' является частью магистерской работы, "
            "посвящённой созданию системы голосового помощника в сфере "
            "видеомонтажа Voice3Frame.\n\n"
            "Используемые технологии:\n"
            "- Whisper для распознавания речи\n"
            "- SQLite для хранения данных\n"
            "- Aiogram 3.x для работы с Telegram API"
        ),
        reply_markup=project_keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data == 'author_info')
async def author_info(callback: CallbackQuery):
    # Получаем фото профиля автора
    author_photos = await callback.bot.get_user_profile_photos(settings.bots.admin_id)
    
    author_text = (
        "👨‍💻 <b>Об авторе</b>\n\n"
        "Разработчик: Валентин Трифонов\n"
        "Telegram: @valeonl\n\n"
        "🎓 Образование:\n"
        "- Магистрант НИУ ИТМО\n"
        "- Бакалавр СПБГУАП\n\n"
        "💼 Текущая деятельность:\n"
        "- Разработка системы Voice3Frame\n"
        "- Исследования в области речевых технологий"
    )

    # Если есть фото профиля, отправляем с фото
    if author_photos and author_photos.total_count > 0:
        photo = author_photos.photos[0][-1]
        await callback.message.answer_photo(
            photo=photo.file_id,
            caption=author_text,
            reply_markup=author_keyboard,
            parse_mode="HTML"
        )
    else:
        await callback.message.answer(
            author_text,
            reply_markup=author_keyboard,
            parse_mode="HTML"
        )
    
    # Удаляем предыдущее сообщение
    await callback.message.delete()

@router.callback_query(F.data == 'project_info')
async def return_to_project_info(callback: CallbackQuery):
    try:
        photo_id = "AgACAgIAAxkDAAOWZx_5uCSgtlqgw-wGK7ySD0siGG0AAtPhMRu1awABSf9ysR7lIyeoAQADAgADeAADNgQ"
        await callback.message.edit_media(
            media=InputMediaPhoto(
                media=photo_id,
                caption=(
                    "🤖 <b>О проекте</b>\n\n"
                    "Чат-бот 'Разметыш' является частью магистерской работы, "
                    "посвящённой созданию системы голосового помощника в сфере "
                    "видеомонтажа Voice3Frame.\n\n"
                    "Используемые технологии:\n"
                    "- Whisper для распознавания речи\n"
                    "- SQLite для хранения данных\n"
                    "- Aiogram 3.x для работы с Telegram API"
                ),
                parse_mode="HTML"
            ),
            reply_markup=project_keyboard
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении информации о проекте: {e}")
        # Пробуем отправить новое сообщение вместо редактирования
        await callback.message.delete()
        await callback.message.answer_photo(
            photo=photo_id,
            caption=(
                "🤖 <b>О проекте</b>\n\n"
                "Чат-бот 'Разметыш' является частью магистерской работы, "
                "посвящённой созданию системы голосового помощника в сфере "
                "видеомонтажа Voice3Frame.\n\n"
                "Используемые технологии:\n"
                "- Whisper для распознавания речи\n"
                "- SQLite для хранения данных\n"
                "- Aiogram 3.x для работы с Telegram API"
            ),
            reply_markup=project_keyboard,
            parse_mode="HTML"
        ) 