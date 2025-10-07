from dark_libraries.logging import LoggerMixin
from models.enums.inventory_offset import InventoryOffset

class PartyInventory(LoggerMixin):
    def __init__(self):
        super().__init__()
        self.inventory: dict[InventoryOffset,int] = {}

    def add(self, inventory_offset: InventoryOffset, additional_qty: int):
        current_qty = self.inventory.get(inventory_offset, 0)
        self.inventory[inventory_offset] = current_qty + additional_qty
        assert self.inventory[inventory_offset] >= 0, "Cannot have a negative amount of something, it's the dark ages."
        self.log(f"Updated party inventory: {inventory_offset.name} {current_qty} -> {current_qty + additional_qty}")

    def get_quantity(self, inventory_offset: InventoryOffset):
        return self.inventory.get(inventory_offset, 0)
    
    def __iter__(self):
        yield from self.inventory

    def __len__(self):
        return len(self.inventory)
    