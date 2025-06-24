"""
Главное приложение TUI на базе Textual.
Связывает panelflow.core с визуальным представлением в терминале.
"""

import logging
from textual.app import App
from textual.widgets import Header, Footer

from panelflow.core import Application as CoreApplication
from panelflow.core.events import StateChangedEvent, ErrorOccurredEvent, BaseEvent
from panelflow.logging_config import get_logger

from .screens import MainScreen, ErrorScreen

# Инициализируем логгер для TUI
logger = get_logger(__name__)


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

        logger.info("Инициализация TuiApplication")
        logger.debug(f"Ядро приложения: {type(core_app).__name__}")

        # Подписываемся на события от Ядра
        self.core.subscribe_to_events(self._on_core_event)
        logger.debug("Подписка на события ядра выполнена")

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
        logger.info(f"========== ПОЛУЧЕНО СОБЫТИЕ ОТ ЯДРА ==========")
        logger.info(f"Тип события: {type(event).__name__}")

        if isinstance(event, StateChangedEvent):
            logger.info("Это StateChangedEvent - планируем обработку")
            logger.debug(f"tree_root в событии: {event.tree_root}")

            try:
                # Сначала попробуем прямой вызов для диагностики
                logger.debug("ПОПЫТКА ПРЯМОГО ВЫЗОВА _handle_state_change")
                self._handle_state_change(event)
                logger.debug("Прямой вызов выполнен")

                # Затем используем call_from_thread для безопасного обновления UI
                logger.debug("Вызов call_from_thread для _handle_state_change")
                self.call_from_thread(self._handle_state_change_safe, event)
                logger.debug("call_from_thread выполнен без ошибок")
            except Exception as e:
                logger.error(f"ОШИБКА в обработке StateChangedEvent: {e}", exc_info=True)

        elif isinstance(event, ErrorOccurredEvent):
            logger.warning(f"Получено ErrorOccurredEvent: {event.title}")
            try:
                self.call_from_thread(self._handle_error, event)
            except Exception as e:
                logger.error(f"ОШИБКА в call_from_thread для ошибки: {e}", exc_info=True)
        else:
            logger.debug(f"Неизвестное событие от ядра: {type(event).__name__}")

        logger.info("========== КОНЕЦ ОБРАБОТКИ СОБЫТИЯ ==========")

    def _handle_state_change_safe(self, event: StateChangedEvent) -> None:
        """
        Безопасная версия обработчика состояния для call_from_thread.
        """
        logger.info("ВЫЗОВ _handle_state_change_safe из потока UI")
        try:
            self._handle_state_change(event)
        except Exception as e:
            logger.error(f"ОШИБКА в _handle_state_change_safe: {e}", exc_info=True)

    def _handle_state_change(self, event: StateChangedEvent) -> None:
        """
        Обработчик события изменения состояния от Ядра.
        Запускает перерисовку на главном экране.
        """
        logger.info("========================================")
        logger.info("ОБРАБОТКА StateChangedEvent")
        logger.debug(f"main_screen существует: {self.main_screen is not None}")

        if self.main_screen:
            logger.debug(f"Тип main_screen: {type(self.main_screen).__name__}")
            logger.debug(f"Есть ли метод update_view: {hasattr(self.main_screen, 'update_view')}")

            if hasattr(self.main_screen, 'update_view'):
                try:
                    logger.info("Вызов update_view на MainScreen")
                    logger.debug(f"tree_root: {event.tree_root}")
                    logger.debug(f"tree_root.panel_template.title: {event.tree_root.panel_template.title if event.tree_root else 'None'}")

                    self.main_screen.update_view(event.tree_root)
                    logger.info("update_view завершен успешно")

                except Exception as e:
                    logger.error(f"ОШИБКА в update_view: {e}", exc_info=True)
            else:
                logger.error("MainScreen не имеет метода update_view!")
        else:
            logger.error("MainScreen не существует!")

        logger.info("КОНЕЦ ОБРАБОТКИ StateChangedEvent")
        logger.info("========================================")

    def _handle_error(self, event: ErrorOccurredEvent) -> None:
        """
        Обработчик события ошибки от Ядра.
        Показывает экран ошибки.
        """
        logger.error(f"Обработка ошибки: {event.title} - {event.message}")
        if self.error_screen:
            self.error_screen.show_error(event.title, event.message)
            # Временно показываем экран ошибки
            self.push_screen(self.error_screen)
            logger.debug("Экран ошибки отображен")
        else:
            logger.error("ErrorScreen недоступен для отображения ошибки")