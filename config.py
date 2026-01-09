"""
Конфигурация приложения.
Загружает настройки из переменных окружения.
"""
import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Определяем путь к .env файлу (в директории проекта)
env_path = Path(__file__).parent / '.env'
env_local_path = Path(__file__).parent / '.env.local'

# Загружаем переменные окружения: сначала .env, потом .env.local (если существует)
# .env.local имеет приоритет и перезаписывает значения из .env
# Используем override=True для обоих, чтобы перезаписать системные переменные окружения
if env_local_path.exists():
    # Если .env.local существует, загружаем его (он имеет приоритет)
    load_dotenv(dotenv_path=env_local_path, override=True)
    # Затем загружаем .env для остальных переменных (если они не заданы в .env.local)
    load_dotenv(dotenv_path=env_path, override=False)
else:
    # Если .env.local не существует, загружаем только .env
    load_dotenv(dotenv_path=env_path, override=True)


class Config:
    """Конфигурация приложения."""
    
    # Telegram Bot
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    
    # Database
    DB_HOST: str = os.getenv("DB_HOST", "localhost")
    DB_PORT: int = int(os.getenv("DB_PORT", "5432"))
    DB_NAME: str = os.getenv("DB_NAME", "debt_bot")
    DB_USER: str = os.getenv("DB_USER", "postgres")
    DB_PASSWORD: str = os.getenv("DB_PASSWORD", "")
    
    # Application
    INVITE_TOKEN_EXPIRY_DAYS: int = int(os.getenv("INVITE_TOKEN_EXPIRY_DAYS", "7"))
    
    @classmethod
    def validate(cls) -> None:
        """Проверяет, что все обязательные настройки заданы."""
        if not cls.BOT_TOKEN:
            raise ValueError("BOT_TOKEN не задан в переменных окружения")
        if not cls.DB_NAME:
            raise ValueError("DB_NAME не задан в переменных окружения")
        if not cls.DB_USER:
            raise ValueError("DB_USER не задан в переменных окружения")


# Создаём экземпляр конфигурации
config = Config()

