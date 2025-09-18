from typing import Dict

from game.interactable.interactable_factory import InteractableFactory
from game.interactable.interactable_factory_registry import InteractableFactoryRegistry
from maps.u5map import U5Map
from .world_item import WorldItem
from .global_location import GlobalLocation
from .item_container import ItemContainer
    
class WorldLootRegistry(InteractableFactory):

    # need to override the pretend Protocol constructor.
    def __init__(self):
        pass

    # Injectable    
    interactable_factory_registry: InteractableFactoryRegistry

    def _after_inject(self):
        self.item_containers: Dict[GlobalLocation, ItemContainer] = {}
        self.interactable_factory_registry.register_interactable_factory(self)

    def register_loot(self, world_item: WorldItem, global_location: GlobalLocation):
        key = global_location
        con = self.item_containers

        #
        # TODO: Use global_location to look up the actual tile_id, we're gonna need a map registry
        #
        tile_id = 1 

        if not key in con.keys():
            con[key] = ItemContainer(global_location=global_location, original_tile_id=tile_id)
        con[key].add(world_item)

    def get_loot_container(self, global_location: GlobalLocation) -> ItemContainer | None:
        return self.item_containers.get(global_location, None)
    

    # InteractableFactory implementation: start
    def load_level(self, factory_registry: 'InteractableFactoryRegistry', u5map: U5Map, level_index: int):
        for global_location in self.item_containers.keys():
            if global_location.location_index == u5map.location_metadata.location_index and global_location.level_index == level_index:
                item_container = self.item_containers[global_location]
                factory_registry.register_interactable(global_location.coord, item_container)
                print(f"[items] Registered interactable loot container at {global_location.coord}.")
    # InteractableFactory implementation: end


    