# file: game/usable_items.py

from enum import Enum

from .item_type import InventoryOffset, ItemType
from .item_type_registry import ItemTypeRegistry

class TileId(Enum):
    CHEST = 257
    GOLD = 258
    POTION = 259        # has subtypes
    SCROLL = 260        # has subtypes
    KEY = 263           # has subtypes
    GEM = 264
    TORCH = 269
    FOOD = 271

class ConsumableItemType(ItemType):
    pass

class Scroll(ConsumableItemType):
    spell_id: int

class Potion(ConsumableItemType):
    effect_id: int

class ConsumableItemTypeLoader:

    # Injectable
    item_type_registry: ItemTypeRegistry

    def build_consumable(self, tile_id: TileId, inventory_offset: InventoryOffset):
        item_type = ConsumableItemType(
            item_id=tile_id.value,
            inventory_offset=inventory_offset,
            tile_id=tile_id.value,
            name=tile_id.name.capitalize()
        )
        self.item_type_registry.register_item_type(item_type)
        print(f"[items] registered consumable item type: {item_type.name}")

    def register_item_types(self):
        self.build_consumable(TileId.CHEST, None)
        self.build_consumable(TileId.GOLD, InventoryOffset.GOLD)
        self.build_consumable(TileId.GEM, InventoryOffset.GEMS)
        self.build_consumable(TileId.TORCH, InventoryOffset.TORCHES)
        self.build_consumable(TileId.FOOD, InventoryOffset.FOOD)

        
