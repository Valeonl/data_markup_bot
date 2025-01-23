import pandas as pd
from datetime import datetime
import os

def export_commands_to_csv(data: list) -> str:
    """
    Создает CSV файл с данными о командах
    
    Args:
        data: список словарей с данными
        
    Returns:
        str: путь к созданному файлу
    """
    # Создаем директорию для экспорта если её нет
    os.makedirs('exports', exist_ok=True)
    
    # Создаем DataFrame
    df = pd.DataFrame(data)
    
    # Генерируем имя файла с текущей датой
    filename = f'exports/commands_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    # Сохраняем в CSV
    df.to_csv(filename, index=False, encoding='utf-8-sig')
    
    return filename 