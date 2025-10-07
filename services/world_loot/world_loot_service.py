from dark_libraries.dark_math import Coord

from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.data_ovl import DataOVL
from models.consumable_items import TileId as ConsumableTileId
from models.global_location import GlobalLocation
from services.world_loot.item_container import ItemContainer
from models.item_type import ItemType
from models.world_item import WorldItem

ItemContainerDict = dict[GlobalLocation, ItemContainer]

class WorldLootService(LoggerMixin):

    # Injectable
    dataOvl: DataOVL
    global_registry: GlobalRegistry

    def _build_item_containers(self) -> ItemContainerDict:

        TILE_ID_OFFSET = 256 # technically - the tile that is a circle of white dots on a black background.

        hidden_object_tiles     = DataOVL.to_ints(self.dataOvl.hidden_object_tiles)
        hidden_object_qualities = DataOVL.to_ints(self.dataOvl.hidden_object_qualities) # maybe "quantities" is a better name for it.
        hidden_object_locations = DataOVL.to_ints(self.dataOvl.hidden_object_locations)

        hidden_object_x_coords = DataOVL.to_ints(self.dataOvl.hidden_object_x_coords)
        hidden_object_y_coords = DataOVL.to_ints(self.dataOvl.hidden_object_y_coords)
        hidden_object_z_coords = DataOVL.to_ints(self.dataOvl.hidden_object_z_coords)

        item_containers = ItemContainerDict()

        for index in range(len(hidden_object_tiles)):
            tile_id = TILE_ID_OFFSET + hidden_object_tiles[index]

            # for tile_ids that uniquely identify the kind of item (e.g. chest, keys, gems, torches, food, gold) - this is a QUANTITY
            # for tile_ids that only identify a category of item (e.g. armour, weapon, helm, shield, ring, amulet, potion, scroll) this is an "item id"

            if tile_id in [
                ConsumableTileId.FOOD.value,  # 271
                ConsumableTileId.GEM.value,   # 264
                ConsumableTileId.TORCH.value  # 269
            ]:
                quantity = hidden_object_qualities[index]
                item_id = tile_id
            else:
                quantity = 1
                item_id  = hidden_object_qualities[index]

            location_ix = hidden_object_locations[index]
            world_coord = Coord(
                hidden_object_x_coords[index],
                hidden_object_y_coords[index]
            )
            level_index = hidden_object_z_coords[index]

            item_type: ItemType = self.global_registry.item_types.get(item_id)

#            assert item_type, f"Unregistered ItemType item_id: {item_id}"
            if item_type is None:
                self.log(f"ERROR: Skipping loot placement for unregistered item_id: {item_id}")
                continue

            world_item = WorldItem(item_type = item_type, quantity = quantity)
            global_location = GlobalLocation(location_index = location_ix, level_index = level_index, coord = world_coord)
            
            if not global_location in item_containers.keys():
                item_containers[global_location] = ItemContainer(global_location, lambda global_location: self.unregister_loot_container(global_location))
            item_containers[global_location].add(world_item)

            # This is just for logging purpii.
            map_name = self.global_registry.maps.get(global_location.location_index).location_metadata.name
            self.log(f"Loaded world loot {world_item.item_type.name} x {world_item.quantity} at {map_name}:{global_location}")

        return item_containers

    def register_loot_containers(self):
        for global_location, item_container in self._build_item_containers().items():
            self.global_registry.world_loot.register(global_location, item_container)

    def unregister_loot_container(self, global_location: GlobalLocation):
        self.global_registry.world_loot.unregister(global_location)
        self.log(f"Removed empty world loot container at {global_location}")

'''
#
# MAIN
#         
if __name__ == "__main__":

    from data.loaders.equipable_item_type_loader import EquipableItemTypeLoader

    dataOvl = DataOVL.load()

    global_registry = GlobalRegistry()
    global_registry._after_inject()

    item_type_factory = EquipableItemTypeLoader()
    item_type_factory.global_registry = global_registry
    item_type_factory.dataOvl = dataOvl
    item_type_factory.build()

    print(f"Item Types Registered: {len(global_registry.item_types)}")

    loader = WorldLootLoader()
    loader.dataOvl = dataOvl
    loader.global_registry = global_registry
    loader.register_loot_containers()

    for global_location, item_container in global_registry.world_loot.items():
        print(f"World Loot at location {global_location}:")
        item_container.open()
        while item_container.has_items():
            world_item: WorldItem = item_container.pop()
            print(f"    Item: item_id={world_item.item_type.item_id}, tile_id={world_item.item_type.tile_id}, name={world_item.item_type.name}, quantity={world_item.quantity}")

'''
