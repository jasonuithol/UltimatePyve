from dark_libraries.dark_math import Coord

from models.global_location import GlobalLocation
from models.npc_metadata import NpcMetadata
from models.sprite import Sprite

class NpcAgent:

    def __init__(self, tile_id: int, sprite: Sprite, npc_metadata: NpcMetadata, global_location: GlobalLocation):
        self.tile_id = tile_id # ID of the first frame
        self.sprite = sprite
        self.npc_metadata = npc_metadata
        self.global_location = global_location

    def get_coord(self):
        return self.global_location.coord
    
    def move_to(self, coord: Coord):
        self.global_location.coord = coord
