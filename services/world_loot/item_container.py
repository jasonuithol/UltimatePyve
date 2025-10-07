from typing import Callable, List
from dark_libraries.service_provider import ServiceProvider

from models.interactable import Interactable
from models.interactable import MoveIntoResult

from models.party_inventory import PartyInventory
from models.world_item import WorldItem

from services.console_service import ConsoleService

from models.global_location import GlobalLocation

class ItemContainer(Interactable):
    def __init__(self, global_location: GlobalLocation, unregister_func: Callable[[GlobalLocation], None]):
        self.world_items: List[WorldItem] = []
        self.global_location = global_location
        self.unregister_func = unregister_func
        self.opened = False

        self.console_service: ConsoleService = ServiceProvider.get_provider().resolve(ConsoleService)
        self.party_inventory: PartyInventory = ServiceProvider.get_provider().resolve(PartyInventory)

    def add(self, item: WorldItem):
        assert not self.opened, "Cannot add to an already opened ItemContainer."
        self.world_items.append(item)

    def peek(self) -> WorldItem:
        assert self.opened, "Cannot peek into an unopened ItemContainer."
        return self.world_items[0]

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
            return None

    def move_into(self) -> MoveIntoResult:
        if not self.opened:
            self.open()
            return MoveIntoResult(traversal_allowed = False, alternative_action_taken = True)
        if self.has_items():
            self.get()
            return MoveIntoResult(traversal_allowed = False, alternative_action_taken = True)
        raise ValueError("Empty container's should already have been unregistered upon emptying.")

    def open(self):
        assert not self.opened, "Cannot open an already opened ItemContainer."
        self.opened = True

    def get(self):
        item = self.pop()
        self.party_inventory.add(item.item_type.inventory_offset, item.quantity)
        self.console_service.print_ascii(item.item_type.name + " !")

        if not self.has_items():
            self.unregister_func(self.global_location.coord)
            print(f"[items] Unregistered empty item container at {self.global_location.coord}.")
    # Interactable implementation: end
