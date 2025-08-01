# Событийная модель и встроенные обработчики ядра PanelFlow

## 1. Обзор и философия

Взаимодействие между Слоем Ядра (`panelflow.core`) и Слоем Рендеринга (UI) построено на асинхронной, однонаправленной событийной модели. Эта архитектура обеспечивает полное разделение бизнес-логики и ее визуального представления.

1. **Рендерер** перехватывает низкоуровневые действия пользователя (нажатия клавиш, клики) и преобразует их в высокоуровневые **События**, понятные для Ядра.
    
2. Рендерер отправляет эти События в Ядро через единственный публичный метод: `Application.post_event(event)`.
    
3. **Ядро** обрабатывает событие, изменяет свое внутреннее состояние (дерево `TreeNode`) и, в свою очередь, оповещает Рендерер о произошедших изменениях, публикуя собственные События (например, `StateChangedEvent`).
    
4. Рендерер, подписанный на эти события, получает их и обновляет интерфейс.
    

Обработчики, описанные в этом документе, являются **встроенными и непереопределяемыми**. Они составляют внутреннюю логику фреймворка, обеспечивающую его корректную и предсказуемую работу.

## 2. Каталог событий

### 2.1. Входящие события (Renderer → Core)

Эти события информируют Ядро о намерениях пользователя.

- **`WidgetSubmittedEvent(widget_id: str, value: Any)`**
    
    - **Назначение**: Пользователь подтвердил ввод или выбор значения в виджете.
        
    - **Триггеры**: Нажатие `Enter` в `TextInput`, выбор элемента в `OptionSelect`, нажатие на `Button` или `PanelLink`.
        
    - **Результат**: Запускает основную бизнес-логику, связанную с виджетом, и возможную последующую навигацию.
        
- **`HorizontalNavigationEvent(direction: Literal["next", "previous"])`**
    
    - **Назначение**: Пользователь запросил смену фокуса между колонками.
        
    - **Триггеры**: `Ctrl` + `→` (`next`), `Ctrl` + `←` (`previous`).
        
    - **Результат**: Изменяет активную панель (`active_node`) без изменения структуры дерева.
        
- **`VerticalNavigationEvent(direction: Literal["up", "down"])`**
    
    - **Назначение**: Пользователь запросил перемещение по стеку панелей внутри текущей колонки.
        
    - **Триггеры**: `Ctrl` + `↑` (`up`), `Ctrl` + `↓` (`down`).
        
    - **Результат**: Изменяет, какая панель из стека является активной (верхней).
        
- **`BackNavigationEvent()`**
    
    - **Назначение**: Пользователь хочет закрыть текущую панель и вернуться на шаг назад.
        
    - **Триггеры**: `←` (стрелка влево) или `Backspace`.
        
    - **Результат**: Уничтожает текущую активную панель (и всю ее дочернюю ветку), возвращая фокус на предыдущую панель в стеке или на родительскую панель.
        

### 2.2. Исходящие события (Core → Renderer)

- **`StateChangedEvent(tree_root: TreeNode)`**
    
    - **Назначение**: Сообщает Рендереру, что состояние дерева изменилось.
        
    - **Триггеры**: Любое действие, которое меняет структуру дерева или активный узел.
        
    - **Результат**: Рендерер должен полностью перерисовать интерфейс на основе нового состояния дерева.
        
- **`ErrorOccurredEvent(title: str, message: str)`**
    
    - **Назначение**: Сообщает Рендереру, что произошла внутренняя ошибка.
        
    - **Триггеры**: Ошибки парсинга конфигурации, исключения в пользовательских обработчиках, любые другие внутренние сбои Ядра.
        
    - **Результат**: Рендерер должен отобразить специальный экран ошибки.
        

## 3. Внутренние обработчики событий в `Application`

Метод `Application.post_event` — это единая точка входа, которая маршрутизирует события к соответствующим внутренним обработчикам. Весь метод обернут в `try...except`, что гарантирует перехват любых ошибок и создание `ErrorOccurredEvent`.

### `_handle_widget_submission(event: WidgetSubmittedEvent)`

1. Вызвать вспомогательную функцию `_find_node_by_widget_id(event.widget_id)`, чтобы найти узел (`source_node`), в котором находится виджет. Если узел не найден, прервать выполнение.
    
2. Автоматически обновить данные формы: `source_node.form_data[event.widget_id] = event.value`.
    
3. Получить имя класса-обработчика из `source_node.panel_template.handler_class_name`.
    
4. Если обработчик определен и существует в `handler_map`, создать его экземпляр: `HandlerClass(context=source_node.context, form_data=source_node.form_data)`.
    
5. Вызвать метод `on_widget_update` этого экземпляра.
    
6. Если `on_widget_update` вернул команду навигации (например, `("navigate_down", target)`), вызвать `_execute_navigation_down(source_node, event.widget_id, target)`.
    
7. Если навигации не было, все равно опубликовать `StateChangedEvent`, так как `form_data` изменились.
    

### `_execute_navigation_down(source_node, source_widget_id, target)`

1. Проверить, существует ли стек для `source_widget_id` в `source_node.children_stacks`.
    
2. Если да, рекурсивно уничтожить все узлы в этом стеке с помощью вспомогательной функции `_destroy_stack_recursively`, чтобы очистить старую ветку.
    
3. Определить шаблон для новой панели. Если `target` — это строка, найти шаблон в `self._panel_templates`. Если `target` — это объект `AbstractPanel`, использовать его напрямую.
    
4. Создать новый `TreeNode`, передав ему шаблон и `context=source_node.form_data`.
    
5. Создать новый стек: `source_node.children_stacks[source_widget_id] = [new_node]`.
    
6. Сделать `new_node` активным, сняв флаг `is_active` со `source_node`.
    
7. Опубликовать `StateChangedEvent`.
    

### `_handle_vertical_navigation(event: VerticalNavigationEvent)`

1. Найти `active_node` и его родителя `parent`. Если их нет, прервать выполнение.
    
2. Найти ключ стека (`stack_key`) и сам стек (`stack`) в `parent.children_stacks`, которому принадлежит `active_node`.
    
3. Найти текущий индекс `active_node` в стеке.
    
4. Вычислить новый индекс. Для `direction="up"` это `index + 1`, для `direction="down"` это `index - 1`.
    
5. Если новый индекс валиден, переместить узел с нового индекса в конец списка (на вершину стека) с помощью `stack.append(stack.pop(new_index))`.
    
6. Сделать новый узел на вершине стека (`stack[-1]`) активным, сняв флаг со старого `active_node`.
    
7. Опубликовать `StateChangedEvent`.
    

### `_handle_back_navigation(event: BackNavigationEvent)`

1. Найти `active_node` и его родителя `parent`. Если родителя нет (это корневой узел), действие не выполняется.
    
2. Рекурсивно уничтожить все дочерние стеки самого `active_node` (`_destroy_stack_recursively`).
    
3. Найти ключ стека и сам стек в `parent.children_stacks`, которому принадлежит `active_node`.
    
4. Удалить `active_node` из стека.
    
5. Определить новый фокус:
    
    - Если в стеке остались узлы, верхний из них (`stack[-1]`) становится `active_node`.
        
    - Если стек опустел, `parent` становится `active_node`.
        
6. Опубликовать `StateChangedEvent`.
    

### `_handle_horizontal_navigation(event: HorizontalNavigationEvent)`

1. Получить путь до `active_node` с помощью вспомогательной функции `_get_path_to_active_node()`.
    
2. Найти индекс `active_node` в этом пути.
    
3. Вычислить новый индекс (`+1` для `next`, `-1` для `previous`).
    
4. Если новый индекс валиден, сделать узел по новому индексу активным, сняв флаг со старого.
    
5. Опубликовать `StateChangedEvent`.