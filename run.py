import sys
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import os
import fnmatch

# Настройка логирования
logging.basicConfig(level=logging.INFO,
                   format='%(asctime)s - %(message)s',
                   datefmt='%Y-%m-%d %H:%M:%S')

class BotReloader(FileSystemEventHandler):
    def __init__(self):
        self.process = None
        self.ignored_patterns = self.get_ignored_patterns()
        self.start_bot()

    def get_ignored_patterns(self):
        """Читаем паттерны из .gitignore"""
        patterns = ['venv/*', '*.pyc', '__pycache__/*', '*.log', '.git/*']  # Стандартные паттерны
        try:
            with open('.gitignore', 'r') as f:
                # Добавляем паттерны из .gitignore, пропуская пустые строки и комментарии
                patterns.extend(line.strip() for line in f if line.strip() and not line.startswith('#'))
        except FileNotFoundError:
            logging.warning('.gitignore не найден, используются стандартные паттерны')
        return patterns

    def should_ignore(self, path):
        """Проверяем, нужно ли игнорировать файл"""
        # Преобразуем путь в относительный
        rel_path = os.path.relpath(path)
        
        # Проверяем каждый паттерн
        for pattern in self.ignored_patterns:
            if fnmatch.fnmatch(rel_path, pattern):
                return True
            # Проверяем также директории
            if fnmatch.fnmatch(os.path.dirname(rel_path), pattern):
                return True
        return False

    def start_bot(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
        logging.info('Запуск бота...')
        self.process = subprocess.Popen([sys.executable, 'bot.py'])

    def on_modified(self, event):
        if event.src_path.endswith('.py') and not self.should_ignore(event.src_path):
            logging.info(f'Обнаружено изменение в файле: {event.src_path}')
            self.start_bot()

if __name__ == "__main__":
    path = '.'  # Текущая директория
    event_handler = BotReloader()
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        if event_handler.process:
            event_handler.process.terminate()
    observer.join() 