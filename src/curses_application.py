import curses
import threading
import time
import queue


class CursesConnectorApp:
    def __init__(self):
        self.panel1_content = ["ИСТОЧНИК", "Данные готовы", "Статус: ОК"]
        self.panel2_content = ["ОБРАБОТКА", "Алгоритм: ML", "Прогресс: 75%"]
        self.panel3_content = ["РЕЗУЛЬТАТ", "Выход готов", "Формат: JSON"]
        self.command_queue = queue.Queue()
        self.running = True

    def draw_box(self, win, y, x, height, width, title=""):
        """Рисуем рамку с заголовком"""
        # Углы и линии
        win.addch(y, x, '┌')
        win.addch(y, x + width - 1, '┐')
        win.addch(y + height - 1, x, '└')
        win.addch(y + height - 1, x + width - 1, '┘')

        # Горизонтальные линии
        for i in range(1, width - 1):
            win.addch(y, x + i, '─')
            win.addch(y + height - 1, x + i, '─')

        # Вертикальные линии
        for i in range(1, height - 1):
            win.addch(y + i, x, '│')
            win.addch(y + i, x + width - 1, '│')

        # Заголовок
        if title:
            title_x = x + (width - len(title)) // 2
            win.addstr(y, title_x, title)

    def draw_horizontal_connector(self, win, y, x, width, style="arrows"):
        """Рисуем горизонтальную перемычку"""
        if style == "arrows":
            win.addch(y, x, '◄')
            for i in range(1, width - 1):
                win.addch(y, x + i, '═')
            win.addch(y, x + width - 1, '►')
        elif style == "line":
            for i in range(width):
                win.addch(y, x + i, '─')

    def draw_vertical_connector(self, win, y, x, height, style="arrows"):
        """Рисуем вертикальную перемычку"""
        if style == "arrows":
            win.addch(y, x, '▲')
            for i in range(1, height - 1):
                win.addch(y + i, x, '║')
            win.addch(y + height - 1, x, '▼')
        elif style == "line":
            for i in range(height):
                win.addch(y + i, x, '│')

    def draw_complex_connector(self, win, y, x):
        """Рисуем сложную перемычку"""
        lines = [
            "    ┌─────────┐",
            "    │  DATA   │",
            "◄───┤  FLOW   ├───►",
            "    │  NODE   │",
            "    └─────────┘"
        ]

        for i, line in enumerate(lines):
            if y + i < curses.LINES - 1 and x + len(line) < curses.COLS:
                win.addstr(y + i, x, line)

    def draw_interface(self, stdscr):
        """Рисуем весь интерфейс"""
        stdscr.clear()

        height, width = stdscr.getmaxyx()

        # Размеры панелей
        panel_width = width // 4
        panel_height = 8
        start_y = 3

        # Позиции панелей
        panel1_x = 2
        panel2_x = panel1_x + panel_width + 6
        panel3_x = panel2_x + panel_width + 6

        # Рисуем заголовок
        title = "Система обработки данных - v1.0"
        stdscr.addstr(1, (width - len(title)) // 2, title, curses.A_BOLD)

        # Рисуем панели
        self.draw_box(stdscr, start_y, panel1_x, panel_height, panel_width, "Источник")
        self.draw_box(stdscr, start_y, panel2_x, panel_height, panel_width, "Обработка")
        self.draw_box(stdscr, start_y, panel3_x, panel_height, panel_width, "Результат")

        # Заполняем содержимое панелей
        for i, line in enumerate(self.panel1_content):
            if i < panel_height - 2:
                stdscr.addstr(start_y + i + 1, panel1_x + 2, line[:panel_width - 4])

        for i, line in enumerate(self.panel2_content):
            if i < panel_height - 2:
                stdscr.addstr(start_y + i + 1, panel2_x + 2, line[:panel_width - 4])

        for i, line in enumerate(self.panel3_content):
            if i < panel_height - 2:
                stdscr.addstr(start_y + i + 1, panel3_x + 2, line[:panel_width - 4])

        # Рисуем горизонтальные перемычки между панелями
        conn_y = start_y + panel_height // 2

        # Между панелью 1 и 2
        self.draw_horizontal_connector(stdscr, conn_y, panel1_x + panel_width, 6, "arrows")

        # Между панелью 2 и 3
        self.draw_horizontal_connector(stdscr, conn_y, panel2_x + panel_width, 6, "arrows")

        # Центральная перемычка снизу
        complex_y = start_y + panel_height + 2
        complex_x = (width - 20) // 2
        self.draw_complex_connector(stdscr, complex_y, complex_x)

        # Вертикальные соединители к центральной перемычке
        for panel_x in [panel1_x + panel_width // 2, panel2_x + panel_width // 2, panel3_x + panel_width // 2]:
            self.draw_vertical_connector(stdscr, start_y + panel_height, panel_x, 3, "line")

        # Горизонтальные линии к центральному узлу
        center_y = complex_y + 2
        left_conn_x = panel1_x + panel_width // 2
        right_conn_x = panel3_x + panel_width // 2

        # Левая линия
        for x in range(left_conn_x, complex_x):
            stdscr.addch(center_y, x, '─')

        # Правая линия
        for x in range(complex_x + 17, right_conn_x + 1):
            stdscr.addch(center_y, x, '─')

        # Информация внизу
        info_y = height - 3
        info = "Команды: demo, flow, panel1 текст, exit | Поток: ИСТОЧНИК → ОБРАБОТКА → РЕЗУЛЬТАТ"
        if len(info) < width:
            stdscr.addstr(info_y, (width - len(info)) // 2, info)

        stdscr.refresh()

    def process_command(self, command):
        """Обрабатываем команды"""
        if command.lower() == "exit":
            self.running = False
        elif command.startswith("panel1 "):
            content = command[7:]
            self.panel1_content = [content[:20], "", ""]
        elif command.startswith("panel2 "):
            content = command[7:]
            self.panel2_content = [content[:20], "", ""]
        elif command.startswith("panel3 "):
            content = command[7:]
            self.panel3_content = [content[:20], "", ""]
        elif command.lower() == "demo":
            self.panel1_content = ["🌡️ СЕНСОР", "Temp: 25.6°C", "Status: OK"]
            self.panel2_content = ["⚙️ ПРОЦЕССОР", "AI Model", "Load: 45%"]
            self.panel3_content = ["📊 МОНИТОР", "Trend: ↗️", "Format: JSON"]
        elif command.lower() == "flow":
            self.panel1_content = ["📡 INPUT", "Sensor1: OK", "Sensor2: WARN"]
            self.panel2_content = ["🔄 PROCESS", "Filter: 100%", "Analysis: 78%"]
            self.panel3_content = ["📤 OUTPUT", "DB: ✓", "API: pending"]

    def input_handler(self):
        """Обработчик ввода в отдельном потоке"""
        while self.running:
            try:
                command = input()
                self.command_queue.put(command)
            except (EOFError, KeyboardInterrupt):
                self.running = False
                break

    def main_loop(self, stdscr):
        """Главный цикл приложения"""
        curses.curs_set(0)  # Скрыть курсор
        stdscr.nodelay(1)  # Неблокирующий ввод
        stdscr.timeout(100)  # Таймаут 100ms

        # Запускаем обработчик ввода
        input_thread = threading.Thread(target=self.input_handler, daemon=True)
        input_thread.start()

        while self.running:
            # Обрабатываем команды из очереди
            try:
                while True:
                    command = self.command_queue.get_nowait()
                    self.process_command(command)
            except queue.Empty:
                pass

            # Перерисовываем интерфейс
            self.draw_interface(stdscr)

            # Небольшая пауза
            time.sleep(0.1)

    def run(self):
        """Запуск приложения"""
        print("Система с перемычками (Curses)")
        print("Команды: demo, flow, panel1 текст, exit")
        print("Нажмите Enter после ввода команды\n")

        try:
            curses.wrapper(self.main_loop)
        except KeyboardInterrupt:
            pass

        print("\nПриложение завершено.")


if __name__ == "__main__":
    app = CursesConnectorApp()
    app.run()