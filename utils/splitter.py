# build_project.py
import sys
import os
import re


def create_project_from_file(source_file_path):
    """
    Создает структуру папок и файлов на основе одного исходного файла.

    Исходный файл должен содержать строки-маркеры, указывающие пути к файлам.
    Весь текст после строки-маркера (до следующего маркера или конца файла)
    сохраняется в соответствующий файл.

    Примеры строк-маркеров:
    - my_project/module/main.py
    - # my_project/utils/helpers.py

    Args:
        source_file_path (str): Путь к исходному файлу .py.
    """

    # --- Вспомогательная функция для записи файла ---
    def write_file(path, content):
        """Создает необходимые директории и записывает контент в файл."""
        try:
            # Заменяем слэши для совместимости с текущей ОС
            path = os.path.normpath(path)
            # Получаем директорию из пути к файлу
            directory = os.path.dirname(path)

            # Создаем директории, если они не существуют
            # `exist_ok=True` предотвращает ошибку, если папки уже есть
            if directory:
                os.makedirs(directory, exist_ok=True)

            # Записываем контент в файл
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Успешно создан: {path}")

        except OSError as e:
            print(f"Ошибка при создании файла '{path}': {e}")
        except Exception as e:
            print(f"Произошла непредвиденная ошибка: {e}")

    # --- Основная логика ---

    if not os.path.isfile(source_file_path):
        print(f"Ошибка: Исходный файл не найден по пути '{source_file_path}'")
        return

    print(f"Обработка файла: {source_file_path}\n")

    with open(source_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Регулярное выражение для определения строки, содержащей путь к файлу.
    # Оно ищет строки, которые:
    # 1. Могут начинаться с '#' и пробелов.
    # 2. Содержат путь с как минимум одним слэшем ('/' или '\\').
    # 3. Не содержат пробелов в самом пути.
    # 4. Заканчиваются расширением файла (например, .py, .txt).
    # Это помогает отличить маркеры от обычных комментариев.
    path_pattern = re.compile(r'^\s*#?\s*([a-zA-Z0-9_./\\-]+\.\w+)\s*$')

    active_path = None
    content_buffer = []

    for line in lines:
        match = path_pattern.match(line)

        if match:
            # Найдена новая строка с путем к файлу.

            # 1. Если у нас есть накопленный контент для предыдущего файла,
            #    сохраняем его.
            if active_path:
                write_file(active_path, ''.join(content_buffer))

            # 2. Начинаем обработку нового файла.
            active_path = match.group(1).strip()  # Извлекаем чистый путь
            content_buffer = []  # Очищаем буфер для нового контента
        else:
            # Это обычная строка кода.
            # Если мы уже определили, в какой файл писать, добавляем строку
            # в буфер контента.
            if active_path:
                content_buffer.append(line)

    # После окончания цикла не забываем сохранить последний накопленный файл.
    if active_path and content_buffer:
        write_file(active_path, ''.join(content_buffer))

    print("\nПроцесс завершен.")


# --- Точка входа в программу ---
if __name__ == "__main__":
    # Проверяем, был ли передан аргумент командной строки (путь к файлу)
    if len(sys.argv) < 2:
        # Если нет, выводим инструкцию и создаем демонстрационный файл
        script_name = os.path.basename(sys.argv[0])
        print(f"Использование: python {script_name} <путь_к_исходному_файлу>")

        demo_filename = "panelflow-single.py"
        demo_content = """panelflow/core/__init__.py
# Этот файл важен для Python,
# чтобы распознать 'core' как пакет.

# panelflow/core/events.py
class Event:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"Event({self.name})"

# panelflow/core/components.py
# Код для компонентов
class Component:
    def __init__(self, component_id):
        self.id = component_id
        print(f"Component {self.id} initialized.")

panelflow/ui/engine.py
# Код для UI движка
def start_ui():
    print("UI Engine is starting...")
    # Здесь могла бы быть логика инициализации UI
"""
        with open(demo_filename, "w", encoding="utf-8") as f:
            f.write(demo_content)

        print(f"\nСоздан демонстрационный файл '{demo_filename}'.")
        print(f"Попробуйте запустить: python {script_name} {demo_filename}")

    else:
        # Если аргумент передан, запускаем основную функцию
        input_file = sys.argv[1]
        create_project_from_file(input_file)