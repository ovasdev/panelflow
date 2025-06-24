"""
Виджеты TUI для различных типов AbstractWidget.
"""

from typing import Optional, Any, Callable
from textual.widget import Widget

from panelflow.core.components import (
    AbstractWidget, AbstractButton, AbstractTextInput,
    AbstractOptionSelect, PanelLink
)
from panelflow.core.state import TreeNode

from .button import TuiButton
from .input import TuiTextInput
from .select import TuiOptionSelect
from .link import TuiPanelLink


def create_widget(
        abstract_widget: AbstractWidget,
        node: TreeNode,
        post_event_callback: Callable[[str, Any], None]
) -> Optional[Widget]:
    """
    Фабричная функция для создания конкретного TUI-виджета
    из абстрактного описания.

    Args:
        abstract_widget: Абстрактное описание виджета
        node: Узел дерева состояний, содержащий виджет
        post_event_callback: Функция для отправки событий

    Returns:
        Конкретный виджет Textual или None если тип неизвестен
    """
    if isinstance(abstract_widget, AbstractButton):
        return TuiButton(abstract_widget, node, post_event_callback)

    elif isinstance(abstract_widget, AbstractTextInput):
        return TuiTextInput(abstract_widget, node, post_event_callback)

    elif isinstance(abstract_widget, AbstractOptionSelect):
        return TuiOptionSelect(abstract_widget, node, post_event_callback)

    elif isinstance(abstract_widget, PanelLink):
        return TuiPanelLink(abstract_widget, node, post_event_callback)

    # Неизвестный тип виджета
    return None


__all__ = [
    'create_widget',
    'TuiButton',
    'TuiTextInput',
    'TuiOptionSelect',
    'TuiPanelLink'
]