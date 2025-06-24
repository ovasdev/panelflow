# test_imports.py
"""Проверка корректности импортов PanelFlow."""


def test_imports():
    """Тестирование всех импортов по порядку."""

    print("🔍 Тестирование импортов PanelFlow...\n")

    try:
        # Проверяем базовые Python импорты
        print("1. Проверка стандартных библиотек...")
        from typing import Any, Dict, Type, Callable
        import json
        from pathlib import Path
        print("   ✅ Стандартные библиотеки")

        # Проверяем внешние зависимости
        print("2. Проверка внешних зависимостей...")
        try:
            import jsonschema
            print("   ✅ jsonschema")
        except ImportError:
            print("   ❌ jsonschema - установите: pip install jsonschema")
            return False

        # Проверяем структуру panelflow
        print("3. Проверка структуры panelflow...")

        try:
            import panelflow
            print("   ✅ panelflow (основной пакет)")
        except ImportError as e:
            print(f"   ❌ panelflow - {e}")
            print("      Проверьте структуру папок и __init__.py файлы")
            return False

        try:
            import panelflow.core
            print("   ✅ panelflow.core")
        except ImportError as e:
            print(f"   ❌ panelflow.core - {e}")
            return False

        # Проверяем отдельные модули
        print("4. Проверка модулей ядра...")

        try:
            from panelflow.core import events
            print("   ✅ events")
        except ImportError as e:
            print(f"   ❌ events - {e}")
            return False

        try:
            from panelflow.core import components
            print("   ✅ components")
        except ImportError as e:
            print(f"   ❌ components - {e}")
            return False

        try:
            from panelflow.core import state
            print("   ✅ state")
        except ImportError as e:
            print(f"   ❌ state - {e}")
            return False

        try:
            from panelflow.core import handlers
            print("   ✅ handlers")
        except ImportError as e:
            print(f"   ❌ handlers - {e}")
            return False

        try:
            from panelflow.core import application
            print("   ✅ application")
        except ImportError as e:
            print(f"   ❌ application - {e}")
            return False

        # Проверяем основные классы
        print("5. Проверка основных классов...")

        try:
            from panelflow.core import Application
            print("   ✅ Application")
        except ImportError as e:
            print(f"   ❌ Application - {e}")
            return False

        try:
            from panelflow.core.handlers import BasePanelHandler
            print("   ✅ BasePanelHandler")
        except ImportError as e:
            print(f"   ❌ BasePanelHandler - {e}")
            return False

        try:
            from panelflow.core.events import (
                WidgetSubmittedEvent,
                StateChangedEvent,
                ErrorOccurredEvent,
                HorizontalNavigationEvent,
                VerticalNavigationEvent,
                BackNavigationEvent
            )
            print("   ✅ События")
        except ImportError as e:
            print(f"   ❌ События - {e}")
            return False

        try:
            from panelflow.core.components import (
                AbstractPanel,
                AbstractWidget,
                AbstractButton,
                AbstractTextInput,
                PanelLink
            )
            print("   ✅ Компоненты")
        except ImportError as e:
            print(f"   ❌ Компоненты - {e}")
            return False

        try:
            from panelflow.core.state import TreeNode
            print("   ✅ TreeNode")
        except ImportError as e:
            print(f"   ❌ TreeNode - {e}")
            return False

        # Проверяем создание экземпляров
        print("6. Проверка создания объектов...")

        try:
            # Создаем простой обработчик
            class TestHandler(BasePanelHandler):
                def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
                    return None

            print("   ✅ Наследование от BasePanelHandler")
        except Exception as e:
            print(f"   ❌ Создание обработчика - {e}")
            return False

        try:
            # Создаем простую панель
            panel = AbstractPanel(
                id="test",
                title="Test Panel"
            )
            print("   ✅ Создание AbstractPanel")
        except Exception as e:
            print(f"   ❌ Создание панели - {e}")
            return False

        try:
            # Создаем событие
            event = WidgetSubmittedEvent(widget_id="test", value="test")
            print("   ✅ Создание событий")
        except Exception as e:
            print(f"   ❌ Создание события - {e}")
            return False

        print("\n🎉 Все импорты успешны! Можно запускать тесты.")
        return True

    except Exception as e:
        print(f"\n❌ Неожиданная ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False


def diagnose_environment():
    """Диагностика окружения."""

    print("\n🔧 Диагностика окружения:")

    import sys
    import os

    print(f"Python версия: {sys.version}")
    print(f"Рабочая директория: {os.getcwd()}")
    print(f"Python path: {sys.path[:3]}...")  # Показываем первые 3 пути

    # Проверяем наличие файлов
    print("\nПроверка файлов:")
    files_to_check = [
        "panelflow/__init__.py",
        "panelflow/core/__init__.py",
        "panelflow/core/application.py",
        "panelflow/core/components.py",
        "panelflow/core/state.py",
        "panelflow/core/handlers.py",
        "panelflow/core/events.py"
    ]

    for file_path in files_to_check:
        if Path(file_path).exists():
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} - ОТСУТСТВУЕТ")


if __name__ == "__main__":
    diagnose_environment()
    success = test_imports()

    if success:
        print("\n🚀 Готово к тестированию! Запустите:")
        print("   python simple_test.py")
    else:
        print("\n🔧 Исправьте ошибки импорта перед продолжением.")
        print("\nВозможные решения:")
        print("1. Убедитесь, что все файлы PanelFlow скопированы")
        print("2. Проверьте наличие __init__.py файлов")
        print("3. Установите зависимости: pip install jsonschema")
        print("4. Запускайте из правильной директории")