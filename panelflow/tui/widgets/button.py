"""
TUI-виджет кнопки.
"""

import logging
from typing import Any
from textual.widgets import Button
from textual.binding import Binding

from panelflow.core.components import AbstractButton
from panelflow.core.state import TreeNode
from panelflow.logging_config import get_logger

from .base import BaseWidgetMixin, FocusableWidgetCSS

# Инициализируем логгер для кнопок
logger = get_logger(__name__)


class TuiButton(BaseWidgetMixin, FocusableWidgetCSS, Button):
    """
    TUI-реализация AbstractButton на базе Textual Button.
    """

    DEFAULT_CSS = FocusableWidgetCSS.DEFAULT_CSS + """
    TuiButton {
        width: 100%;
        height: 3;
        margin: 1 0;
    }
    
    TuiButton.focused {
        background: $accent;
        color: $text-accent;
        border: solid $accent-lighten-1;
    }
    
    TuiButton:hover {
        background: $primary-lighten-1;
    }
    """

    BINDINGS = [
        Binding("enter,space", "press", "Активировать"),
    ]

    def __init__(
        self,
        abstract_widget: AbstractButton,
        node: TreeNode,
        post_event_callback
    ):
        logger.debug(f"Создание TuiButton: '{abstract_widget.title}' (id: {abstract_widget.id})")

        # Инициализация Button с заголовком
        Button.__init__(
            self,
            label=abstract_widget.title,
            id=abstract_widget.id
        )

        # Инициализация миксина
        BaseWidgetMixin.__init__(self, abstract_widget, node, post_event_callback)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Обработчик нажатия кнопки.
        Преобразует событие Textual в событие panelflow.core.
        """
        logger.info(f"Кнопка '{self.abstract_widget.id}' нажата мышью")
        event.stop()
        self._submit_value(self.abstract_widget.value)

    def action_press(self) -> None:
        """Действие для клавиш Enter/Space."""
        logger.info(f"Кнопка '{self.abstract_widget.id}' активирована клавишей")
        self._submit_value(self.abstract_widget.value)

    def _set_initial_value(self, value: Any) -> None:
        """Кнопка не имеет редактируемого значения."""
        pass

    def get_current_value(self) -> Any:
        """Возвращает значение кнопки (обычно None или фиксированное значение)."""
        return self.abstract_widget.value

    def _update_focus_styling(self) -> None:
        """Обновление стилей при изменении фокуса."""
        super()._update_focus_styling()

        # Дополнительно выделяем кнопку когда она в фокусе
        if self._has_focus:
            self.variant = "primary"
        else:
            self.variant = "default"