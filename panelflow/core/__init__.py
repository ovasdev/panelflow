"""
PanelFlow Core Package
Центральный, платформо-независимый модуль для управления состоянием,
навигацией и бизнес-логикой приложений PanelFlow.
"""

from .application import Application
from .components import (
    AbstractWidget,
    AbstractTextInput,
    AbstractButton,
    AbstractOptionSelect,
    PanelLink,
    AbstractPanel
)
from .events import (
    BaseEvent,
    WidgetSubmittedEvent,
    HorizontalNavigationEvent,
    VerticalNavigationEvent,
    BackNavigationEvent,
    StateChangedEvent,
    ErrorOccurredEvent
)
from .handlers import BasePanelHandler
from .state import TreeNode

__all__ = [
    'Application',
    'AbstractWidget',
    'AbstractTextInput',
    'AbstractButton',
    'AbstractOptionSelect',
    'PanelLink',
    'AbstractPanel',
    'TreeNode',
    'BasePanelHandler',
    'BaseEvent',
    'WidgetSubmittedEvent',
    'HorizontalNavigationEvent',
    'VerticalNavigationEvent',
    'BackNavigationEvent',
    'StateChangedEvent',
    'ErrorOccurredEvent'
]
