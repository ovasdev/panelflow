# debug_navigation.py
"""
Диагностический скрипт для отладки проблем с навигацией.
"""

import tempfile
import json
from pathlib import Path
from typing import Any

from panelflow.core import Application
from panelflow.core.handlers import BasePanelHandler
from panelflow.core.events import WidgetSubmittedEvent, StateChangedEvent, ErrorOccurredEvent


class DebugHandler(BasePanelHandler):
    """Обработчик с детальной отладкой."""

    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        print(f"\n🔧 === ВЫЗОВ ОБРАБОТЧИКА ===")
        print(f"widget_id: {widget_id}")
        print(f"value: {value}")
        print(f"context: {self.context}")
        print(f"form_data: {self.form_data}")

        if widget_id == "goto_child":
            command = ("navigate_down", "child")
            print(f"ВОЗВРАЩАЮ: {command}")
            return command
        else:
            print("ВОЗВРАЩАЮ: None")
            return None


def create_debug_config():
    """Минимальная конфигурация для отладки."""
    return {
        "entryPanel": "main",
        "panels": [
            {
                "id": "main",
                "title": "Главная",
                "handler_class_name": "DebugHandler",
                "widgets": [
                    {
                        "id": "goto_child",
                        "type": "button",
                        "title": "К дочерней панели"
                    }
                ]
            },
            {
                "id": "child",
                "title": "Дочерняя",
                "widgets": [
                    {
                        "id": "child_button",
                        "type": "button",
                        "title": "Дочерняя кнопка"
                    }
                ]
            }
        ]
    }


def debug_application_methods():
    """Отладка методов Application."""

    print("🔍 === ОТЛАДКА МЕТОДОВ APPLICATION ===\n")

    # Создаем приложение
    config = create_debug_config()
    handler_map = {"DebugHandler": DebugHandler}

    temp_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False, encoding='utf-8'
    )
    json.dump(config, temp_file, ensure_ascii=False, indent=2)
    temp_file.close()

    try:
        app = Application(temp_file.name, handler_map)

        print("1. НАЧАЛЬНОЕ СОСТОЯНИЕ:")
        print(f"   active_node: {app.active_node.panel_template.id}")
        print(f"   is_active: {app.active_node.is_active}")
        print(f"   children_stacks: {app.active_node.children_stacks}")

        # Отладка поиска виджета
        print(f"\n2. ПОИСК ВИДЖЕТА 'goto_child':")
        found_node = app._find_node_by_widget_id("goto_child")
        if found_node:
            print(f"   ✅ Найден в панели: {found_node.panel_template.id}")

            # Проверяем сам виджет
            for widget in found_node.panel_template.widgets:
                if widget.id == "goto_child":
                    print(f"   Виджет: {widget.type} '{widget.title}'")
                    break
        else:
            print("   ❌ Виджет не найден!")
            return

        # Проверяем панель назначения
        print(f"\n3. ПРОВЕРКА ПАНЕЛИ 'child':")
        if "child" in app._panel_templates:
            child_panel = app._panel_templates["child"]
            print(f"   ✅ Панель найдена: '{child_panel.title}'")
        else:
            print("   ❌ Панель 'child' не найдена!")
            return

        # Подписываемся на события
        events = []

        def event_handler(event):
            events.append(event)
            print(f"\n📢 СОБЫТИЕ: {type(event).__name__}")
            if isinstance(event, ErrorOccurredEvent):
                print(f"   ❌ ОШИБКА: {event.title} - {event.message}")

        app.subscribe_to_events(event_handler)

        print(f"\n4. ОТПРАВКА СОБЫТИЯ WidgetSubmittedEvent:")
        print(f"   Отправляю: widget_id='goto_child', value=True")

        app.post_event(WidgetSubmittedEvent(widget_id="goto_child", value=True))

        print(f"\n5. СОСТОЯНИЕ ПОСЛЕ СОБЫТИЯ:")
        print(f"   active_node: {app.active_node.panel_template.id}")
        print(f"   События получено: {len(events)}")

        if app.active_node.parent:
            print(f"   Родитель: {app.active_node.parent.panel_template.id}")
            print(f"   Стеки родителя: {list(app.active_node.parent.children_stacks.keys())}")

        # Проверяем, есть ли ошибки
        for event in events:
            if isinstance(event, ErrorOccurredEvent):
                print(f"\n❌ НАЙДЕНА ОШИБКА:")
                print(f"   Заголовок: {event.title}")
                print(f"   Сообщение: {event.message}")

        if app.active_node.panel_template.id == "child":
            print(f"\n🎉 УСПЕХ! Навигация сработала корректно")
        else:
            print(f"\n❌ ПРОВАЛ! Ожидали 'child', получили '{app.active_node.panel_template.id}'")

            # Дополнительная диагностика
            print(f"\nДОПОЛНИТЕЛЬНАЯ ДИАГНОСТИКА:")
            print(f"   Метод _handle_widget_submission существует: {hasattr(app, '_handle_widget_submission')}")
            print(f"   Метод _execute_navigation_down существует: {hasattr(app, '_execute_navigation_down')}")
            print(f"   Обработчик в handler_map: {'DebugHandler' in app.handler_map}")

    finally:
        Path(temp_file.name).unlink()


if __name__ == "__main__":
    debug_application_methods()