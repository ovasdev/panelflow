# -*- coding: utf-8 -*-
"""
PanelFlow: A Declarative TUI Framework for Hierarchical Navigation
-------------------------------------------------------------------
This script contains both the PanelFlow library implementation and a file
manager application built using it, as per the technical specification.
"""

import os
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widgets import Header, Label, Static, TextArea
from textual.events import Key


# ==============================================================================
# SECTION 1: PanelFlow Library Core
# ==============================================================================

class BasePanelHandler(ABC):
    """
    Abstract base class for Panel logic.
    """

    def __init__(self, context: Dict[str, Any]):
        self.context = context
        self._form_data: Dict[str, Any] = {}

    def on_widget_update(self, widget_id: str, value: Any) -> Optional[Tuple[str, str]]:
        self.form_data[widget_id] = value
        return None

    def on_execute(self) -> Optional[Tuple[str, str]]:
        return None

    @property
    def form_data(self) -> Dict[str, Any]:
        return self._form_data

    @form_data.setter
    def form_data(self, value: Dict[str, Any]):
        self._form_data = value


class BaseWidgetHandler(ABC):
    """
    Abstract base class for DataWidget logic.
    """

    def __init__(self, panel_context: Dict[str, Any], panel_form_data: Dict[str, Any]):
        self.panel_context = panel_context
        self.panel_form_data = panel_form_data

    @abstractmethod
    def get_items(self) -> List[Any]:
        pass

    @abstractmethod
    def on_select(self, selected_item: Any) -> Any:
        pass

    def get_item_display_name(self, item: Any) -> str:
        return str(item)


class TreeNode:
    """Represents a single node in the navigation tree."""

    def __init__(self, panel_id: str, handler: BasePanelHandler, parent: Optional['TreeNode'] = None):
        self.panel_id = panel_id
        self.handler = handler
        self.parent = parent
        self.children: List['TreeNode'] = []
        self.active_child_idx = 0

    def get_active_child(self) -> Optional['TreeNode']:
        if not self.children or not (0 <= self.active_child_idx < len(self.children)):
            return None
        return self.children[self.active_child_idx]


class PanelHeader(Static):
    """Displays the title and description of a panel."""

    def __init__(self, title: str, description: str, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.description = description

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="panel-title")
        if self.description:
            yield Label(self.description, classes="panel-description")


class PanelLinkWidget(Label):
    """A simple, non-interactive widget that represents a link to a panel."""
    pass


class DataWidget(VerticalScroll):
    """The interactive widget that displays a list of selectable items."""
    items = reactive([])
    active_item_idx = reactive(0)

    def __init__(self, handler: BaseWidgetHandler, **kwargs):
        super().__init__(**kwargs)
        self.handler = handler

    def on_mount(self) -> None:
        self.items = self.handler.get_items()

    def watch_items(self, new_items: List[Any]) -> None:
        self.active_item_idx = 0
        for child in self.query(Label):
            child.remove()
        for item in new_items:
            display_name = self.handler.get_item_display_name(item)
            self.mount(Label(display_name))
        self._update_highlight()

    def watch_active_item_idx(self) -> None:
        self._update_highlight()
        if self.query(Label):
            labels = self.query(Label)
            if 0 <= self.active_item_idx < len(labels):
                active_label = labels[self.active_item_idx]
                self.scroll_to_widget(active_label, top=True)

    def _update_highlight(self) -> None:
        for idx, label in enumerate(self.query(Label)):
            label.set_class(idx == self.active_item_idx, "active-item")

    # FIX: Explicitly handle key events to ensure selection works over default scroll.
    def on_key(self, event: Key) -> None:
        if event.key == "up":
            event.stop()
            self.action_move_up()
        elif event.key == "down":
            event.stop()
            self.action_move_down()

    def action_move_up(self):
        self.active_item_idx = max(0, self.active_item_idx - 1)

    def action_move_down(self):
        if self.items:
            self.active_item_idx = min(len(self.items) - 1, self.active_item_idx + 1)

    def get_selected_item(self) -> Optional[Any]:
        if self.items and 0 <= self.active_item_idx < len(self.items):
            return self.items[self.active_item_idx]
        return None


class WidgetWrapper(Vertical):
    """A container for any widget, providing focus highlighting and a title."""
    is_active = reactive(False)

    def __init__(self, title: str, widget: Static, **kwargs):
        super().__init__(**kwargs)
        self.widget_title = title
        self.widget = widget

    def compose(self) -> ComposeResult:
        yield Label(self.widget_title, classes="widget-title")
        yield self.widget

    def watch_is_active(self, active: bool):
        self.set_class(active, "widget-active")


class PanelWidget(Vertical):
    """
    The main container for a single panel.
    """
    is_active_panel = reactive(False)

    def __init__(self, node: 'TreeNode', panels_config: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.node = node
        self.panels_config = panels_config

    def compose(self) -> ComposeResult:
        """Creates the content of the panel when it is mounted."""
        panel_config = self.panels_config[self.node.panel_id]

        title = getattr(self.node.handler, 'dynamic_title', panel_config['title'])
        yield PanelHeader(title, panel_config.get('description', ''))

        widgets_config = panel_config.get('widgets', {})
        for widget_id, widget_config in widgets_config.items():
            widget_title = widget_config['title']
            widget_type = widget_config['type']

            if widget_type == "PanelLink":
                actual_widget = PanelLinkWidget(widget_title)
            else:
                handler_class_path = widget_config['handler_class']
                handler_class = globals()[handler_class_path.split('.')[-1]]
                handler = handler_class(self.node.handler.context, self.node.handler.form_data)
                actual_widget = DataWidget(handler)

            yield WidgetWrapper(widget_title, actual_widget, id=f"widget_{widget_id}")

    def watch_is_active_panel(self, active: bool):
        self.set_class(active, "panel-active")


class PanelFlowApp(App):
    """The main application engine for the PanelFlow framework."""

    CSS_PATH = None
    CSS = """
    Screen { overflow: hidden; }
    Horizontal { height: 100%; width: 100%; }
    #panels_container { height: 1fr; }
    PanelWidget { width: 33.33%; height: 100%; border: solid #666; }
    PanelWidget.panel-active { border: heavy green; }
    PanelHeader { height: auto; padding: 0 1; background: #222; }
    .panel-title { text-style: bold; }
    .panel-description { color: #888; }
    WidgetWrapper { border: round #444; margin: 0 1 1 1; padding: 1; height: 1fr; }
    WidgetWrapper.widget-active { border: round green; }
    .widget-title { color: #999; }
    DataWidget { background: #111; height: 1fr; }
    .active-item { background: green; color: black; }
    #input_container { height: 3; padding: 0 1; background: #111; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("up", "move_up", "Move Up", show=False),
        Binding("down", "move_down", "Move Down", show=False),
        Binding("enter", "activate_item", "Activate", show=False),
        Binding("left", "navigate_back", "Navigate Back", show=False),
        Binding("ctrl+left", "focus_prev_panel", "Focus Left", show=False),
        Binding("ctrl+right", "focus_next_panel", "Focus Right", show=False),
        Binding("ctrl+up", "switch_prev_tab", "Prev Tab", show=False),
        Binding("ctrl+down", "switch_next_tab", "Next Tab", show=False),
    ]

    def __init__(self, config: Dict[str, Any], **kwargs):
        super().__init__(**kwargs)
        self.config = config
        self.panels_config = {p['id']: p for p in config['panels']}
        self.root_node: Optional[TreeNode] = None
        self.active_node: Optional[TreeNode] = None
        self.active_panel_idx = 0
        self.active_widget_idx = 0
        self.input_widget: Optional[TextArea] = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Horizontal(id="panels_container")
        yield Vertical(Label("Command:"), TextArea(id="input_area", show_line_numbers=False), id="input_container")

    def on_mount(self) -> None:
        self.input_widget = self.query_one("#input_area", TextArea)
        entry_panel_id = self.config['entryPanel']
        self.root_node = self._create_tree_node(entry_panel_id, context={})
        self.active_node = self.root_node
        self._update_view()

    def _create_tree_node(self, panel_id: str, context: Dict[str, Any], parent: Optional[TreeNode] = None) -> TreeNode:
        panel_config = self.panels_config[panel_id]
        handler_path = panel_config.get('handler_class')
        if handler_path:
            handler_class = globals()[handler_path.split('.')[-1]]
            handler = handler_class(context)
        else:
            handler = BasePanelHandler(context)
        return TreeNode(panel_id, handler, parent)

    def _update_view(self):
        if not self.active_node:
            return

        path_to_active = []
        curr = self.active_node
        while curr:
            path_to_active.insert(0, curr)
            curr = curr.parent

        window_size = 3
        last_visible_idx = len(path_to_active) - 1
        first_visible_idx = max(0, last_visible_idx - window_size + 1)
        visible_path = path_to_active[first_visible_idx: last_visible_idx + 1]

        hidden_left = first_visible_idx
        active_panel_dynamic_title = getattr(self.active_node.handler, 'dynamic_title', None)
        active_panel_title = active_panel_dynamic_title or self.panels_config[self.active_node.panel_id]['title']

        header_parts = []
        if hidden_left > 0:
            header_parts.append(f"◀ {hidden_left}")
        header_parts.append(active_panel_title)

        self.query_one(Header).tall = False
        self.query_one(Header).title = " | ".join(header_parts)

        container = self.query_one("#panels_container")

        # FIX: Instead of remove_children, intelligently update or create panels.
        # This is a more robust approach that avoids ID conflicts.
        existing_panels = container.query(PanelWidget)

        # Mount new panels if needed
        while len(existing_panels) < len(visible_path):
            new_panel = PanelWidget(node=visible_path[len(existing_panels)], panels_config=self.panels_config)
            container.mount(new_panel)
            existing_panels = container.query(PanelWidget)

        # Remove extra panels if needed
        while len(existing_panels) > len(visible_path):
            existing_panels[-1].remove()
            existing_panels = container.query(PanelWidget)

        # Update the nodes for the remaining panels
        for i, panel_widget in enumerate(existing_panels):
            panel_widget.node = visible_path[i]
            # This is a bit of a hack. A better way would be a custom message
            # to tell the panel to re-compose itself. For now, we remove and re-add.
            panel_widget.remove_children()
            panel_widget.compose()

        self._update_active_states()

    def _update_active_states(self):
        panels = self.query(PanelWidget)
        for i, panel in enumerate(panels):
            is_active_panel = (i == self.active_panel_idx)
            panel.is_active_panel = is_active_panel

            if is_active_panel:
                widgets = panel.query(WidgetWrapper)
                for j, widget in enumerate(widgets):
                    widget.is_active = (j == self.active_widget_idx)

    def _is_input_focused(self) -> bool:
        return self.input_widget.has_focus and self.input_widget.text != ""

    def get_active_data_widget(self) -> Optional[DataWidget]:
        try:
            panels = self.query(PanelWidget)
            if not panels: return None
            active_panel = panels[self.active_panel_idx]

            widgets = active_panel.query(WidgetWrapper)
            if not widgets: return None
            active_wrapper = widgets[self.active_widget_idx]

            if isinstance(active_wrapper.widget, DataWidget):
                return active_wrapper.widget
        except IndexError:
            return None
        return None

    def action_move_up(self) -> None:
        if self._is_input_focused(): return
        active_data_widget = self.get_active_data_widget()
        if active_data_widget:
            active_data_widget.action_move_up()

    def action_move_down(self) -> None:
        if self._is_input_focused(): return
        active_data_widget = self.get_active_data_widget()
        if active_data_widget:
            active_data_widget.action_move_down()

    def action_activate_item(self) -> None:
        if self._is_input_focused(): return

        panels = self.query(PanelWidget)
        if not panels or self.active_panel_idx >= len(panels): return

        panel = panels[self.active_panel_idx]
        widgets = panel.query(WidgetWrapper)
        if not widgets or self.active_widget_idx >= len(widgets):
            nav_instruction = self.active_node.handler.on_execute()
            if nav_instruction: self._handle_navigation(nav_instruction)
            return

        active_widget_wrapper = widgets[self.active_widget_idx]
        widget_id = active_widget_wrapper.id.split('_', 1)[1]
        widget_config = self.panels_config[self.active_node.panel_id]['widgets'][widget_id]

        if widget_config['type'] == 'PanelLink':
            next_panel_id = widget_config['panel_id']
            self._handle_navigation(("navigate_down", next_panel_id))

        elif widget_config['type'] == 'DataWidget':
            data_widget = active_widget_wrapper.widget
            selected_item = data_widget.get_selected_item()
            if selected_item is not None:
                return_value = data_widget.handler.on_select(selected_item)
                nav_instruction = self.active_node.handler.on_widget_update(widget_id, return_value)
                if nav_instruction: self._handle_navigation(nav_instruction)

    def action_navigate_back(self) -> None:
        if self._is_input_focused(): return

        if self.active_node and self.active_node.parent:
            parent = self.active_node.parent
            # Remove the node from its parent's children list
            if self.active_node in parent.children:
                parent.children.remove(self.active_node)

            self.active_node = parent
            self.active_panel_idx = min(self.active_panel_idx, 2)
            self.active_widget_idx = 0
            self._update_view()

    def action_focus_prev_panel(self) -> None:
        if self._is_input_focused(): return
        self.active_panel_idx = max(0, self.active_panel_idx - 1)
        self.input_widget.text = ""
        self._update_active_states()

    def action_focus_next_panel(self) -> None:
        if self._is_input_focused(): return
        self.active_panel_idx = min(len(self.query(PanelWidget)) - 1, self.active_panel_idx + 1)
        self.input_widget.text = ""
        self._update_active_states()

    def action_switch_prev_tab(self) -> None:
        if self._is_input_focused(): return
        if self.active_node and self.active_node.parent:
            parent = self.active_node.parent
            if len(parent.children) > 1:
                parent.active_child_idx = (parent.active_child_idx - 1) % len(parent.children)
                # FIX: Set active_node to the *newly selected* active child
                self.active_node = parent.get_active_child()
                self._update_view()

    def action_switch_next_tab(self) -> None:
        if self._is_input_focused(): return
        if self.active_node and self.active_node.parent:
            parent = self.active_node.parent
            if len(parent.children) > 1:
                parent.active_child_idx = (parent.active_child_idx + 1) % len(parent.children)
                # FIX: Set active_node to the *newly selected* active child
                self.active_node = parent.get_active_child()
                self._update_view()

    def _handle_navigation(self, instruction: Tuple[str, str]):
        nav_type, panel_id = instruction
        if nav_type == "navigate_down":
            context = self.active_node.handler.form_data.copy()
            new_node = self._create_tree_node(panel_id, context, self.active_node)
            self.active_node.children.append(new_node)
            self.active_node.active_child_idx = len(self.active_node.children) - 1

            self.active_node = new_node

            path_len = len(self.get_path_to_active())
            self.active_panel_idx = min(path_len - 1, 2)
            self.active_widget_idx = 0
            self._update_view()

    def get_path_to_active(self) -> List[TreeNode]:
        """Helper to get the list of nodes from root to active."""
        path = []
        curr = self.active_node
        while curr:
            path.insert(0, curr)
            curr = curr.parent
        return path


# ==============================================================================
# SECTION 2: File Manager Application
# ==============================================================================

APP_CONFIG_JSON = """
{
  "appName": "PanelFlow File Manager",
  "entryPanel": "file_browser",
  "panels": [
    {
      "id": "file_browser",
      "title": "File Browser",
      "description": "Select a file or directory",
      "handler_class": "FileSystemPanelHandler",
      "widgets": {
        "file_list": {
          "type": "DataWidget",
          "title": "Contents",
          "handler_class": "FileSystemWidgetHandler"
        }
      }
    }
  ]
}
"""


class FileSystemWidgetHandler(BaseWidgetHandler):
    def get_items(self) -> List[Path]:
        path_str = self.panel_context.get("path", str(Path.home()))
        path = Path(path_str).expanduser()

        items = []
        try:
            if path.is_dir():
                # FIX: More robust check for parent directory
                if path.parent.resolve() != path.resolve():
                    items.append(path.parent)

                dirs = sorted([p for p in path.iterdir() if p.is_dir()])
                files = sorted([p for p in path.iterdir() if p.is_file()])
                items.extend(dirs)
                items.extend(files)
        except (PermissionError, FileNotFoundError):
            pass

        return items

    def on_select(self, selected_item: Path) -> Path:
        return selected_item

    def get_item_display_name(self, item: Path) -> str:
        current_path_str = self.panel_context.get("path", str(Path.home()))
        current_path = Path(current_path_str).expanduser()
        if item.resolve() == current_path.parent.resolve():
            return "../"
        if item.is_dir():
            return f"{item.name}/"
        return item.name


class FileSystemPanelHandler(BasePanelHandler):
    def __init__(self, context: Dict[str, Any]):
        super().__init__(context)
        path_str = self.context.get("path", str(Path.home()))
        path = Path(path_str)
        self.dynamic_title = f"{path.name if path.name else '/'}"

    def on_widget_update(self, widget_id: str, value: Any) -> Optional[Tuple[str, str]]:
        super().on_widget_update(widget_id, value)

        selected_path: Path = value
        if selected_path.is_dir():
            return ("navigate_down", "file_browser")

        return None

    @property
    def form_data(self) -> Dict[str, Any]:
        selected_path = self._form_data.get("file_list")
        if selected_path:
            return {"path": str(selected_path)}
        return {}

    @form_data.setter
    def form_data(self, value):
        self._form_data = value


# ==============================================================================
# SECTION 3: Main Execution
# ==============================================================================

if __name__ == "__main__":
    config = json.loads(APP_CONFIG_JSON)
    app = PanelFlowApp(config=config)
    app.run()
