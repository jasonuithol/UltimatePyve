from typing import Iterable

from dark_libraries.dark_math import Coord

from game.map_content.coord_contents import CoordContents
from maps.u5map import U5Map
from npc.npc_interactable import NpcInteractable
from display.tileset import TILE_ID_GRASS

from ..interactable.interactable import Interactable

class MapLevelContents:
    def __init__(self, u5_map: U5Map, level_index: int):

        self._data: dict[Coord, CoordContents] = {}
        for coord in u5_map.size_in_tiles:
            self._data[coord] = CoordContents(u5_map.get_tile_id(level_index, coord))

        self.out_of_bounds_tile_grass = CoordContents(TILE_ID_GRASS)

    def load_interactables(self, interactables: Iterable[Interactable]):
        for interactable in interactables:
            self._data[interactable.coord].set_terrain_interactable(interactable)

    def remove_interactable(self, coord: Coord):
        self._data[coord].set_terrain_interactable(None)

    def add_npc(self, coord: Coord, npc: NpcInteractable):
        self._data[coord].set_npc(npc)

    def remove_npc(self, coord: Coord):
        self._data[coord].set_npc(None)

    def move_npc(self, from_coord: Coord, to_coord: Coord):
        npc = self._data[from_coord].npc
        self._data[from_coord].set_npc(None)
        self._data[to_coord].set_npc(npc)

    def get_coord_contents(self, coord: Coord) -> CoordContents:
        return self._data.get(coord, self.out_of_bounds_tile_grass)

    def __iter__(self) -> Iterable[tuple[Coord, CoordContents]]:
        return self._data.items()