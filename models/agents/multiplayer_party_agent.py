from dark_libraries.dark_math import Coord

from dark_libraries.service_provider import ServiceProvider
from models.agents.npc_agent import NpcAgent
from models.global_location import GlobalLocation
from models.tile import Tile
from services.avatar_sprite_factory import AvatarSpriteFactory

class MultiplayerPartyAgent(NpcAgent):

    def __init__(self, name: str, dexterity: int, location: GlobalLocation, remote_multiplayer_id: str = None):

        super().__init__()

        self._name      = name
        self._dexterity = dexterity
        self._location  = location

        self._transport_mode_index = 0 # walk
        self._transport_direction  = 0 # east

        if remote_multiplayer_id is None:
            self._multiplayer_id = str(id(self))
        else:
            self._multiplayer_id = remote_multiplayer_id
    
        provider = ServiceProvider.get_provider()
        self._avatar_sprite_factory: AvatarSpriteFactory = provider.resolve(AvatarSpriteFactory)
        self._sprite_time_offset: int = None

    # NPC AGENT IMPLEMENTATION: Start
    #
    @property
    def tile_id(self) -> int:
        return 284

    @property
    def name(self) -> str:
        return self._name

    @property
    def current_tile(self) -> Tile:
        sprite = self._avatar_sprite_factory.create_player(self._transport_mode_index, self._transport_direction)
        if self._sprite_time_offset is None:
            self._sprite_time_offset = sprite.create_random_time_offset()
        return sprite.get_current_frame(self._sprite_time_offset)

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
