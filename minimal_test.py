# minimal_test.py
"""
Минимальный тест для пошаговой диагностики навигации.
"""

import tempfile
import json
from pathlib import Path
from typing import Any

from panelflow.core import Application
from panelflow.core.handlers import BasePanelHandler
from panelflow.core.events import WidgetSubmittedEvent, StateChangedEvent, ErrorOccurredEvent


class MinimalHandler(BasePanelHandler):
    """Минимальный обработчик с максимальной отладкой."""

    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        print(f"\n🎯 === ОБРАБОТЧИК ВЫЗВАН ===")
        print(f"widget_id: '{widget_id}'")
        print(f"value: {value}")
        print(f"context: {self.context}")
        print(f"form_data: {self.form_data}")

        if widget_id == "test_button":
            result = ("navigate_down", "second")
            print(f"🚀 Возвращаю команду: {result}")
            return result
        else:
            print(f"🚫 Неизвестный виджет, возвращаю None")
            return None


def create_minimal_config():
    """Минимальная конфигурация - всего 2 панели."""
    return {
        "entryPanel": "first",
        "panels": [
            {
                "id": "first",
                "title": "Первая панель",
                "handler_class_name": "MinimalHandler",
                "widgets": [
                    {
                        "id": "test_button",
                        "type": "button",
                        "title": "Тестовая кнопка"
                    }
                ]
            },
            {
                "id": "second",
                "title": "Вторая панель",
                "widgets": [
                    {
                        "id": "second_button",
                        "type": "button",
                        "title": "Кнопка второй панели"
                    }
                ]
            }
        ]
    }


def test_step_by_step():
    """Пошаговое тестирование каждого компонента."""

    print("🔬 === ПОШАГОВАЯ ДИАГНОСТИКА ===\n")

    # Шаг 1: Создание приложения
    print("📁 Шаг 1: Создание конфигурации и приложения")
    config = create_minimal_config()
    handler_map = {"MinimalHandler": MinimalHandler}

    temp_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False, encoding='utf-8'
    )
    json.dump(config, temp_file, ensure_ascii=False, indent=2)
    temp_file.close()

    try:
        app = Application(temp_file.name, handler_map)
        print("✅ Приложение создано успешно")
    except Exception as e:
        print(f"❌ Ошибка создания приложения: {e}")
        return
    finally:
        Path(temp_file.name).unlink()

    # Шаг 2: Проверка начального состояния
    print(f"\n🏠 Шаг 2: Проверка начального состояния")
    print(f"   Корневая панель: {app.tree_root.panel_template.id}")
    print(f"   Активная панель: {app.active_node.panel_template.id}")
    print(f"   Активность: {app.active_node.is_active}")
    print(f"   Дочерние стеки: {app.active_node.children_stacks}")
    print(f"   Доступные панели: {list(app._panel_templates.keys())}")

    if app.active_node.panel_template.id != "first":
        print(f"❌ Неверная начальная панель!")
        return
    print("✅ Начальное состояние корректно")

    # Шаг 3: Проверка поиска виджета
    print(f"\n🔍 Шаг 3: Тест поиска виджета")
    found_node = app._find_node_by_widget_id("test_button")
    if found_node:
        print(f"✅ Виджет найден в панели: {found_node.panel_template.id}")
    else:
        print(f"❌ Виджет 'test_button' не найден!")
        return

    # Шаг 4: Проверка целевой панели
    print(f"\n🎯 Шаг 4: Проверка целевой панели")
    if "second" in app._panel_templates:
        second_panel = app._panel_templates["second"]
        print(f"✅ Целевая панель найдена: '{second_panel.title}'")
    else:
        print(f"❌ Панель 'second' не найдена!")
        return

    # Шаг 5: Подписка на события
    print(f"\n📡 Шаг 5: Подписка на события")
    events = []

    def event_callback(event):
        events.append(event)
        print(f"   📢 Событие: {type(event).__name__}")
        if isinstance(event, ErrorOccurredEvent):
            print(f"      ❌ ОШИБКА: {event.title}")
            print(f"      📝 {event.message}")

    app.subscribe_to_events(event_callback)
    print("✅ Подписка оформлена")

    # Шаг 6: Отправка события
    print(f"\n🚀 Шаг 6: Отправка события навигации")
    print(f"   Отправляю: WidgetSubmittedEvent('test_button', True)")

    events.clear()
    app.post_event(WidgetSubmittedEvent(widget_id="test_button", value=True))

    # Шаг 7: Анализ результата
    print(f"\n📊 Шаг 7: Анализ результата")
    print(f"   События получено: {len(events)}")
    print(f"   Активная панель: {app.active_node.panel_template.id}")

    if events:
        for i, event in enumerate(events):
            print(f"   Событие {i + 1}: {type(event).__name__}")
            if isinstance(event, ErrorOccurredEvent):
                print(f"      ❌ {event.title}: {event.message}")

    # Проверяем навигацию
    if app.active_node.panel_template.id == "second":
        print(f"\n🎉 УСПЕХ! Навигация работает корректно")

        # Дополнительные проверки
        if app.active_node.parent:
            print(f"   ✅ Родитель: {app.active_node.parent.panel_template.id}")
            if "test_button" in app.active_node.parent.children_stacks:
                print(f"   ✅ Стек создан: test_button")
                stack = app.active_node.parent.children_stacks["test_button"]
                print(f"   ✅ В стеке: {[node.panel_template.id for node in stack]}")
            else:
                print(f"   ❌ Стек не создан!")
        else:
            print(f"   ❌ Нет родителя!")

    else:
        print(f"\n❌ ПРОВАЛ! Навигация не сработала")
        print(f"   Ожидали: 'second'")
        print(f"   Получили: '{app.active_node.panel_template.id}'")

        # Детальная диагностика
        print(f"\n🔧 ДЕТАЛЬНАЯ ДИАГНОСТИКА:")

        # Проверяем form_data (должны обновиться при любом событии)
        print(f"   1. Form data активной панели: {app.active_node.form_data}")
        if "test_button" in app.active_node.form_data:
            print(f"      ✅ Виджет обработан (_handle_widget_submission сработал)")
        else:
            print(f"      ❌ Виджет НЕ обработан (_handle_widget_submission НЕ сработал)")

        # Проверяем обработчик
        print(f"   2. Обработчик в handler_map: {'MinimalHandler' in app.handler_map}")

        # Проверяем методы
        print(f"   3. Метод _handle_widget_submission: {hasattr(app, '_handle_widget_submission')}")
        print(f"   4. Метод _execute_navigation_down: {hasattr(app, '_execute_navigation_down')}")
        print(f"   5. Метод post_event: {hasattr(app, 'post_event')}")

        # Проверяем структуру дерева
        print(f"   6. Дочерние стеки корня: {app.tree_root.children_stacks}")

        return False

    return True


if __name__ == "__main__":
    success = test_step_by_step()

    if success:
        print(f"\n🚀 Система навигации работает! Можно переходить к полным тестам.")
    else:
        print(f"\n🔧 Требуется исправление. Проанализируйте вывод выше.")
        print(f"\n💡 Возможные проблемы:")
        print(f"   1. Не реализован _handle_widget_submission")
        print(f"   2. Не реализован _execute_navigation_down")
        print(f"   3. Ошибка в логике обработчиков")
        print(f"   4. Проблема с системой событий")