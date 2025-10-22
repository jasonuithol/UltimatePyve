from dark_libraries.custom_decorators import auto_init, immutable
from models.enums.inventory_offset import InventoryOffset
from models.enums.reagents import Reagent
from models.enums.spell_target_type import SpellTargetType

@immutable
@auto_init
class SpellType:
    name: str
    level: int
    reagents: list[Reagent]
    target_type: SpellTargetType

    premix_inventory_offset: InventoryOffset    
    peace_allowed: bool
    combat_allowed: bool

    def __eq__(self, value):
        return type(value) is SpellType and self.name == value.name
