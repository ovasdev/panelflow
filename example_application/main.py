"""
Пример использования panelflow.tui с ядром panelflow.core.

Этот пример демонстрирует создание простого TUI-приложения
с использованием JSON-конфигурации и пользовательских обработчиков.
"""

import json
from pathlib import Path
from typing import Any

# Импорты из panelflow.core
from panelflow.core import Application as CoreApplication
from panelflow.core.handlers import BasePanelHandler

# Импорт TUI-рендерера
from panelflow.tui import TuiApplication
from panelflow.logging_config import init_core_logging

init_core_logging()

# Пример пользовательского обработчика
class MainMenuHandler(BasePanelHandler):
    """
    Обработчик для главного меню приложения.
    """

    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        """
        Обработка обновлений виджетов в главном меню.
        """
        if widget_id == "settings_button":
            # Переход к панели настроек
            return ("navigate_down", "settings_panel")

        elif widget_id == "files_button":
            # Переход к панели файлов
            return ("navigate_down", "files_panel")

        elif widget_id == "name_input":
            # Сохраняем имя пользователя в контексте
            print(f"Пользователь ввел имя: {value}")
            return None

        return None


class FilesHandler(BasePanelHandler):
    """
    Обработчик для панели работы с файлами.
    """

    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        """
        Обработка действий с файлами.
        """
        if widget_id == "file_type_select":
            print(f"Выбран тип файла: {value}")
            # Можно создать динамическую панель на основе выбора
            return None

        elif widget_id == "open_button":
            print("Открытие файла...")
            return None

        return None


def create_example_config():
    """
    Создание примера конфигурации application.json.
    """
    config = {
        "entryPanel": "main_menu",
        "panels": [
            {
                "id": "main_menu",
                "title": "Главное меню",
                "description": "Добро пожаловать в PanelFlow!",
                "handler_class_name": "MainMenuHandler",
                "widgets": [
                    {
                        "id": "name_input",
                        "type": "text_input",
                        "title": "Ваше имя",
                        "placeholder": "Введите ваше имя...",
                        "value": ""
                    },
                    {
                        "id": "settings_button",
                        "type": "button",
                        "title": "Настройки",
                        "value": "settings"
                    },
                    {
                        "id": "files_button",
                        "type": "button",
                        "title": "Работа с файлами",
                        "value": "files"
                    },
                    {
                        "id": "about_link",
                        "type": "panel_link",
                        "title": "О программе",
                        "description": "Информация о PanelFlow",
                        "target_panel_id": "about_panel"
                    }
                ]
            },
            {
                "id": "settings_panel",
                "title": "Настройки",
                "description": "Настройки приложения",
                "widgets": [
                    {
                        "id": "theme_select",
                        "type": "option_select",
                        "title": "Выберите тему",
                        "options": ["Светлая", "Темная", "Автоматическая"],
                        "value": "Темная"
                    },
                    {
                        "id": "save_button",
                        "type": "button",
                        "title": "Сохранить настройки",
                        "value": "save"
                    }
                ]
            },
            {
                "id": "files_panel",
                "title": "Файлы",
                "description": "Работа с файлами",
                "handler_class_name": "FilesHandler",
                "widgets": [
                    {
                        "id": "file_type_select",
                        "type": "option_select",
                        "title": "Тип файла",
                        "options": ["Текстовые", "Изображения", "Документы"],
                        "value": "Текстовые"
                    },
                    {
                        "id": "file_path_input",
                        "type": "text_input",
                        "title": "Путь к файлу",
                        "placeholder": "/path/to/file"
                    },
                    {
                        "id": "open_button",
                        "type": "button",
                        "title": "Открыть файл",
                        "value": "open"
                    }
                ]
            },
            {
                "id": "about_panel",
                "title": "О программе",
                "description": "PanelFlow - фреймворк для создания многопанельных приложений",
                "widgets": [
                    {
                        "id": "version_info",
                        "type": "text_input",
                        "title": "Версия",
                        "value": "1.0.0"
                    }
                ]
            }
        ]
    }

    return config


def main():
    """
    Главная функция запуска примера TUI-приложения.
    """

    # Создаем конфигурацию
    config = create_example_config()

    # Сохраняем во временный файл
    config_path = Path("example_application.json")
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

    try:
        # Словарь обработчиков
        handler_map = {
            "MainMenuHandler": MainMenuHandler,
            "FilesHandler": FilesHandler,
        }

        # Создаем ядро приложения
        core_app = CoreApplication(config_path, handler_map)

        # Создаем TUI-приложение
        tui_app = TuiApplication(core_app)

        # Запускаем приложение
        tui_app.run()

    except Exception as e:
        print(f"Ошибка при запуске приложения: {e}")

    finally:
        # Удаляем временный файл конфигурации
        if config_path.exists():
            config_path.unlink()


if __name__ == "__main__":
    main()