"""
TUI-виджет текстового ввода.
"""

from typing import Any
from textual.widgets import Input, Label
from textual.containers import Vertical
from textual.binding import Binding

from panelflow.core.components import AbstractTextInput
from panelflow.core.state import TreeNode

from .base import BaseWidgetMixin, FocusableWidgetCSS


class TuiTextInput(BaseWidgetMixin, FocusableWidgetCSS, Vertical):
    """
    TUI-реализация AbstractTextInput на базе Textual Input.
    Включает заголовок и поле ввода.
    """

    DEFAULT_CSS = FocusableWidgetCSS.DEFAULT_CSS + """
    TuiTextInput {
        height: auto;
        margin: 1 0;
    }
    
    TuiTextInput .input-label {
        color: $text;
        margin-bottom: 1;
        text-style: bold;
    }
    
    TuiTextInput Input {
        width: 100%;
    }
    
    TuiTextInput Input:focus {
        border: solid $accent;
    }
    
    TuiTextInput.focused .input-label {
        color: $accent;
    }
    """

    def __init__(
        self,
        abstract_widget: AbstractTextInput,
        node: TreeNode,
        post_event_callback
    ):
        # Инициализация контейнера
        Vertical.__init__(self, id=abstract_widget.id)

        # Инициализация миксина
        BaseWidgetMixin.__init__(self, abstract_widget, node, post_event_callback)

        # Создаем компоненты
        self.label = Label(abstract_widget.title, classes="input-label")
        self.input_widget = Input(
            placeholder=abstract_widget.placeholder,
            value=str(abstract_widget.value) if abstract_widget.value is not None else ""
        )

    def compose(self):
        """Создание структуры виджета."""
        yield self.label
        yield self.input_widget

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """
        Обработчик подтверждения ввода (Enter).
        """
        event.stop()
        value = event.input.value
        self._submit_value(value)

    def _set_initial_value(self, value: Any) -> None:
        """Установка начального значения в поле ввода."""
        if hasattr(self, 'input_widget'):
            self.input_widget.value = str(value) if value is not None else ""

    def get_current_value(self) -> str:
        """Получение текущего значения из поля ввода."""
        if hasattr(self, 'input_widget'):
            return self.input_widget.value
        return ""

    def set_focus(self, focus: bool) -> None:
        """Установка фокуса на поле ввода."""
        super().set_focus(focus)

        if focus and hasattr(self, 'input_widget'):
            self.input_widget.focus()

    def on_key(self, event) -> None:
        """Перенаправление клавиш в поле ввода."""
        if hasattr(self, 'input_widget') and self._has_focus:
            # Передаем событие клавиши в поле ввода
            if event.key == "enter":
                value = self.input_widget.value
                self._submit_value(value)
                event.stop()