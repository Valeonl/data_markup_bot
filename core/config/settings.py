from typing import Optional
from environs import Env
from dataclasses import dataclass, field
from vosk import Model
import speech_recognition as sr
from faster_whisper import WhisperModel
import subprocess

def get_ffmpeg_path() -> str:
    """Получает путь к ffmpeg при запуске бота"""
    try:
        result = subprocess.run(['where', 'ffmpeg'], 
                              capture_output=True, 
                              text=True, 
                              check=True)
        ffmpeg_path = result.stdout.strip().split('\n')[0]  # Берем первый путь
        print(f"Found ffmpeg at: {ffmpeg_path}")
        return ffmpeg_path
    except Exception as e:
        print(f"Error finding ffmpeg: {e}")
        return 'ffmpeg'  # Возвращаем просто 'ffmpeg' если не удалось найти путь

@dataclass
class Bots:
    bot_token: str
    admin_id: int
    google_model: Optional[sr.Recognizer] = None
    whisper: Optional[WhisperModel] = None
    vosk_model: Optional[Model] = None
    ffmpeg_path: str = r"C:\ProgramData\chocolatey\bin\ffmpeg.exe"  # Фиксированный путь

@dataclass
class Emoji:
    emoji_mapping = {
        "disappointment": "😞",
        "sadness": "😢",
        "annoyance": "😠",
        "neutral": "😐",
        "disapproval": "👎",
        "realization": "😮",
        "nervousness": "😬",
        "approval": "👍",
        "happiness": "😄",
        "anger": "😡",
        "embarrassment": "😳",
        "caring": "🤗",
        "remorse": "😔",
        "disgust": "🤢",
        "grief": "😥",
        "confusion": "😕",
        "relief": "😌",
        "desire": "😍",
        "admiration": "😌",
        "optimism": "😊",
        "fear": "😨",
        "love": "❤️",
        "excitement": "🎉",
        "curiosity": "🤔",
        "amusement": "😄",
        "surprise": "😲",
        "gratitude": "🙏",
        "pride": "🦁"
    }

@dataclass
class Settings:
    bots: Bots

def get_settings(path: str):
    env = Env()
    env.read_env(path)

    return Settings(
        bots=Bots(
            bot_token=env.str("BOT_TOKEN"),
            admin_id=1175574901,
            whisper=WhisperModel("small", device="cpu", compute_type="int8"),
            google_model=sr.Recognizer(),
            vosk_model=Model("model/vosk-model-small-ru-0.22")
            # ffmpeg_path будет использовать значение по умолчанию
        )
    )

settings = get_settings('.env')