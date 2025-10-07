from typing import Dict

from services.interactable_factory import InteractableFactory
    
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

        if not key in con.keys():
            con[key] = ItemContainer(global_location=global_location)
        con[key].add(world_item)

    def get_loot_container(self, global_location: GlobalLocation) -> ItemContainer | None:
        return self.item_containers.get(global_location, None)

    # InteractableFactory implementation: start
    def load_level(self, factory_registry: 'InteractableFactoryRegistry', u5map: U5Map, level_index: int):
        for global_location in self.item_containers.keys():
            if global_location.location_index == u5map.location_metadata.location_index and global_location.level_index == level_index:
                item_container = self.item_containers[global_location]
                factory_registry.register_interactable(global_location.coord, item_container)
                print(f"[loot] Registered interactable loot container at {global_location.coord}.")
    # InteractableFactory implementation: end


    