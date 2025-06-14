#!/usr/bin/env python3
"""
UI Library for Panel-based Console Applications
Библиотека для создания панельных консольных приложений
"""

import curses
import math
from typing import List, Dict, Optional, Callable, Any
from enum import Enum
from dataclasses import dataclass


class PanelType(Enum):
    DIRECTORY = "directory"
    FILE = "file"
    BINARY = "binary"
    ARCHIVE = "archive"


@dataclass
class PanelState:
    """Состояние панели"""
    title: str
    content: List[str]
    selected_index: int = 0
    scroll_offset: int = 0
    panel_type: PanelType = PanelType.DIRECTORY
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class Panel:
    """Класс для работы с отдельной панелью"""

    def __init__(self, x: int, y: int, width: int, height: int, state: PanelState):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.state = state
        self.window = None

    def create_window(self, stdscr):
        """Создание окна панели"""
        self.window = curses.newwin(self.height, self.width, self.y, self.x)
        self.window.keypad(True)

    def draw(self, is_active: bool = False):
        """Отрисовка панели"""
        if not self.window:
            return

        self.window.clear()  # Вернул clear для надёжности

        # Рамка панели
        border_attr = curses.A_BOLD if is_active else curses.A_NORMAL
        try:
            self.window.box()
        except curses.error:
            pass

        # Заголовок панели
        title = self.state.title[:self.width - 4] if len(self.state.title) > self.width - 4 else self.state.title
        title_x = max(1, (self.width - len(title)) // 2)
        try:
            self.window.addstr(0, title_x, title, border_attr)
        except curses.error:
            pass

        # Содержимое панели
        content_height = self.height - 2
        if content_height <= 0:
            self.window.refresh()
            return

        visible_content = self.state.content[
                          self.state.scroll_offset:self.state.scroll_offset + content_height
                          ]

        for i, line in enumerate(visible_content):
            if i >= content_height:
                break

            y_pos = i + 1
            if y_pos >= self.height - 1:
                break

            # Обрезаем строку по ширине
            display_line = line[:self.width - 2] if len(line) > self.width - 2 else line

            # Выделение текущего элемента
            attr = curses.A_NORMAL
            if (i + self.state.scroll_offset) == self.state.selected_index:
                attr = curses.A_REVERSE if is_active else curses.A_UNDERLINE

            # Простое цветовое выделение (безопасно)
            if curses.has_colors():
                try:
                    if self.state.panel_type == PanelType.DIRECTORY:
                        if line.startswith('📁') or 'DIR' in line:
                            attr |= curses.color_pair(1)  # Синий для папок
                        elif line.startswith('📄'):
                            attr |= curses.color_pair(2)  # Зелёный для файлов
                        elif line.startswith('📦'):
                            attr |= curses.color_pair(3)  # Красный для архивов
                except:
                    pass

            try:
                self.window.addstr(y_pos, 1, display_line, attr)
            except curses.error:
                pass

        # Скроллбар (упрощённый)
        if len(self.state.content) > content_height and content_height > 0:
            try:
                scrollbar_pos = int(self.state.scroll_offset * content_height / len(self.state.content))
                self.window.addstr(scrollbar_pos + 1, self.width - 1, '█')
            except (curses.error, ZeroDivisionError):
                pass

        self.window.refresh()

    def _draw_scrollbar(self, content_height: int):
        """Отрисовка скроллбара"""
        total_items = len(self.state.content)
        if total_items <= content_height:
            return

        scrollbar_height = max(1, content_height * content_height // total_items)
        scrollbar_pos = self.state.scroll_offset * content_height // total_items

        for i in range(content_height):
            char = '│'
            if scrollbar_pos <= i < scrollbar_pos + scrollbar_height:
                char = '█'
            try:
                self.window.addstr(i + 1, self.width - 1, char)
            except curses.error:
                pass

    def move_selection(self, delta: int):
        """Перемещение выделения"""
        old_index = self.state.selected_index
        self.state.selected_index = max(0, min(len(self.state.content) - 1,
                                               self.state.selected_index + delta))

        # Обновление прокрутки
        content_height = self.height - 2
        if self.state.selected_index < self.state.scroll_offset:
            self.state.scroll_offset = self.state.selected_index
        elif self.state.selected_index >= self.state.scroll_offset + content_height:
            self.state.scroll_offset = self.state.selected_index - content_height + 1

        return old_index != self.state.selected_index

    def get_selected_item(self) -> Optional[str]:
        """Получение выделенного элемента"""
        if 0 <= self.state.selected_index < len(self.state.content):
            return self.state.content[self.state.selected_index]
        return None


class StatusBar:
    """Статусная строка"""

    def __init__(self, y: int, width: int):
        self.y = y
        self.width = width
        self.window = None

    def create_window(self, stdscr):
        """Создание окна статусной строки"""
        self.window = curses.newwin(1, self.width, self.y, 0)

    def draw(self, left_panels: int, current_title: str, right_panels: int,
             extra_info: str = ""):
        """Отрисовка статусной строки"""
        if not self.window:
            return

        self.window.clear()

        # Упрощённая строка статуса
        if current_title:
            status_text = f"[{left_panels}] {current_title} [{right_panels}]"
            if extra_info:
                status_text += f" - {extra_info}"
        else:
            status_text = "File Manager"

        # Обрезаем по ширине
        if len(status_text) > self.width:
            status_text = status_text[:self.width - 3] + "..."

        try:
            self.window.addstr(0, 0, status_text, curses.A_REVERSE)
        except curses.error:
            pass

        self.window.refresh()


class CommandLine:
    """Командная строка"""

    def __init__(self, y: int, width: int):
        self.y = y
        self.width = width
        self.window = None
        self.prompt = "Command: "
        self.text = ""
        self.cursor_pos = 0

    def create_window(self, stdscr):
        """Создание окна командной строки"""
        self.window = curses.newwin(1, self.width, self.y, 0)

    def draw(self):
        """Отрисовка командной строки"""
        if not self.window:
            return

        self.window.clear()

        display_text = self.prompt + self.text
        if len(display_text) > self.width:
            # Обрезаем текст если он не помещается
            start_pos = max(0, len(display_text) - self.width + 1)
            display_text = display_text[start_pos:]

        try:
            self.window.addstr(0, 0, display_text)
            # Позиционируем курсор
            cursor_x = min(len(self.prompt) + self.cursor_pos, self.width - 1)
            self.window.move(0, cursor_x)
        except curses.error:
            pass

        self.window.refresh()

    def handle_key(self, key: int) -> Optional[str]:
        """Обработка нажатий клавиш"""
        if key == curses.KEY_BACKSPACE or key == 127 or key == 8:
            if self.cursor_pos > 0:
                self.text = self.text[:self.cursor_pos - 1] + self.text[self.cursor_pos:]
                self.cursor_pos -= 1
        elif key == curses.KEY_DC:  # Delete
            if self.cursor_pos < len(self.text):
                self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
        elif key == curses.KEY_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
        elif key == curses.KEY_RIGHT:
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
        elif key == curses.KEY_HOME:
            self.cursor_pos = 0
        elif key == curses.KEY_END:
            self.cursor_pos = len(self.text)
        elif key == ord('\n') or key == ord('\r'):
            # Enter - возвращаем команду
            command = self.text
            self.clear()
            return command
        elif 32 <= key <= 126:  # Печатаемые символы
            self.text = self.text[:self.cursor_pos] + chr(key) + self.text[self.cursor_pos:]
            self.cursor_pos += 1

        return None

    def clear(self):
        """Очистка командной строки"""
        self.text = ""
        self.cursor_pos = 0


class FunctionKeys:
    """Строка функциональных клавиш"""

    def __init__(self, y: int, width: int):
        self.y = y
        self.width = width
        self.window = None
        self.keys = {}

    def create_window(self, stdscr):
        """Создание окна функциональных клавиш"""
        self.window = curses.newwin(1, self.width, self.y, 0)

    def set_keys(self, keys: Dict[str, str]):
        """Установка функциональных клавиш"""
        self.keys = keys

    def draw(self):
        """Отрисовка функциональных клавиш"""
        if not self.window:
            return

        self.window.clear()

        # Формирование строки функциональных клавиш
        key_strings = []
        for key, action in self.keys.items():
            key_strings.append(f"{key}:{action}")

        keys_line = " ".join(key_strings)
        if len(keys_line) > self.width:
            keys_line = keys_line[:self.width - 3] + "..."

        try:
            self.window.addstr(0, 0, keys_line, curses.A_REVERSE)
        except curses.error:
            pass

        self.window.refresh()


class PanelManager:
    """Менеджер панелей"""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.panels: List[Panel] = []
        self.current_panel_index = 0
        self.branches: Dict[str, List[PanelState]] = {}

        # Инициализация цветов (безопасно)
        if curses.has_colors():
            curses.start_color()
            try:
                curses.use_default_colors()
                curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)  # Папки
                curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)  # Файлы
                curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)  # Архивы
                curses.init_pair(4, curses.COLOR_YELLOW, curses.COLOR_BLACK)  # Изображения
            except:
                # Если цвета не поддерживаются, используем обычные атрибуты
                pass

        # Размеры экрана
        self.height, self.width = stdscr.getmaxyx()

        # Создание компонентов UI
        self.status_bar = StatusBar(0, self.width)
        self.status_bar.create_window(stdscr)

        self.command_line = CommandLine(self.height - 2, self.width)
        self.command_line.create_window(stdscr)

        self.function_keys = FunctionKeys(self.height - 1, self.width)
        self.function_keys.create_window(stdscr)

        # Обработчики команд
        self.command_handlers: Dict[str, Callable] = {}

    def add_panel(self, state: PanelState) -> int:
        """Добавление новой панели"""
        # Удаляем все панели справа от текущей
        if self.panels:
            self.panels = self.panels[:self.current_panel_index + 1]

        # Вычисляем размеры и позицию новой панели
        panel_count = len(self.panels) + 1
        content_height = self.height - 4  # Статус + командная строка + функц. клавиши + отступ
        content_width = self.width

        if panel_count <= 3:
            panel_width = content_width // 3
            panel_height = content_height
            panel_x = len(self.panels) * panel_width
            panel_y = 1
        else:
            # Для большего количества панелей делаем прокрутку
            panel_width = content_width // 3
            panel_height = content_height
            panel_x = 2 * panel_width  # Показываем только последние 3 панели
            panel_y = 1

        panel = Panel(panel_x, panel_y, panel_width, panel_height, state)
        panel.create_window(self.stdscr)

        self.panels.append(panel)
        self.current_panel_index = len(self.panels) - 1

        # Пересчитываем позиции всех панелей
        self._recalculate_panel_positions()

        return len(self.panels) - 1

    def remove_panel(self, index: int = None):
        """Удаление панели и всех справа от неё"""
        if index is None:
            index = self.current_panel_index

        if 0 <= index < len(self.panels):
            # Удаляем панель и все справа
            self.panels = self.panels[:index]

            # Корректируем текущий индекс
            if self.panels:
                self.current_panel_index = len(self.panels) - 1
            else:
                self.current_panel_index = 0

            self._recalculate_panel_positions()

    def _recalculate_panel_positions(self):
        """Пересчёт позиций панелей"""
        if not self.panels:
            return

        content_height = self.height - 4
        content_width = self.width

        visible_panels = min(3, len(self.panels))
        panel_width = content_width // 3

        # Определяем какие панели показывать
        if len(self.panels) <= 3:
            start_index = 0
        else:
            # Показываем текущую панель и соседние
            start_index = max(0, self.current_panel_index - 2)
            start_index = min(start_index, len(self.panels) - 3)

        for i, panel in enumerate(self.panels):
            display_index = i - start_index
            if 0 <= display_index < 3:
                panel.x = display_index * panel_width
                panel.y = 1
                panel.width = panel_width
                panel.height = content_height

                # Пересоздаём окно с новыми размерами
                if panel.window:
                    del panel.window
                panel.create_window(self.stdscr)

    def switch_panel(self, direction: int):
        """Переключение между панелями"""
        if not self.panels:
            return

        new_index = self.current_panel_index + direction
        if 0 <= new_index < len(self.panels):
            self.current_panel_index = new_index
            self._recalculate_panel_positions()

    def get_current_panel(self) -> Optional[Panel]:
        """Получение текущей панели"""
        if 0 <= self.current_panel_index < len(self.panels):
            return self.panels[self.current_panel_index]
        return None

    def save_branch(self, name: str):
        """Сохранение текущей ветки панелей"""
        states = [panel.state for panel in self.panels]
        self.branches[name] = states

    def load_branch(self, name: str):
        """Загрузка сохранённой ветки"""
        if name in self.branches:
            self.panels.clear()
            for state in self.branches[name]:
                self.add_panel(state)
            self.current_panel_index = len(self.panels) - 1

    def draw(self):
        """Отрисовка всех компонентов"""
        # Очищаем главное окно
        self.stdscr.clear()

        # Отрисовка панелей
        visible_start = 0
        if len(self.panels) > 3:
            visible_start = max(0, self.current_panel_index - 2)
            visible_start = min(visible_start, len(self.panels) - 3)

        for i, panel in enumerate(self.panels):
            display_index = i - visible_start
            if 0 <= display_index < 3:
                is_active = (i == self.current_panel_index)
                panel.draw(is_active)

        # Отрисовка статусной строки
        current_title = "File Manager"
        extra_info = ""
        if self.panels:
            current_panel = self.get_current_panel()
            if current_panel:
                current_title = current_panel.state.title
                if current_panel.state.metadata:
                    meta = current_panel.state.metadata
                    if 'items' in meta:
                        extra_info = f"{meta.get('items', 0)} items"

        self.status_bar.draw(
            self.current_panel_index,
            current_title,
            max(0, len(self.panels) - self.current_panel_index - 1),
            extra_info
        )

        # Отрисовка командной строки и функциональных клавиш
        self.command_line.draw()
        self.function_keys.draw()

        # Обновляем главное окно
        self.stdscr.refresh()

    def handle_key(self, key: int) -> Optional[str]:
        """Обработка нажатий клавиш"""
        # Обработка в командной строке
        command = self.command_line.handle_key(key)
        if command:
            return command

        # Обработка навигации по панелям
        current_panel = self.get_current_panel()
        if current_panel:
            if key == curses.KEY_UP:
                current_panel.move_selection(-1)
            elif key == curses.KEY_DOWN:
                current_panel.move_selection(1)
            elif key == curses.KEY_PPAGE:  # Page Up
                current_panel.move_selection(-10)
            elif key == curses.KEY_NPAGE:  # Page Down
                current_panel.move_selection(10)
            elif key == curses.KEY_HOME:
                current_panel.state.selected_index = 0
                current_panel.state.scroll_offset = 0
            elif key == curses.KEY_END:
                current_panel.state.selected_index = len(current_panel.state.content) - 1
                content_height = current_panel.height - 2
                current_panel.state.scroll_offset = max(0, len(current_panel.state.content) - content_height)

        # Переключение между панелями
        if key == ord('\t'):  # Tab
            self.switch_panel(1)
        elif key == curses.KEY_BTAB:  # Shift+Tab
            self.switch_panel(-1)
        elif key == 27:  # Escape
            self.remove_panel()

        return None

    def register_command_handler(self, command: str, handler: Callable):
        """Регистрация обработчика команды"""
        self.command_handlers[command] = handler

    def execute_command(self, command: str):
        """Выполнение команды"""
        parts = command.split()
        if not parts:
            return

        cmd = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        if cmd in self.command_handlers:
            self.command_handlers[cmd](args)