from typing import List
from dark_libraries.service_provider import ServiceProvider
from display.interactive_console import InteractiveConsole
from game.interactable import Interactable
from game.interactable.interactable import MoveIntoResult
from game.interactable.interactable_factory_registry import InteractableFactoryRegistry
from items.party_inventory import PartyInventory
from .world_item import WorldItem
from .global_location import GlobalLocation

class ItemContainer(Interactable):
    def __init__(self, global_location: GlobalLocation):
        self.world_items: List[WorldItem] = []
        self.global_location = global_location
        self.opened = False

        self.interactive_console: InteractiveConsole                    = ServiceProvider.get_provider().resolve(InteractiveConsole)
        self.party_inventory: PartyInventory                            = ServiceProvider.get_provider().resolve(PartyInventory)
        self.interactable_factory_registry: InteractableFactoryRegistry = ServiceProvider.get_provider().resolve(InteractableFactoryRegistry)

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
        self.interactive_console.print_ascii(item.item_type.name + " !")

        if not self.has_items():
            self.interactable_factory_registry.unregister_interactable(self.global_location.coord)
            print(f"[items] Unregistered empty item container at {self.global_location.coord}.")
    # Interactable implementation: end
