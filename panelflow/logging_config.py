"""
Конфигурация системы логирования для PanelFlow.
Настраивает единое логирование для всех компонентов проекта.
"""

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    log_level: str = "DEBUG",
    log_file: Optional[str] = None,
    console_output: bool = False
) -> logging.Logger:
    """
    Настройка системы логирования для PanelFlow.

    Args:
        log_level: Уровень логирования (DEBUG, INFO, WARNING, ERROR)
        log_file: Путь к файлу логов (по умолчанию panelflow.log)
        console_output: Выводить ли логи также в консоль

    Returns:
        Корневой логгер для PanelFlow
    """
    # Определяем путь к файлу логов
    if log_file is None:
        log_file = Path.cwd() / "panelflow.log"
    else:
        log_file = Path(log_file)

    # Создаем директорию для логов если не существует
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Конфигурируем корневой логгер
    logger = logging.getLogger("panelflow")
    logger.setLevel(getattr(logging, log_level.upper()))

    # Очищаем существующие обработчики
    logger.handlers.clear()

    # Создаем форматтер
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-20s | %(message)s",
        datefmt="%H:%M:%S"
    )

    # Файловый обработчик (перезаписывает файл при каждом запуске)
    file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # Консольный обработчик (опционально)
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper()))
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # Предотвращаем дублирование в родительских логгерах
    logger.propagate = False

    # Логируем старт системы логирования
    logger.info("=" * 60)
    logger.info("PanelFlow Application Started")
    logger.info(f"Log level: {log_level.upper()}")
    logger.info(f"Log file: {log_file}")
    logger.info("=" * 60)

    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Получение логгера для конкретного модуля.

    Args:
        name: Имя модуля (обычно __name__)

    Returns:
        Логгер для указанного модуля
    """
    return logging.getLogger(f"panelflow.{name}")


# Удобные функции для инициализации логирования
def init_core_logging() -> logging.Logger:
    """Инициализация логирования для ядра."""
    return setup_logging(log_level="DEBUG", console_output=False)


def init_tui_logging() -> logging.Logger:
    """Инициализация логирования для TUI (только в файл)."""
    return setup_logging(log_level="DEBUG", console_output=False)


def init_debug_logging() -> logging.Logger:
    """Инициализация отладочного логирования (БЕЗ вывода в консоль для TUI)."""
    return setup_logging(log_level="DEBUG", console_output=False)


def init_console_logging() -> logging.Logger:
    """Инициализация логирования с выводом в консоль (только для CLI утилит)."""
    return setup_logging(log_level="DEBUG", console_output=True)