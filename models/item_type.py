from models.enums.inventory_offset import InventoryOffset


class ItemType(tuple):
    __slots__ = ()    

    def __new__(cls, item_id: int, inventory_offset: InventoryOffset, tile_id: int, name: str):
        return super().__new__(cls, (item_id, inventory_offset, tile_id, name))

    @property
    def item_id(self) -> int:
        return self[0]

    @property
    def inventory_offset(self) -> InventoryOffset:
        return self[1]

    @property
    def tile_id(self) -> int:
        return self[2]

    @property
    def name(self) -> str:
        return self[3]