from typing import Dict
from .world_item import WorldItem
from .global_location import GlobalLocation
from .item_container import ItemContainer
    
class WorldLootRegistry:
    
    def _after_inject(self):
        self.item_containers: Dict[GlobalLocation, ItemContainer] = {}

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