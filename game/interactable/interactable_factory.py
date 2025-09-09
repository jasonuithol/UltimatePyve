from typing import Protocol

from dark_libraries.dark_math import Coord

from .interactable import Interactable

class InteractableFactory(Protocol):
    def create_interactable(self, coord: Coord) -> Interactable:
        ...
