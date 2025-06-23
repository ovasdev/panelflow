from textual.app import App, ComposeResult
from textual.widgets import Static, Input


class SimpleInputTest(App):
    """Простейший тест Input виджета"""

    CSS = """
    Screen {
        layout: vertical;
    }

    Static {
        height: 1fr;
        border: solid white;
        padding: 1;
    }

    Input {
        height: 3;
        border: solid green;
    }
    """

    def compose(self) -> ComposeResult:
        """Создаем простейший интерфейс"""
        yield Static("Тест поля ввода\n\nВведите текст в поле ниже:")
        yield Input(placeholder="Введите текст здесь...")

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Обрабатываем ввод"""
        static = self.query_one(Static)
        static.update(f"Введено: '{event.value}'\n\nДлина: {len(event.value)} символов\n\nВведите ещё:")
        event.input.value = ""

    def on_mount(self):
        """Устанавливаем фокус на Input"""
        input_widget = self.query_one(Input)
        input_widget.focus()


if __name__ == "__main__":
    app = SimpleInputTest()
    app.run()