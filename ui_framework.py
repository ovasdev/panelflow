#!/usr/bin/env python3
"""
Clean UI Framework for Panel-based Console Applications
Чистый UI фреймворк для панельных консольных приложений
"""

import curses
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, field


@dataclass
class PanelState:
    """Состояние панели (данные)"""
    title: str
    content: List[str]
    selected_index: int = 0
    scroll_offset: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Panel:
    """Класс для работы с отдельной панелью (отображение)"""

    def __init__(self, state: PanelState):
        self.state = state
        self.window: Optional[curses.window] = None

    def resize(self, x: int, y: int, width: int, height: int, stdscr):
        """Создание или изменение размера окна панели."""
        try:
            if width > 0 and height > 0:
                self.window = curses.newwin(height, width, y, x)
                self.window.keypad(True)
            else:
                self.window = None
        except curses.error:
            self.window = None

    def draw(self, is_active: bool = False):
        """Отрисовка панели в буфер (без обновления экрана)."""
        if not self.window:
            return

        try:
            self.window.erase()
            self.window.box()

            # Заголовок
            title = f" {self.state.title} "[:self.window.getmaxyx()[1] - 2]
            title_x = max(1, (self.window.getmaxyx()[1] - len(title)) // 2)
            attr = curses.A_REVERSE if is_active else curses.A_BOLD
            self.window.addstr(0, title_x, title, attr)

            # Содержимое
            height, width = self.window.getmaxyx()
            content_height = height - 2
            for i in range(content_height):
                line_index = self.state.scroll_offset + i
                if line_index >= len(self.state.content):
                    break

                line = self.state.content[line_index]
                display_line = line.ljust(width - 2)
                display_line = display_line[:width - 2]

                attr = curses.A_REVERSE if is_active and line_index == self.state.selected_index else curses.A_NORMAL
                if not is_active and line_index == self.state.selected_index:
                    attr = curses.A_UNDERLINE

                self.window.addstr(i + 1, 1, display_line, attr)

            self.window.noutrefresh()
        except curses.error:
            pass

    def move_selection(self, delta: int):
        """Перемещение выделения в панели."""
        if not self.state.content: return

        new_index = self.state.selected_index + delta
        self.state.selected_index = max(0, min(len(self.state.content) - 1, new_index))

        content_height = self.window.getmaxyx()[0] - 2 if self.window else 0
        if content_height > 0:
            if self.state.selected_index < self.state.scroll_offset:
                self.state.scroll_offset = self.state.selected_index
            elif self.state.selected_index >= self.state.scroll_offset + content_height:
                self.state.scroll_offset = self.state.selected_index - content_height + 1

    def get_selected_item(self) -> Optional[str]:
        """Получение выделенного элемента."""
        if 0 <= self.state.selected_index < len(self.state.content):
            return self.state.content[self.state.selected_index]
        return None


class StatusBar:
    """Статусная строка"""

    def __init__(self, y: int, width: int):
        self.window: Optional[curses.window] = None
        self.resize(y, width)

    def resize(self, y: int, width: int):
        try:
            self.window = curses.newwin(1, width, y, 0)
        except curses.error:
            self.window = None

    def draw(self, left_count: int, current_title: str, right_count: int, extra_info: str = ""):
        if not self.window: return
        try:
            self.window.erase()
            left_str = f"[{left_count}]" if left_count > 0 else ""
            right_str = f"[{right_count}]" if right_count > 0 else ""

            status_text = f"{left_str} {current_title} {right_str}".strip()
            if extra_info:
                status_text += f" | {extra_info}"

            self.window.addstr(0, 0, status_text.ljust(self.window.getmaxyx()[1]), curses.A_REVERSE)
            self.window.noutrefresh()
        except curses.error:
            pass


class CommandLine:
    """Командная строка"""

    def __init__(self, y: int, width: int):
        self.prompt = ": "
        self.text = ""
        self.cursor_pos = 0
        self.is_active = False
        self.window: Optional[curses.window] = None
        self.resize(y, width)

    def resize(self, y: int, width: int):
        try:
            self.window = curses.newwin(1, width, y, 0)
        except curses.error:
            self.window = None

    def draw(self):
        if not self.window: return
        try:
            self.window.erase()
            self.window.addstr(0, 0, self.prompt + self.text)
            if self.is_active:
                self.window.move(0, len(self.prompt) + self.cursor_pos)
            self.window.noutrefresh()
        except curses.error:
            pass

    def handle_key(self, key: int) -> Optional[str]:
        if key in (curses.KEY_BACKSPACE, 127, 8):
            if self.cursor_pos > 0: self.text = self.text[:self.cursor_pos - 1] + self.text[
                                                                                  self.cursor_pos:]; self.cursor_pos -= 1
        elif key == curses.KEY_DC:
            self.text = self.text[:self.cursor_pos] + self.text[self.cursor_pos + 1:]
        elif key == curses.KEY_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
        elif key == curses.KEY_RIGHT:
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
        elif key == curses.KEY_HOME:
            self.cursor_pos = 0
        elif key == curses.KEY_END:
            self.cursor_pos = len(self.text)
        elif key in (ord('\n'), ord('\r')):
            command = self.text; self.clear(); return command
        elif isinstance(key, int) and 32 <= key < 256:
            self.text = self.text[:self.cursor_pos] + chr(key) + self.text[self.cursor_pos:]; self.cursor_pos += 1
        return None

    def clear(self):
        self.text = ""; self.cursor_pos = 0; self.is_active = False


class FunctionKeys:
    """Строка функциональных клавиш"""

    def __init__(self, y: int, width: int):
        self.keys: Dict[str, str] = {}
        self.window: Optional[curses.window] = None
        self.resize(y, width)

    def resize(self, y: int, width: int):
        try:
            self.window = curses.newwin(1, width, y, 0)
        except curses.error:
            self.window = None

    def set_keys(self, keys: Dict[str, str]):
        self.keys = keys.copy()

    def draw(self):
        if not self.window: return
        try:
            self.window.erase()
            key_strings = [f"{key}:{action}" for key, action in self.keys.items()]
            keys_line = " ".join(key_strings)
            self.window.addstr(0, 0, keys_line.ljust(self.window.getmaxyx()[1]), curses.A_REVERSE)
            self.window.noutrefresh()
        except curses.error:
            pass


class PanelManager:
    """Менеджер панелей"""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.panels: List[Panel] = []
        self.current_panel_index = 0
        self.is_command_mode = False
        self.height, self.width = stdscr.getmaxyx()

        self.status_bar = StatusBar(0, self.width)
        self.command_line = CommandLine(self.height - 2, self.width)
        self.function_keys = FunctionKeys(self.height - 1, self.width)
        self.command_handlers: Dict[str, Callable] = {}

        if curses.has_colors():
            try:
                curses.start_color(); curses.use_default_colors()
            except:
                pass

    def add_panel(self, state: PanelState, switch_to: bool = True):
        self.panels = self.panels[:self.current_panel_index + 1]
        self.panels.append(Panel(state))
        if switch_to: self.current_panel_index = len(self.panels) - 1
        self._recalculate_layout()

    def remove_panel(self, index: int = None):
        if index is None: index = self.current_panel_index
        if 0 < index < len(self.panels):
            self.panels = self.panels[:index]
            self.current_panel_index = len(self.panels) - 1
            self._recalculate_layout()

    def _recalculate_layout(self):
        """ИСПРАВЛЕНО: Пересчитывает макет, размещая до 3 панелей по 1/3 экрана."""
        panel_width = self.width // 3
        content_height = self.height - 3

        # Определяем первую видимую панель, чтобы активная была в центре (если возможно)
        start_index = max(0, min(self.current_panel_index - 1, len(self.panels) - 3))
        if len(self.panels) < 3:
            start_index = 0

        for i, panel in enumerate(self.panels):
            # Проверяем, находится ли панель в видимом срезе
            if start_index <= i < start_index + 3:
                pos = i - start_index
                x = pos * panel_width

                # Ширина каждой панели - строго треть экрана.
                w = panel_width

                # Третья видимая панель занимает всё оставшееся место,
                # чтобы избежать щели из-за округления при делении.
                if pos == 2:
                    w = self.width - (panel_width * 2)

                panel.resize(x, 1, w, content_height, self.stdscr)
            else:
                # Скрываем панели, которые не должны быть видны
                panel.resize(0, 0, 0, 0, self.stdscr)

    def switch_panel(self, direction: int):
        """Переключение между панелями."""
        if not self.panels: return
        new_index = self.current_panel_index + direction
        if 0 <= new_index < len(self.panels):
            self.current_panel_index = new_index
            self._recalculate_layout()

    def get_current_panel(self) -> Optional[Panel]:
        return self.panels[self.current_panel_index] if 0 <= self.current_panel_index < len(self.panels) else None

    def handle_resize(self):
        """Обработка изменения размера терминала."""
        self.height, self.width = self.stdscr.getmaxyx()
        curses.resizeterm(self.height, self.width)
        self.status_bar.resize(0, self.width)
        self.command_line.resize(self.height - 2, self.width)
        self.function_keys.resize(self.height - 1, self.width)
        self._recalculate_layout()
        self.stdscr.erase()

    def draw(self):
        """Отрисовывает все видимые компоненты и обновляет экран."""
        try:
            curses.curs_set(1 if self.is_command_mode else 0)
            self.command_line.is_active = self.is_command_mode

            for i, panel in enumerate(self.panels):
                panel.draw(is_active=(i == self.current_panel_index))

            current_panel = self.get_current_panel()
            if current_panel:
                left = self.current_panel_index
                right = len(self.panels) - 1 - self.current_panel_index
                self.status_bar.draw(left, current_panel.state.title, right,
                                     current_panel.state.metadata.get('info', ''))
            else:
                self.status_bar.draw(0, "No panels", 0)

            self.command_line.draw()
            self.function_keys.draw()
            curses.doupdate()  # Обновляем физический экран один раз
        except curses.error:
            pass

    def handle_key(self, key: int):
        """ИСПРАВЛЕНО: Обработка нажатий клавиш."""
        if self.is_command_mode:
            command = self.command_line.handle_key(key)
            if command is not None:
                self.execute_command(command); self.is_command_mode = False
            elif key == 27:
                self.is_command_mode = False; self.command_line.clear()
            return

        # ДОБАВЛЕНО: Переключение по Tab / Shift+Tab
        if key == ord('\t'):
            self.switch_panel(1)
            return
        elif key == curses.KEY_BTAB:  # Shift+Tab
            self.switch_panel(-1)
            return

        # Коды для Ctrl + Стрелка
        if key == 560: self.switch_panel(1); return
        if key == 545: self.switch_panel(-1); return

        current_panel = self.get_current_panel()
        if not current_panel: return

        if key == curses.KEY_UP:
            current_panel.move_selection(-1)
        elif key == curses.KEY_DOWN:
            current_panel.move_selection(1)
        elif key == curses.KEY_PPAGE:
            current_panel.move_selection(-(current_panel.window.getmaxyx()[0] - 2))
        elif key == curses.KEY_NPAGE:
            current_panel.move_selection(current_panel.window.getmaxyx()[0] - 2)
        elif key == curses.KEY_HOME:
            current_panel.state.selected_index = 0; current_panel.state.scroll_offset = 0
        elif key == curses.KEY_END:
            if current_panel.state.content:
                current_panel.state.selected_index = len(current_panel.state.content) - 1
                content_height = current_panel.window.getmaxyx()[0] - 2 if current_panel.window else 0
                current_panel.state.scroll_offset = max(0, len(current_panel.state.content) - content_height)
        elif key == 27:
            self.remove_panel()  # Escape
        elif key == ord(':'):
            self.is_command_mode = True; self.command_line.clear()

    def register_command_handler(self, command: str, handler: Callable):
        self.command_handlers[command] = handler

    def execute_command(self, command_string: str):
        if not command_string: return
        parts = command_string.split();
        cmd, args = parts[0], parts[1:]
        if cmd in self.command_handlers:
            try:
                self.command_handlers[cmd](args)
            except Exception:
                pass


def demo():
    """Демонстрация работы фреймворка."""

    def run_demo(stdscr):
        stdscr.keypad(True)
        stdscr.timeout(100)  # Неблокирующий ввод

        manager = PanelManager(stdscr)
        for i in range(1, 8):
            content = [f"Item {j} in Panel {i}" for j in range(20 + i * 5)]
            state = PanelState(f"Panel {i}", content, metadata={'info': f'{len(content)} items'})
            manager.add_panel(state, switch_to=False)
        manager.current_panel_index = 1
        manager._recalculate_layout()

        # ИСПРАВЛЕНО: Обновлена подсказка по клавишам
        manager.function_keys.set_keys({"F10": "Quit", ":": "Cmd", "Tab/^Arrows": "Panels"})

        def quit_handler(args):
            raise SystemExit()

        manager.register_command_handler('q', quit_handler)
        manager.register_command_handler('quit', quit_handler)

        while True:
            try:
                manager.draw()
                key = stdscr.getch()
                if key == -1: continue
                if key == curses.KEY_F10: break
                if key == curses.KEY_RESIZE: manager.handle_resize(); continue
                manager.handle_key(key)
            except SystemExit:
                break
            except curses.error:
                manager.handle_resize()

    curses.wrapper(run_demo)


if __name__ == "__main__":
    demo()
