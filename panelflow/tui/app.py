"""
Главное приложение TUI на базе Textual.
Связывает panelflow.core с визуальным представлением в терминале.
"""

from textual.app import App
from textual.widgets import Header, Footer

from panelflow.core import Application as CoreApplication
from panelflow.core.events import StateChangedEvent, ErrorOccurredEvent, BaseEvent

from .screens import MainScreen, ErrorScreen


class TuiApplication(App):
    """
    Класс-обертка, который связывает Textual и panelflow.core.
    Является точкой входа для TUI-рендерера.
    """

    CSS = """
    Screen {
        background: $surface;
    }
    
    Header {
        dock: top;
        height: 1;
    }
    
    Footer {
        dock: bottom;
        height: 1;
    }
    """

    def __init__(self, core_app: CoreApplication):
        super().__init__()
        self.core = core_app
        self.main_screen = None
        self.error_screen = None

        # Подписываемся на события от Ядра
        self.core.subscribe_to_events(self._on_core_event)

    def compose(self):
        """Создание базовой структуры приложения."""
        yield Header()
        yield Footer()

    async def on_mount(self) -> None:
        """При монтировании приложения создаем главный экран."""
        self.main_screen = MainScreen(self.core)
        self.error_screen = ErrorScreen()

        # Устанавливаем главный экран как текущий
        await self.push_screen(self.main_screen)

        # Запускаем первоначальный рендеринг
        if self.core.tree_root:
            self._handle_state_change(StateChangedEvent(tree_root=self.core.tree_root))

    def _on_core_event(self, event: BaseEvent) -> None:
        """
        Универсальный обработчик событий от Ядра.
        Маршрутизирует события к соответствующим обработчикам.
        """
        if isinstance(event, StateChangedEvent):
            # Используем call_from_thread для безопасного обновления UI
            self.call_from_thread(self._handle_state_change, event)
        elif isinstance(event, ErrorOccurredEvent):
            self.call_from_thread(self._handle_error, event)

    def _handle_state_change(self, event: StateChangedEvent) -> None:
        """
        Обработчик события изменения состояния от Ядра.
        Запускает перерисовку на главном экране.
        """
        if self.main_screen and hasattr(self.main_screen, 'update_view'):
            self.main_screen.update_view(event.tree_root)

    def _handle_error(self, event: ErrorOccurredEvent) -> None:
        """
        Обработчик события ошибки от Ядра.
        Показывает экран ошибки.
        """
        if self.error_screen:
            self.error_screen.show_error(event.title, event.message)
            # Временно показываем экран ошибки
            self.push_screen(self.error_screen)