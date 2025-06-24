"""
Базовые классы и миксины для TUI-виджетов.
"""

from typing import Any, Callable
from textual.widget import Widget

from panelflow.core.components import AbstractWidget
from panelflow.core.state import TreeNode


class BaseWidgetMixin:
    """
    Базовый миксин для всех TUI-виджетов PanelFlow.
    Предоставляет общую функциональность.
    """

    def __init__(
        self,
        abstract_widget: AbstractWidget,
        node: TreeNode,
        post_event_callback: Callable[[str, Any], None]
    ):
        self.abstract_widget = abstract_widget
        self.node = node
        self.post_event = post_event_callback
        self._has_focus = False

        # Инициализируем виджет с ID и начальным значением
        super().__init__(id=abstract_widget.id)

        # Устанавливаем начальное значение если есть
        if hasattr(abstract_widget, 'value') and abstract_widget.value is not None:
            self._set_initial_value(abstract_widget.value)

    def _set_initial_value(self, value: Any) -> None:
        """
        Устанавливает начальное значение виджета.
        Должна быть переопределена в наследниках.
        """
        pass

    def set_focus(self, focus: bool) -> None:
        """Установка фокуса на виджет."""
        self._has_focus = focus
        self._update_focus_styling()

        if focus and hasattr(self, 'focus'):
            self.focus()

    def _update_focus_styling(self) -> None:
        """
        Обновление стилей виджета в зависимости от фокуса.
        Может быть переопределена в наследниках.
        """
        if self._has_focus:
            self.add_class("focused")
        else:
            self.remove_class("focused")

    def _submit_value(self, value: Any) -> None:
        """Отправка значения виджета в ядро."""
        self.post_event(self.abstract_widget.id, value)

    def get_current_value(self) -> Any:
        """
        Получение текущего значения виджета.
        Должна быть переопределена в наследниках.
        """
        return self.abstract_widget.value


class FocusableWidgetCSS:
    """
    Общие CSS-стили для фокусируемых виджетов.
    """

    DEFAULT_CSS = """
    .focused {
        border: solid $accent;
        background: $surface-lighten-1;
    }
    
    Widget {
        margin: 1 0;
        padding: 0 1;
    }
    
    Widget.focused {
        background: $primary-lighten-3;
    }
    """