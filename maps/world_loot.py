from game.equipable_items import ItemTypeRegistry
from game.interactable.interactable import Interactable
from .data import DataOVL


class ItemContainer(Interactable):
    pass

class WorldLootLoader:

    # Injectable
    dataOvl: DataOVL
    item_type_registry: ItemTypeRegistry




