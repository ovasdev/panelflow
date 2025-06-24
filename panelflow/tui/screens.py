"""
Экраны для TUI-приложения.
Содержит MainScreen с колонками и ErrorScreen для отображения ошибок.
"""

from typing import List, Optional, Dict, Type, Any
from textual.screen import Screen
from textual.widgets import Static, Label
from textual.containers import Horizontal, Vertical, Container, ScrollableContainer
from textual.binding import Binding
from textual.widget import Widget

from panelflow.core import Application as CoreApplication
from panelflow.core.events import (
    HorizontalNavigationEvent, VerticalNavigationEvent,
    BackNavigationEvent, WidgetSubmittedEvent
)
from panelflow.core.components import AbstractWidget, AbstractPanel
from panelflow.core.state import TreeNode

from .widgets import create_widget


class PanelWidget(ScrollableContainer):
    """
    Виджет, представляющий одну панель в интерфейсе.
    Содержит заголовок, описание и виджеты.
    """

    DEFAULT_CSS = """
    PanelWidget {
        border: solid $primary-darken-1;
        margin: 0 1;
        padding: 1;
    }

    PanelWidget.active {
        border: solid $accent;
        background: $surface-lighten-1;
    }

    PanelWidget .panel-title {
        text-style: bold;
        color: $text;
        margin-bottom: 1;
    }

    PanelWidget .panel-description {
        color: $text-muted;
        margin-bottom: 1;
    }

    PanelWidget .panel-content {
        height: auto;
    }
    """

    def __init__(self, node: TreeNode, core_app: CoreApplication, is_active: bool = False):
        super().__init__()
        self.node = node
        self.core_app = core_app
        self.is_active = is_active
        self.widget_instances: Dict[str, Widget] = {}
        self.focused_widget_id: Optional[str] = None

        if is_active:
            self.add_class("active")

    def compose(self):
        """Создание содержимого панели."""
        panel = self.node.panel_template

        # Заголовок панели
        if panel.title:
            yield Label(panel.title, classes="panel-title")

        # Описание панели
        if panel.description:
            yield Label(panel.description, classes="panel-description")

        # Контейнер для виджетов
        with Vertical(classes="panel-content"):
            for widget_def in panel.widgets:
                try:
                    widget_instance = create_widget(
                        widget_def,
                        self.node,
                        self._post_widget_event
                    )
                    if widget_instance:
                        self.widget_instances[widget_def.id] = widget_instance
                        yield widget_instance
                except Exception as e:
                    # В случае ошибки создания виджета, показываем заглушку
                    yield Label(f"Ошибка виджета: {widget_def.id}", classes="widget-error")

    def _post_widget_event(self, widget_id: str, value: Any) -> None:
        """Отправка события от виджета в ядро."""
        event = WidgetSubmittedEvent(widget_id=widget_id, value=value)
        self.core_app.post_event(event)

    def set_active(self, active: bool) -> None:
        """Установка статуса активности панели."""
        self.is_active = active
        if active:
            self.add_class("active")
            # Установить фокус на первый виджет если есть
            if self.widget_instances and not self.focused_widget_id:
                first_widget_id = list(self.widget_instances.keys())[0]
                self.set_widget_focus(first_widget_id)
        else:
            self.remove_class("active")
            self.focused_widget_id = None

    def set_widget_focus(self, widget_id: str) -> None:
        """Установка фокуса на конкретный виджет."""
        if widget_id in self.widget_instances:
            # Убираем фокус с предыдущего виджета
            if self.focused_widget_id and self.focused_widget_id in self.widget_instances:
                prev_widget = self.widget_instances[self.focused_widget_id]
                if hasattr(prev_widget, 'set_focus'):
                    prev_widget.set_focus(False)

            # Устанавливаем фокус на новый виджет
            widget = self.widget_instances[widget_id]
            if hasattr(widget, 'set_focus'):
                widget.set_focus(True)

            self.focused_widget_id = widget_id

            # Прокручиваем к виджету если нужно
            widget.scroll_visible()

    def focus_next_widget(self) -> bool:
        """Перевод фокуса на следующий виджет. Возвращает True если переход произошел."""
        if not self.widget_instances:
            return False

        widget_ids = list(self.widget_instances.keys())
        if not self.focused_widget_id:
            self.set_widget_focus(widget_ids[0])
            return True

        try:
            current_index = widget_ids.index(self.focused_widget_id)
            next_index = (current_index + 1) % len(widget_ids)
            self.set_widget_focus(widget_ids[next_index])
            return True
        except ValueError:
            return False

    def focus_prev_widget(self) -> bool:
        """Перевод фокуса на предыдущий виджет. Возвращает True если переход произошел."""
        if not self.widget_instances:
            return False

        widget_ids = list(self.widget_instances.keys())
        if not self.focused_widget_id:
            self.set_widget_focus(widget_ids[-1])
            return True

        try:
            current_index = widget_ids.index(self.focused_widget_id)
            prev_index = (current_index - 1) % len(widget_ids)
            self.set_widget_focus(widget_ids[prev_index])
            return True
        except ValueError:
            return False


class MainScreen(Screen):
    """
    Главный экран приложения.
    Содержит систему колонок и обрабатывает навигацию.
    """

    # Определяем горячие клавиши для Textual
    BINDINGS = [
        Binding("ctrl+c", "app.quit", "Выход"),
        Binding("ctrl+l", "horizontal_nav('next')", "Панель →", show=False),
        Binding("ctrl+h", "horizontal_nav('previous')", "Панель ←", show=False),
        Binding("ctrl+j", "vertical_nav('down')", "Стек ↓", show=False),
        Binding("ctrl+k", "vertical_nav('up')", "Стек ↑", show=False),
        Binding("left,backspace", "back_nav", "Назад", show=False),
        Binding("tab", "widget_nav('next')", "Виджет →", show=False),
        Binding("shift+tab", "widget_nav('previous')", "Виджет ←", show=False),
    ]

    DEFAULT_CSS = """
    MainScreen {
        layout: vertical;
    }

    .header-section {
        dock: top;
        height: 3;
        background: $primary;
        color: $text;
        padding: 1;
    }

    .breadcrumbs {
        text-align: right;
        text-style: bold;
    }

    .hidden-indicator {
        text-align: left;
    }

    .columns-container {
        layout: horizontal;
        height: 1fr;
    }

    .column {
        width: 1fr;
        height: 1fr;
        min-width: 20;
    }

    .empty-column {
        border: dashed $primary-darken-3;
        content-align: center middle;
        color: $text-muted;
    }
    """

    def __init__(self, core_app: CoreApplication):
        super().__init__()
        self.core_app = core_app
        self.visible_path: List[TreeNode] = []
        self.panel_widgets: List[PanelWidget] = []
        self.columns: List[Container] = []
        self.active_panel_index = 0

        # Контейнеры для UI
        self.header_section = None
        self.breadcrumbs_label = None
        self.hidden_indicator_label = None
        self.columns_container = None

    def compose(self):
        """Создание структуры экрана."""
        # Заголовок с индикаторами
        with Container(classes="header-section") as header:
            self.header_section = header
            self.hidden_indicator_label = Label("", classes="hidden-indicator")
            self.breadcrumbs_label = Label("", classes="breadcrumbs")
            yield self.hidden_indicator_label
            yield self.breadcrumbs_label

        # Контейнер для колонок
        with Horizontal(classes="columns-container") as columns_container:
            self.columns_container = columns_container
            # Создаем 3 пустые колонки
            for i in range(3):
                column = Container(classes="column")
                self.columns.append(column)
                yield column

    def on_mount(self) -> None:
        """Инициализация после монтирования экрана."""
        # Заполняем колонки пустыми placeholder'ами с небольшой задержкой
        self.set_timer(0.05, self._initialize_empty_columns)

    def _initialize_empty_columns(self) -> None:
        """Инициализация пустых колонок."""
        for column in self.columns:
            if column.is_attached and not column.children:
                try:
                    column.mount(Static("Пустая колонка", classes="empty-column"))
                except Exception:
                    pass

    def update_view(self, tree_root: TreeNode) -> None:
        """
        Основной метод обновления интерфейса на основе состояния ядра.
        """
        if not tree_root:
            return

        # Получаем путь от корня до активного узла
        visible_path = self._get_visible_path(tree_root)

        # Обновляем заголовок
        self._update_header(visible_path)

        # Обновляем колонки с небольшой задержкой
        def update_columns_delayed():
            self._update_columns(visible_path)

        self.set_timer(0.05, update_columns_delayed)

        # Сохраняем текущее состояние
        self.visible_path = visible_path

    def _get_visible_path(self, tree_root: TreeNode) -> List[TreeNode]:
        """Получение пути от корня до активного узла."""

        def find_active_path(node: TreeNode) -> List[TreeNode]:
            if node.is_active:
                return [node]

            for stack in node.children_stacks.values():
                for child in stack:
                    path = find_active_path(child)
                    if path:
                        return [node] + path

            return []

        return find_active_path(tree_root)

    def _update_header(self, visible_path: List[TreeNode]) -> None:
        """Обновление заголовка с хлебными крошками."""
        if not self.breadcrumbs_label or not self.hidden_indicator_label:
            return

        # Определяем, сколько панелей скрыто слева
        total_panels = len(visible_path)
        visible_panels = min(3, total_panels)
        hidden_count = max(0, total_panels - 3)

        # Обновляем индикатор скрытых панелей
        if hidden_count > 0:
            self.hidden_indicator_label.update(f"◀ {hidden_count}")
        else:
            self.hidden_indicator_label.update("")

        # Обновляем хлебные крошки для видимых панелей
        start_index = max(0, total_panels - 3)
        visible_titles = [node.panel_template.title for node in visible_path[start_index:]]
        breadcrumbs_text = " / ".join(visible_titles)
        self.breadcrumbs_label.update(breadcrumbs_text)

    def _update_columns(self, visible_path: List[TreeNode]) -> None:
        """Обновление содержимого колонок."""
        if not self.columns or not self.is_attached:
            return

        # Очищаем текущие панели
        for panel_widget in self.panel_widgets:
            if panel_widget.parent:
                panel_widget.remove()
        self.panel_widgets.clear()

        # Очищаем колонки
        for column in self.columns:
            if column.is_attached:
                for child in list(column.children):
                    child.remove()

        # Определяем видимые узлы (максимум 3)
        total_nodes = len(visible_path)
        visible_nodes = visible_path[-3:] if total_nodes > 3 else visible_path

        # Создаем панели для видимых узлов
        for i, node in enumerate(visible_nodes):
            is_active = node.is_active
            panel_widget = PanelWidget(node, self.core_app, is_active)

            # Добавляем панель в соответствующую колонку
            column_index = i
            if column_index < len(self.columns) and self.columns[column_index].is_attached:
                try:
                    self.columns[column_index].mount(panel_widget)
                    self.panel_widgets.append(panel_widget)

                    if is_active:
                        self.active_panel_index = column_index
                except Exception as e:
                    # Логируем ошибку, но не прерываем работу
                    pass

        # Заполняем пустые колонки placeholder'ами
        for i in range(len(visible_nodes), 3):
            if i < len(self.columns) and self.columns[i].is_attached:
                try:
                    self.columns[i].mount(Static("Пустая колонка", classes="empty-column"))
                except Exception as e:
                    # Логируем ошибку, но не прерываем работу
                    pass

    # --- Обработчики действий для BINDINGS ---

    def action_horizontal_nav(self, direction: str) -> None:
        """Горизонтальная навигация между колонками."""
        event = HorizontalNavigationEvent(direction=direction)
        self.core_app.post_event(event)

    def action_vertical_nav(self, direction: str) -> None:
        """Вертикальная навигация по стеку панелей."""
        event = VerticalNavigationEvent(direction=direction)
        self.core_app.post_event(event)

    def action_back_nav(self) -> None:
        """Навигация назад."""
        event = BackNavigationEvent()
        self.core_app.post_event(event)

    def action_widget_nav(self, direction: str) -> None:
        """Навигация между виджетами в активной панели."""
        if not self.panel_widgets:
            return

        # Находим активную панель
        active_panel = None
        for panel in self.panel_widgets:
            if panel.is_active:
                active_panel = panel
                break

        if not active_panel:
            return

        # Переключаем фокус между виджетами
        if direction == "next":
            active_panel.focus_next_widget()
        else:  # "previous"
            active_panel.focus_prev_widget()


class ErrorScreen(Screen):
    """
    Экран для отображения ошибок.
    """

    BINDINGS = [
        Binding("escape,enter", "dismiss", "Закрыть"),
    ]

    DEFAULT_CSS = """
    ErrorScreen {
        background: $error-lighten-3;
        content-align: center middle;
    }

    .error-container {
        width: 80%;
        max-width: 80;
        height: auto;
        background: $surface;
        border: solid $error;
        padding: 2;
    }

    .error-title {
        text-style: bold;
        color: $error;
        text-align: center;
        margin-bottom: 1;
    }

    .error-message {
        color: $text;
        text-align: center;
        margin-bottom: 2;
    }

    .error-instruction {
        color: $text-muted;
        text-align: center;
        text-style: italic;
    }
    """

    def __init__(self):
        super().__init__()
        self.error_title_label = None
        self.error_message_label = None

    def compose(self):
        """Создание экрана ошибки."""
        with Container(classes="error-container"):
            self.error_title_label = Label("Ошибка", classes="error-title")
            self.error_message_label = Label("Произошла неизвестная ошибка", classes="error-message")
            yield self.error_title_label
            yield self.error_message_label
            yield Label("Нажмите Enter или Escape для закрытия", classes="error-instruction")

    def show_error(self, title: str, message: str) -> None:
        """Показ ошибки с заданным заголовком и сообщением."""
        if self.error_title_label:
            self.error_title_label.update(title)
        if self.error_message_label:
            self.error_message_label.update(message)

    def action_dismiss(self) -> None:
        """Закрытие экрана ошибки."""
        self.app.pop_screen()