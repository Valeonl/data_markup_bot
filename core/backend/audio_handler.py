import os

import requests
import soundfile as sf
from aiogram import Bot
from aiogram.types import Message
from core.config.settings import settings
from core.config.settings import Emoji
import speech_recognition as sr
import json
import re


async def save_voice_to_file(bot: Bot, message: Message, file_path: str) -> str:
    """Скачивает голосовое сообщение и сохраняет в указанный путь"""
    voice = message.voice
    voice_file_info = await bot.get_file(voice.file_id)
    await bot.download_file(voice_file_info.file_path, file_path)
    return file_path


async def voice_to_text_whisper(file_path: str) -> str:
    """Принимает путь к аудио файлу, возвращает транскрибированный текст файла."""
    if not settings.bots.whisper:
        raise ValueError("Whisper model is not initialized")
        
    segments, _ = settings.bots.whisper.transcribe(file_path, language="ru", beam_size=5)
    segments = list(segments)  # The transcription will actually run here.
    result = []
    for segment in segments:
        result.append(segment.text)

    return ' '.join(result)


async def voice_to_text_google(file_path: str) -> str:
    """Принимает путь к аудио файлу, возвращает транскрибированный текст файла."""
    r = settings.bots.google_model
    voice_file = sr.AudioFile(file_path)
    with voice_file as source:
        audio = r.record(source)
    result = r.recognize_google(audio, language="ru-RU")

    print(result)
    result = result[0].upper() + result[1:]
    sentence = await text_to_sentence(result)
    print(sentence)
    # sentenses = '. '.join(text_to_sentence(result))
    # sentenses[0].upper()
    return result


async def text_to_sentence(text: str) -> [str]:
    return re.findall('[А-Я][^А-Я]*', text)


def get_sentiment_emoji(sentiment):
    """Функция соотнесения предсказанной эмоции с смайликом из словаря"""
    return Emoji.emoji_mapping.get(sentiment, "")


async def markup_text_emotional(text: str) -> str:
    """Функция для распознавания тональности сообщений и маркировки их смайликами"""
