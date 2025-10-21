from dark_libraries.custom_decorators import auto_init, immutable

from models.enums.equipable_item_rune_id import EquipableItemRuneId
from models.enums.equipable_item_slot import EquipableItemSlot

from models.item_type import ItemType

@immutable
@auto_init
class EquipableItemType(ItemType):
    short_name: str
    range_:     int
    defence:    int
    attack:     int
    slot:       EquipableItemSlot
    rune_id:    EquipableItemRuneId
    



