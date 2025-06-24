"""
PanelFlow TUI Package
Слой рендеринга для терминального интерфейса на базе Textual.

Пример использования:

```python
from panelflow.core import Application as CoreApplication
from panelflow.tui import TuiApplication

# Создание ядра приложения
core_app = CoreApplication("application.json", handler_map)

# Создание TUI-приложения
tui_app = TuiApplication(core_app)

# Запуск
tui_app.run()
```
"""

from .app import TuiApplication
from .screens import MainScreen, ErrorScreen
from .widgets import create_widget

__all__ = [
    'TuiApplication',
    'MainScreen',
    'ErrorScreen',
    'create_widget'
]