from typing import Protocol
from dark_libraries.dark_math import Coord, Rect
from models.tile import Tile

'''
PARTY_MODE  = 123
COMBAT_MODE = 456

DEFAULT_TILE_IDS = {
    PARTY_MODE:    5,
    COMBAT_MODE: 255
}
'''

ViewPortData = dict[Coord[int], Tile]

class ViewPortDataProvider(Protocol):

    def set_default_tile(self, tile: Tile): ...
    def get_party_map_data(self, world_view_rect: Rect[int]) -> ViewPortData: ...
    def get_combat_map_data(self, world_view_rect: Rect[int]) -> ViewPortData: ...
