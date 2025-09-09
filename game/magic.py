# file: game/magic.py
from enum import Enum

from dark_libraries import auto_init, immutable

# spell target types.
class SpellTargetType(Enum):
    T_NONE = 0
    T_DIRECTION = 1
    T_COORD = 2
    T_PLAYER = 3

# reagents
class Reagent(Enum):
    R_ASH = "volcanic ash"
    R_SILK = "spider's silk"
    R_PEARL = "black pearl" 
    R_MOSS = "blood moss"
    R_GARLIC = "garlic"
    R_GINGER = "ginger"
    R_MANDRAKE = "mandrake"
    R_NIGHTSHADE = "nightshade"

@immutable
@auto_init
class SpellType:
    name: str
    level: int
    reagents: list[Reagent]    
    target_type: SpellTargetType

    def __eq__(self, value):
        return type(value) is SpellType and self.name == value.name

# Level 5 spells
S_MAGIC_UNLOCK = SpellType("magic unlock", 5, [Reagent.R_ASH, Reagent.R_MOSS], SpellTargetType.T_DIRECTION)
