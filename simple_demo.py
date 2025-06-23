#!/usr/bin/env python3
"""
Simple Demo of UI Framework
Максимально простой пример UI фреймворка
"""

import curses
from ui_framework import PanelManager, PanelState

# Тестовые данные - список списков
test_data = {
    "Main Menu": [
        "Animals",
        "Colors",
        "Numbers",
        "Fruits"
    ],
    "Animals": [
        "Cat",
        "Dog",
        "Bird",
        "Fish",
        "Elephant"
    ],
    "Colors": [
        "Red",
        "Blue",
        "Green",
        "Yellow",
        "Purple"
    ],
    "Numbers": [
        "One",
        "Two",
        "Three",
        "Four",
        "Five"
    ],
    "Fruits": [
        "Apple",
        "Banana",
        "Orange",
        "Grape",
        "Strawberry"
    ]
}


class SimpleDemo:
    """Простейшее демо приложение"""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.manager = PanelManager(stdscr)

        # Настройка функциональных клавиш
        self.manager.function_keys.set_keys({
            "Enter": "Open",
            "Esc": "Back",
            "F10": "Quit"
        })

        # Открываем главное меню
        self._open_list("Main Menu")

    def _open_list(self, list_name: str):
        """Открытие списка в новой панели"""
        if list_name in test_data:
            content = test_data[list_name]

            state = PanelState(
                title=list_name,
                content=content,
                metadata={'list_name': list_name, 'items': len(content)}
            )

            self.manager.add_panel(state)

    def run(self):
        """Основной цикл"""
        while True:
            # Отрисовка
            self.manager.draw()

            # Получение клавиши
            key = self.stdscr.getch()

            # Выход
            if key == curses.KEY_F10 or key == ord('q'):
                break

            # Enter - открыть выбранный элемент
            elif key == ord('\n') or key == ord('\r'):
                current_panel = self.manager.get_current_panel()
                if current_panel:
                    selected = current_panel.get_selected_item()
                    if selected and selected in test_data:
                        self._open_list(selected)

            # Остальные клавиши обрабатывает менеджер
            else:
                self.manager.handle_key(key)


def main():
    """Запуск демо"""

    def run_demo(stdscr):
        # Настройка
        curses.curs_set(1)
        stdscr.keypad(True)

        # Запуск
        demo = SimpleDemo(stdscr)
        demo.run()

    curses.wrapper(run_demo)


if __name__ == "__main__":
    main()