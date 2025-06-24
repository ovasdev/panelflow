"""
Компоненты UI: абстрактные классы для описания структуры интерфейса.
Эти классы представляют шаблоны виджетов и панелей.
"""

from abc import ABC
from dataclasses import dataclass, field
from typing import Any


@dataclass
class AbstractWidget(ABC):
    """Базовый класс для всех виджетов."""
    id: str
    type: str = field(init=False)
    title: str
    value: Any = None
    handler_class_name: str | None = None


@dataclass
class AbstractTextInput(AbstractWidget):
    """Виджет текстового ввода."""
    placeholder: str = ""
    type: str = field(default="text_input", init=False)


@dataclass
class AbstractButton(AbstractWidget):
    """Виджет кнопки."""
    type: str = field(default="button", init=False)


@dataclass
class AbstractOptionSelect(AbstractWidget):
    """Виджет выбора из списка опций."""
    options: list = field(default_factory=list)
    type: str = field(default="option_select", init=False)


@dataclass
class PanelLink(AbstractWidget):
    """Виджет ссылки на другую панель."""
    target_panel_id: str = ""
    description: str = ""
    type: str = field(default="panel_link", init=False)


@dataclass
class AbstractPanel:
    """Класс для описания панели (шаблона экрана)."""
    id: str
    title: str
    description: str = ""
    widgets: list[AbstractWidget] = field(default_factory=list)
    handler_class_name: str | None = None
