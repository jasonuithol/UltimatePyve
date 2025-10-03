from typing import Optional

from dark_libraries.dark_math import Coord
from maps.u5map_registry import U5MapRegistry

from .interactable import Interactable
from .interactable_factory import InteractableFactory

#
# NOTE: This is actually BOTH a factory registry AND an interactables registry.
#       The factories are all registered during main.init() and persist over the life of the game instance.
#       The interactables are created as needed per level and are cleared when transitioning to a new level/map.
#
class InteractableFactoryRegistry:

    # Injectable
    u5map_registry: U5MapRegistry

    #
    # SETUP
    #
    def _after_inject(self):

        self.location_index: int = None
        self.level_index: int = None

        self.interactables: dict[Coord, Interactable] = dict()
        self.interactable_factories: list[InteractableFactory] = list()

    def _clear_interactables(self) -> None:
        self.interactables.clear()    
        
    def register_interactable_factory(self, factory: InteractableFactory) -> None:
        self.interactable_factories.append(factory)

    def register_interactable(self, coord: Coord, interactable: Interactable):
        self.interactables[coord] = interactable

    #
    # OPERATIONAL
    #
    def unregister_interactable(self, coord: Coord):
        del self.interactables[coord]

    def load_level(self, location_index: int, level_index: int):
        self._clear_interactables()
        self.location_index = location_index
        self.level_index = level_index

        u5map = self.u5map_registry.get_map(location_index)

        for factory in self.interactable_factories:
            factory.load_level(self, u5map, level_index)

        print(f"[game.interactable] Switched to map {u5map.location_metadata.name}(location_index={u5map.location_metadata.location_index}), level {level_index}")

    def get_interactable(self, coord: Coord) -> Optional[Interactable]:

        assert len(self.interactable_factories) > 0, "no interactable factories registered before we need them."
        assert (not self.location_index is None) and (not self.level_index is None), "Need to call load_level before calling get_interactable."

        # If there's already something at the co-ordinates, return that.
        return self.interactables.get(coord, None)

    def pass_time(self):
        for interactable in self.interactables.values():
            interactable.pass_time()
