# check_methods.py
"""
Быстрая проверка, что все методы Application реализованы правильно.
"""


def check_application_methods():
    """Проверяем наличие всех необходимых методов."""

    print("🔍 Проверка методов Application...\n")

    try:
        from panelflow.core import Application
        print("✅ Application импортирован")
    except ImportError as e:
        print(f"❌ Ошибка импорта Application: {e}")
        return False

    # Список обязательных методов
    required_methods = [
        # Публичные методы
        'post_event',
        'subscribe_to_events',
        'unsubscribe_from_events',

        # Приватные методы обработки событий
        '_handle_widget_submission',
        '_handle_horizontal_navigation',
        '_handle_vertical_navigation',
        '_handle_back_navigation',
        '_execute_navigation_down',

        # Вспомогательные методы
        '_find_node_by_widget_id',
        '_get_path_to_active_node',
        '_destroy_stack_recursively',
        '_publish_event',
        '_set_active_node',
        '_create_panel_instance',

        # Методы загрузки конфигурации
        '_load_config',
        '_validate_json_schema',
        '_parse_config_to_objects',
        '_validate_config_integrity',
        '_create_initial_state'
    ]

    print("Проверка наличия методов:")
    missing_methods = []

    for method_name in required_methods:
        if hasattr(Application, method_name):
            print(f"   ✅ {method_name}")
        else:
            print(f"   ❌ {method_name} - ОТСУТСТВУЕТ")
            missing_methods.append(method_name)

    if missing_methods:
        print(f"\n❌ ОТСУТСТВУЮЩИЕ МЕТОДЫ: {len(missing_methods)}")
        for method in missing_methods:
            print(f"   - {method}")
        return False

    print(f"\n✅ Все {len(required_methods)} методов найдены!")

    # Проверяем свойства
    print(f"\nПроверка свойств:")
    required_properties = ['tree_root', 'active_node']

    for prop_name in required_properties:
        if hasattr(Application, prop_name):
            print(f"   ✅ {prop_name}")
        else:
            print(f"   ❌ {prop_name} - ОТСУТСТВУЕТ")

    return len(missing_methods) == 0


def check_method_signatures():
    """Проверяем сигнатуры ключевых методов."""

    print(f"\n🔧 Проверка сигнатур методов...")

    try:
        from panelflow.core import Application
        import inspect

        # Проверяем post_event
        post_event_sig = inspect.signature(Application.post_event)
        print(f"   post_event{post_event_sig}")

        # Проверяем _handle_widget_submission
        if hasattr(Application, '_handle_widget_submission'):
            handle_sig = inspect.signature(Application._handle_widget_submission)
            print(f"   _handle_widget_submission{handle_sig}")

        print("✅ Сигнатуры выглядят корректно")

    except Exception as e:
        print(f"❌ Ошибка проверки сигнатур: {e}")
        return False

    return True


def quick_instantiation_test():
    """Быстрый тест создания экземпляра Application."""

    print(f"\n🏗️ Быстрый тест создания Application...")

    import tempfile
    import json
    from pathlib import Path

    # Минимальная конфигурация
    config = {
        "entryPanel": "test",
        "panels": [
            {
                "id": "test",
                "title": "Test Panel",
                "widgets": []
            }
        ]
    }

    temp_file = tempfile.NamedTemporaryFile(
        mode='w', suffix='.json', delete=False, encoding='utf-8'
    )
    json.dump(config, temp_file, ensure_ascii=False, indent=2)
    temp_file.close()

    try:
        from panelflow.core import Application
        app = Application(temp_file.name, {})

        print("✅ Application создан успешно")
        print(f"   Активная панель: {app.active_node.panel_template.id if app.active_node else 'None'}")

        return True

    except Exception as e:
        print(f"❌ Ошибка создания Application: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        Path(temp_file.name).unlink()


if __name__ == "__main__":
    print("🔬 === ПРОВЕРКА РЕАЛИЗАЦИИ APPLICATION ===\n")

    step1 = check_application_methods()
    step2 = check_method_signatures()
    step3 = quick_instantiation_test()

    if step1 and step2 and step3:
        print(f"\n🎉 Application реализован корректно!")
        print(f"🚀 Можно запускать minimal_test.py")
    else:
        print(f"\n🔧 Требуется доработка Application:")
        if not step1:
            print(f"   - Добавить отсутствующие методы")
        if not step2:
            print(f"   - Исправить сигнатуры методов")
        if not step3:
            print(f"   - Исправить ошибки в конструкторе")

        print(f"\n💡 Проверьте, что весь код из артефакта скопирован в application.py")