from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Static, Input
from textual.reactive import reactive
from textual import events


class StatusHeader(Static):
    """Заголовок приложения с информацией о панелях"""

    def __init__(self, main_app):
        self.main_app = main_app
        super().__init__("↑/↓ навигация | Enter открыть | ← свернуть | Ctrl+←→ панели")
        self.styles.height = 1
        self.styles.background = "green"
        self.styles.color = "white"
        self.styles.text_align = "center"

    def update_header(self):
        """Обновляем заголовок с информацией о панелях"""
        # Получаем название текущей активной панели
        try:
            active_panel = self.main_app.get_active_panel()
            current_path = active_panel.panel_path or "Панель"
            # Берем только последнюю часть пути
            current_name = current_path.split(" > ")[-1] if " > " in current_path else current_path
        except:
            current_name = "Панель"

        # Информация о скрытых панелях слева
        left_info = ""
        if self.main_app.panel_offset > 0:
            # Есть скрытые панели слева
            try:
                left_panel_data = self.main_app.panel_stack[self.main_app.panel_offset - 1]
                if left_panel_data:
                    left_name = left_panel_data['path'].split(" > ")[-1]
                    left_info = f"◀ {left_name} | "
            except:
                left_info = "◀ ... | "

        # Информация о скрытых панелях справа
        right_info = ""
        max_visible_index = self.main_app.panel_offset + self.main_app.visible_panels - 1
        if max_visible_index + 1 < len(self.main_app.panel_stack):
            # Есть скрытые панели справа
            try:
                right_panel_data = self.main_app.panel_stack[max_visible_index + 1]
                if right_panel_data:
                    right_name = right_panel_data['path'].split(" > ")[-1]
                    right_info = f" | {right_name} ▶"
            except:
                right_info = " | ... ▶"

        # Формируем итоговую строку заголовка
        header_text = f"{left_info}{current_name}{right_info}"
        self.update(header_text)


class NavigablePanel(Static):
    """Панель с навигацией по элементам"""

    elements = reactive(list)
    active_element = reactive(0)
    scroll_offset = reactive(0)
    is_active = reactive(False)
    panel_path = reactive("")

    def __init__(self, panel_id: int, **kwargs):
        super().__init__(**kwargs)
        self.panel_id = panel_id
        self.elements = []
        self.active_element = 0
        self.scroll_offset = 0
        self.is_active = False
        self.panel_path = f"Панель {panel_id}"

    def on_mount(self):
        """Инициализация панели"""
        self.update_display()

    def watch_elements(self):
        """Реакция на изменение элементов"""
        self.update_display()

    def watch_active_element(self):
        """Реакция на изменение активного элемента"""
        self.update_display()

    def watch_is_active(self):
        """Реакция на изменение активности панели"""
        if self.is_active:
            self.remove_class("panel")
            self.add_class("panel-active")
        else:
            self.remove_class("panel-active")
            self.add_class("panel")
        self.update_display()

    def get_panel_height(self):
        """Получаем доступную высоту для содержимого панели"""
        try:
            screen_height = self.app.size.height
            # Вычитаем: header(1) + input(3) + рамки панели(2) + отступы(2)
            available_height = screen_height - 8
            return max(8, available_height)  # Минимум 8 строк для навигационной информации
        except:
            return 15

    def get_content_height(self):
        """Получаем высоту для отображения элементов (без заголовка и навигации)"""
        try:
            total_height = self.get_panel_height()

            # Считаем строки заголовка
            header_lines = 2  # Базовые строки
            if self.panel_path != f"Панель {self.panel_id}":
                header_lines += 1  # Путь
            if self.is_active:
                header_lines += 1  # Отладочная информация

            # Резерв для навигации
            nav_lines = 3

            # Высота для элементов
            content_height = total_height - header_lines - nav_lines
            return max(3, content_height)  # Минимум 3 элемента видно
        except:
            return 8

    def update_scroll(self):
        """Обновляем прокрутку с правильной высотой"""
        if not self.elements:
            return

        content_height = self.get_content_height()
        current_element = self.active_element
        current_offset = self.scroll_offset
        total_elements = len(self.elements)

        # Если активный элемент ниже видимой области
        if current_element >= current_offset + content_height:
            self.scroll_offset = current_element - content_height + 1

        # Если активный элемент выше видимой области
        elif current_element < current_offset:
            self.scroll_offset = current_element

        # Ограничиваем смещение
        max_offset = max(0, total_elements - content_height)
        self.scroll_offset = min(self.scroll_offset, max_offset)
        self.scroll_offset = max(0, self.scroll_offset)

    def update_display(self):
        """Обновляем отображение панели"""
        # Получаем состояние поля ввода
        try:
            input_widget = self.app.query_one("#command-input", CustomInput)
            has_text = bool(input_widget.value)
        except:
            has_text = False

        # Проверяем, скрыта ли панель
        if self.has_class("panel-hidden"):
            # Для скрытых панелей показываем заглушку
            self.update(
                "ПАНЕЛЬ НЕ ОТКРЫТА\n\nИспользуйте Enter на элементе\nпредыдущей панели\nчтобы открыть эту панель")
            return

        # Формируем заголовок для видимых панелей
        panel_status = "(АКТИВНА)" if self.is_active else ""
        actual_panel_number = self.app.panel_offset + self.panel_id  # Абсолютный номер панели
        header = f"ПАНЕЛЬ {actual_panel_number} {panel_status}"

        if self.panel_path != f"Панель {self.panel_id}":
            header += f"\n📍 {self.panel_path}"

        if self.is_active:
            debug_info = f"\n🔧 Поле: {'ЗАПОЛНЕНО' if has_text else 'ПУСТОЕ'}"
            debug_info += f" | Смещение: {self.app.panel_offset} | Видимых: {self.app.visible_panels}"
            header += debug_info

        content_lines = [header, ""]

        # Получаем высоту для элементов
        content_height = self.get_content_height()

        # Основное содержимое панели
        if not self.elements:
            # Заполняем пустыми строками до навигационной информации
            for _ in range(content_height):
                content_lines.append("")
            content_lines[2] = "Пусто - используйте → для открытия"
        else:
            offset = self.scroll_offset

            # Учитываем индикаторы прокрутки
            available_lines = content_height
            if offset > 0:
                available_lines -= 1  # Строка для индикатора сверху

            total_elements = len(self.elements)
            if offset + available_lines < total_elements:
                available_lines -= 1  # Строка для индикатора снизу

            visible_elements = self.elements[offset:offset + available_lines]

            # Индикатор прокрутки сверху
            if offset > 0:
                content_lines.append(f"⬆️ ... ({offset} элементов выше)")

            # Отображаем видимые элементы
            for j, element in enumerate(visible_elements):
                global_index = offset + j
                if self.is_active and global_index == self.active_element:
                    content_lines.append(f"[reverse]► {element}[/reverse]")
                else:
                    content_lines.append(f"► {element}")

            # Индикатор прокрутки снизу
            if offset + len(visible_elements) < total_elements:
                remaining = total_elements - (offset + len(visible_elements))
                content_lines.append(f"⬇️ ... ({remaining} элементов ниже)")

            # Заполняем оставшиеся строки пустыми
            total_content_lines = len(content_lines) - 2  # Вычитаем заголовок
            while total_content_lines < content_height:
                content_lines.append("")
                total_content_lines += 1

        # Добавляем навигационную информацию в самый низ
        if self.is_active and self.elements:
            total_elements = len(self.elements)
            actual_panel_number = self.app.panel_offset + self.panel_id
            status_info = ""

            # Информация о сдвиге для третьей панели и выше
            if actual_panel_number >= 3:
                status_info = " | Enter = СДВИГ вперед"

            # Информация о Ctrl+← для первой панели при наличии скрытых панелей слева
            ctrl_left_info = ""
            if self.panel_id == 1 and self.app.panel_offset > 0:  # Первая панель и есть скрытые слева
                ctrl_left_info = " | Ctrl+← = показать слева"

            content_lines.extend([
                "─" * 30,  # Разделительная линия
                f"Элемент {self.active_element + 1} из {total_elements}{status_info}{ctrl_left_info}",
                "Enter открыть | ↑↓ навигация | ← свернуть" if not has_text else "Редактирование текста"
            ])
        elif self.is_active:
            # Для пустых панелей
            content_lines.extend([
                "─" * 30,
                f"Панель пуста",
                "Введите текст для добавления"
            ])
        else:
            # Для неактивных панелей - просто пустые строки
            content_lines.extend(["", "", ""])

        self.update("\n".join(content_lines))

    def move_up(self):
        """Переход к предыдущему элементу"""
        if self.active_element > 0:
            self.active_element -= 1
            self.update_scroll()

    def move_down(self):
        """Переход к следующему элементу"""
        if self.elements and self.active_element < len(self.elements) - 1:
            self.active_element += 1
            self.update_scroll()

    def add_element(self, text):
        """Добавляем элемент"""
        self.elements = self.elements + [text]
        self.active_element = len(self.elements) - 1
        self.update_scroll()

    def clear_elements(self):
        """Очищаем все элементы"""
        self.elements = []
        self.active_element = 0
        self.scroll_offset = 0


class CustomInput(Input):
    """Упрощенное поле ввода"""

    def __init__(self, **kwargs):
        super().__init__(placeholder="Введите текст для добавления элемента...", **kwargs)
        self.styles.dock = "bottom"
        self.styles.height = 3
        self.styles.margin = 0
        self.styles.padding = 1


class ThreePanelApp(App):
    """Приложение с тремя панелями и интеллектуальным вводом"""

    CSS = """
    Screen {
        layout: vertical;
        padding: 0;
    }

    #main {
        layout: horizontal;
        height: 1fr;
        padding: 0;
        margin: 0;
    }

    .panel {
        width: 33.33%;
        height: 1fr;
        border: solid white;
        padding: 1;
        margin: 0;
    }

    .panel-active {
        width: 33.33%;
        height: 1fr;
        border: solid green;
        background: darkgreen 10%;
        padding: 1;
        margin: 0;
    }

    .panel-hidden {
        width: 33.33%;
        height: 1fr;
        border: solid #333333;
        background: #111111;
        color: #333333;
        padding: 1;
        margin: 0;
    }
    """

    def __init__(self):
        super().__init__()
        self.active_panel = 0
        self.visible_panels = 1  # Количество видимых панелей (1, 2 или 3)
        self.panel_offset = 0  # Смещение "окна" панелей (0 = показаны панели 1-3, 1 = панели 2-4, и т.д.)
        self.panel_stack = []  # Стек данных всех панелей для навигации

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

    def compose(self) -> ComposeResult:
        """Создаем интерфейс"""
        yield StatusHeader(self)

        with Horizontal(id="main"):
            yield NavigablePanel(1, classes="panel-active", id="panel1")
            yield NavigablePanel(2, classes="panel", id="panel2")
            yield NavigablePanel(3, classes="panel", id="panel3")

        yield CustomInput(id="command-input")

    def on_mount(self):
        """Инициализация при запуске"""
        # Инициализируем стек панелей
        initial_data = {
            'elements': ["📁 Документы", "📁 Проекты", "📁 Изображения", "📄 readme.txt", "📄 config.json"],
            'path': "Корневая папка",
            'active_element': 0,
            'scroll_offset': 0
        }
        self.panel_stack = [initial_data]

        # Инициализируем данные в первой панели
        panel1 = self.query_one("#panel1", NavigablePanel)
        panel1.elements = initial_data['elements']
        panel1.is_active = True
        panel1.panel_path = initial_data['path']

        # Скрываем вторую и третью панели
        self.update_panel_visibility()
        self.update_header()

        # Устанавливаем фокус на поле ввода
        input_widget = self.query_one("#command-input", CustomInput)
        input_widget.focus()

    def update_panel_visibility(self):
        """Обновляем видимость панелей"""
        panels = [
            self.query_one("#panel1", NavigablePanel),
            self.query_one("#panel2", NavigablePanel),
            self.query_one("#panel3", NavigablePanel)
        ]

        for i, panel in enumerate(panels):
            if i < self.visible_panels:
                # Панель видима и активна
                panel.remove_class("panel-hidden")
                if i == self.active_panel:
                    panel.remove_class("panel")
                    panel.add_class("panel-active")
                else:
                    panel.remove_class("panel-active")
                    panel.add_class("panel")
            else:
                # Панель скрыта - показываем как пустую
                panel.remove_class("panel")
                panel.remove_class("panel-active")
                panel.add_class("panel-hidden")
                panel.elements = []  # Очищаем содержимое
                panel.panel_path = ""
                panel.is_active = False

    def on_key(self, event: events.Key) -> None:
        """Обрабатываем события клавиатуры осторожно"""
        input_widget = self.query_one("#command-input", CustomInput)

        # Проверяем, если фокус на Input и есть текст, то не вмешиваемся
        if input_widget.has_focus and input_widget.value:
            # Только обрабатываем Esc и Ctrl+стрелки
            if event.key == "escape":
                input_widget.value = ""
                return
            elif event.key in ["ctrl+right", "ctrl+left"]:
                input_widget.value = ""
                # Продолжаем обработку ниже
            else:
                # Позволяем Input обрабатывать событие
                return

        # Обрабатываем навигационные клавиши
        if event.key == "ctrl+right":
            self.navigate_between_visible_panels("right")
        elif event.key == "ctrl+left":
            self.navigate_between_visible_panels("left")
        elif event.key == "left" and not input_widget.value:
            # Сворачиваем текущую панель и все правее
            self.collapse_current_and_right_panels()
        elif event.key == "right" and not input_widget.value:
            # Можно добавить быстрый переход вперед если нужно
            pass
        elif event.key == "enter" and not input_widget.value:
            self.open_element_with_enter()
        elif event.key == "down" and not input_widget.value:
            self.move_element_down()
        elif event.key == "up" and not input_widget.value:
            self.move_element_up()

    def get_active_panel(self) -> NavigablePanel:
        """Получаем активную панель"""
        return self.query_one(f"#panel{self.active_panel + 1}", NavigablePanel)

    def switch_panel(self, new_panel):
        """Переключение панели"""
        # Проверяем, что панель видима
        if new_panel >= self.visible_panels:
            return

        # Деактивируем текущую панель
        current_panel = self.get_active_panel()
        current_panel.is_active = False

        # Активируем новую панель
        self.active_panel = new_panel
        new_active_panel = self.get_active_panel()
        new_active_panel.is_active = True

        # Обновляем видимость и заголовок
        self.update_panel_visibility()
        self.update_header()

    def open_element_with_enter(self):
        """Открываем элемент по Enter - показываем следующую панель или смещаем"""
        current_panel = self.get_active_panel()
        if not current_panel.elements:
            return

        element = current_panel.elements[current_panel.active_element]
        sub_elements = self.sub_elements.get(element, [f"Содержимое: {element}"])

        if self.active_panel == 2:  # Если на третьей панели
            # Смещаем панели: 2→1, 3→2, новая→3
            self.shift_panels_left(element, sub_elements)
        elif self.active_panel == 0:  # Первая панель
            if self.visible_panels == 1:
                # Открываем вторую панель
                self.open_next_panel(element, sub_elements)
            else:
                # Вторая панель уже открыта, обновляем её
                self.update_existing_panel(1, element, sub_elements)
        elif self.active_panel == 1:  # Вторая панель
            if self.visible_panels == 2:
                # Открываем третью панель
                self.open_next_panel(element, sub_elements)
            else:
                # Третья панель уже открыта, обновляем её
                self.update_existing_panel(2, element, sub_elements)

    def update_existing_panel(self, panel_index, selected_element, new_elements):
        """Обновляем уже открытую панель"""
        current_panel = self.get_active_panel()
        target_panel = self.query_one(f"#panel{panel_index + 1}", NavigablePanel)

        target_panel.elements = new_elements
        target_panel.active_element = 0
        target_panel.scroll_offset = 0
        target_panel.panel_path = f"{current_panel.panel_path} > {selected_element}"

        # Обновляем в стеке
        stack_index = self.panel_offset + panel_index
        if stack_index < len(self.panel_stack):
            self.panel_stack[stack_index] = {
                'elements': new_elements[:],
                'path': target_panel.panel_path,
                'active_element': 0,
                'scroll_offset': 0
            }

        # Очищаем панели справа от обновленной
        if panel_index == 1:  # Если обновили вторую панель, очистим третью
            panel3 = self.query_one("#panel3", NavigablePanel)
            panel3.elements = []
            panel3.panel_path = ""
            self.visible_panels = 2

            # Удаляем из стека тоже
            stack_index_3 = self.panel_offset + 2
            if stack_index_3 < len(self.panel_stack):
                self.panel_stack = self.panel_stack[:stack_index_3]

        # Переходим к обновленной панели
        self.switch_panel(panel_index)

    def shift_panels_left(self, selected_element, new_elements):
        """Смещаем панели влево и добавляем новую справа"""
        print(f"🔄 Выполняется сдвиг панелей ВПРАВО. Элемент: {selected_element}")

        panel1 = self.query_one("#panel1", NavigablePanel)
        panel2 = self.query_one("#panel2", NavigablePanel)
        panel3 = self.query_one("#panel3", NavigablePanel)

        # Сохраняем данные текущих панелей в стек
        current_stack_index = self.panel_offset

        # Убеждаемся что в стеке достаточно места
        while len(self.panel_stack) <= current_stack_index + 2:
            self.panel_stack.append(None)

        # Сохраняем текущие данные панелей в стек
        self.panel_stack[current_stack_index] = {
            'elements': panel1.elements[:],
            'path': panel1.panel_path,
            'active_element': panel1.active_element,
            'scroll_offset': panel1.scroll_offset
        }

        self.panel_stack[current_stack_index + 1] = {
            'elements': panel2.elements[:],
            'path': panel2.panel_path,
            'active_element': panel2.active_element,
            'scroll_offset': panel2.scroll_offset
        }

        self.panel_stack[current_stack_index + 2] = {
            'elements': panel3.elements[:],
            'path': panel3.panel_path,
            'active_element': panel3.active_element,
            'scroll_offset': panel3.scroll_offset
        }

        # Увеличиваем смещение (сдвигаемся вправо в истории)
        self.panel_offset += 1

        # Добавляем новую панель в стек
        new_panel_data = {
            'elements': new_elements,
            'path': f"{panel3.panel_path} > {selected_element}",
            'active_element': 0,
            'scroll_offset': 0
        }

        if len(self.panel_stack) <= self.panel_offset + 2:
            self.panel_stack.append(new_panel_data)
        else:
            self.panel_stack[self.panel_offset + 2] = new_panel_data

        # Загружаем данные для нового окна панелей
        self.load_panels_from_stack()

        print(f"✅ Сдвиг вправо завершен. Смещение: {self.panel_offset}")

    def update_header(self):
        """Обновляем заголовок"""
        try:
            header = self.query_one(StatusHeader)
            header.update_header()
        except:
            pass

    def collapse_current_and_right_panels(self):
        """Сворачиваем текущую панель и все правее её"""
        print(f"🔄 Сворачивание панели {self.active_panel + 1} и правее")

        # Сохраняем текущее состояние
        self.save_current_panels_to_stack()

        # Определяем сколько панелей нужно свернуть
        panels_to_collapse = 3 - self.active_panel  # Если активна панель 0, сворачиваем 3, если 1 - то 2, если 2 - то 1

        # Обрезаем стек справа от текущей активной панели
        current_global_index = self.panel_offset + self.active_panel
        self.panel_stack = self.panel_stack[:current_global_index]

        # Если есть скрытые панели слева, сдвигаемся влево
        if self.panel_offset > 0:
            # Вычисляем новое смещение
            new_offset = max(0, self.panel_offset - panels_to_collapse)
            self.panel_offset = new_offset

            # Загружаем панели с новым смещением
            self.load_panels_from_stack()
        else:
            # Если нет скрытых панелей слева, просто уменьшаем количество видимых
            if self.active_panel > 0:
                self.visible_panels = self.active_panel
                self.active_panel = self.active_panel - 1
            else:
                # Сворачиваем все, остается только первая
                self.visible_panels = 1
                self.active_panel = 0

            # Очищаем свернутые панели
            for i in range(self.visible_panels, 3):
                panel = self.query_one(f"#panel{i + 1}", NavigablePanel)
                panel.elements = []
                panel.panel_path = ""
                panel.is_active = False

            # Устанавливаем активность правильной панели
            for i in range(3):
                panel = self.query_one(f"#panel{i + 1}", NavigablePanel)
                panel.is_active = (i == self.active_panel)

            self.update_panel_visibility()

        self.update_header()
        print(f"✅ Сворачивание завершено. Смещение: {self.panel_offset}, видимых: {self.visible_panels}")

    def save_current_panels_to_stack(self):
        """Сохраняем данные текущих панелей в стек"""
        panel1 = self.query_one("#panel1", NavigablePanel)
        panel2 = self.query_one("#panel2", NavigablePanel)
        panel3 = self.query_one("#panel3", NavigablePanel)

        panels = [panel1, panel2, panel3]

        for i, panel in enumerate(panels):
            stack_index = self.panel_offset + i
            if stack_index < len(self.panel_stack) and self.panel_stack[stack_index] is not None:
                self.panel_stack[stack_index] = {
                    'elements': panel.elements[:],
                    'path': panel.panel_path,
                    'active_element': panel.active_element,
                    'scroll_offset': panel.scroll_offset
                }

    def load_panels_from_stack(self):
        """Загружаем данные панелей из стека"""
        panel1 = self.query_one("#panel1", NavigablePanel)
        panel2 = self.query_one("#panel2", NavigablePanel)
        panel3 = self.query_one("#panel3", NavigablePanel)

        panels = [panel1, panel2, panel3]

        for i, panel in enumerate(panels):
            stack_index = self.panel_offset + i
            if stack_index < len(self.panel_stack) and self.panel_stack[stack_index] is not None:
                data = self.panel_stack[stack_index]
                panel.elements = data['elements'][:]
                panel.panel_path = data['path']
                panel.active_element = data['active_element']
                panel.scroll_offset = data['scroll_offset']
                panel.is_active = (i == self.active_panel)
            else:
                # Панель пуста
                panel.elements = []
                panel.panel_path = ""
                panel.active_element = 0
                panel.scroll_offset = 0
                panel.is_active = False

        # Устанавливаем правильное количество видимых панелей
        max_visible = 0
        for i in range(3):
            stack_index = self.panel_offset + i
            if stack_index < len(self.panel_stack) and self.panel_stack[stack_index] is not None:
                max_visible = i + 1

        self.visible_panels = max_visible

        # Активная панель - последняя видимая
        self.active_panel = min(2, max_visible - 1)
        if max_visible > 0:
            panels[self.active_panel].is_active = True

        self.update_panel_visibility()
        self.update_header()

    def open_next_panel(self, selected_element, new_elements):
        """Обычное открытие следующей панели"""
        current_panel = self.get_active_panel()

        # Показываем следующую панель
        self.visible_panels = self.active_panel + 2

        # Обновляем следующую панель
        next_panel_id = self.active_panel + 1
        next_panel = self.query_one(f"#panel{next_panel_id + 1}", NavigablePanel)
        next_panel.elements = new_elements
        next_panel.active_element = 0
        next_panel.scroll_offset = 0
        next_panel.panel_path = f"{current_panel.panel_path} > {selected_element}"

        # Добавляем в стек если нужно
        stack_index = self.panel_offset + next_panel_id
        while len(self.panel_stack) <= stack_index:
            self.panel_stack.append(None)

        self.panel_stack[stack_index] = {
            'elements': new_elements[:],
            'path': next_panel.panel_path,
            'active_element': 0,
            'scroll_offset': 0
        }

        # Очищаем панели справа (если есть)
        if next_panel_id + 1 < 3:
            right_panel = self.query_one("#panel3", NavigablePanel)
            right_panel.elements = []
            right_panel.panel_path = ""

        # Переходим к следующей панели
        self.switch_panel(next_panel_id)

    def navigate_between_visible_panels(self, direction):
        """Навигация только между видимыми панелями"""
        if direction == "right" and self.active_panel < self.visible_panels - 1:
            self.switch_panel(self.active_panel + 1)
        elif direction == "left":
            if self.active_panel > 0:
                # Обычное переключение на предыдущую панель
                self.switch_panel(self.active_panel - 1)
            elif self.active_panel == 0 and self.panel_offset > 0:
                # Специальный случай: на первой панели при наличии скрытых панелей слева
                # Смещаем панели вправо (показываем скрытую панель слева)
                self.shift_panels_right_to_show_left()

    def shift_panels_right_to_show_left(self):
        """Смещаем панели вправо чтобы показать скрытую панель слева"""
        if self.panel_offset <= 0:
            return  # Нет скрытых панелей слева

        print(f"🔄 Смещение панелей ВПРАВО (показываем скрытую панель слева)")

        # Сохраняем текущие данные панелей в стек
        self.save_current_panels_to_stack()

        # Уменьшаем смещение на 1 (сдвигаемся влево в стеке)
        self.panel_offset -= 1

        # Загружаем панели с новым смещением
        self.load_panels_from_stack()

        # Активная панель остается первой
        self.active_panel = 0

        print(f"✅ Смещение вправо завершено. Новое смещение: {self.panel_offset}")
        print(f"   Теперь показаны панели {self.panel_offset + 1}-{self.panel_offset + self.visible_panels}")

    def move_element_down(self):
        """Переход к следующему элементу"""
        active_panel = self.get_active_panel()
        active_panel.move_down()

    def move_element_up(self):
        """Переход к предыдущему элементу"""
        active_panel = self.get_active_panel()
        active_panel.move_up()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Обрабатываем ввод команды"""
        user_input = event.value.strip()

        if not user_input:
            return

        # Обрабатываем команды
        if user_input.lower() == "exit":
            self.exit()
            return
        elif user_input.lower() == "clear":
            active_panel = self.get_active_panel()
            active_panel.clear_elements()
        elif user_input.lower() == "help":
            self.show_help()
        elif user_input.lower() == "reset":
            self.reset_all_panels()
        else:
            # Добавляем новый элемент
            active_panel = self.get_active_panel()
            active_panel.add_element(user_input)

        # Очищаем поле ввода
        event.input.value = ""

    def show_help(self):
        """Показываем справку"""
        help_elements = [
            "=== УМНАЯ НАВИГАЦИЯ ===",
            "• ← на любой панели = СВОРАЧИВАНИЕ",
            "  - Сворачивает текущую и все правее",
            "  - Скрытые панели слева заполняют место",
            "",
            "=== CTRL+СТРЕЛКИ ===",
            "• Ctrl+→ = переход к следующей видимой панели",
            "• Ctrl+← = переход к предыдущей видимой панели",
            "• Ctrl+← НА ПЕРВОЙ ПАНЕЛИ при наличии скрытых слева:",
            "  - Смещает панели ВПРАВО",
            "  - Скрытая панель слева → становится первой",
            "  - Первая панель → становится второй",
            "  - Вторая панель → становится третьей",
            "",
            "=== ЗАГОЛОВОК ===",
            "• Показывает название текущей панели",
            "• ◀ название - скрытые панели слева",
            "• название ▶ - скрытые панели справа",
            "",
            "=== НАВИГАЦИЯ ВПЕРЕД ===",
            "• Enter на элементе:",
            "  - Панели 1-2: открывает следующую",
            "  - Панель ≥3: СДВИГ влево (вперед в истории)",
            "",
            "=== НАВИГАЦИЯ НАЗАД ===",
            "• ← (левая стрелка) = умное сворачивание:",
            "  - На панели 1: ничего не происходит",
            "  - На панели 2: остается только панель 1",
            "  - На панели 3: остаются панели 1-2",
            "  - При наличии скрытых панелей слева:",
            "    они заполняют освободившееся место",
            "",
            "=== УПРАВЛЕНИЕ ===",
            "• ↑/↓ - навигация по элементам",
            "• Enter - открыть элемент",
            "• ← - умное сворачивание",
            "• Ctrl+←/→ - навигация между панелями",
            "• Ctrl+← на первой панели - показать скрытую слева",
            "",
            "=== ВВОД ТЕКСТА ===",
            "• Поле ввода всегда активно",
            "• Пустое поле = навигация клавишами",
            "• Есть текст = редактирование текста",
            "• Esc - очистить поле ввода",
            "",
            "=== КОМАНДЫ ===",
            "• текст - добавить элемент",
            "• clear - очистить панель",
            "• reset - сброс к началу",
            "• exit - выход"
        ]

        active_panel = self.get_active_panel()
        active_panel.elements = help_elements
        active_panel.active_element = 0
        active_panel.scroll_offset = 0

    def reset_all_panels(self):
        """Сброс к начальному состоянию"""
        # Сбрасываем всё к началу
        self.visible_panels = 1
        self.active_panel = 0
        self.panel_offset = 0

        # Сбрасываем стек панелей
        initial_data = {
            'elements': ["📁 Документы", "📁 Проекты", "📁 Изображения", "📄 readme.txt", "📄 config.json"],
            'path': "Корневая папка",
            'active_element': 0,
            'scroll_offset': 0
        }
        self.panel_stack = [initial_data]

        # Загружаем начальное состояние
        self.load_panels_from_stack()

        print("🔄 Сброс к начальному состоянию выполнен")


def main():
    """Главная функция"""
    print("🚀 Файловый менеджер с полной навигацией")
    print("=" * 70)
    print("УМНОЕ СВОРАЧИВАНИЕ:")
    print("• ← на любой панели сворачивает её и все правее")
    print("• Скрытые панели слева автоматически заполняют место")
    print("• На панели 1: ← ничего не делает")
    print("• На панели 2: ← оставляет только панель 1")
    print("• На панели 3: ← оставляет панели 1-2")
    print()
    print("CTRL+СТРЕЛКИ (УМНАЯ НАВИГАЦИЯ):")
    print("• Ctrl+→ - переход к следующей видимой панели")
    print("• Ctrl+← - переход к предыдущей видимой панели")
    print("• Ctrl+← НА ПЕРВОЙ ПАНЕЛИ (при наличии скрытых слева):")
    print("  - Смещает все панели ВПРАВО")
    print("  - Скрытая панель слева → первая панель")
    print("  - Первая панель → вторая панель")
    print("  - Вторая панель → третья панель")
    print("  - Позволяет 'листать' назад по истории навигации")
    print()
    print("ИНФОРМАТИВНЫЙ ЗАГОЛОВОК:")
    print("• Показывает название текущей активной панели")
    print("• ◀ название - если есть скрытые панели слева")
    print("• название ▶ - если есть скрытые панели справа")
    print("• Пример: '◀ Документы | Архив | tests ▶'")
    print()
    print("НАВИГАЦИЯ ВПЕРЕД:")
    print("• Enter на панелях 1-2 - открывает следующую")
    print("• Enter на панели ≥3 - СДВИГ панелей влево (вперед)")
    print("• Показывает панель с большим номером")
    print()
    print("УПРАВЛЕНИЕ:")
    print("• ↑/↓ - перемещение по элементам")
    print("• Enter - открыть элемент (движение вперед)")
    print("• ← - умное сворачивание")
    print("• Ctrl+←/→ - навигация между панелями + смещение при необходимости")
    print()
    print("ВОЗМОЖНОСТИ:")
    print("• Бесконечная глубина навигации в обе стороны")
    print("• Интуитивное сворачивание панелей")
    print("• Полная навигация по истории с Ctrl+стрелками")
    print("• Полная информация о местоположении в заголовке")
    print("• Сохранение состояния всех панелей")
    print("=" * 70)

    input("Нажмите Enter для запуска...")

    app = ThreePanelApp()
    app.run()


if __name__ == "__main__":
    main()