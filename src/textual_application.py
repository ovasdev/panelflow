from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Input
from textual import events


class ThreePanelApp(App):
    """Приложение с прокруткой и открытием элементов на следующей панели"""

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
        self.active_panel = 0  # 0, 1, 2 для панелей 1, 2, 3
        self.active_element = [0, 0, 0]  # Активный элемент для каждой панели
        self.scroll_offset = [0, 0, 0]  # Смещение прокрутки для каждой панели

        # Иерархическая структура: элемент -> список подэлементов
        self.panel_elements = [
            ["📁 Документы", "📁 Проекты", "📁 Изображения", "📄 readme.txt", "📄 config.json"],
            [],  # Будет заполняться при открытии элементов из панели 1
            []  # Будет заполняться при открытии элементов из панели 2
        ]

        # Данные для подэлементов
        self.sub_elements = {
            "📁 Документы": ["📄 отчет.docx", "📄 презентация.pptx", "📁 Архив", "📄 заметки.txt"],
            "📁 Проекты": ["📁 Проект А", "📁 Проект Б", "📄 план.md", "📄 TODO.txt"],
            "📁 Изображения": ["🖼️ фото1.jpg", "🖼️ фото2.png", "🖼️ логотип.svg"],
            "📄 readme.txt": ["Строка 1: Добро пожаловать", "Строка 2: Инструкции", "Строка 3: Контакты"],
            "📄 config.json": ["{ \"version\": \"1.0\" }", "{ \"debug\": true }", "{ \"theme\": \"dark\" }"],
            "📁 Архив": ["📄 старый_файл1.txt", "📄 старый_файл2.doc"],
            "📁 Проект А": ["📄 main.py", "📄 utils.py", "📁 tests"],
            "📁 Проект Б": ["📄 app.js", "📄 style.css", "📄 index.html"],
            "📁 tests": ["📄 test_main.py", "📄 test_utils.py"]
        }

        # Путь для отображения в заголовке
        self.panel_paths = ["Корневая папка", "", ""]

    def compose(self) -> ComposeResult:
        """Создаем интерфейс"""
        yield Static("→/← открыть элемент | ↑/↓ навигация | Ctrl+←→ смена панелей", id="header")

        with Horizontal(id="main"):
            yield Static("", classes="panel-active", id="panel1")
            yield Static("", classes="panel", id="panel2")
            yield Static("", classes="panel", id="panel3")

        yield Input(placeholder="Введите текст для добавления элемента...", id="command-input")

    def get_panel_height(self):
        """Получаем доступную высоту для содержимого панели"""
        # Высота экрана минус заголовок, рамки панели, поле ввода
        screen_height = self.size.height
        available_height = screen_height - 6  # Заголовок(1) + рамки(2) + ввод(3)
        return max(5, available_height - 3)  # Минимум 5 строк, резерв на заголовок панели

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
        elif event.key == "right":
            # Открыть элемент на следующей панели
            self.open_element_right()
            event.prevent_default()
        elif event.key == "left":
            # Открыть элемент на предыдущей панели (назад)
            self.open_element_left()
            event.prevent_default()
        elif event.key == "down":
            # Следующий элемент в активной панели
            self.move_element_down()
            event.prevent_default()
        elif event.key == "up":
            # Предыдущий элемент в активной панели
            self.move_element_up()
            event.prevent_default()

    def move_element_down(self):
        """Переход к следующему элементу с прокруткой"""
        max_elements = len(self.panel_elements[self.active_panel])
        if max_elements > 0 and self.active_element[self.active_panel] < max_elements - 1:
            self.active_element[self.active_panel] += 1
            self.update_scroll()
            self.update_display()

    def move_element_up(self):
        """Переход к предыдущему элементу с прокруткой"""
        if self.active_element[self.active_panel] > 0:
            self.active_element[self.active_panel] -= 1
            self.update_scroll()
            self.update_display()

    def update_scroll(self):
        """Обновляем прокрутку для активной панели"""
        panel_height = self.get_panel_height()
        current_element = self.active_element[self.active_panel]
        current_offset = self.scroll_offset[self.active_panel]

        # Если элемент ниже видимой области
        if current_element >= current_offset + panel_height:
            self.scroll_offset[self.active_panel] = current_element - panel_height + 1

        # Если элемент выше видимой области
        elif current_element < current_offset:
            self.scroll_offset[self.active_panel] = current_element

    def open_element_right(self):
        """Открываем элемент на следующей панели"""
        if self.active_panel < 2 and self.panel_elements[self.active_panel]:
            current_element = self.panel_elements[self.active_panel][self.active_element[self.active_panel]]

            # Получаем подэлементы
            sub_elements = self.sub_elements.get(current_element, [f"Содержимое: {current_element}"])

            # Обновляем следующую панель
            next_panel = self.active_panel + 1
            self.panel_elements[next_panel] = sub_elements
            self.active_element[next_panel] = 0
            self.scroll_offset[next_panel] = 0
            self.panel_paths[next_panel] = f"{self.panel_paths[self.active_panel]} > {current_element}"

            # Очищаем панели справа
            if next_panel + 1 < 3:
                self.panel_elements[next_panel + 1] = []
                self.panel_paths[next_panel + 1] = ""

            # Переходим к следующей панели
            self.active_panel = next_panel
            self.update_display()

    def open_element_left(self):
        """Возврат к предыдущей панели"""
        if self.active_panel > 0:
            self.active_panel -= 1

            # Очищаем панели справа от текущей
            for i in range(self.active_panel + 1, 3):
                self.panel_elements[i] = []
                self.panel_paths[i] = ""

            self.update_display()

    def update_display(self):
        """Обновляем отображение всех панелей с учетом прокрутки"""
        for i in range(3):
            panel = self.query_one(f"#panel{i + 1}", Static)

            # Устанавливаем стиль активной/неактивной панели
            if i == self.active_panel:
                panel.remove_class("panel")
                panel.add_class("panel-active")
                panel_status = "(АКТИВНА)"
            else:
                panel.remove_class("panel-active")
                panel.add_class("panel")
                panel_status = ""

            # Формируем заголовок панели
            path = self.panel_paths[i] or f"Панель {i + 1}"
            header = f"ПАНЕЛЬ {i + 1} {panel_status}"
            if path != f"Панель {i + 1}":
                header += f"\n📍 {path}"

            content_lines = [header, ""]

            # Получаем видимые элементы с учетом прокрутки
            if not self.panel_elements[i]:
                content_lines.append("Пусто - используйте → для открытия")
            else:
                panel_height = self.get_panel_height()
                offset = self.scroll_offset[i]
                visible_elements = self.panel_elements[i][offset:offset + panel_height]

                # Показываем индикатор прокрутки сверху
                if offset > 0:
                    content_lines.append(f"⬆️ ... ({offset} элементов выше)")

                # Отображаем видимые элементы
                for j, element in enumerate(visible_elements):
                    global_index = offset + j
                    if i == self.active_panel and global_index == self.active_element[i]:
                        # Выделяем активный элемент
                        content_lines.append(f"[reverse]► {element}[/reverse]")
                    else:
                        content_lines.append(f"► {element}")

                # Показываем индикатор прокрутки снизу
                total_elements = len(self.panel_elements[i])
                if offset + panel_height < total_elements:
                    remaining = total_elements - (offset + panel_height)
                    content_lines.append(f"⬇️ ... ({remaining} элементов ниже)")

                # Добавляем информацию о позиции для активной панели
                if i == self.active_panel:
                    content_lines.extend([
                        "",
                        f"Элемент {self.active_element[i] + 1} из {total_elements}",
                        "→ открыть | ↑↓ навигация"
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
        self.update_scroll()
        self.update_display()

    def edit_active_element(self, new_text):
        """Редактируем активный элемент"""
        if self.panel_elements[self.active_panel]:
            old_text = self.panel_elements[self.active_panel][self.active_element[self.active_panel]]
            self.panel_elements[self.active_panel][self.active_element[self.active_panel]] = new_text

            # Обновляем ключ в sub_elements если это был родительский элемент
            if old_text in self.sub_elements:
                self.sub_elements[new_text] = self.sub_elements.pop(old_text)

            self.update_display()

    def delete_active_element(self):
        """Удаляем активный элемент"""
        if self.panel_elements[self.active_panel]:
            element_text = self.panel_elements[self.active_panel][self.active_element[self.active_panel]]
            del self.panel_elements[self.active_panel][self.active_element[self.active_panel]]

            # Удаляем из sub_elements если есть
            if element_text in self.sub_elements:
                del self.sub_elements[element_text]

            # Корректируем позицию активного элемента
            if self.active_element[self.active_panel] >= len(self.panel_elements[self.active_panel]):
                self.active_element[self.active_panel] = max(0, len(self.panel_elements[self.active_panel]) - 1)

            self.update_scroll()
            self.update_display()

    def clear_active_panel(self):
        """Очищаем активную панель"""
        self.panel_elements[self.active_panel] = []
        self.active_element[self.active_panel] = 0
        self.scroll_offset[self.active_panel] = 0
        self.update_display()

    def reset_all_panels(self):
        """Сбрасываем все панели к начальному состоянию"""
        self.panel_elements = [
            ["📁 Документы", "📁 Проекты", "📁 Изображения", "📄 readme.txt", "📄 config.json"],
            [],
            []
        ]
        self.active_element = [0, 0, 0]
        self.scroll_offset = [0, 0, 0]
        self.panel_paths = ["Корневая папка", "", ""]
        self.active_panel = 0
        self.update_display()

    def show_help(self):
        """Показываем справку в активной панели"""
        help_elements = [
            "=== НАВИГАЦИЯ ===",
            "• → - открыть элемент справа",
            "• ← - вернуться назад",
            "• ↑/↓ - навигация по элементам",
            "• Ctrl+←/→ - смена панелей",
            "",
            "=== ПРОКРУТКА ===",
            "• Автоматическая при навигации",
            "• Индикаторы ⬆️⬇️ показывают",
            "  скрытые элементы",
            "",
            "=== КОМАНДЫ ===",
            "• текст - добавить элемент",
            "• edit текст - изменить",
            "• delete - удалить",
            "• clear - очистить панель",
            "• reset - сброс к началу",
            "• exit - выход"
        ]

        self.panel_elements[self.active_panel] = help_elements
        self.active_element[self.active_panel] = 0
        self.scroll_offset[self.active_panel] = 0
        self.update_display()

    def on_mount(self):
        """Инициализация при запуске"""
        input_widget = self.query_one("#command-input", Input)
        input_widget.focus()
        self.update_display()


def main():
    """Главная функция"""
    print("🚀 Файловый менеджер с прокруткой и навигацией")
    print("=" * 60)
    print("НАВИГАЦИЯ:")
    print("• → - открыть элемент на следующей панели")
    print("• ← - вернуться на предыдущую панель")
    print("• ↑/↓ - перемещение по элементам")
    print("• Ctrl+←/→ - переключение между панелями")
    print()
    print("ПРОКРУТКА:")
    print("• Автоматическая при длинных списках")
    print("• Заголовок панели всегда видим")
    print("• Индикаторы ⬆️⬇️ показывают скрытые элементы")
    print()
    print("КОМАНДЫ:")
    print("• текст - добавить элемент")
    print("• edit текст - редактировать элемент")
    print("• delete - удалить элемент")
    print("• help - справка")
    print("=" * 60)

    input("Нажмите Enter для запуска...")

    app = ThreePanelApp()
    app.run()


if __name__ == "__main__":
    main()