from models.enums.equipable_item_rune_id import EquipableItemRuneId
from models.enums.equipable_item_slot import EquipableItemSlot

from models.item_type import ItemType

class EquipableItemType(ItemType):
    __slots__ = ()

    def __new__(
        cls,
        item_id: int,                        #  (inherited)
        inventory_offset: int,               #  (inherited)
        tile_id: int,                        #  (inherited)
        name: str,                           #  (inherited)
        short_name: str,
        range_: int,
        defence: int,
        attack: int,
        slot: EquipableItemSlot,
        rune_id: EquipableItemRuneId,
        weight: int,
    ):
        return tuple.__new__(cls, (
            item_id,                         #  (inherited)
            inventory_offset,                #  (inherited)
            tile_id,                         #  (inherited)
            name,                            #  (inherited)
            short_name,
            range_,
            defence,
            attack,
            slot,
            rune_id,
            weight,
        ))

    # inherits item_id:int at tuple index 0

    # inherits inventory_offset:int at tuple index 1

    # inherits tile_id:int at tuple index 2

    # inherits name:str at tuple index 3

    @property
    def short_name(self) -> str:
        return self[4]

    @property
    def range_(self) -> int:
        return self[5]

    @property
    def defence(self) -> int:
        return self[6]

    @property
    def attack(self) -> int:
        return self[7]

    @property
    def slot(self) -> EquipableItemSlot:
        return self[8]

    @property
    def rune_id(self) -> EquipableItemRuneId:
        return self[9]

    @property
    def weight(self) -> int:
        return self[10]


