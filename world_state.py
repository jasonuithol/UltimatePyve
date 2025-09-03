from typing import Dict, Optional
from dark_libraries.dark_math import Coord
from interactable import Interactable, InteractableFactory

class WorldState:
    def __init__(self):
        self.interactables: Dict[Coord, Interactable] = dict()
        self.interactable_factories: Dict[int, InteractableFactory] = dict()

    def register_interactable_factory(self, tile_id: int, factory: InteractableFactory) -> None:
        self.interactable_factories[tile_id] = factory

    def get_interactable(self, tile_id: int, coord: Coord) -> Optional[Interactable]:

        assert len(self.interactable_factories) > 0, "no interactable factories registered before we need them."

        # If there's already something at the co-ordinates, return that.
        interactable = self.interactables.get(coord, None)
        if interactable:
            return interactable
        
        # If this is a false alarm, bail.
        if not tile_id in self.interactable_factories.keys():
            return None
        
        # Create an interactable, store and return it.
        interactable = self.interactable_factories[tile_id].create_interactable(coord)
        self.interactables[coord] = interactable
        return interactable

    def clear_interactables(self) -> None:
        self.interactables.clear()
