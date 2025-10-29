from typing import Protocol
from dark_libraries.dark_math import Coord, Rect
from models.tile import Tile

ViewPortData = dict[Coord[int], Tile]

class ViewPortDataProvider(Protocol):

    def set_default_tile(self, tile: Tile): ...
    def get_party_map_data(self, world_view_rect: Rect[int]) -> ViewPortData: ...
    def get_combat_map_data(self, world_view_rect: Rect[int]) -> ViewPortData: ...
