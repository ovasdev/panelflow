# test_config_loader.py
"""
Тесты для загрузчика конфигурации PanelFlow.
Проверяют валидацию, парсинг и целостность конфигурации.
"""

import pytest
import json
import tempfile
from pathlib import Path
from jsonschema import ValidationError

from panelflow.core import Application
from panelflow.core.handlers import BasePanelHandler
from panelflow.core.components import AbstractTextInput, AbstractButton, PanelLink


class TestHandler(BasePanelHandler):
    """Тестовый обработчик для проверок."""

    def on_widget_update(self, widget_id: str, value: None) -> tuple | None:
        return None


class TestConfigLoader:
    """Тесты загрузчика конфигурации."""

    def setup_method(self):
        """Подготовка к тестам."""
        self.handler_map = {"TestHandler": TestHandler}

        # Базовая валидная конфигурация
        self.valid_config = {
            "entryPanel": "main",
            "panels": [
                {
                    "id": "main",
                    "title": "Main Panel",
                    "description": "Main panel description",
                    "handler_class_name": "TestHandler",
                    "widgets": [
                        {
                            "id": "text_input",
                            "type": "text_input",
                            "title": "Text Input",
                            "placeholder": "Enter text"
                        },
                        {
                            "id": "button",
                            "type": "button",
                            "title": "Submit"
                        }
                    ]
                }
            ]
        }

    def create_temp_config(self, config_data: dict) -> Path:
        """Создание временного файла конфигурации."""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False,
            encoding='utf-8'
        )
        json.dump(config_data, temp_file, ensure_ascii=False, indent=2)
        temp_file.close()
        return Path(temp_file.name)

    def test_valid_config_loading(self):
        """Тест успешной загрузки валидной конфигурации."""
        config_path = self.create_temp_config(self.valid_config)

        try:
            app = Application(config_path, self.handler_map)

            # Проверки
            assert app._entry_panel_id == "main"
            assert len(app._panel_templates) == 1
            assert "main" in app._panel_templates

            main_panel = app._panel_templates["main"]
            assert main_panel.title == "Main Panel"
            assert len(main_panel.widgets) == 2
            assert isinstance(main_panel.widgets[0], AbstractTextInput)
            assert isinstance(main_panel.widgets[1], AbstractButton)

            # Проверка начального состояния
            assert app.tree_root is not None
            assert app.active_node is not None
            assert app.active_node.panel_template.id == "main"
            assert app.active_node.is_active is True

        finally:
            config_path.unlink()  # Удаление временного файла

    def test_missing_config_file(self):
        """Тест ошибки при отсутствии файла конфигурации."""
        with pytest.raises(FileNotFoundError):
            Application("nonexistent.json", self.handler_map)

    def test_invalid_json(self):
        """Тест ошибки при невалидном JSON."""
        temp_file = tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.json',
            delete=False
        )
        temp_file.write("{ invalid json }")
        temp_file.close()

        try:
            with pytest.raises(json.JSONDecodeError):
                Application(temp_file.name, self.handler_map)
        finally:
            Path(temp_file.name).unlink()

    def test_schema_validation_missing_required_fields(self):
        """Тест валидации схемы - отсутствие обязательных полей."""
        invalid_configs = [
            # Отсутствует entryPanel
            {
                "panels": [{"id": "main", "title": "Main"}]
            },
            # Отсутствует panels
            {
                "entryPanel": "main"
            },
            # Отсутствует id панели
            {
                "entryPanel": "main",
                "panels": [{"title": "Main"}]
            },
            # Отсутствует title панели
            {
                "entryPanel": "main",
                "panels": [{"id": "main"}]
            }
        ]

        for invalid_config in invalid_configs:
            config_path = self.create_temp_config(invalid_config)
            try:
                with pytest.raises(ValidationError):
                    Application(config_path, self.handler_map)
            finally:
                config_path.unlink()

    def test_schema_validation_invalid_widget_types(self):
        """Тест валидации неизвестных типов виджетов."""
        invalid_config = {
            "entryPanel": "main",
            "panels": [
                {
                    "id": "main",
                    "title": "Main",
                    "widgets": [
                        {
                            "id": "invalid_widget",
                            "type": "unknown_type",  # Неизвестный тип
                            "title": "Invalid Widget"
                        }
                    ]
                }
            ]
        }

        config_path = self.create_temp_config(invalid_config)
        try:
            with pytest.raises(ValidationError):
                Application(config_path, self.handler_map)
        finally:
            config_path.unlink()

    def test_integrity_nonexistent_entry_panel(self):
        """Тест проверки целостности - несуществующая entryPanel."""
        invalid_config = {
            "entryPanel": "nonexistent",
            "panels": [
                {
                    "id": "main",
                    "title": "Main Panel"
                }
            ]
        }

        config_path = self.create_temp_config(invalid_config)
        try:
            with pytest.raises(ValueError, match="Панель входа 'nonexistent' не найдена"):
                Application(config_path, self.handler_map)
        finally:
            config_path.unlink()

    def test_integrity_invalid_panel_link_target(self):
        """Тест проверки целостности - несуществующий target_panel_id."""
        invalid_config = {
            "entryPanel": "main",
            "panels": [
                {
                    "id": "main",
                    "title": "Main Panel",
                    "widgets": [
                        {
                            "id": "link",
                            "type": "panel_link",
                            "title": "Go to Settings",
                            "target_panel_id": "nonexistent"  # Несуществующая панель
                        }
                    ]
                }
            ]
        }

        config_path = self.create_temp_config(invalid_config)
        try:
            with pytest.raises(ValueError, match="Целевая панель 'nonexistent'"):
                Application(config_path, self.handler_map)
        finally:
            config_path.unlink()

    def test_integrity_invalid_handler_class(self):
        """Тест проверки целостности - несуществующий обработчик."""
        invalid_config = {
            "entryPanel": "main",
            "panels": [
                {
                    "id": "main",
                    "title": "Main Panel",
                    "handler_class_name": "NonexistentHandler",  # Несуществующий обработчик
                    "widgets": [
                        {
                            "id": "button",
                            "type": "button",
                            "title": "Button"
                        }
                    ]
                }
            ]
        }

        config_path = self.create_temp_config(invalid_config)
        try:
            with pytest.raises(ValueError, match="Обработчик 'NonexistentHandler'"):
                Application(config_path, self.handler_map)
        finally:
            config_path.unlink()

    def test_widget_creation_all_types(self):
        """Тест создания всех типов виджетов."""
        config_with_all_widgets = {
            "entryPanel": "main",
            "panels": [
                {
                    "id": "main",
                    "title": "Main Panel",
                    "widgets": [
                        {
                            "id": "text",
                            "type": "text_input",
                            "title": "Text Input",
                            "placeholder": "Enter text",
                            "value": "default"
                        },
                        {
                            "id": "button",
                            "type": "button",
                            "title": "Button"
                        },
                        {
                            "id": "select",
                            "type": "option_select",
                            "title": "Select",
                            "options": ["Option 1", "Option 2"],
                            "value": "Option 1"
                        },
                        {
                            "id": "link",
                            "type": "panel_link",
                            "title": "Link",
                            "target_panel_id": "target",
                            "description": "Go to target"
                        }
                    ]
                },
                {
                    "id": "target",
                    "title": "Target Panel"
                }
            ]
        }

        config_path = self.create_temp_config(config_with_all_widgets)
        try:
            app = Application(config_path, self.handler_map)

            widgets = app._panel_templates["main"].widgets
            assert len(widgets) == 4

            # Проверка типов виджетов
            assert isinstance(widgets[0], AbstractTextInput)
            assert widgets[0].placeholder == "Enter text"
            assert widgets[0].value == "default"

            assert isinstance(widgets[1], AbstractButton)

            from panelflow.core.components import AbstractOptionSelect
            assert isinstance(widgets[2], AbstractOptionSelect)
            assert widgets[2].options == ["Option 1", "Option 2"]
            assert widgets[2].value == "Option 1"

            assert isinstance(widgets[3], PanelLink)
            assert widgets[3].target_panel_id == "target"
            assert widgets[3].description == "Go to target"

        finally:
            config_path.unlink()


if __name__ == "__main__":
    # Запуск тестов
    pytest.main([__file__, "-v"])