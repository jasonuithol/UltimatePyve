from dark_libraries.custom_decorators import auto_init, immutable
from .item_type import ItemType

@immutable
@auto_init
class WorldItem:
    item_type: ItemType
    quantity: int