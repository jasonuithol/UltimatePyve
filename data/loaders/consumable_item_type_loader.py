
from dark_libraries.logging import LoggerMixin

from data.global_registry import GlobalRegistry

from models.consumable_items import ConsumableItemType, TileId
from models.enums.inventory_offset  import InventoryOffset

class ConsumableItemTypeLoader(LoggerMixin):

    # Injectable
    global_registry: GlobalRegistry

    def build_consumable(self, tile_id: TileId, inventory_offset: InventoryOffset):
        item_type = ConsumableItemType(
            item_id=tile_id.value,
            inventory_offset=inventory_offset,
            tile_id=tile_id.value,
            name=tile_id.name.capitalize()
        )
        self.global_registry.item_types.register(tile_id.value, item_type)
        self.log(f"DEBUG: Registered consumable item type: {item_type.name}")

    def register_item_types(self):
        before = len(self.global_registry.item_types)
        self.build_consumable(TileId.CHEST, None)
        self.build_consumable(TileId.GOLD,  InventoryOffset.GOLD)
        self.build_consumable(TileId.GEM,   InventoryOffset.GEMS)
        self.build_consumable(TileId.TORCH, InventoryOffset.TORCHES)
        self.build_consumable(TileId.FOOD,  InventoryOffset.FOOD)
        after = len(self.global_registry.item_types)
        self.log(f"Registered {after - before} consumable item types.")

        
