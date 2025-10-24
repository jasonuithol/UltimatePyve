from models.enums.reagents          import Reagent
from models.enums.inventory_offset  import InventoryOffset
from models.enums.spell_target_type import SpellTargetType

class SpellType(tuple):
    __slots__ = ()

    def __new__(cls, 
                spell_key: str, 
                name: str, 
                level: int, 
                reagents: list[Reagent], 
                target_type: SpellTargetType, 
                premix_inventory_offset: InventoryOffset, 
                peace_allowed: bool, 
                combat_allowed: bool
    ):      
        return super().__new__(cls, (spell_key, name, level, reagents, target_type, premix_inventory_offset, peace_allowed, combat_allowed))

    @property
    def spell_key(self) -> str:
        return self[0]

    @property
    def name(self) -> str:
        return self[1]

    @property
    def level(self) -> int:
        return self[2]

    @property
    def reagents(self) -> list[Reagent]:
        return self[3]

    @property
    def target_type(self) -> SpellTargetType:
        return self[4]

    @property
    def premix_inventory_offset(self) -> InventoryOffset:
        return self[5]

    @property
    def peace_allowed(self) -> bool:
        return self[6]

    @property
    def combat_allowed(self) -> bool:
        return self[7]

    def __eq__(self, value):
        return type(value) is SpellType and self.name == value.name
