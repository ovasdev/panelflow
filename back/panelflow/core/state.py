"""
Управление состоянием приложения через дерево узлов.
TreeNode представляет экземпляр панели в дереве навигации.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from uuid import UUID, uuid4
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .components import AbstractPanel


@dataclass
class TreeNode:
    """
    Узел дерева состояний, представляющий экземпляр панели.

    Каждый узел содержит:
    - Ссылку на шаблон панели
    - Контекст от родителя
    - Собранные данные формы
    - Навигационные связи с дочерними узлами
    """

    # Ссылка на "шаблон" панели
    panel_template: AbstractPanel

    # Контекст, полученный от родителя
    context: dict = field(default_factory=dict)

    # Данные формы, собранные виджетами этого узла
    form_data: dict = field(default_factory=dict)

    # Навигационные связи
    parent: TreeNode | None = None

    # КЛЮЧЕВАЯ СТРУКТУРА ДЛЯ НАВИГАЦИИ
    # Словарь, где ключ - ID виджета-родителя, породившего ветку,
    # а значение - стек дочерних узлов.
    children_stacks: dict[str, list[TreeNode]] = field(default_factory=dict)

    # Уникальный ID экземпляра
    node_id: UUID = field(default_factory=uuid4)

    # Флаг фокуса
    is_active: bool = False
