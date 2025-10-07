from typing import Iterable

from dark_libraries.dark_math import Coord

from services.map_cache.coord_contents import CoordContents
from models.interactable               import Interactable

class MapLevelContents:

    # This cannot be set until initialisation is over.
    _out_of_bounds_tile_grass: CoordContents = None

    @classmethod
    def set_out_of_bounds_coord_content(cls, coord_contents: CoordContents):
        __class__._out_of_bounds_tile_grass = coord_contents

    def __init__(self, coord_contents: dict[Coord, CoordContents]):
        self._data = coord_contents

    def load_interactables(self, interactables: Iterable[Interactable]):
        for interactable in interactables:
            self._data[interactable.coord].set_terrain_interactable(interactable)

    def remove_interactable(self, coord: Coord):
        self._data[coord].set_terrain_interactable(None)

    def get_coord_contents(self, coord: Coord) -> CoordContents:
        return self._data.get(coord,  __class__._out_of_bounds_tile_grass)

    def __iter__(self) -> Iterable[tuple[Coord, CoordContents]]:
        return self._data.items()