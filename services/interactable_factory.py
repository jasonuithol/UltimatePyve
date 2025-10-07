from typing import Protocol

from models.u5_map import U5Map

class InteractableFactory(Protocol):
    def load_level(self, u5map: U5Map, level_index: int):
        ...
