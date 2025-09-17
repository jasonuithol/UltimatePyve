from typing import Protocol

from dark_libraries.dark_math import Coord

from .interactable import Interactable

class InteractableFactory(Protocol):
    def create_interactable(self, coord: Coord) -> Interactable:
        ...

    def load_level(self, factory_registry: 'InteractableFactoryRegistry', u5map: 'U5Map', level_index: int):
        ...
