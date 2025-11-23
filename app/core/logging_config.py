"""Logging configuration."""

import logging
import sys
from pathlib import Path

from app.core.config import settings


def setup_logging():
    """
    Настройка логирования для приложения.

    Логи выводятся в консоль и опционально в файл.
    """
    # Создаем директорию для логов
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Определяем уровень логирования
    log_level = logging.DEBUG if settings.DEBUG else logging.INFO

    # Формат логов
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"

    # Настраиваем root logger
    logging.basicConfig(
        level=log_level,
        format=log_format,
        datefmt=date_format,
        handlers=[
            # Console handler
            logging.StreamHandler(sys.stdout),
            # File handler
            logging.FileHandler(log_dir / "app.log", encoding="utf-8"),
        ],
    )

    # Настраиваем логгеры сторонних библиотек
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.pool").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.dialects").setLevel(logging.WARNING)
    logging.getLogger("python_multipart.multipart").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured. Level: {logging.getLevelName(log_level)}")


def get_logger(name: str) -> logging.Logger:
    """
    Получить logger для модуля.

    Args:
        name: Имя модуля (обычно __name__)

    Returns:
        logging.Logger: Настроенный logger
    """
    return logging.getLogger(name)
