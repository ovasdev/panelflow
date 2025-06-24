# simple_test.py
"""
Простой тест для проверки основного функционала системы навигации.
"""

import tempfile
import json
from pathlib import Path
from typing import Any

# Импортируем все компоненты PanelFlow
from panelflow.core import Application
from panelflow.core.handlers import BasePanelHandler
from panelflow.core.events import (
    WidgetSubmittedEvent,
    HorizontalNavigationEvent,
    BackNavigationEvent,
    StateChangedEvent,
    ErrorOccurredEvent
)


class SimpleHandler(BasePanelHandler):
    """Простой обработчик для тестирования."""

    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        print(f"Обработчик вызван: widget_id={widget_id}, value={value}")

        if widget_id == "goto_child":
            print("→ Навигация к дочерней панели")
            return ("navigate_down", "child")

        return None


def create_simple_config():
    """Создает простую конфигурацию для тестирования."""
    return {
        "entryPanel": "main",
        "panels": [
            {
                "id": "main",
                "title": "Главная",
                "description": "Главная панель",
                "handler_class_name": "SimpleHandler",
                "widgets": [
                    {
                        "id": "text_field",
                        "type": "text_input",
                        "title": "Текстовое поле",
                        "placeholder": "Введите текст"
                    },
                    {
                        "id": "goto_child",
                        "type": "button",
                        "title": "Перейти к дочерней панели"
                    }
                ]
            },
            {
                "id": "child",
                "title": "Дочерняя",
                "description": "Дочерняя панель",
                "widgets": [
                    {
                        "id": "child_button",
                        "type": "button",
                        "title": "Кнопка в дочерней панели"
                    }
                ]
            }
        ]
    }


def main():
    """Основная функция тестирования."""
    print("🚀 Запуск простого теста навигации PanelFlow\n")

    # Создаем обработчики
    handler_map = {"SimpleHandler": SimpleHandler}

    # Создаем временный файл конфигурации
    config = create_simple_config()
    temp_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False, encoding='utf-8'
    )
    json.dump(config, temp_file, ensure_ascii=False, indent=2)
    temp_file.close()

    try:
        # Создаем приложение
        print("1. Создание приложения...")
        app = Application(temp_file.name, handler_map)
        print("✅ Приложение создано")

        # Подписываемся на события
        events_received = []

        def event_callback(event):
            events_received.append(event)
            print(f"📢 Получено событие: {type(event).__name__}")

        app.subscribe_to_events(event_callback)

        # Тест 1: Проверка начального состояния
        print("\n2. Проверка начального состояния...")
        assert app.tree_root is not None
        assert app.active_node is not None
        assert app.active_node.panel_template.id == "main"
        assert app.active_node.is_active == True
        print("✅ Начальное состояние корректно")

        # Тест 2: Заполнение формы
        print("\n3. Заполнение текстового поля...")
        events_received.clear()
        app.post_event(WidgetSubmittedEvent(widget_id="text_field", value="test data"))

        assert len(events_received) == 1
        assert isinstance(events_received[0], StateChangedEvent)
        assert app.active_node.form_data["text_field"] == "test data"
        print("✅ Заполнение формы работает")

        # Тест 3: Навигация вниз
        print("\n4. Тест навигации к дочерней панели...")
        events_received.clear()
        app.post_event(WidgetSubmittedEvent(widget_id="goto_child", value=True))

        assert len(events_received) == 1
        assert isinstance(events_received[0], StateChangedEvent)
        assert app.active_node.panel_template.id == "child"
        assert app.active_node.parent.panel_template.id == "main"
        assert "test data" in str(app.active_node.context)  # Данные должны передаться
        print("✅ Навигация вниз работает")

        # Тест 4: Горизонтальная навигация
        print("\n5. Тест горизонтальной навигации...")
        events_received.clear()

        # Идем влево (к родителю)
        app.post_event(HorizontalNavigationEvent(direction="previous"))
        assert app.active_node.panel_template.id == "main"

        # Идем вправо (к дочерней)
        app.post_event(HorizontalNavigationEvent(direction="next"))
        assert app.active_node.panel_template.id == "child"

        print("✅ Горизонтальная навигация работает")

        # Тест 5: Навигация назад
        print("\n6. Тест навигации назад...")
        events_received.clear()
        app.post_event(BackNavigationEvent())

        assert app.active_node.panel_template.id == "main"
        assert len(app.active_node.children_stacks) == 0  # Дочерние стеки очищены
        print("✅ Навигация назад работает")

        # Тест 6: Повторная навигация (проверка замены стека)
        print("\n7. Тест повторной навигации...")

        # Создаем новую дочернюю панель
        app.post_event(WidgetSubmittedEvent(widget_id="goto_child", value=True))
        new_child_id = app.active_node.node_id

        # Возвращаемся
        app.post_event(BackNavigationEvent())

        # Создаем еще одну дочернюю панель
        app.post_event(WidgetSubmittedEvent(widget_id="goto_child", value=True))
        another_child_id = app.active_node.node_id

        # ID должны отличаться (новые экземпляры)
        assert new_child_id != another_child_id
        print("✅ Замена стека работает")

        # Сводка
        print("\n🎉 Все тесты пройдены успешно!")
        print(f"📊 Всего событий обработано: {len(events_received)}")
        print(f"🏗️  Текущая структура:")
        print(f"   Корневая панель: {app.tree_root.panel_template.title}")
        print(f"   Активная панель: {app.active_node.panel_template.title}")
        print(f"   Дочерних стеков: {len(app.active_node.parent.children_stacks) if app.active_node.parent else 0}")

    except Exception as e:
        print(f"\n❌ Ошибка в тесте: {e}")
        import traceback
        traceback.print_exc()

    finally:
        # Удаляем временный файл
        Path(temp_file.name).unlink()


if __name__ == "__main__":
    main()