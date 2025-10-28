from typing import Iterable

from dark_libraries.dark_math import Coord

from services.map_cache.coord_contents import CoordContents
from models.interactable               import Interactable

class MapLevelContents:

    # This cannot be set until initialisation is over.
#    _out_of_bounds_tile_grass: CoordContents = None

    '''
    @classmethod
    def set_out_of_bounds_coord_content(cls, coord_contents: CoordContents):
        __class__._out_of_bounds_tile_grass = coord_contents
    '''

    def __init__(self, coord_contents_dict: dict[Coord[int], CoordContents]):
        self._coord_contents_dict = coord_contents_dict

    def load_interactables(self, interactables: Iterable[Interactable]):
        for interactable in interactables:
            self._coord_contents_dict[interactable.coord].set_terrain_interactable(interactable)

    def remove_interactable(self, coord: Coord[int]):
        self._coord_contents_dict[coord].set_terrain_interactable(None)

    def get_coord_contents(self, coord: Coord[int]) -> CoordContents:
        return self._coord_contents_dict.get(coord,  None)
#        return self._coord_contents_dict.get(coord,  __class__._out_of_bounds_tile_grass)

    def __iter__(self) -> Iterable[tuple[Coord[int], CoordContents]]:
        return self._coord_contents_dict.items().__iter__()