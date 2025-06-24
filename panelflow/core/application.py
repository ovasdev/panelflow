"""
Главный оркестратор приложения PanelFlow.
Управляет состоянием, обрабатывает события и координирует взаимодействие
между компонентами системы.
"""

from pathlib import Path
from typing import Dict, Type, Any, Callable
import json
import jsonschema
from jsonschema import validate, ValidationError

from .components import (
    AbstractPanel, AbstractWidget, AbstractTextInput,
    AbstractButton, AbstractOptionSelect, PanelLink
)
from .state import TreeNode
from .handlers import BasePanelHandler
from .events import (
    BaseEvent,
    WidgetSubmittedEvent,
    HorizontalNavigationEvent,
    VerticalNavigationEvent,
    BackNavigationEvent,
    StateChangedEvent,
    ErrorOccurredEvent
)

# JSON Schema для валидации конфигурации PanelFlow
APPLICATION_CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "required": ["entryPanel", "panels"],
    "properties": {
        "entryPanel": {
            "type": "string",
            "description": "ID панели, которая будет показана при запуске приложения"
        },
        "panels": {
            "type": "array",
            "description": "Массив определений панелей",
            "items": {
                "$ref": "#/definitions/panel"
            }
        }
    },
    "definitions": {
        "panel": {
            "type": "object",
            "required": ["id", "title"],
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Уникальный идентификатор панели"
                },
                "title": {
                    "type": "string",
                    "description": "Заголовок панели"
                },
                "description": {
                    "type": "string",
                    "description": "Описание панели",
                    "default": ""
                },
                "handler_class_name": {
                    "type": ["string", "null"],
                    "description": "Имя класса обработчика для панели"
                },
                "widgets": {
                    "type": "array",
                    "description": "Массив виджетов панели",
                    "items": {
                        "$ref": "#/definitions/widget"
                    },
                    "default": []
                }
            }
        },
        "widget": {
            "type": "object",
            "required": ["id", "type", "title"],
            "properties": {
                "id": {
                    "type": "string",
                    "description": "Уникальный идентификатор виджета"
                },
                "type": {
                    "type": "string",
                    "enum": ["text_input", "button", "option_select", "panel_link"],
                    "description": "Тип виджета"
                },
                "title": {
                    "type": "string",
                    "description": "Заголовок виджета"
                },
                "value": {
                    "description": "Значение виджета по умолчанию"
                },
                "handler_class_name": {
                    "type": ["string", "null"],
                    "description": "Имя класса обработчика для виджета"
                }
            },
            "allOf": [
                {
                    "if": {
                        "properties": {"type": {"const": "text_input"}}
                    },
                    "then": {
                        "properties": {
                            "placeholder": {
                                "type": "string",
                                "description": "Текст-подсказка для поля ввода",
                                "default": ""
                            }
                        }
                    }
                },
                {
                    "if": {
                        "properties": {"type": {"const": "option_select"}}
                    },
                    "then": {
                        "properties": {
                            "options": {
                                "type": "array",
                                "description": "Список доступных опций",
                                "items": {
                                    "type": "string"
                                },
                                "default": []
                            }
                        }
                    }
                },
                {
                    "if": {
                        "properties": {"type": {"const": "panel_link"}}
                    },
                    "then": {
                        "required": ["target_panel_id"],
                        "properties": {
                            "target_panel_id": {
                                "type": "string",
                                "description": "ID целевой панели для навигации"
                            },
                            "description": {
                                "type": "string",
                                "description": "Описание ссылки",
                                "default": ""
                            }
                        }
                    }
                }
            ]
        }
    }
}


class Application:
    """
    Основной класс приложения PanelFlow.

    Отвечает за:
    - Загрузку и валидацию конфигурации
    - Управление деревом состояний
    - Обработку событий навигации
    - Координацию работы обработчиков
    """

    def __init__(self, config_path: str | Path, handler_map: Dict[str, Type[BasePanelHandler]]):
        """
        Инициализация приложения.

        Args:
            config_path: Путь к файлу конфигурации (application.json)
            handler_map: Словарь соответствия имен классов обработчиков их типам

        Raises:
            FileNotFoundError: Если файл конфигурации не найден
            ValidationError: Если конфигурация не прошла валидацию
            ValueError: Если найдены ошибки целостности конфигурации
        """
        self.config_path = Path(config_path)
        self.handler_map = handler_map
        self._panel_templates: Dict[str, AbstractPanel] = {}
        self._tree_root: TreeNode | None = None
        self._active_node: TreeNode | None = None
        self._event_subscribers: list[Callable[[BaseEvent], None]] = []
        self._entry_panel_id: str = ""

        # Инициализация
        self._load_config()
        self._validate_config_integrity()
        self._create_initial_state()

    def subscribe_to_events(self, callback: Callable[[BaseEvent], None]) -> None:
        """
        Подписка на события от ядра.

        Args:
            callback: Функция обратного вызова для обработки событий
        """
        ...

    def unsubscribe_from_events(self, callback: Callable[[BaseEvent], None]) -> None:
        """
        Отписка от событий.

        Args:
            callback: Функция обратного вызова для удаления из подписчиков
        """
        ...

    def post_event(self, event: BaseEvent) -> None:
        """
        Единственная публичная точка входа для обработки событий.
        Маршрутизирует события к соответствующим внутренним обработчикам.

        Args:
            event: Событие для обработки
        """
        try:
            if isinstance(event, WidgetSubmittedEvent):
                self._handle_widget_submission(event)
            elif isinstance(event, HorizontalNavigationEvent):
                self._handle_horizontal_navigation(event)
            elif isinstance(event, VerticalNavigationEvent):
                self._handle_vertical_navigation(event)
            elif isinstance(event, BackNavigationEvent):
                self._handle_back_navigation(event)
        except Exception as e:
            self._publish_event(ErrorOccurredEvent(
                title="Внутренняя ошибка",
                message=str(e)
            ))

    @property
    def tree_root(self) -> TreeNode | None:
        """Получение корневого узла дерева состояний."""
        return self._tree_root

    @property
    def active_node(self) -> TreeNode | None:
        """Получение текущего активного узла."""
        return self._active_node

    # Приватные методы для инициализации

    def _load_config(self) -> None:
        """
        Загрузка и парсинг конфигурации из application.json.
        Создает объекты AbstractPanel на основе JSON-конфигурации.

        Raises:
            FileNotFoundError: Если файл конфигурации не найден
            ValidationError: Если JSON не соответствует схеме
            json.JSONDecodeError: Если файл содержит невалидный JSON
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Файл конфигурации не найден: {self.config_path}")

        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config_data = json.load(file)
        except json.JSONDecodeError as e:
            raise json.JSONDecodeError(f"Ошибка парсинга JSON конфигурации: {e.msg}", e.doc, e.pos)

        # Валидация по схеме
        self._validate_json_schema(config_data)

        # Парсинг в объекты
        self._parse_config_to_objects(config_data)

    def _validate_json_schema(self, config_data: dict) -> None:
        """
        Валидация JSON-конфигурации по схеме.

        Args:
            config_data: Данные конфигурации для валидации

        Raises:
            ValidationError: Если данные не соответствуют схеме
        """
        try:
            validate(instance=config_data, schema=APPLICATION_CONFIG_SCHEMA)
        except ValidationError as e:
            raise ValidationError(f"Ошибка валидации конфигурации: {e.message}")

    def _parse_config_to_objects(self, config_data: dict) -> None:
        """
        Преобразование JSON-конфигурации в объекты AbstractPanel.

        Args:
            config_data: Валидированные данные конфигурации
        """
        self._entry_panel_id = config_data["entryPanel"]
        self._panel_templates = {}

        for panel_data in config_data["panels"]:
            # Парсинг виджетов
            widgets = []
            for widget_data in panel_data.get("widgets", []):
                widget = self._create_widget_from_data(widget_data)
                widgets.append(widget)

            # Создание панели
            panel = AbstractPanel(
                id=panel_data["id"],
                title=panel_data["title"],
                description=panel_data.get("description", ""),
                widgets=widgets,
                handler_class_name=panel_data.get("handler_class_name")
            )

            self._panel_templates[panel.id] = panel

    def _create_widget_from_data(self, widget_data: dict) -> AbstractWidget:
        """
        Создание виджета на основе данных из конфигурации.

        Args:
            widget_data: Данные виджета из JSON

        Returns:
            Экземпляр соответствующего виджета

        Raises:
            ValueError: Если тип виджета неизвестен
        """
        widget_type = widget_data["type"]
        common_params = {
            "id": widget_data["id"],
            "title": widget_data["title"],
            "value": widget_data.get("value"),
            "handler_class_name": widget_data.get("handler_class_name")
        }

        if widget_type == "text_input":
            return AbstractTextInput(
                placeholder=widget_data.get("placeholder", ""),
                **common_params
            )
        elif widget_type == "button":
            return AbstractButton(**common_params)
        elif widget_type == "option_select":
            return AbstractOptionSelect(
                options=widget_data.get("options", []),
                **common_params
            )
        elif widget_type == "panel_link":
            return PanelLink(
                target_panel_id=widget_data["target_panel_id"],
                description=widget_data.get("description", ""),
                **common_params
            )
        else:
            raise ValueError(f"Неизвестный тип виджета: {widget_type}")

    def _validate_config_integrity(self) -> None:
        """
        Проверка целостности конфигурации:
        - Существование entryPanel
        - Корректность target_panel_id у PanelLink
        - Существование handler_class_name в handler_map

        Raises:
            ValueError: Если найдены ошибки целостности
        """
        errors = []

        # Проверка существования entryPanel
        if self._entry_panel_id not in self._panel_templates:
            errors.append(f"Панель входа '{self._entry_panel_id}' не найдена в конфигурации")

        # Проверка всех панелей
        for panel_id, panel in self._panel_templates.items():
            # Проверка handler_class_name панели
            if panel.handler_class_name and panel.handler_class_name not in self.handler_map:
                errors.append(
                    f"Обработчик '{panel.handler_class_name}' для панели '{panel_id}' не найден в handler_map")

            # Проверка виджетов
            for widget in panel.widgets:
                # Проверка handler_class_name виджета
                if widget.handler_class_name and widget.handler_class_name not in self.handler_map:
                    errors.append(
                        f"Обработчик '{widget.handler_class_name}' для виджета '{widget.id}' не найден в handler_map")

                # Проверка target_panel_id у PanelLink
                if isinstance(widget, PanelLink):
                    if widget.target_panel_id not in self._panel_templates:
                        errors.append(f"Целевая панель '{widget.target_panel_id}' для ссылки '{widget.id}' не найдена")

        if errors:
            raise ValueError("Ошибки целостности конфигурации:\n" + "\n".join(f"- {error}" for error in errors))

    def _create_initial_state(self) -> None:
        """
        Создание начального состояния приложения:
        корневого TreeNode и установка его как активного.

        Raises:
            ValueError: Если панель входа не найдена
        """
        if self._entry_panel_id not in self._panel_templates:
            raise ValueError(f"Панель входа '{self._entry_panel_id}' не найдена")

        entry_panel = self._panel_templates[self._entry_panel_id]

        # Создание корневого узла
        self._tree_root = TreeNode(
            panel_template=entry_panel,
            context={},
            form_data={},
            parent=None,
            is_active=True
        )

        # Установка активного узла
        self._active_node = self._tree_root

    # Приватные методы обработки событий

    def _handle_widget_submission(self, event: WidgetSubmittedEvent) -> None:
        """
        Обработка подтверждения ввода в виджете.

        Алгоритм:
        1. Найти узел, содержащий виджет
        2. Обновить form_data узла
        3. Вызвать пользовательский обработчик
        4. Выполнить навигацию, если требуется

        Args:
            event: Событие подтверждения виджета
        """
        ...

    def _handle_horizontal_navigation(self, event: HorizontalNavigationEvent) -> None:
        """
        Обработка горизонтальной навигации между колонками.

        Args:
            event: Событие горизонтальной навигации
        """
        ...

    def _handle_vertical_navigation(self, event: VerticalNavigationEvent) -> None:
        """
        Обработка вертикальной навигации по стеку панелей.

        Args:
            event: Событие вертикальной навигации
        """
        ...

    def _handle_back_navigation(self, event: BackNavigationEvent) -> None:
        """
        Обработка навигации назад (закрытие текущей панели).

        Args:
            event: Событие навигации назад
        """
        ...

    # Приватные методы навигации

    def _execute_navigation_down(self, source_node: TreeNode, source_widget_id: str,
                                 target: str | AbstractPanel) -> None:
        """
        Выполнение навигации вниз (создание дочерней панели).

        Args:
            source_node: Узел-источник навигации
            source_widget_id: ID виджета, инициировавшего навигацию
            target: ID панели или объект AbstractPanel для навигации
        """
        ...

    def _find_node_by_widget_id(self, widget_id: str) -> TreeNode | None:
        """
        Поиск узла, содержащего виджет с указанным ID.

        Args:
            widget_id: ID искомого виджета

        Returns:
            Узел, содержащий виджет, или None если не найден
        """
        ...

    def _destroy_stack_recursively(self, stack: list[TreeNode]) -> None:
        """
        Рекурсивное уничтожение стека узлов и всех их дочерних стеков.

        Args:
            stack: Стек узлов для уничтожения
        """
        ...

    def _get_path_to_active_node(self) -> list[TreeNode]:
        """
        Получение пути от корня до активного узла.

        Returns:
            Список узлов от корня до активного узла
        """
        ...

    # Приватные вспомогательные методы

    def _publish_event(self, event: BaseEvent) -> None:
        """
        Публикация события для всех подписчиков.

        Args:
            event: Событие для публикации
        """
        ...

    def _set_active_node(self, node: TreeNode) -> None:
        """
        Установка активного узла с корректным снятием флага с предыдущего.

        Args:
            node: Узел для установки как активный
        """
        ...

    def _create_panel_instance(self, target: str | AbstractPanel, context: dict) -> AbstractPanel:
        """
        Создание экземпляра панели по ID или объекту.

        Args:
            target: ID панели или объект AbstractPanel
            context: Контекст для панели

        Returns:
            Экземпляр AbstractPanel
        """
        ...