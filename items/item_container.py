from typing import List
from game.interactable import Interactable, InteractionResult
from .world_item import WorldItem
from .global_location import GlobalLocation

class ItemContainer(Interactable):
    def __init__(self, global_location: GlobalLocation, original_tile_id: int):
        self.world_items: List[WorldItem] = []
        self.global_location = global_location
        self.original_tile_id = original_tile_id
        self.opened = False

    def add(self, item: WorldItem):
        assert not self.opened, "Cannot add to an already opened ItemContainer."
        self.world_items.append(item)

    def open(self):
        assert not self.opened, "Cannot open an already opened ItemContainer."
        self.opened = True

    def peek(self) -> WorldItem:
        assert self.opened, "Cannot peek into an unopened ItemContainer."
        return next(self.world_items)

    def has_items(self) -> bool:
        assert self.opened, "Should not check has_items on an unopened ItemContainer."
        return len(self.world_items) > 0

    def pop(self) -> WorldItem | None:
        assert self.opened, "Cannot pop from an unopened ItemContainer."
        if self.has_items():
            return self.world_items.pop(0)
        return None

    # Interactable implementation: start
    def get_current_tile_id(self) -> int:
        if self.opened and self.has_items():
            return self.peek().item_type.tile_id
        else:
            return self.original_tile_id

    def move_into(self, actor=None) -> InteractionResult:
        if not self.opened:
            self.open()
            return InteractionResult.ok(message=InteractionResult.R_FOUND_ITEM)
        elif self.has_items():
            item = self.pop()
            return InteractionResult.ok(message=InteractionResult.R_FOUND_ITEM, payload=item)
        
        return InteractionResult.nothing()
    # Interactable implementation: end