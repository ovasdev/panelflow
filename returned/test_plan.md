Руководство по проверке PanelFlow
1. Подготовка окружения
Установите зависимости:
bash
pip install jsonschema pytest
Создайте структуру проекта:
project/
├── panelflow/
│   ├── __init__.py
│   └── core/
│       ├── __init__.py
│       ├── application.py
│       ├── components.py
│       ├── state.py
│       ├── handlers.py
│       └── events.py
├── application.json
├── example_handlers.py
└── test_config_loader.py
2. Создайте файлы
Скопируйте код из артефактов:
panelflow/core/ - все файлы из первого артефакта
application.json - из второго артефакта
example_handlers.py - из третьего артефакта
test_config_loader.py - из четвертого артефакта
Создайте пустые __init__.py:
bash
touch panelflow/__init__.py
touch panelflow/core/__init__.py
3. Базовые проверки
Проверка импорта модулей:
python
# test_import.py
try:
    from panelflow.core import Application
    from panelflow.core.components import AbstractPanel
    from panelflow.core.events import WidgetSubmittedEvent
    print("✅ Все модули импортируются корректно")
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
Проверка загрузки конфигурации:
python
# test_basic_loading.py
from example_handlers import HANDLER_MAP
from panelflow.core import Application

try:
    # Попытка создать приложение
    app = Application("application.json", HANDLER_MAP)
    
    print("✅ Приложение создано успешно")
    print(f"Панель входа: {app._entry_panel_id}")
    print(f"Количество панелей: {len(app._panel_templates)}")
    print(f"Активная панель: {app.active_node.panel_template.title}")
    
    # Проверка структуры
    for panel_id, panel in app._panel_templates.items():
        print(f"\nПанель '{panel_id}':")
        print(f"  Заголовок: {panel.title}")
        print(f"  Виджетов: {len(panel.widgets)}")
        for widget in panel.widgets:
            print(f"    - {widget.id}: {widget.type} '{widget.title}'")
            
except Exception as e:
    print(f"❌ Ошибка: {e}")
4. Запуск тестов
Запустите полный набор тестов:
bash
python -m pytest test_config_loader.py -v
Или запустите конкретные тесты:
bash
# Тест успешной загрузки
python -m pytest test_config_loader.py::TestConfigLoader::test_valid_config_loading -v

# Тест валидации схемы
python -m pytest test_config_loader.py::TestConfigLoader::test_schema_validation_missing_required_fields -v

# Тест проверки целостности
python -m pytest test_config_loader.py::TestConfigLoader::test_integrity_nonexistent_entry_panel -v
5. Проверка обработки ошибок
Тест с неправильной конфигурацией:
python
# test_error_handling.py
from panelflow.core import Application
from example_handlers import HANDLER_MAP

# Тест 1: Несуществующий файл
try:
    app = Application("nonexistent.json", HANDLER_MAP)
except FileNotFoundError as e:
    print("✅ Корректно обработана ошибка отсутствующего файла")

# Тест 2: Невалидный JSON
with open("invalid.json", "w") as f:
    f.write("{ invalid json }")

try:
    app = Application("invalid.json", HANDLER_MAP)
except Exception as e:
    print("✅ Корректно обработан невалидный JSON")

# Тест 3: Ошибка схемы
import json
invalid_config = {"panels": []}  # Отсутствует entryPanel

with open("invalid_schema.json", "w") as f:
    json.dump(invalid_config, f)

try:
    app = Application("invalid_schema.json", HANDLER_MAP)
except Exception as e:
    print("✅ Корректно обработана ошибка схемы")

# Очистка
import os
os.remove("invalid.json")
os.remove("invalid_schema.json")
6. Интерактивная проверка
Создайте простой тестовый скрипт:
python
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
7. Ожидаемые результаты
При успешном запуске вы должны увидеть:
✅ Все тесты проходят (зеленые галочки в pytest)
✅ Приложение создается без ошибок
✅ Все панели и виджеты корректно парсятся
✅ Проверки целостности проходят успешно
✅ Ошибки обрабатываются корректно
Структура вывода interactive_test.py:
=== Тест загрузчика конфигурации PanelFlow ===

1. Создание приложения...
✅ Приложение создано успешно

2. Информация о конфигурации:
   - Панель входа: main_menu
   - Всего панелей: 4
   - Активная панель: Главное меню

3. Детали панелей:
   [Подробная информация о каждой панели и виджетах]

4. Состояние дерева:
   - Корневой узел: main_menu
   - Активный узел: main_menu
   - Флаг активности: True
   [...]

✅ Все проверки пройдены успешно!
8. Команды для быстрой проверки
bash
# Полная проверка (рекомендуется)
python interactive_test.py

# Запуск всех тестов
python -m pytest test_config_loader.py -v

# Проверка базового импорта
python test_basic_loading.py

# Проверка обработки ошибок
python test_error_handling.py
Если все тесты проходят успешно, значит загрузчик конфигурации работает в соответствии со спецификацией!

