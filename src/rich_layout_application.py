import os
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel


class SimpleApp:
    def __init__(self):
        self.console = Console()
        self.panel1_content = "Содержимое панели 1"
        self.panel2_content = "Содержимое панели 2"
        self.panel3_content = "Содержимое панели 3"
        self.command_history = []

    def create_layout(self):
        layout = Layout()

        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", ratio=10)
        )

        layout["main"].split_row(
            Layout(name="panel1"),
            Layout(name="panel2"),
            Layout(name="panel3")
        )

        # Заполняем панели с зелёными рамками
        layout["header"].update(Panel("Статусная строка - версия 1.0", title="Статус", border_style="green"))
        layout["panel1"].update(Panel(self.panel1_content, title="Панель 1", border_style="green"))
        layout["panel2"].update(Panel(self.panel2_content, title="Панель 2", border_style="green"))
        layout["panel3"].update(Panel(self.panel3_content, title="Панель 3", border_style="green"))

        return layout

    def clear_screen(self):
        """Очищаем экран"""
        os.system('cls' if os.name == 'nt' else 'clear')

    def show_interface(self):
        """Показываем интерфейс"""
        self.clear_screen()
        self.console.print(self.create_layout())
        print()  # Пустая строка перед вводом

    def process_command(self, command):
        """Обрабатываем команду"""
        if not command.strip():
            return True

        command = command.strip()
        self.command_history.append(command)

        if command.lower() == "exit":
            return False
        elif command.lower() == "clear":
            self.panel1_content = "Панель очищена"
            self.panel2_content = "Панель очищена"
            self.panel3_content = "Панель очищена"
        elif command.lower() == "history":
            self.panel1_content = "История команд:\n" + "\n".join(
                f"{i + 1}. {cmd}" for i, cmd in enumerate(self.command_history[-10:]))
        elif command.startswith("panel1 "):
            self.panel1_content = command[7:]
        elif command.startswith("panel2 "):
            self.panel2_content = command[7:]
        elif command.startswith("panel3 "):
            self.panel3_content = command[7:]
        elif command.lower() == "help":
            self.panel1_content = """Доступные команды:
• panel1 текст - изменить панель 1
• panel2 текст - изменить панель 2  
• panel3 текст - изменить панель 3
• clear - очистить все панели
• history - показать историю команд
• help - показать справку
• exit - выход"""
        else:
            # Показываем введенную команду в первой панели
            self.panel1_content = f"Введена команда: {command}\n\nВведите 'help' для справки"

        return True

    def run(self):
        """Главный цикл приложения"""
        print("Добро пожаловать! Введите 'help' для справки или 'exit' для выхода.")

        while True:
            try:
                self.show_interface()
                command = input("Введите команду: ")

                if not self.process_command(command):
                    break

            except KeyboardInterrupt:
                print("\n\nВыход из приложения...")
                break
            except EOFError:
                print("\n\nВыход из приложения...")
                break

        print("Приложение завершено.")


if __name__ == "__main__":
    app = SimpleApp()
    app.run()