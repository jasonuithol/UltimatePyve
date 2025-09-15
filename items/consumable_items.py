# file: game/usable_items.py

from enum import Enum

from items.item_type import ItemType

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


