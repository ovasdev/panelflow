"""
TUI-виджет выбора из списка опций.
"""

from typing import Any, Optional
from textual.widgets import Label, OptionList
from textual.containers import Vertical
from textual.binding import Binding

from panelflow.core.components import AbstractOptionSelect
from panelflow.core.state import TreeNode

from .base import BaseWidgetMixin, FocusableWidgetCSS


class TuiOptionSelect(BaseWidgetMixin, FocusableWidgetCSS, Vertical):
    """
    TUI-реализация AbstractOptionSelect на базе Textual OptionList.
    Включает заголовок и список опций для выбора.
    """

    DEFAULT_CSS = FocusableWidgetCSS.DEFAULT_CSS + """
    TuiOptionSelect {
        height: auto;
        max-height: 15;
        margin: 1 0;
    }
    
    TuiOptionSelect .select-label {
        color: $text;
        margin-bottom: 1;
        text-style: bold;
    }
    
    TuiOptionSelect OptionList {
        width: 100%;
        height: auto;
        max-height: 10;
        border: solid $primary;
    }
    
    TuiOptionSelect OptionList:focus {
        border: solid $accent;
    }
    
    TuiOptionSelect.focused .select-label {
        color: $accent;
    }
    
    TuiOptionSelect.focused OptionList {
        border: solid $accent;
    }
    """

    BINDINGS = [
        Binding("enter", "select_option", "Выбрать"),
        Binding("up", "option_up", "Опция вверх", show=False),
        Binding("down", "option_down", "Опция вниз", show=False),
    ]

    def __init__(
        self,
        abstract_widget: AbstractOptionSelect,
        node: TreeNode,
        post_event_callback
    ):
        # Инициализация контейнера
        Vertical.__init__(self, id=abstract_widget.id)

        # Инициализация миксина
        BaseWidgetMixin.__init__(self, abstract_widget, node, post_event_callback)

        # Создаем компоненты
        self.label = Label(abstract_widget.title, classes="select-label")
        self.option_list = OptionList(*abstract_widget.options)

        # Устанавливаем выбранное значение если есть
        if abstract_widget.value and abstract_widget.value in abstract_widget.options:
            try:
                index = abstract_widget.options.index(abstract_widget.value)
                self.option_list.highlighted = index
            except (ValueError, IndexError):
                pass

    def compose(self):
        """Создание структуры виджета."""
        yield self.label
        yield self.option_list

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """
        Обработчик выбора опции из списка.
        """
        event.stop()
        if event.option and hasattr(event.option, 'prompt'):
            selected_value = str(event.option.prompt)
            self._submit_value(selected_value)

    def action_select_option(self) -> None:
        """Действие для клавиши Enter - выбрать текущую опцию."""
        if self.option_list.highlighted is not None:
            highlighted_option = self.option_list.get_option_at_index(self.option_list.highlighted)
            if highlighted_option and hasattr(highlighted_option, 'prompt'):
                selected_value = str(highlighted_option.prompt)
                self._submit_value(selected_value)

    def action_option_up(self) -> None:
        """Действие для стрелки вверх."""
        if hasattr(self.option_list, 'action_cursor_up'):
            self.option_list.action_cursor_up()

    def action_option_down(self) -> None:
        """Действие для стрелки вниз."""
        if hasattr(self.option_list, 'action_cursor_down'):
            self.option_list.action_cursor_down()

    def _set_initial_value(self, value: Any) -> None:
        """Установка начально выбранной опции."""
        if hasattr(self, 'option_list') and hasattr(self.abstract_widget, 'options'):
            try:
                if value in self.abstract_widget.options:
                    index = self.abstract_widget.options.index(value)
                    self.option_list.highlighted = index
            except (ValueError, IndexError, AttributeError):
                pass

    def get_current_value(self) -> Optional[str]:
        """Получение текущей выбранной опции."""
        if hasattr(self, 'option_list') and self.option_list.highlighted is not None:
            highlighted_option = self.option_list.get_option_at_index(self.option_list.highlighted)
            if highlighted_option and hasattr(highlighted_option, 'prompt'):
                return str(highlighted_option.prompt)
        return None

    def set_focus(self, focus: bool) -> None:
        """Установка фокуса на список опций."""
        super().set_focus(focus)

        if focus and hasattr(self, 'option_list'):
            self.option_list.focus()