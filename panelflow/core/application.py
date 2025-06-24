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
import logging
from panelflow.logging_config import get_logger

# Инициализируем логгер для ядра
logger = get_logger(__name__)

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
        logger.info("Инициализация Application (ядро PanelFlow)")
        logger.debug(f"Путь конфигурации: {config_path}")
        logger.debug(f"Обработчики: {list(handler_map.keys())}")

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
        if callback not in self._event_subscribers:
            self._event_subscribers.append(callback)

    def unsubscribe_from_events(self, callback: Callable[[BaseEvent], None]) -> None:
        """
        Отписка от событий.

        Args:
            callback: Функция обратного вызова для удаления из подписчиков
        """
        if callback in self._event_subscribers:
            self._event_subscribers.remove(callback)

    def post_event(self, event: BaseEvent) -> None:
        """
        Единственная публичная точка входа для обработки событий.
        Маршрутизирует события к соответствующим внутренним обработчикам.

        Args:
            event: Событие для обработки
        """
        logger.debug(f"Получено событие: {type(event).__name__}")

        if isinstance(event, WidgetSubmittedEvent):
            logger.info(f"WidgetSubmittedEvent: виджет='{event.widget_id}', значение={event.value}")

        try:
            if isinstance(event, WidgetSubmittedEvent):
                self._handle_widget_submission(event)
            elif isinstance(event, HorizontalNavigationEvent):
                self._handle_horizontal_navigation(event)
            elif isinstance(event, VerticalNavigationEvent):
                self._handle_vertical_navigation(event)
            elif isinstance(event, BackNavigationEvent):
                self._handle_back_navigation(event)
            else:
                # Неизвестный тип события - игнорируем
                pass

        except Exception as e:
            # Перехватываем любые внутренние ошибки и публикуем событие ошибки
            logger.error(f"Ошибка при обработке события {type(event).__name__}: {e}", exc_info=True)

            self._publish_event(ErrorOccurredEvent(
                title="Внутренняя ошибка ядра",
                message=f"Ошибка при обработке события {type(event).__name__}: {str(e)}"
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
        logger.info(f"Загрузка конфигурации из {self.config_path}")

        if not self.config_path.exists():
            logger.error(f"Файл конфигурации не найден: {self.config_path}")
            raise FileNotFoundError(f"Файл конфигурации не найден: {self.config_path}")

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
        logger.debug("Парсинг конфигурации в объекты")
        self._entry_panel_id = config_data["entryPanel"]
        logger.info(f"Панель входа: {self._entry_panel_id}")

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
        logger.info(f"Загружено {len(self._panel_templates)} панелей")

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
        logger.debug(f"Обработка подтверждения виджета '{event.widget_id}'")

        # Находим узел, содержащий виджет
        source_node = self._find_node_by_widget_id(event.widget_id)
        if not source_node:
            # Виджет не найден - игнорируем событие
            return

        logger.debug(f"Найден узел панели: '{source_node.panel_template.title}'")

        # Автоматически обновляем данные формы
        source_node.form_data[event.widget_id] = event.value

        # Определяем обработчик
        handler_class_name = None

        # Сначала ищем обработчик у самого виджета
        for widget in source_node.panel_template.widgets:
            if widget.id == event.widget_id and widget.handler_class_name:
                handler_class_name = widget.handler_class_name
                break

        # Если у виджета нет обработчика, используем обработчик панели
        if not handler_class_name:
            handler_class_name = source_node.panel_template.handler_class_name

        navigation_command = None

        # Если обработчик определен, вызываем его
        if handler_class_name and handler_class_name in self.handler_map:
            try:
                # Создаем экземпляр обработчика
                handler_class = self.handler_map[handler_class_name]
                handler_instance = handler_class(
                    context=source_node.context,
                    form_data=source_node.form_data
                )

                # Вызываем обработчик
                navigation_command = handler_instance.on_widget_update(
                    event.widget_id,
                    event.value
                )

            except Exception as e:
                # Ошибка в пользовательском обработчике
                self._publish_event(ErrorOccurredEvent(
                    title="Ошибка в обработчике",
                    message=f"Ошибка в обработчике '{handler_class_name}': {str(e)}"
                ))
                return

        # Выполняем навигацию, если команда была возвращена
        if navigation_command and isinstance(navigation_command, tuple):
            command_type = navigation_command[0]

            if command_type == "navigate_down" and len(navigation_command) >= 2:
                target = navigation_command[1]
                self._execute_navigation_down(source_node, event.widget_id, target)
                return  # StateChangedEvent уже опубликован в _execute_navigation_down

        # Если навигации не было, публикуем событие изменения состояния
        # так как form_data изменились
        self._publish_event(StateChangedEvent(tree_root=self._tree_root))

    def _handle_horizontal_navigation(self, event: HorizontalNavigationEvent) -> None:
        """
        Обработка горизонтальной навигации между колонками.

        Args:
            event: Событие горизонтальной навигации
        """
        logger.debug(f"Горизонтальная навигация: {event.direction}")
        if not self._active_node:
            return

        # Получаем путь от корня до активного узла
        path = self._get_path_to_active_node()
        if len(path) <= 1:
            # Нет панелей для навигации
            return

        # Находим индекс активного узла в пути
        try:
            current_index = path.index(self._active_node)
        except ValueError:
            # Активный узел не найден в пути (не должно происходить)
            return

        # Вычисляем новый индекс
        if event.direction == "next":
            new_index = current_index + 1
        else:  # "previous"
            new_index = current_index - 1

        # Проверяем валидность нового индекса
        if 0 <= new_index < len(path):
            # Устанавливаем новый активный узел
            new_active_node = path[new_index]
            self._set_active_node(new_active_node)

            # Публикуем событие изменения состояния
            self._publish_event(StateChangedEvent(tree_root=self._tree_root))

    def _handle_vertical_navigation(self, event: VerticalNavigationEvent) -> None:
        """
        Обработка вертикальной навигации по стеку панелей.

        Args:
            event: Событие вертикальной навигации
        """
        logger.debug(f"Вертикальная навигация: {event.direction}")
        if not self._active_node or not self._active_node.parent:
            # Нет активного узла или это корневой узел
            return

        active_node = self._active_node
        parent = active_node.parent

        # Находим стек, которому принадлежит активный узел
        stack_key = None
        stack = None

        for key, current_stack in parent.children_stacks.items():
            if active_node in current_stack:
                stack_key = key
                stack = current_stack
                break

        if not stack or len(stack) <= 1:
            # Стек не найден или в нем только один элемент
            return

        # Находим индекс активного узла в стеке
        try:
            current_index = stack.index(active_node)
        except ValueError:
            # Активный узел не найден в стеке (не должно происходить)
            return

        # Вычисляем новый индекс
        if event.direction == "up":
            new_index = current_index + 1
        else:  # "down"
            new_index = current_index - 1

        # Проверяем валидность нового индекса
        if 0 <= new_index < len(stack):
            # Перемещаем узел с нового индекса на вершину стека (в конец списка)
            target_node = stack.pop(new_index)
            stack.append(target_node)

            # Устанавливаем новый узел на вершине стека как активный
            self._set_active_node(target_node)

            # Публикуем событие изменения состояния
            self._publish_event(StateChangedEvent(tree_root=self._tree_root))

    def _handle_back_navigation(self, event: BackNavigationEvent) -> None:
        """
        Обработка навигации назад (закрытие текущей панели).

        Args:
            event: Событие навигации назад
        """
        logger.info("Обработка навигации назад")

        if not self._active_node:
            logger.warning("Нет активного узла для навигации назад")
            return

        active_node = self._active_node
        logger.debug(f"Закрытие панели: '{active_node.panel_template.title}'")
        parent = active_node.parent

        # Если это корневой узел, навигация назад невозможна
        if not parent:
            return

        # Рекурсивно уничтожаем все дочерние стеки активного узла
        for child_stack in list(active_node.children_stacks.values()):
            self._destroy_stack_recursively(child_stack)
        active_node.children_stacks.clear()

        # Находим стек, которому принадлежит активный узел
        stack_key = None
        stack = None

        for key, current_stack in parent.children_stacks.items():
            if active_node in current_stack:
                stack_key = key
                stack = current_stack
                break

        if not stack:
            # Стек не найден (не должно происходить)
            return

        # Удаляем активный узел из стека
        try:
            stack.remove(active_node)
        except ValueError:
            # Узел не найден в стеке (не должно происходить)
            return

        # Разрываем связь активного узла с родителем
        active_node.parent = None
        active_node.is_active = False

        # Определяем новый фокус
        if stack:
            # Если в стеке остались узлы, верхний становится активным
            new_active_node = stack[-1]
        else:
            # Если стек опустел, удаляем его и возвращаемся к родителю
            del parent.children_stacks[stack_key]
            new_active_node = parent

        # Устанавливаем новый активный узел
        self._set_active_node(new_active_node)

        # Публикуем событие изменения состояния
        self._publish_event(StateChangedEvent(tree_root=self._tree_root))
        logger.debug("Навигация назад завершена")

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
        logger.info(f"Навигация вниз: от '{source_node.panel_template.title}' -> '{target}'")

        # Проверяем, существует ли стек для данного виджета
        if source_widget_id in source_node.children_stacks:
            # Уничтожаем старую ветку
            old_stack = source_node.children_stacks[source_widget_id]
            self._destroy_stack_recursively(old_stack)

        # Создаем экземпляр панели
        try:
            panel_template = self._create_panel_instance(target, source_node.form_data)
        except ValueError as e:
            # Публикуем ошибку и прерываем выполнение
            self._publish_event(ErrorOccurredEvent(
                title="Ошибка навигации",
                message=str(e)
            ))
            return

        # Создаем новый узел
        new_node = TreeNode(
            panel_template=panel_template,
            context=source_node.form_data.copy(),  # Контекст = данные формы родителя
            form_data={},  # Новая пустая форма
            parent=source_node,
            is_active=False  # Пока не активный
        )
        logger.debug(f"Создан новый узел для панели '{panel_template.title}'")

        # Создаем новый стек с этим узлом
        source_node.children_stacks[source_widget_id] = [new_node]

        # Делаем новый узел активным
        self._set_active_node(new_node)

        # Публикуем событие изменения состояния
        self._publish_event(StateChangedEvent(tree_root=self._tree_root))

        logger.debug("Навигация вниз завершена успешно")

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
        for node in stack:
            # Рекурсивно уничтожаем все дочерние стеки
            for child_stack in list(node.children_stacks.values()):
                self._destroy_stack_recursively(child_stack)

            # Очищаем дочерние стеки узла
            node.children_stacks.clear()

            # Разрываем связь с родителем
            node.parent = None

            # Снимаем флаг активности если он был активным
            if node.is_active:
                node.is_active = False

        # Очищаем сам стек
        stack.clear()

    def _get_path_to_active_node(self) -> list[TreeNode]:
        """
        Получение пути от корня до активного узла.

        Returns:
            Список узлов от корня до активного узла
        """
        ...

    # Приватные вспомогательные методы

    def _get_path_to_active_node(self) -> list[TreeNode]:
        """
        Получение пути от корня до активного узла.

        Returns:
            Список узлов от корня до активного узла
        """
        if not self._active_node:
            return []

        path = []
        current = self._active_node

        # Идем от активного узла вверх по родителям до корня
        while current:
            path.append(current)
            current = current.parent

        # Разворачиваем путь, чтобы он шел от корня к активному узлу
        path.reverse()
        return path

    def _find_node_by_widget_id(self, widget_id: str) -> TreeNode | None:
        """
        Поиск узла, содержащего виджет с указанным ID.

        Args:
            widget_id: ID искомого виджета

        Returns:
            Узел, содержащий виджет, или None если не найден
        """

        def search_node(node: TreeNode) -> TreeNode | None:
            # Проверяем виджеты в текущем узле
            for widget in node.panel_template.widgets:
                if widget.id == widget_id:
                    return node

            # Рекурсивно ищем в дочерних стеках
            for stack in node.children_stacks.values():
                for child_node in stack:
                    result = search_node(child_node)
                    if result:
                        return result

            return None

        if not self._tree_root:
            return None

        return search_node(self._tree_root)

    def _publish_event(self, event: BaseEvent) -> None:
        """
        Публикация события для всех подписчиков.

        Args:
            event: Событие для публикации
        """
        for callback in self._event_subscribers:
            try:
                callback(event)
            except Exception as e:
                # Логируем ошибку в колбэке, но не прерываем обработку
                print(f"Ошибка в обработчике события: {e}")

    def _set_active_node(self, node: TreeNode) -> None:
        """
        Установка активного узла с корректным снятием флага с предыдущего.

        Args:
            node: Узел для установки как активный
        """
        # Снимаем флаг активности с предыдущего узла
        if self._active_node:
            self._active_node.is_active = False

        # Устанавливаем новый активный узел
        self._active_node = node
        if node:
            node.is_active = True

    def _create_panel_instance(self, target: str | AbstractPanel, context: dict) -> AbstractPanel:
        """
        Создание экземпляра панели по ID или объекту.

        Args:
            target: ID панели или объект AbstractPanel
            context: Контекст для панели

        Returns:
            Экземпляр AbstractPanel

        Raises:
            ValueError: Если панель с указанным ID не найдена
        """
        if isinstance(target, str):
            if target not in self._panel_templates:
                raise ValueError(f"Панель с ID '{target}' не найдена")
            return self._panel_templates[target]
        elif isinstance(target, AbstractPanel):
            return target
        else:
            raise ValueError(f"Неверный тип target: {type(target)}")