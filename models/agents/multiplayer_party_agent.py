from dark_libraries.dark_math import Coord

from models.agents.npc_agent import NpcAgent
from models.global_location import GlobalLocation
from models.sprite import Sprite
from models.tile import Tile

class MultiplayerPartyAgent(NpcAgent):

    def __init__(self, name: str, tile_id: int, sprite: Sprite, dexterity: int, location: GlobalLocation, action_points: float, remote_multiplayer_id: str = None):

        super().__init__(action_points = action_points)

        self._name      = name
        self._tile_id   = tile_id
        self._sprite_time_offset: float = None
        self.set_sprite(sprite)

        self._dexterity = dexterity
        self._location  = location

        if remote_multiplayer_id is None:
            # I'm the server, and am the authoritative source of multiplayer_id's
            self._multiplayer_id = str(id(self))
        else:
            # I'm the client, and am supplied multiplayer_id's from the server
            self._multiplayer_id = remote_multiplayer_id
   

    # NPC AGENT IMPLEMENTATION: Start
    #
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
        return self._location.coord
    
    @coord.setter
    def coord(self, value: Coord[int]):
        #
        # TODO: This may or may not require a network action
        #
        self._location = self._location.move_to_coord(value)

    @property
    def dexterity(self) -> int:
        return self._dexterity
    #
    # NPC AGENT IMPLEMENTATION: End

    @property
    def location_index(self) -> int:
        return self._location.location_index
    
    @property
    def level_index(self) -> int:
        return self._location.level_index
    
    @property
    def location_index(self) -> int:
        return self._location.location_index
    
    @property
    def location(self) -> GlobalLocation:
        return self._location
    
    @location.setter
    def location(self, value: GlobalLocation):
        self._location = value

    @property
    def multiplayer_id(self) -> str:
        return self._multiplayer_id

    def change_coord(self, coord: Coord):
        self._location = self._location.move_to_coord(coord)

    def set_sprite(self, sprite: Sprite):
        self._sprite = sprite
        if self._sprite_time_offset is None:
            self._sprite_time_offset = sprite.create_random_time_offset()
