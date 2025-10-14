from enum import Enum

from models.enums.npc_tile_id import NpcTileId

class CharacterClassToTileId(Enum):
    B = NpcTileId.BARD
    F = NpcTileId.FIGHTER
    A = NpcTileId.ADVENTURER
    M = NpcTileId.MAGE
