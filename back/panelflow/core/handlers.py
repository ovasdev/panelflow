"""
Базовые классы для пользовательских обработчиков бизнес-логики.
Предоставляет интерфейс для реализации пользовательской логики.
"""

from abc import ABC, abstractmethod
from typing import Any


class BasePanelHandler(ABC):
    """
    Базовый класс для обработчиков панелей.
    Пользователи должны наследовать этот класс и реализовать on_widget_update.
    """

    def __init__(self, context: dict, form_data: dict):
        """
        Инициализация обработчика.

        Args:
            context: Контекст, переданный от родительской панели
            form_data: Текущие данные формы панели
        """
        self.context = context
        self.form_data = form_data

    @abstractmethod
    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        """
        Обработка обновления виджета.

        Args:
            widget_id: ID виджета, который был обновлен
            value: Новое значение виджета

        Returns:
            Команда навигации в формате:
            - ("navigate_down", "panel_id") для навигации по ID панели
            - ("navigate_down", AbstractPanel(...)) для навигации по объекту панели
            - None, если навигация не требуется
        """
        pass

