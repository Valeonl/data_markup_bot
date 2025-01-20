from typing import Optional
from environs import Env
from dataclasses import dataclass
from vosk import Model
import speech_recognition as sr
from faster_whisper import WhisperModel

@dataclass
class Bots:
    bot_token: str
    admin_id: int
    google_model: Optional[sr.Recognizer] = None
    whisper: Optional[WhisperModel] = None
    vosk_model: Optional[Model] = None

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
            #google_model=sr.Recognizer(),
            #vosk_model=Model("model/vosk-model-small-ru-0.22")
        )
    )

settings = get_settings('.env')