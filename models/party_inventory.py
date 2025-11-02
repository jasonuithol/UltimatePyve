from data.global_registry import GlobalRegistry
from models.enums.inventory_offset import InventoryOffset
from models.saved_game import SavedGame

U16S = [
    InventoryOffset.FOOD,
    InventoryOffset.GOLD
]

class PartyInventory:

    # Injectable
    global_registry: GlobalRegistry

    @property
    def saved_game(self) -> SavedGame:
        return self.global_registry.saved_game

    def max(self, inventory_offset: InventoryOffset) -> int:
        if inventory_offset in U16S:
            return 9999
        else:
            return 99

    def read(self, inventory_offset: InventoryOffset) -> int:
        if inventory_offset in U16S:
            return self.saved_game.read_u16(inventory_offset.value)
        else:
            return self.saved_game.read_u8(inventory_offset.value)

    def write(self, inventory_offset: InventoryOffset, value: int):

        assert value >= 0, f"Cannot have a negative amount ({value}) of {inventory_offset.name}.  Negative number's aren't invented yet."

        the_max = self.max(inventory_offset)
        assert value <= the_max, f"In this game, you can only have a maximum of {the_max} {inventory_offset.name}, not {value}"

        if inventory_offset in U16S:
            return self.saved_game.write_u16(inventory_offset.value, value)
        else:
            return self.saved_game.write_u8(inventory_offset.value, value)

    def add(self, inventory_offset: InventoryOffset, delta: int):
        current = self.read(inventory_offset)
        self.write(inventory_offset, current + delta)

    def safe_add(self, inventory_offset: InventoryOffset, delta: int):
        current = self.read(inventory_offset)
        the_max = self.max(inventory_offset)
        self.write(inventory_offset, min(the_max, current + delta))

    def has(self, inventory_offset: InventoryOffset, amount: int = 1) -> bool:
        current = self.read(inventory_offset)
        return current >= amount

    def use(self, inventory_offset: InventoryOffset, amount: int = 1) -> bool:
        if self.has(inventory_offset, amount):
            self.add(inventory_offset, -1 * amount)
            return True
        else:
            return False


