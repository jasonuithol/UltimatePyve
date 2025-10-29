from dark_libraries.logging import LoggerMixin
from data.global_registry import GlobalRegistry

from models.data_ovl import DataOVL
from models.enums.inventory_offset import InventoryOffset
from models.enums.reagents import Reagent
from models.enums.spell_target_type import SpellTargetType
from models.spell_type import SpellType

ASH = Reagent.R_ASH
MOS = Reagent.R_MOSS
GAR = Reagent.R_GARLIC
GIN = Reagent.R_GINSENG

SLK = Reagent.R_SILK
PRL = Reagent.R_PEARL
MAN = Reagent.R_MANDRAKE
NYT = Reagent.R_NIGHTSHADE

T_NON = SpellTargetType.T_NONE
T_PTY = SpellTargetType.T_PARTY_MEMBER
T_CRD = SpellTargetType.T_COORD
T_DIR = SpellTargetType.T_DIRECTION

class SpellTypeLoader(LoggerMixin):

    global_registry: GlobalRegistry

    def load(self):

        self._spell_names = {
            "".join([rune[0].lower() for rune in spell_name.split(" ")]) : spell_name
            for spell_name in DataOVL.to_strs(self.global_registry.data_ovl.spell_names) if len(spell_name) > 0
        }

        self._level = 1

        self._register_spell_type  ("an", [GIN, GAR], T_PTY) # An Nox
        self._register_spell_type  ("m" , [GIN, SLK], T_PTY) # Mani
        self._register_spell_type  ("az", [GIN, GAR], T_PTY) # An Zu

        self._register_peace_spell ("il", [ASH     ], T_NON) # In Lor
        self._register_peace_spell ("ay", [GAR, MOS], T_CRD) # An Ylem
        self._register_combat_spell("gp", [ASH, PRL], T_CRD) # Grav Por

        self._level = 2

        self._level = 5

        self._register_peace_spell("iep", [ASH, MOS], T_DIR) # In Ex Por
        self._register_combat_spell("iz", [GIN, SLK, NYT], T_DIR) # In Zu

        self.log(f"Registered {self.global_registry.spell_types} spell types")

    def _register_spell_type(self, 
                                spell_key: str, 
                                reagents: list[Reagent], 
                                target_type: SpellTargetType, 

                                peace_allowed = True, 
                                combat_allowed = True
                             ) -> SpellType:
        
        spell_name = self._spell_names[spell_key]
        premix_inventory_offset_name = f"MIXED_{spell_name.upper().replace(" ", "_")}"
        premix_inventory_offset = InventoryOffset[premix_inventory_offset_name]
        assert premix_inventory_offset, f"Could not find premix_inventory_offset for premix_inventory_offset_name={premix_inventory_offset_name}"

        spell_type = SpellType(
            spell_key = spell_key,
            name     = spell_name,
            level    = self._level,
            reagents = reagents,

            target_type = target_type,

            premix_inventory_offset = premix_inventory_offset,

            peace_allowed  = peace_allowed,
            combat_allowed = combat_allowed
        )

        self.global_registry.spell_types.register(spell_key, spell_type)

    def _register_combat_spell(self, spell_key: str, reagents: list[Reagent] ,target_type: SpellTargetType):
        self._register_spell_type(spell_key, reagents, target_type, peace_allowed = False, combat_allowed = True)

    def _register_peace_spell(self, spell_key: str, reagents: list[Reagent], target_type: SpellTargetType):
        self._register_spell_type(spell_key, reagents, target_type, peace_allowed = True, combat_allowed = False)

