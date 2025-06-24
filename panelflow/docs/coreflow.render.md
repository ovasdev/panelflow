# Техническая спецификация: Слой Рендеринга PanelFlow

## 1. Философия и назначение

**Слой Рендеринга (Renderer Layer)** — это платформо-зависимый слой, чья единственная задача — "переводить" абстрактное состояние `panelflow.core` в конкретный пользовательский интерфейс и, наоборот, переводить действия пользователя в абстрактные события для Ядра.

**Философия**: Слой Рендеринга является "глупым". Он не содержит бизнес-логики. Он не решает, _что_ должно произойти после нажатия кнопки. Он лишь знает, _как_ нарисовать кнопку и _как_ сообщить Ядру, что на нее нажали.

### Ключевые обязанности:

1. **Подписка на события Ядра**: При инициализации он подписывается на события от Ядра (в первую очередь, на `StateChangedEvent` и `ErrorOccurredEvent`).
    
2. **Рендеринг состояния**: Получив событие `StateChangedEvent`, он полностью перерисовывает интерфейс в соответствии с новым деревом состояний.
    
3. **Создание событий пользователя**: Он перехватывает низкоуровневые события UI-фреймворка (нажатия клавиш, клики мыши) и преобразует их в высокоуровневые события `panelflow.core` (например, `WidgetSubmittedEvent`, `FocusEvent`).
    
4. **Отправка событий в Ядро**: Он отправляет созданные события в Ядро через единственный метод `core.post_event()`.
    
5. **Управление UI-специфичным состоянием**: Он отвечает за состояние, которое не имеет значения для бизнес-логики, например, точное положение курсора в текстовом поле или анимации перехода.
    

## 2. Пример реализации: TUI Renderer на базе `Textual`

`Textual` — идеальный кандидат для создания консольного рендерера благодаря своей компонентной модели и системе событий.

### 2.1. Структура файлов (`panelflow/tui/`)

```
tui/
├── __init__.py
├── app.py          # Класс TuiApplication - точка входа
├── screens.py      # Главный экран с панелями-слотами
└── widgets/
    ├── __init__.py
    ├── base.py     # Общие миксины для виджетов
    ├── button.py   # Реализация TuiButton
    └── input.py    # Реализация TuiTextInput
```

### 2.2. Главный класс `TuiApplication` (`app.py`)

```
from textual.app import App
from panelflow.core import Application, StateChangedEvent, ErrorOccurredEvent
from .screens import MainScreen

class TuiApplication(App):
    """
    Класс-обертка, который связывает Textual и panelflow.core.
    """
    def __init__(self, core_app: Application):
        super().__init__()
        self.core = core_app

        # 1. Подписываемся на события от Ядра
        self.core.subscribe(StateChangedEvent, self.on_core_state_change)
        self.core.subscribe(ErrorOccurredEvent, self.on_core_error)

    def on_mount(self):
        """При монтировании приложения создаем главный экран."""
        self.main_screen = MainScreen(self.core)
        self.push_screen(self.main_screen)
        
        # Запускаем первоначальный рендеринг
        self.on_core_state_change(StateChangedEvent(tree_root=self.core.root_node))

    def on_core_state_change(self, event: StateChangedEvent):
        """
        Обработчик события от Ядра. Запускает перерисовку на главном экране.
        Выполняется в потоке Textual для безопасности UI.
        """
        self.call_from_thread(self.main_screen.update_view, event.tree_root)

    def on_core_error(self, event: ErrorOccurredEvent):
        """Обработчик события ошибки от Ядра."""
        # Здесь будет логика для отображения специального экрана ошибки
        pass
```

### 2.3. Фабрика виджетов и обработка клавиш (`screens.py`)

Рендерер должен знать, как `AbstractWidget` превратить в конкретный виджет `Textual`. Для этого используется паттерн "Фабрика".

```
from textual.screen import Screen
from textual.widgets import Header, Footer, Static
from textual.binding import Binding
from panelflow.core import events as pfe
# ... импорты конкретных виджетов из .widgets
from panelflow.core import components as pfc

class MainScreen(Screen):
    # Определяем горячие клавиши для Textual
    BINDINGS = [
        Binding("ctrl+r", "quit", "Выход"),
        Binding("ctrl+l", "horizontal_nav('next')", "Панель →", show=False),
        Binding("ctrl+h", "horizontal_nav('previous')", "Панель ←", show=False),
        Binding("ctrl+j", "vertical_nav('down')", "Стек ↓", show=False),
        Binding("ctrl+k", "vertical_nav('up')", "Стек ↑", show=False),
        Binding("backspace", "back_nav", "Назад", show=False),
    ]

    def __init__(self, core_app: Application):
        super().__init__()
        self.core = core_app
        
        # Фабрика, которая сопоставляет абстрактные типы с конкретными
        self.widget_factory = {
            pfc.AbstractButton: TuiButton,
            pfc.AbstractTextInput: TuiTextInput,
            # ... и другие виджеты
        }
    
    def update_view(self, tree_root: pfc.TreeNode):
        # ... (логика очистки и рендеринга панелей)
        pass

    # --- Обработчики действий для BINDINGS ---

    def action_horizontal_nav(self, direction: str):
        self.core.post_event(pfe.HorizontalNavigationEvent(direction=direction))

    def action_vertical_nav(self, direction: str):
        self.core.post_event(pfe.VerticalNavigationEvent(direction=direction))
        
    def action_back_nav(self):
        self.core.post_event(pfe.BackNavigationEvent())
```

### 2.4. Пример конкретного виджета: `TuiButton` (`widgets/button.py`)

```
from textual.widgets import Button
from panelflow.core import events as pfe
from panelflow.core.components import AbstractButton

class TuiButton(Button):
    def __init__(self, abstract_widget: AbstractButton, post_event_callback: callable):
        super().__init__(label=abstract_widget.title, id=abstract_widget.id)
        self.abstract_widget = abstract_widget
        self.post_event = post_event_callback

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """
        Перехватывает событие Textual и преобразует его в событие panelflow.core.
        """
        # Создаем событие, понятное для Ядра
        core_event = pfe.WidgetSubmittedEvent(
            widget_id=self.abstract_widget.id,
            value=self.abstract_widget.value # или любое другое значение
        )
        
        # Отправляем его в Ядро через колбэк
        self.post_event(core_event)
```

## 3. Краткое руководство для других платформ

Этот же подход можно применить к любой другой технологии.

### 3.1. Веб (FastAPI + HTMX/React)

- **Роутер**: `FastAPI` выступает в роли `TuiApplication`, принимая HTTP-запросы.
    
- **Обработчики**: Эндпоинты (например, `@app.post("/submit_widget")`) принимают данные от клиента, создают соответствующее событие (например, `WidgetSubmittedEvent`) и вызывают `core.post_event()`.
    
- **Обновление UI**:
    
    - **HTMX**: Обработчик `StateChangedEvent` рендерит новый HTML-шаблон (Jinja2) и возвращает его в ответе. HTMX на клиенте заменяет часть страницы.
        
    - **React**: Обработчик `StateChangedEvent` возвращает JSON с новым состоянием. React-приложение использует этот JSON для обновления своего состояния и перерисовки компонентов.
        

### 3.2. Десктоп (PyQt/PySide)

- **Сигналы и слоты**: Сигналы от виджетов (например, `QPushButton.clicked`) подключаются к слотам (методам), которые создают событие и вызывают `core.post_event()`.
    
- **Обновление UI**: Обработчик `StateChangedEvent`, подписанный на Ядро, вручную обновляет свойства виджетов (`widget.setText()`, `widget.clear()`, `widget.addItems()`, и т.д.), итерируясь по новому дереву состояний. Важно выполнять эти обновления в главном потоке GUI.
    

Ключевым является сохранение **однонаправленного потока данных** и **четкого разделения ответственности** между Ядром и Рендерером.