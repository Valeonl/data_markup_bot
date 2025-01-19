import os

import requests
import soundfile as sf
from aiogram import Bot
from aiogram.types import Message
from core.settings import settings
from core.settings import Emoji
import speech_recognition as sr
import json
import re


async def save_voice_to_file(bot: Bot, message: Message) -> str:
    """Скачивает голосовое сообщение и сохраняет в формате mp3"""
    voice = message.voice
    forward_date = message.date
    formatted_date = forward_date.strftime("%Y-%m-%d")
    formatted_time = forward_date.strftime("%H-%M-%S")

    voice_file_info = await bot.get_file(voice.file_id)
    file = requests.get('https://api.telegram.org/file/bot{0}/{1}'.format(settings.bots.bot_token, voice_file_info.file_path))
    #print(file.content)
    voice_ogg_path = f"voice_records/{message.from_user.username}-{formatted_date}-{formatted_time}.ogg"
    voice_wav_path = f"voice_records/{message.from_user.username}-{formatted_date}-{formatted_time}.wav"
    with open(voice_ogg_path, 'wb') as f:
        f.write(file.content)
    data, samplerate = sf.read(voice_ogg_path)
    sf.write(voice_wav_path, data, samplerate)
    os.remove(voice_ogg_path)
    return voice_wav_path


async def voice_to_text_whisper(file_path: str) -> str:
    """Принимает путь к аудио файлу, возвращает транскрибированный текст файла."""
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
