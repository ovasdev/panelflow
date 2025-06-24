# 🔧 Инструкция по диагностике PanelFlow

## Пошаговая диагностика проблем

### Шаг 1: Глубокая диагностика

```bash
python debug_navigation.py
```

Этот скрипт покажет **детальную** информацию о том, что происходит при навигации:

- Вызывается ли обработчик
- Возвращает ли он правильную команду
- Находится ли виджет и панель назначения
- Какие события генерируются
- Где именно происходит сбой

### Шаг 2: Простой тест с отладкой

```bash
python simple_test.py
```

Покажет подробную информацию о каждом шаге навигации.

### Шаг 3: Полные тесты через pytest

```bash
pytest test_navigation.py -v
```

Или без pytest:

```bash
python test_navigation.py
```

## Возможные причины проблем

### 1. ❌ AssertionError в simple_test

**Причины:**

- Обработчик не вызывается
- Обработчик не возвращает команду навигации
- Ошибка в `_execute_navigation_down`
- Панель назначения не найдена

**Диагностика:** Запустите `debug_navigation.py` - он покажет точное место сбоя.

### 2. ❌ Empty suite в pytest

**Причина:** Pytest не находит тестовых функций.

**Решение:** Исправлен `test_navigation.py` - теперь использует pytest фикстуры и правильные имена функций.

### 3. 🔧 Методы не реализованы

Если `debug_navigation.py` показывает, что методы отсутствуют:

```python
# Проверьте наличие в application.py:
def _handle_widget_submission(self, event): ...
def _execute_navigation_down(self, source_node, source_widget_id, target): ...
def _find_node_by_widget_id(self, widget_id): ...
```

## Ожидаемый вывод debug_navigation.py

```
🔍 === ОТЛАДКА МЕТОДОВ APPLICATION ===

1. НАЧАЛЬНОЕ СОСТОЯНИЕ:
   active_node: main
   is_active: True
   children_stacks: {}

2. ПОИСК ВИДЖЕТА 'goto_child':
   ✅ Найден в панели: main
   Виджет: button 'К дочерней панели'

3. ПРОВЕРКА ПАНЕЛИ 'child':
   ✅ Панель найдена: 'Дочерняя'

4. ОТПРАВКА СОБЫТИЯ WidgetSubmittedEvent:
   Отправляю: widget_id='goto_child', value=True

🔧 === ВЫЗОВ ОБРАБОТЧИКА ===
widget_id: goto_child
value: True
context: {}
form_data: {'goto_child': True}
ВОЗВРАЩАЮ: ('navigate_down', 'child')

📢 СОБЫТИЕ: StateChangedEvent

5. СОСТОЯНИЕ ПОСЛЕ СОБЫТИЯ:
   active_node: child
   События получено: 1
   Родитель: main
   Стеки родителя: ['goto_child']

🎉 УСПЕХ! Навигация сработала корректно
```

## Если навигация не работает

Выход `debug_navigation.py` покажет, где именно проблема:

1. **Обработчик не вызывается** → проблема в `_handle_widget_submission`
2. **Обработчик вызывается, но навигация не происходит** → проблема в `_execute_navigation_down`
3. **Генерируется ErrorOccurredEvent** → смотрите сообщение об ошибке
4. **Виджет/панель не найдены** → проблема в конфигурации

## Следующие действия

После успешной диагностики:

1. ✅ Если `debug_navigation.py` показывает успех → ядро работает
2. ✅ Если `simple_test.py` проходит → можно запускать полные тесты
3. ✅ Если `pytest test_navigation.py` проходит → готовы к TUI рендереру

**Главное:** запустите сначала `debug_navigation.py` - он даст полную картину происходящего!