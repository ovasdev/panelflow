from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Input
from textual import events


class ThreePanelApp(App):
    """Приложение с навигацией между панелями и элементами внутри панелей"""

    CSS = """
    Screen {
        layout: vertical;
    }

    #header {
        height: 1;
        background: green;
        color: white;
        text-align: center;
        margin-bottom: 1;
    }

    #main {
        layout: horizontal;
        height: 1fr;
    }

    .panel {
        width: 1fr;
        border: solid white;
        padding: 1;
    }

    .panel-active {
        width: 1fr;
        border: solid green;
        background: darkgreen 10%;
        padding: 1;
    }

    #input-container {
        height: 3;
        margin-top: 1;
    }

    Input {
        margin: 1;
    }
    """

    def __init__(self):
        super().__init__()
        self.input_history = []
        self.active_panel = 0  # 0, 1, 2 для панелей 1, 2, 3
        self.active_element = [0, 0, 0]  # Активный элемент для каждой панели
        self.panel_elements = [
            ["Добро пожаловать!", "Используйте стрелки для навигации", "Ctrl+стрелки для смены панелей"],
            ["Элемент 1 панели 2", "Элемент 2 панели 2"],
            ["Элемент 1 панели 3", "Элемент 2 панели 3", "Элемент 3 панели 3"]
        ]

    def compose(self) -> ComposeResult:
        """Создаем интерфейс"""
        yield Static("Навигация: Ctrl+стрелки (панели) | ↑↓←→ (элементы)", id="header")

        with Horizontal(id="main"):
            yield Static("", classes="panel-active", id="panel1")
            yield Static("", classes="panel", id="panel2")
            yield Static("", classes="panel", id="panel3")

        yield Input(placeholder="Введите текст - он добавится как новый элемент...", id="command-input")

    def on_key(self, event: events.Key) -> None:
        """Обрабатываем нажатия клавиш"""
        if event.key == "ctrl+right":
            # Переход к следующей панели
            if self.active_panel < 2:
                self.active_panel += 1
                self.update_display()
                event.prevent_default()
        elif event.key == "ctrl+left":
            # Переход к предыдущей панели
            if self.active_panel > 0:
                self.active_panel -= 1
                self.update_display()
                event.prevent_default()
        elif event.key == "down" or event.key == "right":
            # Следующий элемент в активной панели
            max_elements = len(self.panel_elements[self.active_panel])
            if max_elements > 0 and self.active_element[self.active_panel] < max_elements - 1:
                self.active_element[self.active_panel] += 1
                self.update_display()
                event.prevent_default()
        elif event.key == "up" or event.key == "left":
            # Предыдущий элемент в активной панели
            if self.active_element[self.active_panel] > 0:
                self.active_element[self.active_panel] -= 1
                self.update_display()
                event.prevent_default()

    def update_display(self):
        """Обновляем отображение всех панелей"""
        for i in range(3):
            panel = self.query_one(f"#panel{i + 1}", Static)

            # Устанавливаем стиль активной/неактивной панели
            if i == self.active_panel:
                panel.remove_class("panel")
                panel.add_class("panel-active")
                panel_title = f"ПАНЕЛЬ {i + 1} (АКТИВНА)"
            else:
                panel.remove_class("panel-active")
                panel.add_class("panel")
                panel_title = f"ПАНЕЛЬ {i + 1}"

            # Формируем содержимое панели
            content_lines = [panel_title, ""]

            if not self.panel_elements[i]:
                content_lines.append("Нет элементов")
            else:
                for j, element in enumerate(self.panel_elements[i]):
                    if i == self.active_panel and j == self.active_element[i]:
                        # Выделяем активный элемент
                        content_lines.append(f"[reverse]► {element}[/reverse]")
                    else:
                        content_lines.append(f"► {element}")

            # Добавляем информацию о навигации для активной панели
            if i == self.active_panel:
                content_lines.extend([
                    "",
                    f"Элемент {self.active_element[i] + 1} из {len(self.panel_elements[i])}",
                    "↑↓ - навигация по элементам"
                ])

            panel.update("\n".join(content_lines))

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Обрабатываем ввод команды"""
        user_input = event.value.strip()

        if not user_input:
            return

        # Обрабатываем специальные команды
        if user_input.lower() == "exit":
            self.exit()
            return
        elif user_input.lower() == "clear":
            self.clear_active_panel()
        elif user_input.lower() == "delete":
            self.delete_active_element()
        elif user_input.lower() == "help":
            self.show_help()
        elif user_input.lower() == "reset":
            self.reset_all_panels()
        elif user_input.startswith("edit "):
            # Редактируем текущий элемент
            new_text = user_input[5:]
            self.edit_active_element(new_text)
        else:
            # Добавляем новый элемент
            self.add_element_to_active_panel(user_input)

        # Очищаем поле ввода
        event.input.value = ""

    def add_element_to_active_panel(self, text):
        """Добавляем новый элемент к активной панели"""
        self.panel_elements[self.active_panel].append(text)
        # Переходим к новому элементу
        self.active_element[self.active_panel] = len(self.panel_elements[self.active_panel]) - 1
        self.update_display()

    def edit_active_element(self, new_text):
        """Редактируем активный элемент"""
        if self.panel_elements[self.active_panel]:
            self.panel_elements[self.active_panel][self.active_element[self.active_panel]] = new_text
            self.update_display()

    def delete_active_element(self):
        """Удаляем активный элемент"""
        if self.panel_elements[self.active_panel]:
            del self.panel_elements[self.active_panel][self.active_element[self.active_panel]]
            # Корректируем позицию активного элемента
            if self.active_element[self.active_panel] >= len(self.panel_elements[self.active_panel]):
                self.active_element[self.active_panel] = max(0, len(self.panel_elements[self.active_panel]) - 1)
            self.update_display()

    def clear_active_panel(self):
        """Очищаем активную панель"""
        self.panel_elements[self.active_panel] = []
        self.active_element[self.active_panel] = 0
        self.update_display()

    def reset_all_panels(self):
        """Сбрасываем все панели к начальному состоянию"""
        self.panel_elements = [
            ["Добро пожаловать!", "Используйте стрелки для навигации", "Ctrl+стрелки для смены панелей"],
            ["Элемент 1 панели 2", "Элемент 2 панели 2"],
            ["Элемент 1 панели 3", "Элемент 2 панели 3", "Элемент 3 панели 3"]
        ]
        self.active_element = [0, 0, 0]
        self.input_history = []
        self.update_display()

    def show_help(self):
        """Показываем справку в активной панели"""
        help_elements = [
            "=== СПРАВКА ===",
            "",
            "НАВИГАЦИЯ ПАНЕЛИ:",
            "• Ctrl+→ - следующая панель",
            "• Ctrl+← - предыдущая панель",
            "",
            "НАВИГАЦИЯ ЭЛЕМЕНТЫ:",
            "• ↑ или ← - предыдущий элемент",
            "• ↓ или → - следующий элемент",
            "",
            "КОМАНДЫ:",
            "• текст - добавить элемент",
            "• edit текст - изменить элемент",
            "• delete - удалить элемент",
            "• clear - очистить панель",
            "• reset - сбросить всё",
            "• help - эта справка",
            "• exit - выход"
        ]

        self.panel_elements[self.active_panel] = help_elements
        self.active_element[self.active_panel] = 0
        self.update_display()

    def on_mount(self):
        """Инициализация при запуске"""
        # Фокусируемся на поле ввода
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()

        # Обновляем отображение
        self.update_display()


def main():
    """Главная функция"""
    print("🚀 Запуск приложения с навигацией по элементам")
    print("=" * 60)
    print("НАВИГАЦИЯ ПАНЕЛИ:")
    print("• Ctrl+→ (стрелка вправо) - следующая панель")
    print("• Ctrl+← (стрелка влево) - предыдущая панель")
    print()
    print("НАВИГАЦИЯ ЭЛЕМЕНТЫ:")
    print("• ↑ или ← - предыдущий элемент")
    print("• ↓ или → - следующий элемент")
    print("• Активный элемент выделен инверсией")
    print()
    print("КОМАНДЫ:")
    print("• текст - добавить новый элемент")
    print("• edit текст - изменить текущий элемент")
    print("• delete - удалить текущий элемент")
    print("• clear - очистить панель")
    print("• reset - сбросить всё к начальному состоянию")
    print("• help - показать справку")
    print("• exit - выход")
    print("=" * 60)

    input("Нажмите Enter для запуска...")

    app = ThreePanelApp()
    app.run()


if __name__ == "__main__":
    main()