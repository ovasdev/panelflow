"""
TUI-виджет ссылки на панель.
"""

from typing import Any
from textual.widgets import Label
from textual.containers import Vertical
from textual.binding import Binding

from panelflow.core.components import PanelLink
from panelflow.core.state import TreeNode

from .base import BaseWidgetMixin, FocusableWidgetCSS


class TuiPanelLink(BaseWidgetMixin, FocusableWidgetCSS, Vertical):
    """
    TUI-реализация PanelLink.
    Отображается как кликабельная ссылка с заголовком и описанием.
    """

    DEFAULT_CSS = FocusableWidgetCSS.DEFAULT_CSS + """
    TuiPanelLink {
        height: auto;
        margin: 1 0;
        padding: 1;
        border: solid $primary-darken-1;
        background: $surface;
    }
    
    TuiPanelLink:hover {
        background: $primary-lighten-3;
        border: solid $primary;
    }
    
    TuiPanelLink.focused {
        background: $accent-lighten-3;
        border: solid $accent;
    }
    
    TuiPanelLink .link-title {
        color: $primary;
        text-style: bold;
        margin-bottom: 1;
    }
    
    TuiPanelLink .link-description {
        color: $text-muted;
        text-style: italic;
    }
    
    TuiPanelLink .link-arrow {
        color: $accent;
        text-align: right;
    }
    
    TuiPanelLink.focused .link-title {
        color: $accent;
        text-style: bold underline;
    }
    
    TuiPanelLink.focused .link-arrow {
        color: $text-accent;
    }
    """

    BINDINGS = [
        Binding("enter,space", "activate_link", "Открыть"),
    ]

    def __init__(
        self,
        abstract_widget: PanelLink,
        node: TreeNode,
        post_event_callback
    ):
        # Инициализация контейнера
        Vertical.__init__(self, id=abstract_widget.id)

        # Инициализация миксина
        BaseWidgetMixin.__init__(self, abstract_widget, node, post_event_callback)

        # Создаем компоненты
        self.title_label = Label(abstract_widget.title, classes="link-title")
        self.description_label = None
        self.arrow_label = Label("→", classes="link-arrow")

        # Добавляем описание если есть
        if abstract_widget.description:
            self.description_label = Label(abstract_widget.description, classes="link-description")

    def compose(self):
        """Создание структуры виджета."""
        yield self.title_label

        if self.description_label:
            yield self.description_label

        yield self.arrow_label

    def on_click(self, event) -> None:
        """Обработчик клика мышью."""
        event.stop()
        self._activate_link()

    def action_activate_link(self) -> None:
        """Действие для клавиш Enter/Space - активировать ссылку."""
        self._activate_link()

    def _activate_link(self) -> None:
        """Активация ссылки - отправка события в ядро."""
        # Для PanelLink значением является target_panel_id
        target_panel_id = self.abstract_widget.target_panel_id
        self._submit_value(target_panel_id)

    def _set_initial_value(self, value: Any) -> None:
        """PanelLink не имеет редактируемого значения."""
        pass

    def get_current_value(self) -> str:
        """Возвращает целевую панель."""
        return self.abstract_widget.target_panel_id

    def _update_focus_styling(self) -> None:
        """Обновление стилей при изменении фокуса."""
        super()._update_focus_styling()

        # Дополнительные стили уже определены в CSS через .focused класс
        if self._has_focus:
            # Можно добавить дополнительную логику при необходимости
            pass

    def on_key(self, event) -> None:
        """Обработка клавиш."""
        if event.key in ("enter", "space") and self._has_focus:
            self._activate_link()
            event.stop()