"""
Система событий для взаимодействия между Слоем Ядра и Слоем Рендеринга.
Определяет все типы событий, используемые в PanelFlow.
"""

from abc import ABC
from dataclasses import dataclass
from typing import Any, Literal


@dataclass
class BaseEvent(ABC):
    """Базовый класс для всех событий в системе."""
    pass


# Входящие события (Renderer → Core)

@dataclass
class WidgetSubmittedEvent(BaseEvent):
    """
    Событие подтверждения ввода или выбора значения в виджете.
    Триггеры: Enter в TextInput, выбор в OptionSelect, клик на Button/PanelLink.
    """
    widget_id: str
    value: Any


@dataclass
class HorizontalNavigationEvent(BaseEvent):
    """
    Событие навигации между колонками.
    Триггеры: Ctrl + → (next), Ctrl + ← (previous).
    """
    direction: Literal["next", "previous"]


@dataclass
class VerticalNavigationEvent(BaseEvent):
    """
    Событие навигации по стеку панелей внутри колонки.
    Триггеры: Ctrl + ↑ (up), Ctrl + ↓ (down).
    """
    direction: Literal["up", "down"]


@dataclass
class BackNavigationEvent(BaseEvent):
    """
    Событие возврата назад (закрытие текущей панели).
    Триггеры: ← (стрелка влево) или Backspace.
    """
    pass


# Исходящие события (Core → Renderer)

@dataclass
class StateChangedEvent(BaseEvent):
    """
    Событие изменения состояния дерева.
    Сообщает Рендереру о необходимости перерисовки интерфейса.
    """
    tree_root: 'TreeNode'


@dataclass
class ErrorOccurredEvent(BaseEvent):
    """
    Событие возникновения внутренней ошибки.
    Сообщает Рендереру о необходимости отображения экрана ошибки.
    """
    title: str
    message: str

