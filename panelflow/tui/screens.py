"""
Экраны для TUI-приложения.
Содержит MainScreen с колонками и ErrorScreen для отображения ошибок.
"""

import logging
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
from panelflow.logging_config import get_logger

from .widgets import create_widget

# Инициализируем логгер для экранов
logger = get_logger(__name__)


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

        logger.debug(f"Создание PanelWidget для панели '{node.panel_template.title}' (active={is_active})")

        if is_active:
            self.add_class("active")
            logger.debug(f"Панель '{node.panel_template.title}' помечена как активная")

    def compose(self):
        """Создание содержимого панели."""
        panel = self.node.panel_template
        logger.debug(f"Компоновка панели '{panel.title}' с {len(panel.widgets)} виджетами")

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
                    logger.debug(f"Создание виджета '{widget_def.id}' типа '{widget_def.type}'")
                    widget_instance = create_widget(
                        widget_def,
                        self.node,
                        self._post_widget_event
                    )
                    if widget_instance:
                        self.widget_instances[widget_def.id] = widget_instance
                        logger.debug(f"Виджет '{widget_def.id}' успешно создан")
                        yield widget_instance
                    else:
                        logger.warning(f"Не удалось создать виджет '{widget_def.id}' типа '{widget_def.type}'")
                        yield Label(f"Неподдерживаемый виджет: {widget_def.type}", classes="widget-error")
                except Exception as e:
                    logger.error(f"Ошибка создания виджета '{widget_def.id}': {e}")
                    yield Label(f"Ошибка виджета: {widget_def.id}", classes="widget-error")

        logger.debug(f"Панель '{panel.title}' скомпонована с {len(self.widget_instances)} виджетами")

    def _post_widget_event(self, widget_id: str, value: Any) -> None:
        """Отправка события от виджета в ядро."""
        logger.info(f"Событие от виджета '{widget_id}': {value}")
        event = WidgetSubmittedEvent(widget_id=widget_id, value=value)
        logger.debug(f"Создано WidgetSubmittedEvent: {event}")
        self.core_app.post_event(event)
        logger.debug("WidgetSubmittedEvent отправлено в ядро")

    def set_active(self, active: bool) -> None:
        """Установка статуса активности панели."""
        logger.debug(f"Установка активности панели '{self.node.panel_template.title}': {active}")
        self.is_active = active
        if active:
            self.add_class("active")
            logger.debug(f"Добавлен CSS класс 'active' для панели '{self.node.panel_template.title}'")
            # Установить фокус на первый виджет если есть
            if self.widget_instances and not self.focused_widget_id:
                first_widget_id = list(self.widget_instances.keys())[0]
                logger.debug(f"Установка фокуса на первый виджет: '{first_widget_id}'")
                self.set_widget_focus(first_widget_id)
        else:
            self.remove_class("active")
            logger.debug(f"Удален CSS класс 'active' для панели '{self.node.panel_template.title}'")
            self.focused_widget_id = None

    def set_widget_focus(self, widget_id: str) -> None:
        """Установка фокуса на конкретный виджет."""
        logger.debug(f"Установка фокуса на виджет '{widget_id}' в панели '{self.node.panel_template.title}'")

        if widget_id not in self.widget_instances:
            logger.error(f"Виджет '{widget_id}' не найден в панели '{self.node.panel_template.title}'")
            return

        # Убираем фокус с предыдущего виджета
        if self.focused_widget_id and self.focused_widget_id in self.widget_instances:
            prev_widget = self.widget_instances[self.focused_widget_id]
            if hasattr(prev_widget, 'set_focus'):
                prev_widget.set_focus(False)
                logger.debug(f"Снят фокус с виджета '{self.focused_widget_id}'")

        # Устанавливаем фокус на новый виджет
        widget = self.widget_instances[widget_id]
        if hasattr(widget, 'set_focus'):
            widget.set_focus(True)
            logger.debug(f"Установлен фокус на виджет '{widget_id}'")
        else:
            logger.warning(f"Виджет '{widget_id}' не поддерживает установку фокуса")

        self.focused_widget_id = widget_id

        # Прокручиваем к виджету если нужно
        try:
            widget.scroll_visible()
            logger.debug(f"Виджет '{widget_id}' прокручен в видимую область")
        except Exception as e:
            logger.debug(f"Не удалось прокрутить виджет '{widget_id}': {e}")

    def focus_next_widget(self) -> bool:
        """Перевод фокуса на следующий виджет. Возвращает True если переход произошел."""
        logger.debug(f"Попытка перевода фокуса на следующий виджет в панели '{self.node.panel_template.title}'")
        logger.debug(f"Доступные виджеты: {list(self.widget_instances.keys())}")
        logger.debug(f"Текущий фокус: {self.focused_widget_id}")

        if not self.widget_instances:
            logger.debug("Нет виджетов для навигации")
            return False

        widget_ids = list(self.widget_instances.keys())
        if not self.focused_widget_id:
            self.set_widget_focus(widget_ids[0])
            logger.debug(f"Установлен фокус на первый виджет: {widget_ids[0]}")
            return True

        try:
            current_index = widget_ids.index(self.focused_widget_id)
            next_index = (current_index + 1) % len(widget_ids)
            next_widget_id = widget_ids[next_index]
            self.set_widget_focus(next_widget_id)
            logger.debug(f"Фокус переведен на виджет: {next_widget_id}")
            return True
        except ValueError:
            logger.error(f"Текущий виджет {self.focused_widget_id} не найден в списке виджетов")
            return False

    def focus_prev_widget(self) -> bool:
        """Перевод фокуса на предыдущий виджет. Возвращает True если переход произошел."""
        logger.debug(f"Попытка перевода фокуса на предыдущий виджет в панели '{self.node.panel_template.title}'")

        if not self.widget_instances:
            logger.debug("Нет виджетов для навигации")
            return False

        widget_ids = list(self.widget_instances.keys())
        if not self.focused_widget_id:
            self.set_widget_focus(widget_ids[-1])
            logger.debug(f"Установлен фокус на последний виджет: {widget_ids[-1]}")
            return True

        try:
            current_index = widget_ids.index(self.focused_widget_id)
            prev_index = (current_index - 1) % len(widget_ids)
            prev_widget_id = widget_ids[prev_index]
            self.set_widget_focus(prev_widget_id)
            logger.debug(f"Фокус переведен на виджет: {prev_widget_id}")
            return True
        except ValueError:
            logger.error(f"Текущий виджет {self.focused_widget_id} не найден в списке виджетов")
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

        logger.info("Инициализация MainScreen")

        # Контейнеры для UI
        self.header_section = None
        self.breadcrumbs_label = None
        self.hidden_indicator_label = None
        self.columns_container = None

    def compose(self):
        """Создание структуры экрана."""
        logger.debug("Создание структуры MainScreen")

        # Заголовок с индикаторами
        with Container(classes="header-section") as header:
            self.header_section = header
            self.hidden_indicator_label = Label("", classes="hidden-indicator")
            self.breadcrumbs_label = Label("PanelFlow", classes="breadcrumbs")
            yield self.hidden_indicator_label
            yield self.breadcrumbs_label
            logger.debug("Заголовочная секция создана")

        # Контейнер для колонок
        with Horizontal(classes="columns-container") as columns_container:
            self.columns_container = columns_container
            logger.debug("Создание 3 колонок")
            # Создаем 3 пустые колонки
            for i in range(3):
                column = Container(classes="column", id=f"column_{i}")
                self.columns.append(column)
                logger.debug(f"Создана колонка {i}")
                yield column

        logger.debug(f"MainScreen структура создана: {len(self.columns)} колонок")

    def on_mount(self) -> None:
        """Инициализация после монтирования экрана."""
        logger.debug("Монтирование MainScreen")
        # Заполняем колонки пустыми placeholder'ами с небольшой задержкой
        self.set_timer(0.05, self._initialize_empty_columns)

    def _initialize_empty_columns(self) -> None:
        """Инициализация пустых колонок."""
        logger.debug("Инициализация пустых колонок")
        initialized_count = 0
        for i, column in enumerate(self.columns):
            logger.debug(f"Колонка {i}: attached={column.is_attached}, children_count={len(column.children)}")
            if column.is_attached and not column.children:
                try:
                    empty_widget = Static("Пустая колонка", classes="empty-column")
                    column.mount(empty_widget)
                    initialized_count += 1
                    logger.debug(f"Колонка {i} инициализирована пустым содержимым")
                except Exception as e:
                    logger.error(f"Ошибка инициализации колонки {i}: {e}")
        logger.info(f"Инициализировано {initialized_count} пустых колонок из {len(self.columns)}")

    def update_view(self, tree_root: TreeNode) -> None:
        """
        Основной метод обновления интерфейса на основе состояния ядра.
        """
        if not tree_root:
            logger.warning("Попытка обновления с пустым корневым узлом")
            return

        logger.info("=" * 50)
        logger.info("НАЧАЛО ОБНОВЛЕНИЯ ПРЕДСТАВЛЕНИЯ")
        logger.debug(f"Корневой узел: '{tree_root.panel_template.title}' (active={tree_root.is_active})")

        # Получаем путь от корня до активного узла
        visible_path = self._get_visible_path(tree_root)
        logger.debug(f"Получен путь навигации: {[node.panel_template.title for node in visible_path]}")

        # Обновляем заголовок
        logger.debug("Обновление заголовка")
        self._update_header(visible_path)

        # Обновляем колонки с задержкой
        def update_columns_delayed():
            logger.debug("Запуск отложенного обновления колонок")
            self._update_columns(visible_path)
            logger.info("ОБНОВЛЕНИЕ ПРЕДСТАВЛЕНИЯ ЗАВЕРШЕНО")
            logger.info("=" * 50)

        # Увеличиваем задержку для стабильности
        self.set_timer(0.1, update_columns_delayed)
        logger.debug("Запланировано отложенное обновление колонок через 0.1с")

        # Сохраняем текущее состояние
        self.visible_path = visible_path

    def _get_visible_path(self, tree_root: TreeNode) -> List[TreeNode]:
        """Получение пути от корня до активного узла."""
        def find_active_path(node: TreeNode) -> List[TreeNode]:
            logger.debug(f"Проверка узла '{node.panel_template.title}' (active={node.is_active})")

            if node.is_active:
                logger.debug(f"Найден активный узел: '{node.panel_template.title}'")
                return [node]

            # Рекурсивно ищем в дочерних стеках
            for stack_key, stack in node.children_stacks.items():
                logger.debug(f"Проверка стека '{stack_key}' с {len(stack)} узлами")
                for child in stack:
                    path = find_active_path(child)
                    if path:
                        logger.debug(f"Найден путь через '{node.panel_template.title}' -> {[n.panel_template.title for n in path]}")
                        return [node] + path

            return []

        logger.debug("Поиск видимого пути от корня до активного узла")
        path = find_active_path(tree_root)
        logger.info(f"Видимый путь: {[node.panel_template.title for node in path]}")
        return path

    def _update_header(self, visible_path: List[TreeNode]) -> None:
        """Обновление заголовка с хлебными крошками."""
        if not self.breadcrumbs_label or not self.hidden_indicator_label:
            logger.warning("Заголовочные элементы не инициализированы")
            return

        # Определяем, сколько панелей скрыто слева
        total_panels = len(visible_path)
        visible_panels = min(3, total_panels)
        hidden_count = max(0, total_panels - 3)

        logger.debug(f"Заголовок: всего панелей={total_panels}, видимых={visible_panels}, скрытых={hidden_count}")

        # Обновляем индикатор скрытых панелей
        if hidden_count > 0:
            indicator_text = f"◀ {hidden_count}"
            self.hidden_indicator_label.update(indicator_text)
            logger.debug(f"Индикатор скрытых панелей: '{indicator_text}'")
        else:
            self.hidden_indicator_label.update("")
            logger.debug("Индикатор скрытых панелей очищен")

        # Обновляем хлебные крошки для видимых панелей
        start_index = max(0, total_panels - 3)
        visible_titles = [node.panel_template.title for node in visible_path[start_index:]]
        breadcrumbs_text = " / ".join(visible_titles)
        self.breadcrumbs_label.update(breadcrumbs_text)
        logger.debug(f"Хлебные крошки: '{breadcrumbs_text}'")

    def _update_columns(self, visible_path: List[TreeNode]) -> None:
        """Обновление содержимого колонок."""
        logger.debug(f"Начало обновления колонок. Путь: {[node.panel_template.title for node in visible_path]}")

        if not self.columns or not self.is_attached:
            logger.warning("Колонки недоступны или экран не присоединен")
            return

        logger.debug(f"Доступно {len(self.columns)} колонок, экран присоединен: {self.is_attached}")

        # Очищаем текущие панели
        logger.debug(f"Очистка {len(self.panel_widgets)} существующих панелей")
        for i, panel_widget in enumerate(self.panel_widgets):
            if panel_widget.parent:
                logger.debug(f"Удаление панели {i}: '{panel_widget.node.panel_template.title}'")
                panel_widget.remove()
        self.panel_widgets.clear()

        # Очищаем колонки
        total_children_removed = 0
        for i, column in enumerate(self.columns):
            if column.is_attached:
                children_count = len(column.children)
                for child in list(column.children):
                    child.remove()
                total_children_removed += children_count
                logger.debug(f"Колонка {i}: удалено {children_count} дочерних элементов")

        logger.debug(f"Всего удалено {total_children_removed} дочерних элементов из колонок")

        # Определяем видимые узлы (максимум 3)
        total_nodes = len(visible_path)
        visible_nodes = visible_path[-3:] if total_nodes > 3 else visible_path

        logger.info(f"Видимые узлы ({len(visible_nodes)} из {total_nodes}): {[node.panel_template.title for node in visible_nodes]}")

        # Создаем панели для видимых узлов
        for i, node in enumerate(visible_nodes):
            is_active = node.is_active
            logger.debug(f"Создание панели {i}: '{node.panel_template.title}' (active={is_active})")

            try:
                panel_widget = PanelWidget(node, self.core_app, is_active)

                # Добавляем панель в соответствующую колонку
                column_index = i
                if column_index < len(self.columns) and self.columns[column_index].is_attached:
                    self.columns[column_index].mount(panel_widget)
                    self.panel_widgets.append(panel_widget)
                    logger.info(f"Панель '{node.panel_template.title}' добавлена в колонку {column_index}")

                    if is_active:
                        self.active_panel_index = column_index
                        logger.debug(f"Активная панель установлена: индекс {column_index}")

                        # Принудительно устанавливаем активность и фокус
                        def setup_active_panel():
                            logger.debug(f"Настройка активной панели '{node.panel_template.title}'")
                            panel_widget.set_active(True)
                            # Устанавливаем фокус на панель
                            if hasattr(panel_widget, 'focus'):
                                panel_widget.focus()
                                logger.debug(f"Фокус установлен на панель '{node.panel_template.title}'")

                        # Выполняем настройку активной панели с небольшой задержкой
                        self.set_timer(0.05, setup_active_panel)

                else:
                    logger.error(f"Колонка {column_index} недоступна для монтирования")

            except Exception as e:
                logger.error(f"Ошибка создания панели '{node.panel_template.title}': {e}", exc_info=True)

        # Заполняем пустые колонки placeholder'ами
        empty_columns_count = 0
        for i in range(len(visible_nodes), 3):
            if i < len(self.columns) and self.columns[i].is_attached:
                try:
                    self.columns[i].mount(Static("Пустая колонка", classes="empty-column"))
                    empty_columns_count += 1
                    logger.debug(f"Колонка {i} заполнена пустышкой")
                except Exception as e:
                    logger.error(f"Ошибка заполнения пустой колонки {i}: {e}")

        logger.info(f"Обновление колонок завершено: {len(self.panel_widgets)} панелей, {empty_columns_count} пустых колонок")

        # Принудительно обновляем экран
        try:
            self.refresh()
            logger.debug("Экран принудительно обновлен")
        except Exception as e:
            logger.error(f"Ошибка принудительного обновления экрана: {e}")

        # Логируем финальное состояние колонок
        for i, column in enumerate(self.columns):
            children_info = [type(child).__name__ for child in column.children]
            logger.debug(f"Колонка {i} финальное состояние: {len(column.children)} детей - {children_info}")

    # --- Обработчики действий для BINDINGS ---

    def action_horizontal_nav(self, direction: str) -> None:
        """Горизонтальная навигация между колонками."""
        logger.info(f"Горизонтальная навигация: {direction}")
        event = HorizontalNavigationEvent(direction=direction)
        self.core_app.post_event(event)

    def action_vertical_nav(self, direction: str) -> None:
        """Вертикальная навигация по стеку панелей."""
        logger.info(f"Вертикальная навигация: {direction}")
        event = VerticalNavigationEvent(direction=direction)
        self.core_app.post_event(event)

    def action_back_nav(self) -> None:
        """Навигация назад."""
        logger.info("Навигация назад")
        event = BackNavigationEvent()
        self.core_app.post_event(event)

    def action_widget_nav(self, direction: str) -> None:
        """Навигация между виджетами в активной панели."""
        logger.debug("=" * 40)
        logger.debug(f"НАЧАЛО НАВИГАЦИИ ПО ВИДЖЕТАМ: {direction}")
        self._debug_application_state()

        if not self.panel_widgets:
            logger.debug("Нет панелей для навигации по виджетам")
            return

        # Находим активную панель
        active_panel = None
        for i, panel in enumerate(self.panel_widgets):
            logger.debug(f"Панель {i}: '{panel.node.panel_template.title}' (active={panel.is_active})")
            if panel.is_active:
                active_panel = panel
                break

        if not active_panel:
            logger.warning("Активная панель не найдена для навигации по виджетам")
            # Попробуем взять панель с индексом active_panel_index
            if 0 <= self.active_panel_index < len(self.panel_widgets):
                active_panel = self.panel_widgets[self.active_panel_index]
                logger.debug(f"Используем панель по индексу {self.active_panel_index}: '{active_panel.node.panel_template.title}'")
            else:
                logger.error(f"Некорректный индекс активной панели: {self.active_panel_index}")
                return

        logger.debug(f"Навигация по виджетам в панели: '{active_panel.node.panel_template.title}'")

        # Переключаем фокус между виджетами
        if direction == "next":
            success = active_panel.focus_next_widget()
        else:  # "previous"
            success = active_panel.focus_prev_widget()

        if success:
            logger.debug(f"Фокус виджета переключен: {direction}")
        else:
            logger.debug(f"Не удалось переключить фокус виджета: {direction}")

        logger.debug("КОНЕЦ НАВИГАЦИИ ПО ВИДЖЕТАМ")
        logger.debug("=" * 40)

    def _debug_application_state(self) -> None:
        """Отладочный метод для вывода полного состояния приложения."""
        logger.debug("СОСТОЯНИЕ ПРИЛОЖЕНИЯ:")
        logger.debug(f"  - Всего колонок: {len(self.columns)}")
        logger.debug(f"  - Всего панелей: {len(self.panel_widgets)}")
        logger.debug(f"  - Активный индекс: {self.active_panel_index}")
        logger.debug(f"  - Видимый путь: {len(self.visible_path)} узлов")

        for i, column in enumerate(self.columns):
            logger.debug(f"  - Колонка {i}: attached={column.is_attached}, children={len(column.children)}")
            for j, child in enumerate(column.children):
                child_type = type(child).__name__
                if hasattr(child, 'node'):
                    child_info = f"{child_type}('{child.node.panel_template.title}')"
                else:
                    child_info = child_type
                logger.debug(f"    - Ребенок {j}: {child_info}")

        for i, panel in enumerate(self.panel_widgets):
            logger.debug(f"  - Панель {i}: '{panel.node.panel_template.title}' active={panel.is_active}")
            logger.debug(f"    - Виджеты: {list(panel.widget_instances.keys())}")
            logger.debug(f"    - Фокус: {panel.focused_widget_id}")


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