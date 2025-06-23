class Panel:
    """
    Base class for all panels in the CUI application.
    """

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.active = False

    def render(self):
        """
        Render the panel. This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    def handle_input(self, input_data: str):
        """
        Handle input for the panel. This method should be overridden by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")