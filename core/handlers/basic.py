import os

from aiogram import Bot
from aiogram.types import Message
from core.backend.audio_handler import save_voice_to_file, voice_to_text_google, text_to_sentence,voice_to_text_whisper


async def get_start(message: Message, bot: Bot):
    """Функция при отправке боту сообщения /start"""
    await bot.send_message(message.from_user.id, f"<b>Привет, {message.from_user.first_name}!</b>")
    await message.answer(f"Привет, {message.from_user.username}!")
    await message.reply(f"Привет, {message.from_user.first_name}!")


async def get_voice(message: Message, bot:Bot):
    """Функция для получения голосовых сообщений пользователя"""
    await message.answer("Вы прислали аудиофайл!")
    voice_path = await save_voice_to_file(bot, message)
    #transcript_voice_text_with_google = await voice_to_text_google(voice_path)
    transcript_voice_text_with_whisper = await voice_to_text_whisper(voice_path)
    transcript_voice_text = (f"<b>Расшифровка от Whisper:</b> {transcript_voice_text_with_whisper}")
    #transcript_voice_text = (f"<b>Google:</b> {transcript_voice_text_with_google}\n\n"
    #                         f"<b>Whisper:</b> {transcript_voice_text_with_whisper}")
    forward_date = message.date
    formatted_date = forward_date.strftime("%Y-%m-%d")
    formatted_time = forward_date.strftime("%H:%M:%S")
    os.remove(voice_path)

    if transcript_voice_text:
        #text_sentence = await text_to_sentence(transcript_voice_text)
        text_sentence = "\n".join(transcript_voice_text)
        await message.reply(text=transcript_voice_text)
        print(f"{formatted_date} {formatted_time} | Получено аудиосообщение от {message.from_user.username}:\nТекст сообщения: '{transcript_voice_text}'")