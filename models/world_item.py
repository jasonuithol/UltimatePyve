from .item_type import ItemType

class WorldItem(tuple):
    __slots__ = ()

    def __new__(
        cls,
        item_type: ItemType,
        quantity: int,
    ):
        return tuple.__new__(cls, (
            item_type,
            quantity,
        ))

    @property
    def item_type(self) -> ItemType:
        return self[0]

    @property
    def quantity(self) -> int:
        return self[1]