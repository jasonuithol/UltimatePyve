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

    def _after_inject(self):

        self.location_index: int = None
        self.level_index: int = None

        self.interactables: dict[Coord, Interactable] = dict()
        self.interactable_factories: dict[int, InteractableFactory] = dict()

    def _clear_interactables(self) -> None:
        self.interactables.clear()    
        
    def register_interactable_factory(self, tile_id: int, factory: InteractableFactory) -> None:
        self.interactable_factories[tile_id] = factory

    def register_interactable(self, coord: Coord, interactable: Interactable):
        self.interactables[coord] = interactable

    def load_level(self, location_index: int, level_index: int):
        self._clear_interactables()
        self.location_index = location_index
        self.level_index = level_index

        u5map = self.u5map_registry.get_map(location_index)

        for factory in self.interactable_factories.values():
            factory.load_level(self, u5map, level_index)

    # TODO: Abstract out the need for tile_id
    # This means every map load will create ALL interactables for that level,
    # instead of having ViewPort create them on the fly via tile_id.
    def get_interactable(self, tile_id: int, coord: Coord) -> Optional[Interactable]:

        assert len(self.interactable_factories) > 0, "no interactable factories registered before we need them."
        assert (not self.location_index is None) and (not self.level_index is None), "Need to call load_level before calling get_interactable."

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

    def pass_time(self):
        for interactable in self.interactables.values():
            interactable.pass_time()
