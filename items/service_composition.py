# file: game/service_composition.py
from dark_libraries.service_provider import ServiceProvider

from .item_type_registry import ItemTypeRegistry
from .equipable_items import EquipableItemTypeFactory
from .world_loot import WorldLootLoader
from .world_loot import WorldLootRegistry

def compose(provider: ServiceProvider):
    provider.register(ItemTypeRegistry)
    provider.register(EquipableItemTypeFactory)
    provider.register(WorldLootRegistry)
    provider.register(WorldLootLoader)
