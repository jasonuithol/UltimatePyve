from typing import Dict, List, Self
from dark_libraries.custom_decorators import auto_init, immutable
from dark_libraries.dark_math import Coord
from .equipable_items import ItemType, ItemTypeRegistry
from .consumable_items import TileId as ConsumableTileId
from game.interactable import Interactable, InteractionResult
from maps.data import DataOVL

@immutable
@auto_init
class GlobalLocation:
    location_index: int
    level: int
    coord: Coord

    def __eq__(self, other: Self):
        return type(other) is GlobalLocation and self.location_index == other.location_index and self.level == other.level and self.coord == other.coord
    
    def __hash__(self):
        return hash((self.location_index, self.level, self.coord))
    
    def __str__(self):
        return f"location={self.location_index}, level={self.level}, coord={self.coord}"
    
    def __repr__(self):
        return self.__str__()

@immutable
@auto_init
class WorldItem:
    item_type: ItemType
    quantity: int

class ItemContainer(Interactable):
    def __init__(self, global_location: GlobalLocation, original_tile_id: int):
        self.world_items: List[WorldItem] = []
        self.global_location = global_location
        self.original_tile_id = original_tile_id
        self.opened = False

    def add(self, item: WorldItem):
        assert not self.opened, "Cannot add to an already opened ItemContainer."
        self.world_items.append(item)

    def open(self):
        assert not self.opened, "Cannot open an already opened ItemContainer."
        self.opened = True

    def peek(self) -> WorldItem:
        assert self.opened, "Cannot peek into an unopened ItemContainer."
        return next(self.world_items)

    def has_items(self) -> bool:
        assert self.opened, "Should not check has_items on an unopened ItemContainer."
        return len(self.world_items) > 0

    def pop(self) -> WorldItem | None:
        assert self.opened, "Cannot pop from an unopened ItemContainer."
        if self.has_items():
            return self.world_items.pop(0)
        return None

    # Interactable implementation: start
    def get_current_tile_id(self) -> int:
        if self.opened and self.has_items():
            return self.peek().item_type.tile_id
        else:
            return self.original_tile_id

    def move_into(self, actor=None) -> InteractionResult:
        if not self.opened:
            self.open()
            return InteractionResult.ok(message=InteractionResult.R_FOUND_ITEM)
        elif self.has_items():
            item = self.pop()
            return InteractionResult.ok(message=InteractionResult.R_FOUND_ITEM, payload=item)
        
        return InteractionResult.nothing()
    # Interactable implementation: end
    
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

            # even worse, what IS an item_id ?

            location_ix = hidden_object_locations[index]
            world_coord = Coord(
                hidden_object_x_coords[index],
                hidden_object_y_coords[index]
            )
            level = hidden_object_z_coords[index]

            item_type = self.item_type_registry.get_item_type(item_id)

            # TODO: probably should build consumables separately
            if item_type is None:
                item_type = ItemType(item_id = item_id, tile_id = tile_id, name = ConsumableTileId(tile_id).name)
                self.item_type_registry.register_item_type(item_type)

            world_item = WorldItem(item_type = item_type, quantity = quantity)
            global_location = GlobalLocation(location_index = location_ix, level = level, coord = world_coord)
            
            self.world_loot_registry.register_loot(world_item=world_item, global_location=global_location)

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

