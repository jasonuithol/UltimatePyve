from dark_libraries.dark_math import Coord
from maps.data import DataOVL
from .world_item import WorldItem
from .global_location import GlobalLocation
from .equipable_items import ItemType, ItemTypeRegistry
from .consumable_items import TileId as ConsumableTileId
from .world_loot_registry import WorldLootRegistry

class WorldLootLoader:

    # Injectable
    dataOvl: DataOVL
    item_type_registry: ItemTypeRegistry
    world_loot_registry: WorldLootRegistry

    def register_loot_containers(self):

        TILE_ID_OFFSET = 256 # technically - the tile that is a circle of white dots on a black background.

        hidden_object_tiles = DataOVL.to_ints(self.dataOvl.hidden_object_tiles)
        hidden_object_qualities = DataOVL.to_ints(self.dataOvl.hidden_object_qualities) # maybe "quantities" is a better name for it.
        hidden_object_locations = DataOVL.to_ints(self.dataOvl.hidden_object_locations)

        hidden_object_x_coords = DataOVL.to_ints(self.dataOvl.hidden_object_x_coords)
        hidden_object_y_coords = DataOVL.to_ints(self.dataOvl.hidden_object_y_coords)
        hidden_object_z_coords = DataOVL.to_ints(self.dataOvl.hidden_object_z_coords)

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

            item_type = self.item_type_registry.get_item_type(item_id)

            # TODO: probably should build consumables separately
            if item_type is None:
                item_type = ItemType(item_id = item_id, tile_id = tile_id, name = ConsumableTileId(tile_id).name)
                self.item_type_registry.register_item_type(item_type)

            world_item = WorldItem(item_type = item_type, quantity = quantity)
            global_location = GlobalLocation(location_index = location_ix, level_index = level_index, coord = world_coord)
            
            self.world_loot_registry.register_loot(world_item=world_item, global_location=global_location)
            print(f"[items] Loaded world loot {world_item.item_type.name} x {world_item.quantity} at {global_location}")

#
# MAIN
#         
if __name__ == "__main__":

    from .equipable_items import EquipableItemTypeFactory

    dataOvl = DataOVL.load()

    item_type_registry = ItemTypeRegistry()
    item_type_registry._after_inject()
    item_type_factory = EquipableItemTypeFactory()

    item_type_factory.item_type_registry = item_type_registry
    item_type_factory.dataOvl = dataOvl
    item_type_factory.build()

    print(f"Item Types Registered: {len(item_type_registry.item_types)}")

    registry = WorldLootRegistry()
    registry._after_inject()

    loader = WorldLootLoader()
    loader.dataOvl = dataOvl
    loader.world_loot_registry = registry
    loader.item_type_registry = item_type_registry
    loader.register_loot_containers()

    for global_location in registry.item_containers.keys():
        print(f"World Loot at location {global_location}:")
        item_container = registry.get_loot_container(global_location)
        item_container.open()
        while item_container.has_items():
            item = item_container.pop()
            print(f"    Item: item_id={item.item_type.item_id}, tile_id={item.item_type.tile_id}, name={item.item_type.name}, quantity={item.quantity}")

