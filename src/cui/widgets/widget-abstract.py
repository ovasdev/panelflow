class Widget():
    def __init__(self, name: str):
        self.name = name

    def render(self) -> str:
        raise NotImplementedError("Subclasses must implement the render method.")

    def get_name(self) -> str:
        return self.name

    def set_name(self, name: str):
        self.name = name