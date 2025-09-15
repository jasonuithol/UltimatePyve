from .item_type import ItemType

class ItemTypeRegistry:

    def _after_inject(self):
        self.item_types: dict[int, ItemType] = dict()

    def register_item_type(self, item_type: ItemType):
        self.item_types[item_type.item_id] = item_type

    def get_item_type(self, item_id: int) -> ItemType | None:
        return self.item_types.get(item_id, None)
