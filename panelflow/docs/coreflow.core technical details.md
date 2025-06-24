# Техническая спецификация: Слой Ядра (panelflow.core)

## 1. Назначение и архитектура

**Слой Ядра (`panelflow.core`)** — это центральный, платформо-независимый мозг любого приложения, созданного на базе PanelFlow. Он не занимается отображением, а полностью сосредоточен на управлении состоянием, потоками данных, навигацией и исполнением бизнес-логики.

**Ключевые обязанности:**

- Быть единственным источником правды (`single source of truth`) о состоянии приложения.
    
- Обрабатывать логику навигации в двумерной модели (колонки и стеки).
    
- Предоставлять интерфейс для реализации пользовательской бизнес-логики через обработчики.
    
- Взаимодействовать с внешним миром (Слоем Рендеринга) исключительно через строго определенную систему событий.
    

## 2. Структура файлов

```
panelflow/
└── core/
    ├── __init__.py
    ├── application.py    # Класс Application (главный оркестратор)
    ├── components.py     # Абстрактные классы Panel, Widget
    ├── state.py          # Класс TreeNode (узел дерева состояний)
    ├── handlers.py       # Базовые классы для пользовательских обработчиков
    └── events.py         # Определение всех классов событий
```

## 3. Компоненты (`components.py`)

Это классы-данные, описывающие структуру UI. Рекомендуется использовать `dataclasses`.

#### `AbstractWidget` (базовый класс)

```
@dataclass
class AbstractWidget:
    id: str
    type: str = field(init=False)
    title: str
    value: Any = None
    handler_class_name: str | None = None
```

#### Наследники `AbstractWidget`

- `AbstractTextInput(placeholder: str)`
    
- `AbstractButton()`
    
- `AbstractOptionSelect(options: list)`
    
- `PanelLink(target_panel_id: str, description: str)`
    

#### `AbstractPanel`

```
@dataclass
class AbstractPanel:
    id: str
    title: str
    description: str = ""
    widgets: list[AbstractWidget] = field(default_factory=list)
    handler_class_name: str | None = None
```

## 4. Управление состоянием (`state.py`)

#### `TreeNode`

Этот класс представляет **экземпляр** панели в дереве навигации.

```
from __future__ import annotations
from uuid import UUID, uuid4

@dataclass
class TreeNode:
    # Ссылка на "шаблон" панели
    panel_template: AbstractPanel
    
    # Контекст, полученный от родителя
    context: dict = field(default_factory=dict)
    
    # Данные формы, собранные виджетами этого узла
    form_data: dict = field(default_factory=dict)
    
    # Навигационные связи
    parent: TreeNode | None = None
    
    # КЛЮЧЕВАЯ СТРУКТУРА ДЛЯ НАВИГАЦИИ
    # Словарь, где ключ - ID виджета-родителя, породившего ветку,
    # а значение - стек дочерних узлов.
    children_stacks: dict[str, list[TreeNode]] = field(default_factory=dict)
    
    # Уникальный ID экземпляра
    node_id: UUID = field(default_factory=uuid4)
    
    # Флаг фокуса
    is_active: bool = False
```

## 5. Система событий (`events.py`)

#### Входящие (Renderer → Core)

```
@dataclass
class WidgetSubmittedEvent(BaseEvent):
    widget_id: str
    value: Any

@dataclass
class HorizontalNavigationEvent(BaseEvent):
    direction: Literal["next", "previous"]

@dataclass
class VerticalNavigationEvent(BaseEvent):
    direction: Literal["up", "down"]

@dataclass
class BackNavigationEvent(BaseEvent):
    pass
```

#### Исходящие (Core → Renderer)

```
@dataclass
class StateChangedEvent(BaseEvent):
    tree_root: TreeNode

@dataclass
class ErrorOccurredEvent(BaseEvent):
    title: str
    message: str
```

## 6. Базовые обработчики (`handlers.py`)

```
from abc import ABC, abstractmethod

class BasePanelHandler(ABC):
    def __init__(self, context: dict, form_data: dict):
        self.context = context
        self.form_data = form_data

    @abstractmethod
    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        # Может вернуть команду навигации, например:
        # ("navigate_down", "panel_id")
        # или ("navigate_down", AbstractPanel(...))
        pass
```

## 7. Ядро приложения (`application.py`)

Это самый сложный класс, реализующий всю логику.

#### `Application.__init__`

1. Принимает `config_path` и `handler_map`.
    
2. Вызывает `_load_config`, который читает, валидирует (через JSON Schema для максимальной надежности) и парсит `application.json` в объекты `AbstractPanel`.
    
3. Проверяет целостность конфигурации (существование `entryPanel`, `target_panel_id` у `PanelLink` и `handler_class_name` в `handler_map`).
    
4. Создает корневой `TreeNode` и делает его активным.
    

#### `Application.post_event`

Действует как маршрутизатор, вызывая внутренние методы-обработчики (`_handle_...`) в блоке `try...except` для перехвата любых ошибок. При возникновении исключения генерируется `ErrorOccurredEvent`.

#### Внутренние обработчики и логика

- **`_handle_widget_submission`**:
    
    1. Найти узел (`source_node`), которому принадлежит виджет, с помощью вспомогательной функции поиска по дереву.
        
    2. Автоматически обновить `source_node.form_data[event.widget_id] = event.value`.
        
    3. Инстанциировать (`HandlerClass(context=..., form_data=...)`) и вызвать пользовательский `BasePanelHandler.on_widget_update` в `try...except` блоке.
        
    4. Если обработчик вернул команду навигации, например `("navigate_down", target)`, вызвать `_execute_navigation_down(source_node, event.widget_id, target)`.
        
- **`_execute_navigation_down(source_node, source_widget_id, target)`**:
    
    1. Проверить, есть ли стек для `source_widget_id` в `source_node.children_stacks`. Если да, рекурсивно уничтожить все узлы в этом стеке с помощью `_destroy_stack_recursively`.
        
    2. Создать новый `TreeNode` на основе `target` (который может быть `str` ID или объектом `AbstractPanel`).
        
    3. Создать новый стек: `source_node.children_stacks[source_widget_id] = [new_node]`.
        
    4. Сделать `new_node` активным, сняв флаг `is_active` со `source_node`.
        
    5. Опубликовать `StateChangedEvent`.
        
- **`_handle_vertical_navigation`**:
    
    1. Найти `active_node` и его родителя `parent`. Если их нет, прервать выполнение.
        
    2. Найти стек в `parent.children_stacks`, которому принадлежит `active_node`.
        
    3. Найти индекс `active_node` в стеке.
        
    4. Вычислить новый индекс. Для `direction="up"` это `index + 1`, для `direction="down"` это `index - 1`.
        
    5. Если новый индекс валиден (в пределах границ списка), **переместить узел с нового индекса в конец списка (на вершину стека)**. Это сделает его активным в данной ветке.
        
    6. Сделать новый узел на вершине стека активным (`self.active_node = ...`), сняв флаг со старого.
        
    7. Опубликовать `StateChangedEvent`.
        
- **`_handle_back_navigation`**:
    
    1. Найти `active_node` и его родителя `parent`. Если родителя нет, действие не выполняется.
        
    2. Рекурсивно уничтожить все дочерние стеки самого `active_node` (`_destroy_stack_recursively`).
        
    3. Удалить `active_node` из его стека в `parent.children_stacks`.
        
    4. **Определить новый фокус**:
        
        - Если в стеке остались узлы, верхний из них (последний в списке) становится `active_node`.
            
        - Если стек опустел, `parent` становится `active_node`.
            
    5. Опубликовать `StateChangedEvent`.
        
- **`_handle_horizontal_navigation`**:
    
    1. Получить путь до `active_node` с помощью `_get_path_to_active_node()`. Этот метод строит список узлов, двигаясь от `active_node` вверх по `parent` до корня.
        
    2. Найти индекс `active_node` в этом пути.
        
    3. Вычислить новый индекс (`+1` для `next`, `-1` для `previous`).
        
    4. Если он валиден, сделать узел по новому индексу активным, сняв флаг со старого.
        
    5. Опубликовать `StateChangedEvent`.