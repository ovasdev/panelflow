# Руководство по использованию PanelFlow для LLM-агентов

## Обзор библиотеки

**PanelFlow** — это Python-фреймворк для создания многопанельных приложений с четким разделением бизнес-логики и представления. Библиотека использует трехслойную архитектуру и поддерживает различные платформы рендеринга (TUI, Web, Desktop).

## Архитектурные принципы

### 1. Трехслойная архитектура
```
Слой Приложения (Ваш код)
    ↓ События и конфигурация
Слой Ядра (panelflow.core)  
    ↓ События состояния
Слой Рендеринга (panelflow.tui/web/desktop)
```

**Важно**: Каждый слой должен взаимодействовать только со смежными слоями через строго определенные интерфейсы событий.

### 2. Ключевые компоненты

| Компонент | Назначение | Расположение |
|-----------|------------|--------------|
| `Application` | Главный оркестратор, управление состоянием | `panelflow.core.application` |
| `TreeNode` | Узел дерева состояний, экземпляр панели | `panelflow.core.state` |
| `AbstractPanel/Widget` | Описание структуры UI | `panelflow.core.components` |
| `BasePanelHandler` | Базовый класс для бизнес-логики | `panelflow.core.handlers` |
| События | Связь между слоями | `panelflow.core.events` |

## Структура проекта

```
my_app/
├── main.py                 # Точка входа
├── application.json        # Конфигурация структуры
├── handlers/
│   ├── __init__.py
│   └── my_handlers.py     # Пользовательские обработчики
└── requirements.txt
```

## Пошаговое создание приложения

### Шаг 1: Описание структуры (application.json)

```json
{
  "entryPanel": "main_panel",
  "panels": [
    {
      "id": "main_panel",
      "title": "Главная панель",
      "description": "Описание панели",
      "handler_class_name": "MainHandler",
      "widgets": [
        {
          "type": "TextInput",
          "id": "username_input",
          "title": "Имя пользователя",
          "placeholder": "Введите имя"
        },
        {
          "type": "Button", 
          "id": "submit_btn",
          "title": "Подтвердить"
        },
        {
          "type": "PanelLink",
          "id": "settings_link", 
          "title": "Настройки",
          "target_panel_id": "settings_panel"
        }
      ]
    },
    {
      "id": "settings_panel",
      "title": "Настройки",
      "widgets": [...]
    }
  ]
}
```

### Шаг 2: Реализация бизнес-логики

```python
# handlers/my_handlers.py
from panelflow.core.handlers import BasePanelHandler
from panelflow.core.components import AbstractPanel

class MainHandler(BasePanelHandler):
    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        if widget_id == "username_input":
            # Автоматическое сохранение в form_data
            print(f"Имя изменено на: {value}")
            
        elif widget_id == "submit_btn":
            username = self.form_data.get("username_input", "")
            if username:
                # Навигация к динамически созданной панели
                welcome_panel = AbstractPanel(
                    id="welcome",
                    title=f"Добро пожаловать, {username}!",
                    widgets=[]
                )
                return ("navigate_down", welcome_panel)
            
        return None
```

### Шаг 3: Точка входа приложения

```python
# main.py
from panelflow.core import Application
from panelflow.tui import TuiApplication
from handlers.my_handlers import MainHandler

def main():
    # Карта обработчиков
    handler_map = {
        "MainHandler": MainHandler,
    }
    
    # Создание ядра
    core_app = Application(
        config_path="application.json",
        handler_map=handler_map
    )
    
    # Запуск с TUI рендерером
    tui_app = TuiApplication(core_app)
    tui_app.run()

if __name__ == "__main__":
    main()
```

## Навигационная модель

### Двумерная навигация
```
[Панель 1] → [Панель 2] → [Панель 3]
     ↑           ↑           ↑
  [Стек A]    [Стек B]    [Стек C]
  [Стек B]    [Стек C]    [Стек D] 
```

### Горячие клавиши
| Клавиши | Действие |
|---------|----------|
| `Ctrl + ←/→` | Горизонтальная навигация между колонками |
| `Ctrl + ↑/↓` | Вертикальная навигация по стеку |
| `Tab/Shift+Tab` | Навигация между виджетами |
| `Enter` | Активация виджета |
| `←/Backspace` | Возврат назад |

## Система событий

### Входящие события (Renderer → Core)
```python
# Пользователь ввел данные
WidgetSubmittedEvent(widget_id="my_input", value="текст")

# Навигационные события  
HorizontalNavigationEvent(direction="next")
VerticalNavigationEvent(direction="up")
BackNavigationEvent()
```

### Исходящие события (Core → Renderer)
```python
# Состояние изменилось
StateChangedEvent(tree_root=new_tree_root)

# Произошла ошибка
ErrorOccurredEvent(title="Ошибка", message="Описание")
```

## Рекомендации по разработке

### ✅ Правильные практики

1. **Чистое разделение слоев**: Никогда не импортируйте код рендерера в обработчики
2. **Обработка ошибок**: Все исключения в обработчиках автоматически превращаются в `ErrorOccurredEvent`
3. **Состояние в узлах**: Используйте `context` для данных от родителя, `form_data` для текущих значений
4. **Навигационные команды**: Возвращайте `("navigate_down", target)` для создания дочерних панелей

### ❌ Частые ошибки

1. **Прямое обращение к UI**: Не пытайтесь напрямую изменять виджеты из обработчиков
2. **Нарушение событийной модели**: Не вызывайте методы рендерера из ядра
3. **Блокирующие операции**: Длительные операции должны быть асинхронными
4. **Неправильные ID**: Убедитесь, что все `widget_id` и `panel_id` уникальны

## Типы виджетов

| Тип | Назначение | Обязательные поля |
|-----|------------|-------------------|
| `AbstractTextInput` | Ввод текста | `id`, `title`, `placeholder` |
| `AbstractButton` | Кнопка действия | `id`, `title` |
| `AbstractOptionSelect` | Выбор из списка | `id`, `title`, `options` |
| `PanelLink` | Ссылка на панель | `id`, `title`, `target_panel_id` |

## Жизненный цикл панели

1. **Создание**: Панель создается при навигации `("navigate_down", target)`
2. **Активация**: Новая панель автоматически получает фокус
3. **Замещение**: Повторная навигация из того же виджета заменяет существующую панель
4. **Уничтожение**: При возврате назад (`BackNavigationEvent`) панель и все ее потомки удаляются

## Отладка

### Логирование событий
```python
# В обработчике
def on_widget_update(self, widget_id: str, value: Any):
    print(f"Виджет {widget_id} обновлен: {value}")
    print(f"Текущая форма: {self.form_data}")
    print(f"Контекст: {self.context}")
```

### Валидация конфигурации
Библиотека автоматически валидирует `application.json` через JSON Schema и сообщает о проблемах при запуске.

## Расширение для других платформ

Для создания рендерера под новую платформу:

1. Подпишитесь на события от ядра: `StateChangedEvent`, `ErrorOccurredEvent`
2. Реализуйте фабрику виджетов для преобразования `AbstractWidget` в платформо-специфичные виджеты
3. Переводите действия пользователя в события ядра через `core.post_event()`
4. Обновляйте UI при получении `StateChangedEvent`

Этот подход обеспечивает полную переносимость бизнес-логики между платформами.

## Примеры использования

### Простое приложение-калькулятор

```json
{
  "entryPanel": "calculator",
  "panels": [
    {
      "id": "calculator", 
      "title": "Калькулятор",
      "handler_class_name": "CalculatorHandler",
      "widgets": [
        {
          "type": "TextInput",
          "id": "number1",
          "title": "Первое число",
          "placeholder": "0"
        },
        {
          "type": "TextInput", 
          "id": "number2",
          "title": "Второе число",
          "placeholder": "0"
        },
        {
          "type": "OptionSelect",
          "id": "operation",
          "title": "Операция",
          "options": ["+", "-", "*", "/"]
        },
        {
          "type": "Button",
          "id": "calculate",
          "title": "Вычислить"
        }
      ]
    }
  ]
}
```

```python
class CalculatorHandler(BasePanelHandler):
    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        if widget_id == "calculate":
            try:
                num1 = float(self.form_data.get("number1", 0))
                num2 = float(self.form_data.get("number2", 0))
                op = self.form_data.get("operation", "+")
                
                if op == "+":
                    result = num1 + num2
                elif op == "-":
                    result = num1 - num2
                elif op == "*":
                    result = num1 * num2
                elif op == "/":
                    result = num1 / num2 if num2 != 0 else "Ошибка: деление на ноль"
                
                result_panel = AbstractPanel(
                    id="result",
                    title="Результат",
                    widgets=[
                        AbstractButton(id="back", title="Назад"),
                        AbstractButton(id="new_calc", title="Новый расчет")
                    ]
                )
                return ("navigate_down", result_panel)
                
            except ValueError:
                # Ошибка будет автоматически обработана фреймворком
                raise ValueError("Введите корректные числа")
        
        return None
```

### Файловый менеджер

```python
class FileManagerHandler(BasePanelHandler):
    def on_widget_update(self, widget_id: str, value: Any) -> tuple | None:
        if widget_id == "folder_select":
            # Получаем выбранную папку
            folder_path = value
            
            # Создаем панель с содержимым папки
            files = os.listdir(folder_path)
            
            file_panel = AbstractPanel(
                id="file_list",
                title=f"Файлы в {folder_path}",
                widgets=[
                    AbstractOptionSelect(
                        id="file_select",
                        title="Выберите файл",
                        options=files
                    ),
                    AbstractButton(id="open_file", title="Открыть"),
                    AbstractButton(id="delete_file", title="Удалить")
                ]
            )
            
            return ("navigate_down", file_panel)
        
        elif widget_id == "open_file":
            selected_file = self.form_data.get("file_select")
            if selected_file:
                # Логика открытия файла
                pass
                
        return None
```

## Заключение

PanelFlow предоставляет мощную и гибкую основу для создания сложных многопанельных приложений. Следуя принципам разделения ответственности и событийной архитектуры, вы можете создавать поддерживаемые и расширяемые приложения, которые легко портировать между различными платформами.