from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Input
from textual import events


class ThreePanelApp(App):
    """Приложение с навигацией между панелями и отображением текста на активной панели"""

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
        background: darkgreen;
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
        self.panel_contents = [
            "ПАНЕЛЬ 1 (АКТИВНА)\n\nОжидание ввода...\n\nУправление:\n• Ctrl+→ следующая панель\n• Ctrl+← предыдущая панель",
            "ПАНЕЛЬ 2\n\nСодержимое панели 2",
            "ПАНЕЛЬ 3\n\nСодержимое панели 3"
        ]

    def compose(self) -> ComposeResult:
        """Создаем интерфейс"""
        yield Static("Система мониторинга - Ctrl+стрелки для навигации между панелями", id="header")

        with Horizontal(id="main"):
            yield Static(self.panel_contents[0], classes="panel-active", id="panel1")
            yield Static(self.panel_contents[1], classes="panel", id="panel2")
            yield Static(self.panel_contents[2], classes="panel", id="panel3")

        yield Input(placeholder="Введите текст - он появится на активной панели...", id="command-input")

    def on_key(self, event: events.Key) -> None:
        """Обрабатываем нажатия клавиш"""
        if event.key == "ctrl+right":
            # Переход к следующей панели
            if self.active_panel < 2:
                self.active_panel += 1
                self.update_active_panel()
                event.prevent_default()
        elif event.key == "ctrl+left":
            # Переход к предыдущей панели
            if self.active_panel > 0:
                self.active_panel -= 1
                self.update_active_panel()
                event.prevent_default()

    def update_active_panel(self):
        """Обновляем визуальное выделение активной панели"""
        for i in range(3):
            panel = self.query_one(f"#panel{i + 1}", Static)
            if i == self.active_panel:
                panel.remove_class("panel")
                panel.add_class("panel-active")
                # Обновляем содержимое с указанием активности
                active_content = f"ПАНЕЛЬ {i + 1} (АКТИВНА)\n\n{self.get_panel_content(i)}"
                panel.update(active_content)
            else:
                panel.remove_class("panel-active")
                panel.add_class("panel")
                # Обновляем содержимое без указания активности
                inactive_content = f"ПАНЕЛЬ {i + 1}\n\n{self.get_panel_content(i)}"
                panel.update(inactive_content)

    def get_panel_content(self, panel_index):
        """Получаем содержимое панели без заголовка"""
        content = self.panel_contents[panel_index]
        # Убираем первую строку с заголовком панели
        lines = content.split('\n')
        if lines and lines[0].startswith("ПАНЕЛЬ"):
            return '\n'.join(lines[2:])  # Пропускаем заголовок и пустую строку
        return content

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Обрабатываем ввод команды"""
        user_input = event.value.strip()

        if not user_input:
            return

        # Добавляем в историю
        self.input_history.append(user_input)

        # Обрабатываем специальные команды
        if user_input.lower() == "exit":
            self.exit()
            return
        elif user_input.lower() == "clear":
            self.clear_active_panel()
        elif user_input.lower() == "help":
            self.show_help()
        elif user_input.lower() == "reset":
            self.reset_all_panels()
        else:
            # Добавляем текст к активной панели
            self.add_text_to_active_panel(user_input)

        # Очищаем поле ввода
        event.input.value = ""

    def add_text_to_active_panel(self, text):
        """Добавляем текст к активной панели"""
        current_content = self.get_panel_content(self.active_panel)

        # Если это начальное содержимое, заменяем его
        if "Ожидание ввода" in current_content or "Содержимое панели" in current_content:
            new_content = f"► {text}"
        else:
            # Добавляем к существующему содержимому
            new_content = f"{current_content}\n► {text}"

        # Обновляем содержимое панели
        self.panel_contents[self.active_panel] = f"ПАНЕЛЬ {self.active_panel + 1}\n\n{new_content}"

        # Обновляем отображение
        self.update_active_panel()

    def clear_active_panel(self):
        """Очищаем активную панель"""
        self.panel_contents[self.active_panel] = f"ПАНЕЛЬ {self.active_panel + 1}\n\nПанель очищена"
        self.update_active_panel()

    def reset_all_panels(self):
        """Сбрасываем все панели к начальному состоянию"""
        self.panel_contents = [
            "ПАНЕЛЬ 1\n\nОжидание ввода...\n\nУправление:\n• Ctrl+→ следующая панель\n• Ctrl+← предыдущая панель",
            "ПАНЕЛЬ 2\n\nСодержимое панели 2",
            "ПАНЕЛЬ 3\n\nСодержимое панели 3"
        ]
        self.input_history = []
        self.update_active_panel()

    def show_help(self):
        """Показываем справку на активной панели"""
        help_text = """СПРАВКА:

НАВИГАЦИЯ:
• Ctrl+→ - следующая панель
• Ctrl+← - предыдущая панель

КОМАНДЫ:
• clear - очистить активную панель
• reset - сбросить все панели
• help - показать справку
• exit - выход

ВВОД:
Любой другой текст добавляется 
к содержимому активной панели"""

        self.panel_contents[self.active_panel] = f"ПАНЕЛЬ {self.active_panel + 1}\n\n{help_text}"
        self.update_active_panel()

    def on_mount(self):
        """Инициализация при запуске"""
        # Фокусируемся на поле ввода
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()

        # Устанавливаем первую панель активной
        self.update_active_panel()


def main():
    """Главная функция"""
    print("🚀 Запуск приложения с навигацией между панелями")
    print("=" * 60)
    print("УПРАВЛЕНИЕ:")
    print("• Ctrl+→ (стрелка вправо) - следующая панель")
    print("• Ctrl+← (стрелка влево) - предыдущая панель")
    print()
    print("КОМАНДЫ:")
    print("• clear - очистить активную панель")
    print("• reset - сбросить все панели")
    print("• help - показать справку")
    print("• exit - выход")
    print()
    print("ВВОД:")
    print("• Любой текст добавляется к активной панели")
    print("• Активная панель выделена зелёным цветом")
    print("=" * 60)

    input("Нажмите Enter для запуска...")

    app = ThreePanelApp()
    app.run()


if __name__ == "__main__":
    main()