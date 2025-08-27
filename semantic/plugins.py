from .history import HistorySingleton

from semantic_kernel.functions import kernel_function

class ChatHistoryPlugin:
    def __init__(self):
        self.history = HistorySingleton()

    @kernel_function(
        name="show_chat_history",
        description="Displays the chat history",
    )
    def show_chat_history(self) -> str:
        """Return the chat history as a JSON string."""
        return self.history.model_dump_json()

class LightPlugin:
    def __init__(self):
        self.data = [
            {"id": 1, "name": "Table Lamp", "is_on": False},
            {"id": 2, "name": "Porch light", "is_on": False},
            {"id": 3, "name": "Chandelier", "is_on": True},
        ]

    @kernel_function(
        name="light_list",
        description="Lists all available lights",
    )
    def light_list(self) -> list[dict]:
        """Returns a list of all lights."""
        return self.data

    @kernel_function(
        name="light_available",
        description="Search for lights if its available, will return id if its available or None if it not available",
    )
    def light_available(self, name: str) -> int | None:
        """Checks if a light is available by its name."""
        light = next((light for light in self.data if light["name"] == name), None)
        return light["id"] if light else None

    @kernel_function(
        name="light_state",
        description="Get a light state by its id",
    )
    def get_state(
        self,
        id: int
    ) -> str | None:
        """Gets a light data by its id"""
        return next((light for light in self.data if light["id"] == id), None)

    @kernel_function(
        name="change_state",
        description="Changes the state of the light by its id and desired condition",
    )
    def change_state(
        self,
        id: int,
        is_on: bool,
    ) -> str:
        """Changes the state of the light by its id and desired condition."""
        for light in self.data:
            if light["id"] == id:
                light["is_on"] = is_on
                return light
        return None