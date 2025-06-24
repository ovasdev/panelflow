# interactive_test.py
from panelflow.core import Application
from example_handlers import HANDLER_MAP


def main():
    print("=== Тест загрузчика конфигурации PanelFlow ===\n")

    try:
        # Создание приложения
        print("1. Создание приложения...")
        app = Application("application.json", HANDLER_MAP)
        print("✅ Приложение создано успешно\n")

        # Информация о конфигурации
        print("2. Информация о конфигурации:")
        print(f"   - Панель входа: {app._entry_panel_id}")
        print(f"   - Всего панелей: {len(app._panel_templates)}")
        print(f"   - Активная панель: {app.active_node.panel_template.title}\n")

        # Детали панелей
        print("3. Детали панелей:")
        for panel_id, panel in app._panel_templates.items():
            print(f"   Панель '{panel_id}' ({panel.title}):")
            print(f"     Описание: {panel.description}")
            print(f"     Обработчик: {panel.handler_class_name}")
            print(f"     Виджеты ({len(panel.widgets)}):")

            for widget in panel.widgets:
                print(f"       - {widget.id}: {widget.type}")
                print(f"         Заголовок: {widget.title}")
                if hasattr(widget, 'placeholder'):
                    print(f"         Placeholder: {widget.placeholder}")
                if hasattr(widget, 'options'):
                    print(f"         Опции: {widget.options}")
                if hasattr(widget, 'target_panel_id'):
                    print(f"         Целевая панель: {widget.target_panel_id}")
                print()
            print()

        # Проверка состояния дерева
        print("4. Состояние дерева:")
        print(f"   - Корневой узел: {app.tree_root.panel_template.id}")
        print(f"   - Активный узел: {app.active_node.panel_template.id}")
        print(f"   - Флаг активности: {app.active_node.is_active}")
        print(f"   - Контекст: {app.active_node.context}")
        print(f"   - Данные формы: {app.active_node.form_data}")

        print("\n✅ Все проверки пройдены успешно!")

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()