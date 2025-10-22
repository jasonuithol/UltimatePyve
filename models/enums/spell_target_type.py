from enum import Enum

class SpellTargetType(Enum):
    T_NONE         = 0
    T_DIRECTION    = 1
    T_COORD        = 2
    T_PARTY_MEMBER = 3