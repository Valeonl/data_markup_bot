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
from vosk import KaldiRecognizer
import wave
import subprocess
from pydub import AudioSegment
import asyncio

# Указываем путь к ffmpeg для pydub
AudioSegment.converter = r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"

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
    """Распознавание речи через Google Speech Recognition"""
    try:
        wav_path = file_path.replace('.ogg', '.wav')
        
        # Проверяем успешность конвертации
        if not convert_to_wav(file_path, wav_path):
            print("Failed to convert audio for Google recognition")
            return ""
        
        # Распознаем текст
        recognizer = settings.bots.google_model
        with sr.AudioFile(wav_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language='ru-RU')
        
        return text
    except Exception as e:
        print(f"Google recognition error: {e}")
        return ""


async def voice_to_text_vosk(file_path: str) -> str:
    """Распознавание речи через Vosk"""
    try:
        wav_path = file_path.replace('.ogg', '.wav')
        
        # Проверяем успешность конвертации
        if not convert_to_wav(file_path, wav_path):
            print("Failed to convert audio for Vosk recognition")
            return ""
        
        # Открываем аудиофайл
        wf = wave.open(wav_path, "rb")
        
        # Создаем распознаватель
        model = settings.bots.vosk_model
        rec = KaldiRecognizer(model, wf.getframerate())
        rec.SetWords(True)
        
        # Читаем и распознаем аудио
        result = ""
        while True:
            data = wf.readframes(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                result += json.loads(rec.Result())["text"] + " "
        
        # Получаем последний фрагмент
        final_result = json.loads(rec.FinalResult())
        result += final_result["text"]
        
        return result.strip()
    except Exception as e:
        print(f"Vosk recognition error: {e}")
        return ""


def convert_to_wav(input_path: str, output_path: str, sample_rate: int = 16000) -> bool:
    """
    Конвертация ogg в wav через pydub
    """
    try:
        if not os.path.exists(input_path):
            print(f"Input file not found: {input_path}")
            print(f"Current working directory: {os.getcwd()}")
            print(f"Absolute path to input file: {os.path.abspath(input_path)}")
            return False
            
        print(f"Converting {input_path} to {output_path}")
        print(f"File exists: {os.path.exists(input_path)}")
        print(f"File size: {os.path.getsize(input_path)} bytes")
        
        # Загружаем OGG файл
        audio = AudioSegment.from_ogg(input_path)
        
        # Устанавливаем нужные параметры
        audio = audio.set_frame_rate(sample_rate).set_channels(1)
        
        # Сохраняем в WAV
        audio.export(output_path, format="wav")
        
        if os.path.exists(output_path):
            print(f"Successfully converted {input_path} to {output_path}")
            print(f"Output file size: {os.path.getsize(output_path)} bytes")
            return True
        return False
        
    except Exception as e:
        print(f"Conversion error: {e}")
        print(f"Error type: {type(e)}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False


async def text_to_sentence(text: str) -> [str]:
    return re.findall('[А-Я][^А-Я]*', text)


def get_sentiment_emoji(sentiment):
    """Функция соотнесения предсказанной эмоции с смайликом из словаря"""
    return Emoji.emoji_mapping.get(sentiment, "")


async def markup_text_emotional(text: str) -> str:
    """Функция для распознавания тональности сообщений и маркировки их смайликами"""


async def convert_to_wav_pydub(input_path: str, output_path: str) -> bool:
    """Конвертация ogg в wav через pydub"""
    try:
        audio = AudioSegment.from_ogg(input_path)
        audio = audio.set_frame_rate(16000).set_channels(1)
        audio.export(output_path, format="wav")
        return True
    except Exception as e:
        print(f"Pydub conversion error: {e}")
        return False


async def process_voice_recognition(temp_file: str):
    """Асинхронная обработка голосового сообщения всеми системами распознавания"""
    results = []
    
    # Конвертируем в wav для других систем
    wav_file = temp_file.replace('.ogg', '.wav')
    
    # Используем ffmpeg напрямую вместо pydub
    try:
        process = subprocess.Popen([
            'ffmpeg',
            '-loglevel', 'quiet',
            '-i', temp_file,
            '-ar', '16000',
            '-ac', '1',
            '-f', 'wav',
            wav_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        stdout, stderr = process.communicate()
        conversion_success = process.returncode == 0 and os.path.exists(wav_file)
        
        if not conversion_success:
            print(f"FFmpeg conversion failed: {stderr.decode() if stderr else 'No error output'}")
    except Exception as e:
        print(f"Conversion error: {e}")
        conversion_success = False
    
    if conversion_success:
        # Запускаем системы распознавания параллельно
        tasks = [
            voice_to_text_google(wav_file),
            voice_to_text_vosk(wav_file)
        ]
        other_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Добавляем результаты
        for result, system in zip(other_results, ["🎯 Google Speech", "📝 Vosk"]):
            if isinstance(result, Exception):
                results.append((system, f"Ошибка: {str(result)}"))
            else:
                results.append((system, result))
    else:
        results.extend([
            ("🎯 Google Speech", "Ошибка конвертации аудио"),
            ("📝 Vosk", "Ошибка конвертации аудио")
        ])
    
    return results
