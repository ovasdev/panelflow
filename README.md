PanelFlow
PanelFlow is a Python framework for building complex, multi-panel, state-driven applications. Its core philosophy is to enable developers to write their business logic once and render it anywhere—be it a Terminal UI (TUI), a web interface, or a desktop application.

PanelFlow enforces a strict separation of concerns between the application's logic and its presentation layer. This allows you to focus on what your application does, while the framework handles the complexity of UI state management, navigation, and user input.

✨ Core Concepts
Platform-Agnostic Core: The application logic (panelflow.core) is completely decoupled from the UI. It operates on abstract components and has no knowledge of how they are displayed.

Pluggable Renderers: The user interface is managed by a dedicated Renderer Layer. We provide a TUI renderer based on Textual, but you can create your own for Web (e.g., FastAPI), Desktop (e.g., PyQt), or any other environment.

Declarative UI Structure: Define the layout and structure of your application's panels and widgets in a simple application.json file. This makes your UI architecture easy to understand and maintain.

Powerful Navigation Model: PanelFlow features a unique 2D navigation system:

Horizontal Columns: A Miller-column interface that shows the user's path through a workflow (Step 1 → Step 2 → Step 3).

Vertical Stacks: Within each column, panels can be stacked, allowing for parallel, interchangeable branches of a workflow.

State-Driven & Predictable: The UI is a direct reflection of the application's state. All interactions are handled through a robust event-driven model, ensuring predictable behavior.

архитектура
PanelFlow is built on a three-tiered architecture to ensure maximum flexibility and separation of concerns.

graph TD
    subgraph "Application Layer (Your Code)"
        A[main.py] --> B["application.json (Structure)"];
        A --> C["handlers.py (Logic)"];
    end

    subgraph "Core Engine (panelflow.core)"
        CoreApp[Application Brain]
        Abstracts[Abstract Components]
        Events[Event System]
        HandlersBase[Base Handlers]
    end

    subgraph "Renderer Layer (UI)"
        TUI[TUI (Textual)]
        WEB[Web (FastAPI)]
        Desktop[Desktop (PyQt)]
    end

    A -- "1. Creates & Configures" --> CoreApp;
    CoreApp -- "Loads" --> B;
    CoreApp -- "Links with" --> C;
    A -- "2. Chooses & Runs with" --> TUI;
    
    CoreApp -- "Communicates via" --> Events;
    TUI -- "Communicates via" --> Events;

Core Engine (panelflow.core): The brain of your application. It manages state, data flows, and navigation but knows nothing about how to draw a button.

Renderer Layer (e.g., panelflow.tui): The visual representation. Its job is to render the state provided by the Core and translate user actions (keystrokes, clicks) into events for the Core.

Application Layer: This is your code. You define the UI structure in application.json, implement your business logic in handler classes, and then tie the Core and a Renderer together in a main script.

🚀 Getting Started
(This section would include installation instructions and a minimal "Hello, World" example)

1. Define your UI (application.json)
{
  "appName": "My Awesome App",
  "entryPanel": "main_panel",
  "panels": [
    {
      "id": "main_panel",
      "title": "Main Menu",
      "handler_class": "MainPanelHandler",
      "widgets": [
        {
          "id": "users_link",
          "type": "PanelLink",
          "title": "Manage Users",
          "target_panel_id": "users_panel"
        }
      ]
    },
    {
      "id": "users_panel",
      "title": "Users",
      "widgets": [
        { "id": "user_list", "type": "OptionSelect", "title": "User List" }
      ]
    }
  ]
}

2. Implement your logic (handlers.py)
from panelflow.core import BasePanelHandler

class MainPanelHandler(BasePanelHandler):
    def on_widget_update(self, widget_id, value):
        # This method is called when a widget value is submitted.
        # For a PanelLink, this happens automatically on Enter.
        # No extra logic needed for simple navigation.
        return None

3. Run the application (main.py)
from panelflow.core import Application
from panelflow.tui import TuiApplication # Choose your renderer
from . import handlers

def main():
    # 1. Map handler names from JSON to actual classes
    handler_map = {
        "MainPanelHandler": handlers.MainPanelHandler,
    }

    # 2. Create the core application
    core_app = Application(
        config_path="application.json",
        handler_map=handler_map
    )

    # 3. Create and run the UI with the chosen renderer
    TuiApplication(core_app).run()

if __name__ == "__main__":
    main()

⌨️ Navigation
Ctrl + → / Ctrl + ←: Move focus between horizontal columns.

Ctrl + ↓ / Ctrl + ↑: Navigate the vertical panel stack within a column.

Tab / Shift + Tab: Move focus between widgets on the active panel.

Enter: Submit a widget's value or activate a link.

Backspace / ←: Close the current panel and move back.

Contributing
Contributions are welcome! Please feel free to open an issue or submit a pull request.

(This section would include contribution guidelines)

License
This project is licensed under the MIT License.