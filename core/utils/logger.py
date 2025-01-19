import logging
from typing import Optional
from datetime import datetime
import json
from pathlib import Path

class BotLogger:
    def __init__(self, log_file: str = "bot_actions.log", config_file: str = "logging_config.json"):
        self.log_file = log_file
        self.config_file = config_file
        self.disabled_users = self._load_disabled_users()
        
        # Настройка логгера
        self.logger = logging.getLogger('bot_logger')
        self.logger.setLevel(logging.INFO)
        
        # Хендлер для файла
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        
        # Форматтер
        formatter = logging.Formatter(
            '%(asctime)s - User ID: %(user_id)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        
        self.logger.addHandler(fh)

    def _load_disabled_users(self) -> set:
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
                return set(config.get('disabled_users', []))
        except FileNotFoundError:
            Path(self.config_file).write_text('{"disabled_users": []}')
            return set()

    def _save_disabled_users(self):
        with open(self.config_file, 'w') as f:
            json.dump({'disabled_users': list(self.disabled_users)}, f)

    def disable_logging(self, user_id: int):
        """Отключает логирование для конкретного пользователя"""
        self.disabled_users.add(user_id)
        self._save_disabled_users()

    def enable_logging(self, user_id: int):
        """Включает логирование для конкретного пользователя"""
        self.disabled_users.discard(user_id)
        self._save_disabled_users()

    def log_action(self, user_id: int, action: str, extra_info: Optional[dict] = None):
        """Логирует действие пользователя"""
        if user_id not in self.disabled_users:
            extra = {'user_id': user_id}
            if extra_info:
                action = f"{action} - {json.dumps(extra_info, ensure_ascii=False)}"
            self.logger.info(action, extra=extra)

# Создаем глобальный экземпляр логгера
bot_logger = BotLogger() 