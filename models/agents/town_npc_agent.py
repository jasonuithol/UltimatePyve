from dark_libraries.dark_math import Coord

from models.agents.npc_agent import NpcAgent
from models.sprite import Sprite
from models.tile   import Tile


class TownNpcAgent(NpcAgent):

    def __init__(
        self,
        coord: Coord[int],
        sprite: Sprite[Tile],
        tile_id: int,
        name: str,
        dialog_number: int,
    ):
        super().__init__()
        self._coord = coord
        self._sprite = sprite
        self._sprite_time_offset = sprite.create_random_time_offset()
        self._tile_id = tile_id
        self._name = name
        self._dialog_number = dialog_number
        # Has the Avatar been introduced to this NPC yet? Honoured by the
        # conversation renderer when it hits an IF_ELSE_KNOWS_NAME branch.
        self.has_met_avatar: bool = False

    @property
    def tile_id(self) -> int:
        return self._tile_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def current_tile(self) -> Tile:
        return self._sprite.get_current_frame(self._sprite_time_offset)

    @property
    def coord(self) -> Coord[int]:
        return self._coord

    @coord.setter
    def coord(self, value: Coord[int]):
        self._coord = value

    @property
    def dexterity(self) -> int:
        return 10

    @property
    def slept(self) -> bool:
        return False

    @property
    def dialog_number(self) -> int:
        return self._dialog_number
